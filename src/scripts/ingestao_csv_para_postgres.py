import os
import sys
import pandas as pd

# Garante que o Python encontre a pasta raiz do projeto para os imports funcionarem
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
raiz_projeto = os.path.abspath(os.path.join(diretorio_atual, "..", ".."))
if raiz_projeto not in sys.path:
    sys.path.append(raiz_projeto)

# Importa a conexão que configuramos no arquivo connection.py
from src.database.connection import get_engine


def rodar_ingestao():
    print("⏳ Iniciando o processo de ingestão de dados...")

    # 1. Localiza o arquivo CSV original dentro da nova pasta data/processed/
    caminho_csv = os.path.join(
        raiz_projeto, "data", "processed", "malha_horaria_completa_rp.csv"
    )

    if not os.path.exists(caminho_csv):
        print(f"❌ Erro: Arquivo CSV não encontrado em: {caminho_csv}")
        return

    # 2. Carrega o CSV para a memória usando o Pandas
    print("📖 Lendo o arquivo CSV...")
    df = pd.read_csv(caminho_csv)

    # 3. Conecta ao banco de dados usando o nosso Engine do SQLAlchemy
    print("🔌 Conectando ao PostgreSQL...")
    engine = get_engine()

    # 4. A MÁGICA ACONTECE AQUI:
    # O método .to_sql do Pandas cria a tabela e insere todas as linhas automaticamente!
    print("🚀 Enviando dados para o banco de dados (Tabela: 'malha_horaria')...")
    df.to_sql(
        name="malha_horaria",  # Nome exato da tabela no banco
        con=engine,  # O motor de conexão do SQLAlchemy
        if_exists="replace",  # Se a tabela já existir, ele apaga e cria uma nova atualizada
        index=False,  # Não salva o índice do Pandas como uma coluna no banco
    )

    print("✅ Ingestão concluída com sucesso! Os dados já estão no PostgreSQL.")


if __name__ == "__main__":
    rodar_ingestao()
