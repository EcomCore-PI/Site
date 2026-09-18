import psutil as p
import mysql.connector as m
import time

def conectar():
    return m.connect(
        host="localhost",
        port=3306,
        user="aluno",
        passwd="Seg2805/rocha",
        database="ecommerce"
    )

# def temperatura_cpu():
#     try:
#         temperaturas = p.sensors_temperatures()

#         if not temperaturas:
#             return None
        
#         temperaturas_cpu = []

#         for nome, sensores in temperaturas.items():
#             for sensor in sensores:
#                 if sensor.current is not None:
#                     temperaturas_cpu.append(sensor.current)

#         if len(temperaturas_cpu) > 0:
#             return sum(temperaturas_cpu) / len(temperaturas_cpu)
        
#         return None
    
#     except Exception:
#         return None

def captura_rede():
    rede_inicial = p.net_io_counters()

    time.sleep(1)

    rede_final = p.net_io_counters()

    enviados = rede_final.bytes_sent - rede_inicial.bytes_sent
    recebidos = rede_final.bytes_recv - rede_inicial.bytes_recv

    total = enviados + recebidos

    velocidade_mbps = (total * 8) / 1000000

    return velocidade_mbps

def inserir(cpu, memoria, disco, rede):
    db = conectar()
    if db.is_connected():
        try:
            with db.cursor() as cursor:
                query = """
                    INSERT INTO captura
                    (nome, valor, unidade_de_medida, fk_servidor)
                    VALUES (%s, %s, %s, 1)
                """
                valores = [
                    ("CPU", cpu, "Porcentagem"),
                    ("Memoria", memoria, "Porcentagem"),
                    ("Disco", disco, "Porcentagem"),
                    ("Rede", rede, "Mbps")
                ]
                # if temperatura is not None:
                #     valores.append(("Temperatura CPU", temperatura, "Graus Celsius"))
                    
                cursor.executemany(query, valores)
                db.commit()
                print("Dados inseridos no banco.")

        except m.Error as erro:
            print("Deu esse erro ai:", erro)

        finally:
            db.close()

def pegar_mac():
    interfaces = p.net_if_addrs()

    for nome, enderecos in interfaces.items():
        for endereco in enderecos:
            if endereco.family == p.AF_LINK:
                return endereco.address

def discretizar_cpu(cpu):
    if cpu < 75:
        return "Estável"
    elif cpu < 85:
        return "Alerta"
    else:
        return "Perigo"

def discretizar_memoria(memoria):
    if memoria < 75:
        return "Estável"
    elif memoria < 85:
        return "Alerta"
    else:
        return "Perigo"

def discretizar_disco(disco):
    if disco < 75:
        return "Estável"
    elif disco < 85:
        return "Alerta"
    else:
        return "Perigo"

def discretizar_rede(rede):
    if rede < 50:
        return "Estável"
    elif rede < 100:
        return "Alerta"
    else:
        return "Perigo"

# def discretizar_temperatura(temperatura):
#     if temperatura is None:
#         return "Não disponível"
#     elif temperatura <= 80:
#         return "Estável"
#     elif temperatura < 90:
#         return "Alerta"
#     else:
#         return "Perigo"

def capturar():
    for i in range(5):
        cpu = p.cpu_percent(interval=1)
        memoria = p.virtual_memory().percent
        disco = p.disk_usage("C:\\").percent
        rede = captura_rede()
        # temperatura = temperatura_cpu()

        print("\n===== CAPTURA", i + 1, "=====")
        print("Código MAC:", pegar_mac())
        print("CPU:", cpu, "%", discretizar_cpu(cpu))
        print("Memória:", memoria, "%", discretizar_memoria(memoria))
        print("Disco:", disco, "%", discretizar_disco(disco))
        print("Rede:", rede, "Mbps", discretizar_rede(rede))
        
        # if temperatura is not None:
            # print("Temperatura CPU:", temperatura, "°C", discretizar_temperatura(temperatura))
        # else:
            # print("Temperatura CPU: Não disponível")

        inserir(
            cpu,
            memoria,
            disco,
            rede,
            # temperatura
        )

