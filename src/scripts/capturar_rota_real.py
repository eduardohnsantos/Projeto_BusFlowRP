import os
import sys
import requests

# Garante o path do projeto
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
raiz_projeto = os.path.abspath(os.path.join(diretorio_atual, "..", ".."))
if raiz_projeto not in sys.path:
    sys.path.append(raiz_projeto)

def extrair_coordenadas_osm():
    print("🌐 BusFlow RP — Conectando à Overpass API do OpenStreetMap...")
    
    url_api = "https://overpass-api.de/api/interpreter"
    
    consulta_ql = """
    [out:json][timeout:25];
    area["name"="Ribeirão Preto"] -> .a;
    (
      way["name"="Avenida Saudade"](area.a);
    );
    out geom;
    """
    
    # SOLUÇÃO PARA O ERRO 406: Adicionando cabeçalhos de identificação amigáveis (User-Agent)
    cabecalhos = {
        "User-Agent": "BusFlowRP-DataEngineeringProject/1.0 (wagner.augusto@email.com)",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Accept": "application/json"
    }
    
    try:
        # Envia a requisição passando também o parâmetro headers
        resposta = requests.post(url_api, data={"data": consulta_ql}, headers=cabecalhos)
        resposta.raise_for_status() 
        
        dados_json = resposta.json()
        elementos = dados_json.get("elements", [])
        
        if not elementos:
            print("⚠️ Nenhuma rua encontrada com esse nome em Ribeirão Preto.")
            return

        print(f"✅ Sucesso! Encontrados {len(elementos)} segmentos da Avenida Saudade.")
        print("\n--- 🔍 ESTRUTURA DO DADO RECEBIDO (Exemplo do Primeiro Segmento) ---")
        
        primeiro_segmento = elementos[0]
        print(f"ID do Caminho (Way): {primeiro_segmento.get('id')}")
        print(f"Tipo: {primeiro_segmento.get('type')}")
        
        geometria = primeiro_segmento.get("geometry", [])
        print(f"Quantidade de pontos geográficos neste segmento: {len(geometria)}")
        
        print("\n📍 Primeiras 5 coordenadas reais da Avenida Saudade:")
        for i, ponto in enumerate(geometria[:5]):
            print(f"  Ponto {i+1} -> Latitude: {ponto['lat']}, Longitude: {ponto['lon']}")
            
        print("\n-----------------------------------------------------------------")
        print("💡 Próximo Passo Operacional: Loopar esses pontos e gravá-los no Postgre!")

    except Exception as e:
        print(f"❌ Erro ao conectar ou processar dados da API: {e}")

if __name__ == "__main__":
    extrair_coordenadas_osm()