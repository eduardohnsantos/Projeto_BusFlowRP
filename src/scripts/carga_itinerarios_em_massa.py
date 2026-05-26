import os
import sys
import time
import requests
from sqlalchemy import text

# Garante o path do projeto
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
raiz_projeto = os.path.abspath(os.path.join(diretorio_atual, "..", ".."))
if raiz_projeto not in sys.path:
    sys.path.append(raiz_projeto)

from src.database.connection import get_engine

engine = get_engine()

# Dicionário de mapeamento: Vincula o código da linha a uma avenida real de RP
# Assim, cada ônibus ganha o seu trajeto verídico na cidade!
MAPEAMENTO_VIAS = {
    "210": "Avenida Saudade",
    "101": "Avenida Jerônimo Gonçalves",
    "001": "Avenida Presidente Vargas",
    "302": "Avenida Dom Pedro I",
    "403": "Avenida do Café",
    "504": "Avenida Francisco Junqueira",
}

def buscar_geometria_osm(nome_via):
    url_api = "https://overpass-api.de/api/interpreter"
    
    consulta_ql = f"""
    [out:json][timeout:25];
    area["name"="Ribeirão Preto"] -> .a;
    (
      way["name"="{nome_via}"](area.a);
    );
    out geom;
    """
    
    cabecalhos = {
        "User-Agent": "BusFlowRP-MassIngestion/1.0 (wagner.augusto@email.com)",
        "Accept": "application/json"
    }
    
    resposta = requests.post(url_api, data={ "data": consulta_ql }, headers=cabecalhos)
    resposta.raise_for_status()
    return resposta.json().get("elements", [])

def executar_pipeline_massa():
    print("⚡ BusFlow RP — Iniciando Pipeline de Carga em Massa (Nível Produção)...")
    
    # 1. Busca quais linhas existem no sistema
    with engine.connect() as conn:
        res_linhas = conn.execute(text("SELECT DISTINCT codigo_linha FROM malha_horaria;"))
        linhas_sistema = [row['codigo_linha'] for row in res_linhas.mappings()]
    
    if not linhas_sistema:
        print("⚠️ Nenhuma linha encontrada na tabela 'malha_horaria'. Popule-a primeiro.")
        return

    print(f"📊 Encontradas {len(linhas_sistema)} linhas na malha horária para processamento.")

    # Limpa a tabela de itinerários para reescrever com dados 100% reais
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE itinerarios_linhas;"))
    print("🧽 Tabela 'itinerarios_linhas' limpa para receber a nova carga real.")

    # 2. Loop de Processamento por Linha
    for codigo in sorted(linhas_sistema):
        # Define a via: se estiver no dicionário usa ela, senão adota a Av. Jerônimo Gonçalves como padrão (Centro)
        nome_via = MAPEAMENTO_VIAS.get(codigo, "Avenida Jerônimo Gonçalves")
        print(f"\n🔄 Processando Linha {codigo} via '{nome_via}'...")
        
        try:
            # Extração
            elementos = buscar_geometria_osm(nome_via)
            
            # Transformação
            pontos_filtrados = []
            vistos = set()
            for elem in elementos:
                for ponto in elem.get("geometry", []):
                    coord = (ponto['lat'], ponto['lon'])
                    if coord not in vistos:
                        vistos.add(coord)
                        pontos_filtrados.append(ponto)
            
            if not pontos_filtrados:
                print(f"⚠️ Nenhuma coordenada encontrada para a via da Linha {codigo}. Pulando...")
                continue
                
            # Carga
            with engine.begin() as conn:
                for idx, ponto in enumerate(pontos_filtrados, start=1):
                    query = text("""
                        INSERT INTO itinerarios_linhas (codigo_linha, sequencia, latitude, longitude, nome_ponto)
                        VALUES (:codigo, :seq, :lat, :lon, :nome);
                    """)
                    conn.execute(query, {
                        "codigo": codigo,
                        "seq": idx,
                        "lat": ponto['lat'],
                        "lon": ponto['lon'],
                        "nome": f"{nome_via} — Ponto {idx}"
                    })
            
            print(f"✅ Linha {codigo} carregada com sucesso! ({len(pontos_filtrados)} pontos no banco)")
            
            # Boas práticas: Pausa estratégica para não ser bloqueado pela API pública do OSM
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Erro ao processar a Linha {codigo}: {e}")
            time.sleep(5) # Pausa maior em caso de erro para recuperação do canal

    print("\n🚀 EXTRAÇÃO E CARGA EM MASSA CONCLUÍDAS COM SUCESSO!")

if __name__ == "__main__":
    executar_pipeline_massa()