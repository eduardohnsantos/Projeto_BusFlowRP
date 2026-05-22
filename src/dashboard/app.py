import streamlit as st
import pandas as pd
import os
import sys

# Garante que o Python encontre a pasta 'src' para fazer o import correto do banco
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
raiz_projeto = os.path.abspath(os.path.join(diretorio_atual, "..", ".."))
if raiz_projeto not in sys.path:
    sys.path.append(raiz_projeto)

# Importa a conexão que você testou e funcionou!
from src.database.connection import get_engine

# 1. CONFIGURAÇÃO DA PÁGINA (Identidade Visual)
st.set_page_config(
    page_title="BusFlow RP - Logística e Operações",
    layout="wide",
    page_icon="🚌",
    initial_sidebar_state="expanded"
)

# Estilização CSS adaptativa (Garante visibilidade perfeita no Dark Mode)
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        h1 { color: #1F497D; font-weight: 700; }
        div[data-testid="stMetric"] { 
            background-color: rgba(128, 128, 128, 0.08); 
            padding: 15px; 
            border-radius: 10px; 
            border: 1px solid rgba(128, 128, 128, 0.2); 
        }
    </style>
""", unsafe_allow_html=True)

# 2. CAMADA DE ACESSO A DADOS (PostgreSQL via SQLAlchemy)
@st.cache_resource
def inicializar_banco():
    return get_engine()

engine = inicializar_banco()

@st.cache_data(ttl=600)  # Cache de 10 minutos para performance operacional
def carregar_e_limpar_dados():
    try:
        # Puxando a tabela que seu script de ingestão acabou de criar!
        query = "SELECT * FROM malha_horaria"
        
        # O Pandas lê a query SQL usando o motor do SQLAlchemy
        df = pd.read_sql_query(query, engine)
        
        if df.empty:
            return pd.DataFrame()
            
        # Tratamento dos dados mantendo os padrões anteriores
        df['codigo_linha'] = df['codigo_linha'].astype(str).str.zfill(3)
        df['linha_exibicao'] = df['codigo_linha'] + " — " + df['nome_linha']
        return df
    except Exception as e:
        st.error(f"❌ Erro ao ler dados do PostgreSQL: {e}")
        return pd.DataFrame()

df_linhas = carregar_e_limpar_dados()

# 3. INTERFACE PRINCIPAL & SIDEBAR
st.title("🚌 BusFlow RP")
st.caption("Plataforma de Engenharia de Dados e Monitoramento de Transporte Urbano • Ribeirão Preto")
st.write("---")

if df_linhas.empty:
    st.warning("⚠️ A tabela do banco de dados está vazia ou inacessível. Verifique suas credenciais no arquivo .env e se a tabela existe.")
else:
    lista_opcoes = sorted(df_linhas['linha_exibicao'].unique())

    with st.sidebar:
        st.markdown("### 🎛️ Painel de Controle")
        st.write("Selecione os parâmetros para atualizar a malha analítica.")
        
        with st.form(key="filtro_operacional"):
            linha_selecionada = st.selectbox("Linha Operacional:", options=lista_opcoes)
            botao_buscar = st.form_submit_button(label="⚡ Atualizar Indicadores")
            
    

    # 4. PROCESSAMENTO E EXIBIÇÃO DOS RESULTADOS
    if botao_buscar:
        codigo_solicitado = linha_selecionada.split(" — ")[0]
        df_filtrado = df_linhas[df_linhas['codigo_linha'] == codigo_solicitado].copy()
        
        nome_linha_limpo = df_filtrado['nome_linha'].iloc[0]
        tarifa_linha = df_filtrado['tarifa_r$'].iloc[0]
        total_viagens = len(df_filtrado)  
        sentidos_disponiveis = df_filtrado['sentido'].unique()
        
        # --- CAMADA VISUAL 1: KPIs Principais ---
        st.subheader(f"📊 Indicadores Planejados: Linha {codigo_solicitado}")
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric(label="🚌 Linha", value=nome_linha_limpo)
        col2.metric(label="💰 Tarifa Base", value=f"R$ {tarifa_linha:.2f}")
        col3.metric(label="🔄 Viagens / Dia", value=total_viagens)
        col4.metric(label="🗺️ Itinerários", value=f"{len(sentidos_disponiveis)} sentido(s)")
        
        st.write("---")
        
        # --- CAMADA VISUAL 2: Visão Detalhada por Abas ---
        aba_horarios, aba_analise, aba_trajeto = st.tabs([
            "🕒 Grade Horária Operacional", "📈 Análise Volumétrica", "🗺️ Cobertura Geográfica"
        ])
        
        with aba_horarios:
            st.markdown("#### 📅 Escalonamento por Tipo de Calendário")
            tipo_dia = st.radio("Calendário de Operação:", options=sorted(df_filtrado['tipo_dia'].unique()), horizontal=True)
            
            df_horarios_dia = df_filtrado[df_filtrado['tipo_dia'] == tipo_dia].copy()
            df_horarios_dia = df_horarios_dia.sort_values(by='horario_partida')
            
            df_exibicao = df_horarios_dia[['sentido', 'horario_partida', 'chegada_estimada']].rename(columns={
                'sentido': 'Sentido / Direção',
                'horario_partida': 'Horário de Saída (Partida)',
                'chegada_estimada': 'Previsão de Recolhimento'
            })
            
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
            
        with aba_analise:
            st.markdown("#### 📊 Distribuição de Viagens por Período")
            df_filtrado['hora_pura'] = pd.to_datetime(df_filtrado['horario_partida'], format='%H:%M').dt.hour
            contagem_horas = df_filtrado.groupby(['hora_pura', 'tipo_dia']).size().unstack(fill_value=0)
            st.bar_chart(contagem_horas, use_container_width=True)
            
        with aba_trajeto:
            st.info("⚡ **Próximo Milestone do Projeto:** Conectar dados de GPS em tempo real e cruzar as coordenadas com o PostgreSQL.")
            
    else:
        st.info("👈 Use o Painel de Controle à esquerda para selecionar uma linha operacional.")
        
        st.markdown("""
            ### 🏗️ Arquitetura de Dados do Projeto
            Esta aplicação faz parte do portfólio **BusFlow RP**. O ecossistema foi projetado pensando em escalabilidade:
            1. **Ingestão (Ingest):** Scripts Python coletam dados da API e salvam de forma estruturada.
            2. **Armazenamento (Storage):** Banco de dados relacional PostgreSQL gerenciado via SQLAlchemy.
            3. **Consumo (Analytics):** Painel gerencial construído em Streamlit conectado diretamente à base SQL.
        """)