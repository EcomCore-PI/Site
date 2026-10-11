from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import threading
import psutil as p
import time as t
import mysql.connector

# ---------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------
# Lê as credenciais do banco do mesmo .env.dev usado pelo Node
# (Site/.env.dev). Este arquivo fica em Site/public/Monitoramento/
PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__))
CAMINHO_ENV = os.path.join(PASTA_ATUAL, "..", "..", ".env.dev")

# Intervalo entre cada gravação no banco (segundos)
INTERVALO_GRAVACAO = 5


def carregar_env(caminho):
    variaveis = {}
    try:
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, valor = linha.split("=", 1)
                variaveis[chave.strip()] = valor.strip().strip("'").strip('"')
    except FileNotFoundError:
        print(f"[ERRO] Arquivo .env não encontrado em: {os.path.abspath(caminho)}")
    return variaveis


ENV = carregar_env(CAMINHO_ENV)

CONFIG_BANCO = {
    "host": ENV.get("DB_HOST"),
    "user": ENV.get("DB_USER"),
    "password": ENV.get("DB_PASSWORD"),
    "database": ENV.get("DB_DATABASE"),
    "port": int(ENV.get("DB_PORT", 3306)),
    "connection_timeout": 10,
}

# ID do servidor (tabela `servidor`) ao qual as capturas pertencem.
# Esse id PRECISA existir na tabela servidor, senão o insert falha (FK).
# Para trocar, adicione ID_SERVIDOR=2 no .env.dev
ID_SERVIDOR = int(ENV.get("ID_SERVIDOR", 1))


def coletar_dados():

    uso_cpu = p.cpu_percent(interval=1)

    cpu_count = p.cpu_count(logical=False)

    cpu_freq = p.cpu_freq()
    frequencia = round(cpu_freq.current, 2) if cpu_freq else 0

    memoria = p.virtual_memory()

    memoria_percent = memoria.percent
    memoria_total = round(memoria.total / (1024 ** 3), 2)
    memoria_used = round(memoria.used / (1024 ** 3), 2)

    disco = p.disk_usage("/")

    disco_total = round(disco.total / (1024 ** 3), 2)
    disco_used = round(disco.used / (1024 ** 3), 2)
    disco_free = round(disco.free / (1024 ** 3), 2)
    disco_percent = disco.percent


    horario = t.localtime()
    horario_formatado = t.strftime("%H:%M:%S", horario)

    return {
        "cpu_percent": uso_cpu,
        "cpu_count": cpu_count,
        "cpu_freq": frequencia,
        "memoria_percent": memoria_percent,
        "memoria_total": memoria_total,
        "memoria_used": memoria_used,
        "disco_total": disco_total,
        "disco_used": disco_used,
        "disco_free": disco_free,
        "disco_percent": disco_percent,
        "horario_formatado": horario_formatado,
    }


# ---------------------------------------------------------------
# Gravação no banco
# ---------------------------------------------------------------
# Cadeia de tabelas: servidor -> componente -> captura -> alerta.
# componente.nome e tipo_componente.nome precisam ser iguais (é por
# eles que ligamos um ao outro). Os limites vêm da tabela metrica.
RECURSOS = (
    # (nome no banco, campo em coletar_dados, nome exibido na dashboard)
    ("CPU", "cpu_percent", "CPU"),
    ("Memoria RAM", "memoria_percent", "RAM"),
    ("Disco", "disco_percent", "Disco"),
)


def carregar_componentes(cursor):
    """Devolve {nome: (id_componente, id_tipo, id_metrica, limite_atencao, limite_critico)}."""
    cursor.execute(
        "SELECT c.nome, c.id, t.id, m.id, m.limite_atencao, m.limite_critico "
        "FROM componente c "
        "JOIN tipo_componente t ON t.nome = c.nome "
        "LEFT JOIN metrica m ON m.fk_tipo_componente = t.id AND m.ativo = 1 "
        "WHERE c.fk_servidor = %s AND c.ativo = 1",
        (ID_SERVIDOR,),
    )
    mapa = {}
    for nome, id_comp, id_tipo, id_metrica, atencao, critico in cursor.fetchall():
        mapa[nome] = (id_comp, id_tipo, id_metrica,
                      float(atencao) if atencao is not None else None,
                      float(critico) if critico is not None else None)
    faltando = [nome for nome, _, _ in RECURSOS if nome not in mapa]
    if faltando:
        raise ValueError(
            f"Servidor {ID_SERVIDOR} sem componente/tipo_componente para: {', '.join(faltando)}. "
            "Cadastre-os com o mesmo nome em componente e tipo_componente."
        )
    return mapa


def atualizar_alerta(cursor, info, valor, id_captura):
    id_comp, _, id_metrica, atencao, critico = info
    if id_metrica is None or atencao is None or critico is None:
        return  # sem metrica cadastrada para o tipo, não há o que comparar

    nivel = "critico" if valor >= critico else "atencao" if valor >= atencao else None

    cursor.execute(
        "SELECT id FROM alerta WHERE fk_componente = %s AND ativo = 1 FOR UPDATE",
        (id_comp,),
    )
    alerta = cursor.fetchone()

    if nivel is None:
        if alerta:
            cursor.execute(
                "UPDATE alerta SET ativo = 0, data_fim = CURRENT_TIMESTAMP, "
                "ultima_atualizacao = CURRENT_TIMESTAMP WHERE id = %s",
                (alerta[0],),
            )
    elif alerta:
        cursor.execute(
            "UPDATE alerta SET fk_captura = %s, fk_metrica = %s, valor_medido = %s, "
            "nivel = %s, ultima_atualizacao = CURRENT_TIMESTAMP WHERE id = %s",
            (id_captura, id_metrica, valor, nivel, alerta[0]),
        )
    else:
        cursor.execute(
            "INSERT INTO alerta (fk_captura, fk_metrica, fk_componente, valor_medido, "
            "nivel, ultima_atualizacao, ativo) "
            "VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 1)",
            (id_captura, id_metrica, id_comp, valor, nivel),
        )