def selecionar(opcao):
    db = conectar()
    if db.is_connected():
        try:
            with db.cursor() as cursor:
                if opcao == 1:
                    query = """
                        SELECT id, nome, valor, unidade_de_medida, horario
                        FROM captura
                        ORDER BY id
                    """
                elif opcao == 2:
                    query = """
                        SELECT horario, valor
                        FROM captura
                        WHERE nome = 'CPU'
                        ORDER BY id
                    """
                elif opcao == 3:
                    query = """
                        SELECT horario, valor
                        FROM captura
                        WHERE nome = 'Memoria'
                        ORDER BY id
                    """
                elif opcao == 4:
                    query = """
                        SELECT horario, valor
                        FROM captura
                        WHERE nome = 'Disco'
                        ORDER BY id
                    """
                elif opcao == 5:
                    query = """
                        SELECT horario, valor
                        FROM captura
                        WHERE nome = 'Rede'
                        ORDER BY id
                    """
                # elif opcao == 6:
                #     query = """
                #         SELECT horario, valor
                #         FROM captura
                #         WHERE nome = 'Temperatura CPU'
                #         ORDER BY id
                #     """
                cursor.execute(query)
                resultado = cursor.fetchall()

                if len(resultado) == 0:
                    print("Nenhum dado encontrado.")

                else:
                    for dado in resultado:
                        print(dado)

        except m.Error as erro:
            print("Deu esse erro ai:", erro)

        finally:
            db.close()

def menu_visualizar():
    while True:
        print("""
===== MENU DE CONSULTAS =====

1 - Visualizar todos os dados
2 - Visualizar CPU
3 - Visualizar Memória
4 - Visualizar Disco
5 - Visualizar Rede
6 - Voltar
""")
        resposta = input(": ")

        if resposta.isdigit():
            resposta = int(resposta)
            
        else:
            print("Opção inválida.")
            continue
        
        if resposta >= 1 and resposta <= 5:
            selecionar(resposta)

        elif resposta == 6:
            break

        else:
            print("Opção inválida.")

        input("\nPressione ENTER para voltar ao menu...")

def atualizar():
    db = conectar()
    if db.is_connected():
        try:
            with db.cursor() as cursor:
                query = """
                    UPDATE captura
                    SET horario = NOW()
                    WHERE id IN (
                        SELECT id
                        FROM (
                            SELECT id
                            FROM captura
                            ORDER BY id DESC
                            LIMIT 5
                        ) AS ultima_captura)
                        """
                
                cursor.execute(query)
                db.commit()
                print("Última captura atualizada..")

        except m.Error as erro:
            print("Deu esse erro ai:", erro)

        finally:
            db.close()

def deletar():
    db = conectar()
    if db.is_connected():
        try:
            with db.cursor() as cursor:
                query = """
                    DELETE FROM captura
                    ORDER BY id DESC
                    LIMIT 5
                """
                cursor.execute(query)
                db.commit()
                print("Últimas 5 capturas excluídas.")

        except m.Error as erro:
            print("Deu esse erro ai:", erro)

        finally:
            db.close()

def monitoramento():
    while True:
        print("""
===== MENU PRINCIPAL =====
1 - Capturar dados
2 - Visualizar capturas
3 - Atualizar ultima captura
4 - Deletar ultima captura
5 - Sair
==========================
""")
        resposta = input(": ").lower()
        if resposta == "1" or resposta == "capturar":
            capturar()

        elif resposta == "2" or resposta == "visualizar":
            menu_visualizar()

        elif resposta == "3" or resposta == "atualizar":
            atualizar()

        elif resposta == "4" or resposta == "deletar":
            deletar()

        elif resposta == "5" or resposta == "sair":
            print("Programa encerrado.")
            break

        else:
            print("Opção inválida.")

        input("\nPressione ENTER para voltar ao menu principal...")

monitoramento()