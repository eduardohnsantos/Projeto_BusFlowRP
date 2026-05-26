import os
import sys
import random
import math  # Corrigido: Importação explícita adicionada
from sqlalchemy import text

# Garante o path do projeto
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
raiz_projeto = os.path.abspath(os.path.join(diretorio_atual, "..", ".."))
if raiz_projeto not in sys.path:
    sys.path.append(raiz_projeto)

from src.database.connection import get_engine

engine = get_engine()

# Centro de Ribeirão Preto como base
LAT_CENTRO = -21.1775
LON_CENTRO = -47.8103

def popular_restante_itinerarios():
    print("⚡ BusFlow RP — Iniciando Autopopulação de Itinerários...")
    
    with engine.begin() as conn:
        # GARANTIA: Cria a tabela de forma automatizada caso ela não exista
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS itinerarios_linhas (
                id SERIAL PRIMARY KEY,
                codigo_linha VARCHAR(10),
                sequencia INT,
                latitude DECIMAL(10, 8),
                longitude DECIMAL(10, 8),
                nome_ponto VARCHAR(100)
            );
        """))
        print("🗄️ Verificação de tabela concluída (itinerarios_linhas pronta).")

    # Abertura de conexão de leitura
    with engine.connect() as conn:
        # 1. Busca todas as linhas cadastradas na malha horária
        res_linhas = conn.execute(text("SELECT DISTINCT codigo_linha, nome_linha FROM malha_horaria;"))
        linhas = [dict(row) for row in res_linhas.mappings()]
        
        # 2. Descobre quais linhas JÁ POSSUEM itinerário para não duplicar
        res_existentes = conn.execute(text("SELECT DISTINCT codigo_linha FROM itinerarios_linhas;"))
        linhas_existentes = {row['codigo_linha'] for row in res_existentes.mappings()}

    # Filtra apenas o que precisa ser gerado
    linhas_para_gerar = [l for l in linhas if l['codigo_linha'] not in linhas_existentes]

    if not linhas_para_gerar:
        print("✨ Todas as linhas já possuem itinerários cadastrados!")
        return

    print(f"🤖 Encontradas {len(linhas_para_gerar)} linhas sem itinerário. Gerando trajetos sintéticos...")

    with engine.begin() as conn:
        for linha in sorted(linhas_para_gerar, key=lambda x: x['codigo_linha']):
            cod = linha['codigo_linha']
            nome = linha['nome_linha']
            
            # Cria um vetor de direção único para cada linha se espalhar pelo mapa
            angulo = random.uniform(0, 2 * 3.14159)
            passo_lat = math.sin(angulo) * 0.004
            passo_lon = math.cos(angulo) * 0.004
            
            # Gera 6 pontos sequenciais lineares para a linha
            for seq in range(1, 7):
                lat_ponto = LAT_CENTRO + (passo_lat * seq)
                lon_ponto = LON_CENTRO + (passo_lon * seq)
                
                query = text("""
                    INSERT INTO itinerarios_linhas (codigo_linha, sequencia, latitude, longitude, nome_ponto)
                    VALUES (:codigo, :seq, :lat, :lon, :nome_ponto);
                """)
                
                conn.execute(query, {
                    "codigo": cod,
                    "seq": seq,
                    "lat": lat_ponto,
                    "lon": lon_ponto,
                    "nome_ponto": f"Ponto {seq} - Rota {nome}"
                })
                
            print(f"✅ Itinerário gerado com sucesso para a Linha {cod} — {nome}")

    print("🚀 População em massa concluída com sucesso!")

if __name__ == "__main__":
    popular_restante_itinerarios()