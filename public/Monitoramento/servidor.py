from http.server import HTTPServer, SimpleHTTPRequestHandler
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

    bytes_recebidos = round((p.net_io_counters().bytes_recv / pow(1024, 2)), 2)
    bytes_enviados = round((p.net_io_counters().bytes_sent / pow(1024, 2)), 2)
    mbps_total = round((bytes_recebidos - bytes_enviados), 2)

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
        "bytes_recebidos": bytes_recebidos,
        "bytes_enviados": bytes_enviados,
        "mbps_total": mbps_total,
        "horario_formatado": horario_formatado,
    }


# ---------------------------------------------------------------
# Gravação no banco
# ---------------------------------------------------------------
def atualizar_alertas(cursor, dados):
    # Mesmos limites exibidos na dashboard: atenção >= 80%, crítico >= 90%.
    # Executado na transação da captura, mesmo com a dashboard fechada.
    for recurso, campo in (("CPU", "cpu_percent"), ("RAM", "memoria_percent"),
                           ("Disco", "disco_percent")):
        valor = dados.get(campo)
        if not isinstance(valor, (int, float)) or not 0 <= valor <= 100:
            continue
        if valor >= 80:
            limite, nivel = (90, "Crítico") if valor >= 90 else (80, "Atenção")
            cursor.execute(
                "INSERT INTO alerta (fk_servidor, componente, valor_medido, limite, nivel) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE valor_medido = %s, limite = %s, nivel = %s, "
                "ultima_atualizacao = CURRENT_TIMESTAMP",
                (ID_SERVIDOR, recurso, valor, limite, nivel, valor, limite, nivel),
            )
        else:
            cursor.execute(
                "UPDATE alerta SET data_fim = CURRENT_TIMESTAMP, "
                "ultima_atualizacao = CURRENT_TIMESTAMP "
                "WHERE fk_servidor = %s AND componente = %s AND ativo = 1",
                (ID_SERVIDOR, recurso),
            )


def gravar_capturas(dados):
    # (nome, valor, unidade_de_medida) -> mesmas colunas da tabela `captura`
    # Os nomes 'CPU' e 'Memoria RAM' seguem os exemplos do banco-ecommerce.sql
    capturas = [
        ("CPU", dados["cpu_percent"], "%"),
        ("Memoria RAM", dados["memoria_percent"], "%"),
        ("Disco", dados["disco_percent"], "%"),
        ("Rede Recebida", dados["bytes_recebidos"], "MB"),
        ("Rede Enviada", dados["bytes_enviados"], "MB"),
    ]

    conexao = mysql.connector.connect(**CONFIG_BANCO)
    cursor = None
    try:
        cursor = conexao.cursor()
        cursor.executemany(
            "INSERT INTO captura (nome, valor, unidade_de_medida, fk_servidor) "
            "VALUES (%s, %s, %s, %s)",
            [(nome, valor, unidade, ID_SERVIDOR) for nome, valor, unidade in capturas],
        )
        atualizar_alertas(cursor, dados)
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
    conexao = mysql.connector.connect(**CONFIG_BANCO)
    try:
        conexao.start_transaction(readonly=True)
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT nome, MAX(horario) AS horario, "
                "MAX(horario) >= NOW() - INTERVAL 30 SECOND AS recente "
                "FROM captura WHERE fk_servidor = %s "
                "AND nome IN ('CPU', 'Memoria RAM', 'Disco') "
                "AND unidade_de_medida = '%' AND valor BETWEEN 0 AND 100 "
                "GROUP BY nome", (ID_SERVIDOR,),
            )
            leituras = cursor.fetchall()
            cursor.execute(
                "SELECT id, componente AS recurso, valor_medido, limite, nivel "
                "FROM alerta WHERE fk_servidor = %s AND ativo = 1 "
                "ORDER BY valor_medido DESC, id ASC", (ID_SERVIDOR,),
            )
            alertas = cursor.fetchall()
            for alerta in alertas:
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

    servidor = HTTPServer(("localhost", 8000), Servidor)

    print("Servidor iniciado!")
    print("Acesse http://localhost:8000")

    servidor.serve_forever()
