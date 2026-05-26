import os
import sys
import requests
from sqlalchemy import text

# Garante o path do projeto
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
raiz_projeto = os.path.abspath(os.path.join(diretorio_atual, "..", ".."))
if raiz_projeto not in sys.path:
    sys.path.append(raiz_projeto)

from src.database.connection import get_engine

engine = get_engine()

def carga_itinerario_real_saudade():
    print("🚀 BusFlow RP — Iniciando Pipeline de Carga Real (Overpass -> Postgres)...")
    
    url_api = "https://overpass-api.de/api/interpreter"
    
    # Consulta para buscar a Avenida Saudade
    consulta_ql = """
    [out:json][timeout:25];
    area["name"="Ribeirão Preto"] -> .a;
    (
      way["name"="Avenida Saudade"](area.a);
    );
    out geom;
    """
    
    cabecalhos = {
        "User-Agent": "BusFlowRP-DataEngineeringProject/1.0 (wagner.augusto@email.com)",
        "Accept": "application/json"
    }
    
    try:
        # 1. Extração (Extract)
        resposta = requests.post(url_api, data={"data": consulta_ql}, headers=cabecalhos)
        resposta.raise_for_status()
        elementos = resposta.json().get("elements", [])
        
        if not elementos:
            print("⚠️ Nenhuma geometria encontrada para a Avenida Saudade.")
            return

        print(f"📦 Dados extraídos. Processando {len(elementos)} segmentos de via...")

        # 2. Transformação (Transform)
        # Vamos extrair os pontos lat/lon e garantir que sejam únicos e sequenciais
        pontos_filtrados = []
        vistos = set() # Evita duplicar coordenadas nos cruzamentos de segmentos
        
        for elemento in elementos:
            geometria = elemento.get("geometry", [])
            for ponto in geometria:
                coord = (ponto['lat'], ponto['lon'])
                if coord not in vistos:
                    vistos.add(coord)
                    pontos_filtrados.append(ponto)

        if not pontos_filtrados:
            print("⚠️ Nenhum ponto geográfico válido após a filtragem.")
            return

        print(f"🧹 Transformação concluída: {len(pontos_filtrados)} pontos geográficos únicos gerados.")

        # 3. Carga (Load)
        # Vamos salvar esses pontos na linha 210, ordenando por uma sequência incremental
        codigo_alvo = "210"
        
        with engine.begin() as conn:
            # Limpa o itinerário de teste anterior apenas para a linha 210
            conn.execute(
                text("DELETE FROM itinerarios_linhas WHERE codigo_linha = :codigo;"),
                {"codigo": codigo_alvo}
            )
            print(f"🧽 Antigo itinerário de teste da Linha {codigo_alvo} removido.")

            # Loop para inserção em massa dos pontos reais das ruas
            for idx, ponto in enumerate(pontos_filtrados, start=1):
                query = text("""
                    INSERT INTO itinerarios_linhas (codigo_linha, sequencia, latitude, longitude, nome_ponto)
                    VALUES (:codigo, :seq, :lat, :lon, :nome);
                """)
                conn.execute(query, {
                    "codigo": codigo_alvo,
                    "seq": idx,
                    "lat": ponto['lat'],
                    "lon": ponto['lon'],
                    "nome": f"Av. Saudade — Trecho Real {idx}"
                })
                
        print(f"✨ Sucesso Absoluto! {len(pontos_filtrados)} pontos reais injetados na Linha {codigo_alvo}.")

    except Exception as e:
        print(f"❌ Falha crítica no pipeline de ETL: {e}")

if __name__ == "__main__":
    carga_itinerario_real_saudade()