def gravar_capturas(dados):
    conexao = mysql.connector.connect(**CONFIG_BANCO)
    cursor = None
    try:
        cursor = conexao.cursor()
        # Serializa as coletas do mesmo servidor até o commit, evitando que
        # dois coletores criem alertas duplicados após consultar ao mesmo tempo.
        cursor.execute("SELECT id FROM servidor WHERE id = %s FOR UPDATE", (ID_SERVIDOR,))
        if cursor.fetchone() is None:
            raise ValueError(f"Servidor {ID_SERVIDOR} não cadastrado na tabela servidor.")

        componentes = carregar_componentes(cursor)

        for nome, campo, _ in RECURSOS:
            valor = dados.get(campo)
            if not isinstance(valor, (int, float)) or not 0 <= valor <= 100:
                continue
            info = componentes[nome]
            cursor.execute(
                "INSERT INTO captura (fk_componente, fk_tipo_componente, valor, unidade_medida) "
                "VALUES (%s, %s, %s, %s)",
                (info[0], info[1], valor, "%"),
            )
            atualizar_alerta(cursor, info, valor, cursor.lastrowid)
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()


def loop_gravacao():
    while True:
        try:
            dados = coletar_dados()
            gravar_capturas(dados)
            print(f"[OK] Capturas gravadas no banco (servidor {ID_SERVIDOR}) "
                  f"às {dados['horario_formatado']}")
        except Exception as erro:
            # Imprime o motivo real para facilitar o diagnóstico
            print(f"[ERRO] Não foi possível gravar no banco: {erro}")
        t.sleep(INTERVALO_GRAVACAO)


def buscar_alertas():
    # Usa o mesmo servidor das capturas; não aceita IDs fornecidos pelo navegador.
    nomes_exibidos = {nome: exibido for nome, _, exibido in RECURSOS}
    conexao = mysql.connector.connect(**CONFIG_BANCO)
    try:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute("START TRANSACTION READ ONLY")
            cursor.execute(
                "SELECT c.nome, MAX(cap.horario) AS horario, "
                "MAX(cap.horario) >= NOW() - INTERVAL 30 SECOND AS recente "
                "FROM captura cap JOIN componente c ON c.id = cap.fk_componente "
                "WHERE c.fk_servidor = %s "
                "AND c.nome IN ('CPU', 'Memoria RAM', 'Disco') "
                "AND cap.unidade_medida = %s AND cap.valor BETWEEN 0 AND 100 "
                "GROUP BY c.nome", (ID_SERVIDOR, "%"),
            )
            leituras = cursor.fetchall()
            cursor.execute(
                "SELECT a.id, c.nome AS recurso, a.valor_medido, a.nivel, "
                "m.limite_atencao, m.limite_critico "
                "FROM alerta a "
                "JOIN componente c ON c.id = a.fk_componente "
                "JOIN metrica m ON m.id = a.fk_metrica "
                "WHERE c.fk_servidor = %s AND a.ativo = 1 "
                "ORDER BY a.valor_medido DESC, a.id ASC", (ID_SERVIDOR,),
            )
            alertas = cursor.fetchall()
            for alerta in alertas:
                # a dashboard espera os rótulos antigos
                critico = alerta["nivel"] == "critico"
                alerta["limite"] = float(alerta.pop("limite_critico" if critico else "limite_atencao"))
                alerta.pop("limite_atencao" if critico else "limite_critico")
                alerta["nivel"] = "Crítico" if critico else "Atenção"
                alerta["recurso"] = nomes_exibidos.get(alerta["recurso"], alerta["recurso"])
                alerta["valor_medido"] = float(alerta["valor_medido"])
            horarios = [leitura["horario"] for leitura in leituras if leitura["horario"]]
            return {
                "alertas": alertas,
                "horario": max(horarios).strftime("%H:%M:%S") if horarios else None,
                "incompleto": len(horarios) < 3,
                "desatualizado": len(horarios) < 3 or any(not leitura["recente"] for leitura in leituras),
            }
        finally:
            cursor.close()
    finally:
        conexao.close()

# ---------------------------------------------------------------
# Servidor HTTP (mantém o /dados que o script.js usa)
# ---------------------------------------------------------------
class Servidor(SimpleHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/alertas":
            try:
                dados = buscar_alertas()
                codigo = 200
            except mysql.connector.Error as erro:
                print(f"[ERRO] Falha na consulta de alertas (código {erro.errno})")
                dados = {"erro": "Não foi possível consultar os alertas no banco."}
                codigo = 503
            resposta = json.dumps(dados, ensure_ascii=False).encode("utf-8")
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(resposta)))
            self.end_headers()
            self.wfile.write(resposta)
            return

        if self.path == "/dados":

            dados = coletar_dados()

            resposta = json.dumps(dados).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resposta)))
            self.end_headers()

            self.wfile.write(resposta)

        else:
            super().do_GET()


if __name__ == "__main__":
    print(f"Banco: {CONFIG_BANCO['host']}:{CONFIG_BANCO['port']} / {CONFIG_BANCO['database']}")

    # Thread separada para gravar no banco sem travar o servidor HTTP
    threading.Thread(target=loop_gravacao, daemon=True).start()

    servidor = ThreadingHTTPServer(("0.0.0.0", 8000), Servidor)

    print("Servidor iniciado!")
    print("Escutando em 0.0.0.0:8000 (acesse http://IP_DA_INSTANCIA:8000)")

    servidor.serve_forever()
