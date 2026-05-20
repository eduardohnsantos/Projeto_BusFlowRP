import pandas as pd
import requests
import json
import os

# A URL exata que você descobriu na aba Rede!
url_api = "https://mobilibus.com/api/timetable"

# Os parâmetros que você descobriu que mapeiam Ribeirão Preto (614)
parametros = {
    "origin": "web",
    "v": "2",
    "project_id": "614",
    "route_id": "576935"
}

# Cabeçalhos padrão para o servidor saber que é uma requisição limpa
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

print("📡 Disparando requisição direta para a API da Mobilibus...")

try:
    resposta = requests.get(url_api, params=parametros, headers=headers)
    
    if resposta.status_code == 200:
        dados = resposta.json()
        print("✅ Dados recebidos com sucesso e convertidos para JSON!")
        
        # Salvando uma cópia limpa localmente de forma automática para garantir
        diretorio_atual = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(diretorio_atual, "resposta_real.json"), "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
        print("💾 Cópia de segurança salva em 'resposta_real.json'.")

        print("\n--- 🔑 Chaves Principais do JSON ---")
        if isinstance(dados, dict):
            print(list(dados.keys()))
        elif isinstance(dados, list) and len(dados) > 0:
            print("O JSON é uma lista. Chaves do primeiro item:")
            print(list(dados[0].keys()))

        print("\n--- 🐼 Processando Estrutura com Pandas ---")
        df_principal = pd.json_normalize(dados)
        print(f"Shape do DataFrame: {df_principal.shape} (Linhas, Colunas)")
        
        print("\n📋 Primeiras colunas identificadas:")
        for col in df_principal.columns.tolist()[:20]:
            print(f" - {col}")

    else:
        print(f"❌ Erro na requisição! O servidor respondeu com Status: {resposta.status_code}")

except Exception as e:
    print(f"❌ Ocorreu um erro ao tentar conectar na API: {e}")