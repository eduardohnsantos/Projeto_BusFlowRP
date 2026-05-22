import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Carrega o .env apenas localmente (na nuvem ele é ignorado)
load_dotenv()

def get_engine():
    # 1. Tenta pegar a URL completa (estratégia que usamos nos Secrets e no .env)
    database_url = os.getenv("DATABASE_URL")
    
    # Se o Streamlit injetar a URL começando com 'postgres://', corrige para 'postgresql://'
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    if database_url:
        return create_engine(database_url, pool_pre_ping=True)
        
    # 2. Fallback caso não ache a DATABASE_URL (Garante que não quebre se tiver chaves separadas)
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "busflow_rp")
    
    url_formatada = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    return create_engine(url_formatada, pool_pre_ping=True)