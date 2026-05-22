import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Puxa a string completa direto do .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ Erro: A variável DATABASE_URL não foi encontrada no arquivo .env")

def get_engine():
    # pool_pre_ping garante que conexões caídas com a nuvem sejam testadas e refeitas automaticamente
    return create_engine(DATABASE_URL, pool_pre_ping=True)

# Configuração da Sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())