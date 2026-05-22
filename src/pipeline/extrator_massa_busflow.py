import pandas as pd
import requests
import json
import time
import os

diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_mestre = os.path.join(diretorio_atual, "lista_mestre_linhas.json")

# Garante que o arquivo do passo anterior existe
if not os.path.exists(caminho_mestre):
    raise FileNotFoundError("❌ Execute primeiro o script 'listar_linhas.py' para gerar a lista mestre!")

with open(caminho_mestre, "r", encoding="utf-8") as f:
    dados_mestre = json.load(f)

# Como validamos que veio uma lista direta do endpoint, usamos ela
linhas = dados_mestre if isinstance(dados_mestre, list) else dados_mestre.get("routes", [])

url_timetable = "https://mobilibus.com/api/timetable"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

todos_os_horarios = []
linhas_com_erro = []

print(f"🚀 Iniciando extração em massa de {len(linhas)} linhas de Ribeirão Preto...\n")

for idx, linha in enumerate(linhas, 1):
    route_id = linha.get("routeId")
    short_name = linha.get("shortName")
    long_name = linha.get("longName")
    
    if not route_id:
        continue
        
    print(f"[{idx}/{len(linhas)}] 🚌 Baixando horários da linha {short_name} - {long_name} (ID: {route_id})...")
    
    parametros = {
        "origin": "web",
        "v": "2",
        "project_id": "614",
        "route_id": str(route_id)
    }
    
    try:
        resposta = requests.get(url_timetable, params=parametros, headers=headers)
        
        if resposta.status_code == 200:
            dados_linha = resposta.json()
            tarifa = dados_linha.get('price', 0)
            
            tt = dados_linha.get("timetable", {})
            directions = tt.get("directions", [])
            
            # Varre a estrutura exata que descobrimos no teste anterior
            for direction in directions:
                dir_desc = direction.get("desc", "Circular")
                for service in direction.get("services", []):
                    tipo_dia = service.get("desc", "").strip()
                    for dep_info in service.get("departures", []):
                        
                        todos_os_horarios.append({
                            "id_rota": route_id,
                            "codigo_linha": short_name,
                            "nome_linha": long_name,
                            "tarifa_r$": tarifa,
                            "sentido": dir_desc,
                            "tipo_dia": tipo_dia,
                            "horario_partida": dep_info.get("dep"),
                            "chegada_estimada": dep_info.get("arr")
                        })
        else:
            print(f"⚠️ Servidor respondeu com status {resposta.status_code} para a linha {short_name}")
            linhas_com_erro.append(short_name)
            
        # ⚠️ Pausa de 1.5 segundos para o servidor não bloquear o seu IP por excesso de requisições
        time.sleep(1.5)
        
    except Exception as e:
        print(f"❌ Erro na linha {short_name}: {e}")
        linhas_com_erro.append(short_name)

# Consolidação e exportação usando Pandas
if todos_os_horarios:
    df_completo = pd.DataFrame(todos_os_horarios)
    
    caminho_csv_final = os.path.join(diretorio_atual, "malha_horaria_completa_rp.csv")
    df_completo.to_csv(caminho_csv_final, index=False, encoding="utf-8")
    
    print("\n" + "="*50)
    print("🏆 PIPELINE CONCLUÍDO COM SUCESSO!")
    print(f"📊 Total de horários estruturados (toda a cidade): {len(df_completo)}")
    print(f"💾 Base de dados unificada salva em: {caminho_csv_final}")
    if linhas_com_erro:
        print(f"⚠️ Linhas que falharam ou vieram vazias: {linhas_com_erro}")
    print("="*50)
else:
    print("\n❌ Nenhuma informação foi extraída. Verifique os logs.")
    