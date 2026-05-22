import requests
import json
import os

url_linhas = "https://mobilibus.com/api/routes"

# Parâmetros exatos extraídos do seu print bem-sucedido
parametros = {"origin": "web", "project_id": "614"}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

print("📡 Buscando a lista mestre de todas as linhas de Ribeirão Preto...")
resposta = requests.get(url_linhas, params=parametros, headers=headers)

if resposta.status_code == 200:
    dados = resposta.json()
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_salvamento = os.path.join(diretorio_atual, "lista_mestre_linhas.json")

    with open(caminho_salvamento, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

    print(f"✅ Sucesso! Lista mestre de linhas salva em: {caminho_salvamento}")

    # Validação do formato dos dados retornados
    if isinstance(dados, list):
        print(f"🚌 Total de linhas encontradas: {len(dados)}")
        print("Amostra da primeira linha encontrada:")
        print(json.dumps(dados[0], indent=2, ensure_ascii=False))
    elif isinstance(dados, dict):
        print(f"Chaves principais encontradas no dicionário: {list(dados.keys())}")
        # Caso as linhas estejam dentro de uma chave específica (ex: 'routes')
        for chave in dados.keys():
            if isinstance(dados[chave], list):
                print(
                    f"  -> A chave '{chave}' contém uma lista com {len(dados[chave])} linhas."
                )
else:
    print(f"❌ Falha ao conectar. Status Code: {resposta.status_code}")
