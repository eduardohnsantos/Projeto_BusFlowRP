import pandas as pd
import json
import os

diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_json = os.path.join(diretorio_atual, "resposta_real.json")

with open(caminho_json, "r", encoding="utf-8") as f:
    dados = json.load(f)

print(f"🚌 Linha: {dados.get('shortName')} - {dados.get('longName')}\n")

tt = dados.get("timetable", {})
directions = tt.get("directions", [])

lista_horarios_final = []

# 1. Entra em cada direção (Ida / Volta / Circular)
for direction in directions:
    dir_desc = direction.get("desc", "Circular")
    services = direction.get("services", [])
    
    # 2. Entra em cada serviço (Dias Úteis, Sábado, Domingo)
    for service in services:
        # O nome do serviço geralmente indica os dias (Ex: "Uteis", "Sabado")
        serv_desc = service.get("desc") or service.get("serviceId")
        
        # Dentro do serviço, buscamos as viagens/horários (geralmente em 'trips' ou 'times')
        # Vamos tentar pegar 'trips' dentro do serviço
        serv_trips = service.get("trips", [])
        
        for trip in serv_trips:
            # Aqui dentro costuma vir o horário formatado ou uma lista de paradas
            # Vamos capturar o horário de partida principal da viagem
            horario = trip.get("time") or trip.get("departureTime") or trip.get("formattedTime")
            
            # Se vier uma lista de horários soltos em vez de objetos
            if not horario and "times" in trip:
                horarios_soltos = trip["times"]
                for h in horarios_soltos:
                    lista_horarios_final.append({
                        "linha": dados.get("shortName"),
                        "sentido": dir_desc,
                        "tipo_dia": serv_desc,
                        "horario": h
                    })
                continue

            if horario:
                lista_horarios_final.append({
                    "linha": dados.get("shortName"),
                    "sentido": dir_desc,
                    "tipo_dia": serv_desc,
                    "horario": horario
                })

# Se o mapeamento acima não encontrar nada, vamos inspecionar a estrutura de um 'service'
if not lista_horarios_final and services:
    print("--- 🔬 Inspecionando a estrutura interna de 'services' ---")
    print(json.dumps(services[0], indent=2, ensure_ascii=False))
    
if lista_horarios_final:
    df_final = pd.DataFrame(lista_horarios_final)
    print("✅ Grade de Horários Extraída com Sucesso!\n")
    print(df_final.to_string(index=False))
    
    # Salva o arquivo final estruturado
    df_final.to_csv(os.path.join(diretorio_atual, "grade_horarios_ribeirao.csv"), index=False)
    print("\n💾 Dados salvos em 'grade_horarios_ribeirao.csv'")