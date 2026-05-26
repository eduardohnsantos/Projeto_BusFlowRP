import os
import sys
import time
import random
import math
from datetime import datetime
from sqlalchemy import text

# Garante o path do projeto
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
raiz_projeto = os.path.abspath(os.path.join(diretorio_atual, "..", ".."))
if raiz_projeto not in sys.path:
    sys.path.append(raiz_projeto)

from src.database.connection import get_engine

engine = get_engine()

# Coordenadas centrais aproximadas de Ribeirão Preto para nossa simulação
LAT_CENTRO = -21.1775
LON_CENTRO = -47.8103
RAIO_LIMITE_KM = 4.5       # Raio máximo permitido da cerca virtual (Geofence)
DISTANCIA_MINIMA_KM = 0.03  # Filtro: Só grava histórico se andar mais de 100 metros (0.1 km)

def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula a distância em quilômetros entre dois pontos geográficos
    usando a fórmula de Haversine.
    """
    R = 6371.0  # Raio da Terra em quilômetros
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def inicializar_simulacao():
    print("🚀 BusFlow RP — Iniciando Simulador com Filtro de Ruído GPS...")
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DISTINCT codigo_linha, nome_linha FROM malha_horaria;"))
        linhas = [dict(row) for row in result.mappings()]
    
    if not linhas:
        print("⚠️ Nenhuma linha encontrada na tabela malha_horaria. Abortando simulador.")
        return

    print(f"🚌 {len(linhas)} linhas carregadas para simulação de GPS.")
    
    # Inicializa posições e guarda o último ponto gravado no histórico
    posicoes = {}
    for l in linhas:
        lat_inicial = LAT_CENTRO + random.uniform(-0.02, 0.02)
        lon_inicial = LON_CENTRO + random.uniform(-0.02, 0.02)
        
        posicoes[l['codigo_linha']] = {
            "nome_linha": l['nome_linha'],
            "lat": lat_inicial,
            "lon": lon_inicial,
            "u_lat_hist": lat_inicial,  # Última latitude salva no histórico
            "u_lon_hist": lon_inicial   # Última longitude salva no histórico
        }

    while True:
        try:
            horario_atual = datetime.now()
            
            with engine.begin() as conn:
                for cod_linha, dados in posicoes.items():
                    # Simula o movimento (ônibus andando)
                    dados["lat"] += random.uniform(-0.0006, 0.0006)
                    dados["lon"] += random.uniform(-0.0006, 0.0006)
                    
                    # Cerca Virtual: Distância até o centro
                    distancia_centro = calcular_distancia_haversine(
                        LAT_CENTRO, LON_CENTRO, dados["lat"], dados["lon"]
                    )
                    status_rota = "⚠️ Fora de Rota" if distancia_centro > RAIO_LIMITE_KM else "No Itinerário"
                    
                    # 1. QUERY REAL-TIME (Sempre atualiza para manter o ponto vivo na tela)
                    query_live = text("""
                        INSERT INTO telemetria_onibus (codigo_linha, nome_linha, latitude, longitude, ultima_atualizacao, status_rota)
                        VALUES (:codigo, :nome, :lat, :lon, :now, :status)
                        ON CONFLICT (codigo_linha) 
                        DO UPDATE SET 
                            latitude = EXCLUDED.latitude,
                            longitude = EXCLUDED.longitude,
                            ultima_atualizacao = EXCLUDED.ultima_atualizacao,
                            status_rota = EXCLUDED.status_rota;
                    """)
                    
                    conn.execute(query_live, {
                        "codigo": cod_linha,
                        "nome": dados["nome_linha"],
                        "lat": dados["lat"],
                        "lon": dados["lon"],
                        "now": horario_atual,
                        "status": status_rota
                    })
                    
                    # Filtro de Deslocamento Mínimo: Distância desde o último ponto do histórico
                    distancia_desde_ultimo_ponto = calcular_distancia_haversine(
                        dados["u_lat_hist"], dados["u_lon_hist"], dados["lat"], dados["lon"]
                    )
                    
                    # 2. QUERY HISTÓRICA (Só insere se o ônibus realmente se deslocou)
                    if distancia_desde_ultimo_ponto >= DISTANCIA_MINIMA_KM:
                        query_historico = text("""
                            INSERT INTO historico_telemetria (codigo_linha, latitude, longitude, ultima_atualizacao)
                            VALUES (:codigo, :lat, :lon, :now);
                        """)
                        
                        conn.execute(query_historico, {
                            "codigo": cod_linha,
                            "lat": dados["lat"],
                            "lon": dados["lon"],
                            "now": horario_atual
                        })
                        
                        # Atualiza a memória com o novo ponto de referência
                        dados["u_lat_hist"] = dados["lat"]
                        dados["u_lon_hist"] = dados["lon"]
            
            print(f"📡 [{horario_atual.strftime('%H:%M:%S')}] Telemetria atualizada. Filtro de ruído aplicado.")
            time.sleep(4)
            
        except KeyboardInterrupt:
            print("\n🛑 Simulador encerrado pelo usuário.")
            break
        except Exception as e:
            print(f"❌ Erro no simulador: {e}")
            time.sleep(5)

if __name__ == "__main__":
    inicializar_simulacao()