import os
import sys
import time
import random
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

def inicializar_simulacao():
    print("🚀 BusFlow RP — Iniciando Simulador de Telemetria GPS...")
    
    # Busca as linhas que existem no seu banco para simular dados reais delas
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DISTINCT codigo_linha, nome_linha FROM malha_horaria;"))
        linhas = [dict(row) for row in result.mappings()]
    
    if not linhas:
        print("⚠️ Nenhuma linha encontrada na tabela malha_horaria. Abortando simulador.")
        return

    print(f"🚌 {len(linhas)} linhas carregadas para simulação de GPS.")
    
    # Cria uma posição inicial aleatória em Ribeirão Preto para cada linha
    posicoes = {}
    for l in linhas:
        posicoes[l['codigo_linha']] = {
            "nome_linha": l['nome_linha'],
            "lat": LAT_CENTRO + random.uniform(-0.04, 0.04),
            "lon": LON_CENTRO + random.uniform(-0.04, 0.04)
        }

    # Loop infinito simulando o movimento dos ônibus pelas ruas
    while True:
        try:
            with engine.begin() as conn:
                for cod_linha, dados in posicoes.items():
                    # Simula um pequeno movimento (o ônibus andando)
                    dados["lat"] += random.uniform(-0.0005, 0.0005)
                    dados["lon"] += random.uniform(-0.0005, 0.0005)
                    
                    # Query SQL estilo UPSERT (Insere se não existir, atualiza se já existir)
                    query = text("""
                        INSERT INTO telemetria_onibus (codigo_linha, nome_linha, latitude, longitude, ultima_atualizacao)
                        VALUES (:codigo, :nome, :lat, :lon, :now)
                        ON CONFLICT (codigo_linha) 
                        DO UPDATE SET 
                            latitude = EXCLUDED.latitude,
                            longitude = EXCLUDED.longitude,
                            ultima_atualizacao = EXCLUDED.ultima_atualizacao;
                    """)
                    
                    conn.execute(query, {
                        "codigo": cod_linha,
                        "nome": dados["nome_linha"],
                        "lat": dados["lat"],
                        "lon": dados["lon"],
                        "now": datetime.now()
                    })
            
            print(f"📡 [{datetime.now().strftime('%H:%M:%S')}] GPS de todas as linhas atualizado no PostgreSQL.")
            time.sleep(4) # Espera 4 segundos para a próxima transmissão de GPS
            
        except KeyboardInterrupt:
            print("\n🛑 Simulador encerrado pelo usuário.")
            break
        except Exception as e:
            print(f"❌ Erro no simulador: {e}")
            time.sleep(5)

if __name__ == "__main__":
    inicializar_simulacao()