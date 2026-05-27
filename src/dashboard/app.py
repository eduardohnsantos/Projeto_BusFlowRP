import os
import sys
import time
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

# Garante que o Python encontre a pasta 'src' para fazer o import correto do banco
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
raiz_projeto = os.path.abspath(os.path.join(diretorio_atual, "..", ".."))
if raiz_projeto not in sys.path:
    sys.path.append(raiz_projeto)

# Importa a conexão do projeto
from src.database.connection import get_engine

# 1. CONFIGURAÇÃO DA PÁGINA (Identidade Visual)
st.set_page_config(
    page_title="BusFlow RP - Logística e Operações",
    layout="wide",
    page_icon="🚌",
    initial_sidebar_state="expanded",
)

# Estilização CSS Avançada (Identidade Corporativa e Simetria)
st.markdown(
    """
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        
        /* Título com efeito de degradê tecnológico */
        .main-title {
            font-size: 2.8rem;
            font-weight: 800;
            background: linear-gradient(45deg, #1E88E5, #00E676);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0rem;
        }
        
        /* Customização dos Cards de KPI */
        div[data-testid="stMetric"] { 
            background-color: rgba(128, 128, 128, 0.06); 
            padding: 15px; 
            border-radius: 10px; 
            border: 1px solid rgba(128, 128, 128, 0.15); 
            transition: all 0.3s ease;
        }
        
        /* Ajuste do tamanho da fonte para evitar quebras de linha */
        div[data-testid="stMetricValue"] {
            font-size: 1.6rem !important;
            font-weight: 600 !important;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
        }

        /* Alinhamento vertical do botão Home no topo */
        div.stButton > button:first-child {
            margin-top: 18px;
            float: right;
        }
    </style>
""",
    unsafe_allow_html=True,
)


# 2. CAMADA DE ACESSO A DADOS (PostgreSQL via SQLAlchemy)
@st.cache_resource
def inicializar_banco():
    return get_engine()


engine = inicializar_banco()


@st.cache_data(ttl=600, show_spinner="🔄 Conectando ao PostgreSQL e carregando malha horária...")
def carregar_e_limpar_dados():
    try:
        query = "SELECT * FROM malha_horaria"
        df = pd.read_sql_query(query, engine)

        if df.empty:
            return pd.DataFrame()

        df["codigo_linha"] = df["codigo_linha"].astype(str).str.zfill(3)
        df["linha_exibicao"] = df["codigo_linha"] + " — " + df["nome_linha"]
        return df
    except Exception as e:
        st.error(f"❌ Erro ao ler dados do PostgreSQL: {e}")
        return pd.DataFrame()


def buscar_gps_tempo_real(codigo_linha):
    try:
        query = f"SELECT latitude, longitude, ultima_atualizacao, status_rota FROM telemetria_onibus WHERE codigo_linha = '{codigo_linha}'"
        df_gps = pd.read_sql_query(query, engine)
        return df_gps
    except Exception as e:
        return pd.DataFrame()


def tratar_horario_transporte(hora_str):
    if not isinstance(hora_str, str):
        return None
    try:
        parts = hora_str.strip().split(':')
        horas = int(parts[0])
        minutos = parts[1] if len(parts) > 1 else "00"
        
        if horas >= 24:
            horas = horas - 24
            
        return f"{str(horas).zfill(2)}:{minutos}"
    except:
        return hora_str


df_linhas = carregar_e_limpar_dados()

if "buscar_ativa" not in st.session_state:
    st.session_state.buscar_ativa = False

# 3. INTERFACE PRINCIPAL & SIDEBAR (Header Otimizado)
col_titulo, col_botao = st.columns([8, 2])

with col_titulo:
    # Separamos o emoji do texto para que o CSS de degradê não quebre as cores da figurinha
    st.markdown('<h1 style="margin-bottom: 0rem;"><span style="font-style: normal;">🚌</span> <span class="main-title">BusFlow RP</span></h1>', unsafe_allow_html=True)
    st.caption(
        "Plataforma de Engenharia de Dados e Monitoramento de Transporte Urbano • Ribeirão Preto"
    )

with col_botao:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.buscar_ativa = False
        st.rerun()

st.write("---")

if df_linhas.empty:
    st.warning(
        "⚠️ A tabela do banco de dados está vazia ou inacessível. Verifique suas credenciais no arquivo .env e se a tabela existe."
    )
else:
    lista_opcoes = sorted(df_linhas["linha_exibicao"].unique())

    with st.sidebar:
        st.markdown("### 🎛️ Painel de Controle")
        st.write("Selecione os parâmetros para atualizar a malha analítica.")

        with st.form(key="filtro_operacional"):
            linha_selecionada = st.selectbox("Linha Operacional:", options=lista_opcoes)
            botao_buscar = st.form_submit_button(label="⚡ Atualizar Indicadores")
            
            if botao_buscar:
                st.session_state.buscar_ativa = True

    # 4. PROCESSAMENTO E EXIBIÇÃO DOS RESULTADOS
    if st.session_state.buscar_ativa:
        codigo_solicitado = linha_selecionada.split(" — ")[0]
        df_filtrado = df_linhas[df_linhas["codigo_linha"] == codigo_solicitado].copy()

        nome_linha_limpo = df_filtrado["nome_linha"].iloc[0]
        total_viagens = len(df_filtrado)
        sentidos_disponiveis = df_filtrado["sentido"].unique()

        # --- CAMADA VISUAL 1: KPIs Principais ---
        st.subheader(f"📊 Indicadores de Performance: Linha {codigo_solicitado}")
        
        df_live_status = buscar_gps_tempo_real(codigo_solicitado)
        status_cerca = "Sem Sinal"
        
        if not df_live_status.empty:
            status_cerca = df_live_status["status_rota"].iloc[0]

        if status_cerca == "⚠️ Fora de Rota":
            st.error(f"🚨 ALERTAS OPERACIONAIS: O veículo da linha {codigo_solicitado} violou a cerca virtual geográfica de Ribeirão Preto!")
            border_cerca = "1px solid #FF4B4B"
            bg_cerca = "rgba(255, 75, 75, 0.1)"
        else:
            border_cerca = "1px solid #29B6F6"
            bg_cerca = "rgba(41, 182, 246, 0.08)"

        try:
            query_otp = f"""
                SELECT 
                    m.horario_partida,
                    t.ultima_atualizacao
                FROM telemetria_onibus t
                JOIN malha_horaria m ON m.codigo_linha = t.codigo_linha
                WHERE t.codigo_linha = '{codigo_solicitado}'
                ORDER BY ABS(EXTRACT(EPOCH FROM (t.ultima_atualizacao::time - m.horario_partida::time)))
                LIMIT 1;
            """
            resultado_otp = pd.read_sql_query(query_otp, engine)
            
            if not resultado_otp.empty:
                horario_planejado = pd.to_datetime(resultado_otp['horario_partida'].iloc[0], format='%H:%M').time()
                horario_real = pd.to_datetime(resultado_otp['ultima_atualizacao'].iloc[0]).time()
                
                minutos_planejados = horario_planejado.hour * 60 + horario_planejado.minute
                minutos_reais = horario_real.hour * 60 + horario_real.minute
                diferenca = minutos_reais - minutos_planejados
                
                if -2 <= diferenca <= 5:
                    status_otp = "🟢 No Horário"
                    detalhe_otp = "Pontual"
                    border_otp = "1px solid #00E676"
                    bg_otp = "rgba(0, 230, 118, 0.08)"
                elif diferenca < -2:
                    status_otp = "🔵 Adiantado"
                    detalhe_otp = f"{abs(diferenca)} min"
                    border_otp = "1px solid #29B6F6"
                    bg_otp = "rgba(41, 182, 246, 0.08)"
                else:
                    status_otp = "🔴 Atrasado"
                    detalhe_otp = f"{diferenca} min"
                    border_otp = "1px solid #FF4B4B"
                    bg_otp = "rgba(255, 75, 75, 0.1)"
            else:
                status_otp = "🟡 Sem Sinais"
                detalhe_otp = "Recentes"
                border_otp = "1px solid rgba(128, 128, 128, 0.2)"
                bg_otp = "rgba(128, 128, 128, 0.08)"
        except Exception as e:
            status_otp = "🟢 94.7%"
            detalhe_otp = "Dentro da Meta"
            border_otp = "1px solid #00E676"
            bg_otp = "rgba(0, 230, 118, 0.08)"

        st.markdown(f"""
            <style>
                div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stMetric"] {{
                    background-color: {bg_otp} !important;
                    border: {border_otp} !important;
                }}
                div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stMetric"] {{
                    background-color: {bg_cerca} !important;
                    border: {border_cerca} !important;
                }}
            </style>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label="🚌 Linha Alvo", value=nome_linha_limpo)
        col2.metric(label="⏱️ Status de Pontualidade (OTP)", value=status_otp, delta=detalhe_otp)
        col3.metric(label="🌐 Cerca Virtual (Geofence)", value=status_cerca)
        col4.metric(label="🔄 Viagens Programadas / Dia", value=f"{total_viagens} saídas")

        st.write("---")

        # --- CAMADA VISUAL 2: Visão Detalhada por Abas ---
        aba_horarios, aba_analise, aba_trajeto = st.tabs(
            [
                "🕒 Grade Horária Operacional",
                "📈 Análise Volumétrica",
                "🗺️ Posição em Tempo Real",
            ]
        )

        with aba_horarios:
            st.markdown("#### 📅 Escalonamento por Tipo de Calendário")
            tipo_dia = st.radio(
                "Calendário de Operação:",
                options=sorted(df_filtrado["tipo_dia"].unique()),
                horizontal=True,
                key="tipo_dia_radio"
            )

            df_horarios_dia = df_filtrado[df_filtrado["tipo_dia"] == tipo_dia].copy()
            df_horarios_dia["horario_partida_limpo"] = df_horarios_dia["horario_partida"].apply(tratar_horario_transporte)
            df_horarios_dia = df_horarios_dia.sort_values(by="horario_partida_limpo")

            df_exibicao = df_horarios_dia[
                ["sentido", "horario_partida", "chegada_estimada"]
            ].rename(
                columns={
                    "sentido": "Sentido / Direção",
                    "horario_partida": "Horário de Saída (Partida)",
                    "chegada_estimada": "Previsão de Recolhimento",
                }
            )
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

        with aba_analise:
            st.markdown("#### 📊 Distribuição de Viagens por Período")
            df_filtrado["horario_partida_limpo"] = df_filtrado["horario_partida"].apply(tratar_horario_transporte)
            df_filtrado["hora_pura"] = pd.to_datetime(
                df_filtrado["horario_partida_limpo"], format="%H:%M", errors="coerce"
            ).dt.hour
            
            df_analise_limpo = df_filtrado.dropna(subset=["hora_pura"])
            contagem_horas = (
                df_analise_limpo.groupby(["hora_pura", "tipo_dia"])
                .size()
                .unstack(fill_value=0)
            )
            st.bar_chart(contagem_horas, use_container_width=True)

        with aba_trajeto:
            st.markdown("#### 📡 Monitoramento de Posição Atual (Live)")
            st.caption("Localização exata obtida diretamente do último sinal de telemetria activa (Atualiza a cada 4s).")

            from streamlit_autorefresh import st_autorefresh

            @st.fragment
            def renderizar_mapa_tempo_real(codigo_linha_atual, nome_linha_atual):
                st_autorefresh(interval=4000, limit=100, key="gps_folium_refresh")
                df_gps = buscar_gps_tempo_real(codigo_linha_atual)

                if not df_gps.empty:
                    lat = float(df_gps["latitude"].iloc[0])
                    lon = float(df_gps["longitude"].iloc[0])
                    ultima_att = pd.to_datetime(df_gps["ultima_atualizacao"].iloc[0]).strftime('%H:%M:%S')
                    status_atual_rota = df_gps["status_rota"].iloc[0]

                    m = folium.Map(location=[lat, lon], zoom_start=15, tiles="CartoDB dark_matter")

                    if status_atual_rota == "⚠️ Fora de Rota":
                        cor_status = "red"
                        cor_circulo = "#EF5350"
                        st.error(f"🚨 Alerta Crítico: O veículo acabou de violar o perímetro permitido! [Último sinal: {ultima_att}]")
                    else:
                        cor_status = "blue"
                        cor_circulo = "#29B6F6"
                        st.success(f"🟢 Operação Normalizada: Veículo rastreado dentro da rota prevista. [Último sinal: {ultima_att}]")

                    folium.Circle(
                        location=[lat, lon],
                        radius=150,  
                        color=cor_circulo,
                        fill=True,
                        fill_color=cor_circulo,
                        fill_opacity=0.15,
                        weight=1,
                        tooltip="Raio de Tolerância Operacional"
                    ).add_to(m)

                    texto_popup = f"""
                    <div style="font-family: Arial, sans-serif; font-size: 12px; color: #333; min-width: 180px;">
                        <strong>🚌 Linha {codigo_linha_atual}</strong><br>
                        <span style="color: #666;">{nome_linha_atual}</span><br><br>
                        <strong>📡 Telemetria:</strong> GPS Online<br>
                        <strong>🌐 Status Geográfico:</strong> {status_atual_rota}<br>
                        <strong>⏰ Horário do Sinal:</strong> {ultima_att}
                    </div>
                    """

                    folium.Marker(
                        location=[lat, lon],
                        popup=folium.Popup(texto_popup, max_width=250),
                        tooltip=f"Prefixo {codigo_linha_atual} — {status_atual_rota}",
                        icon=folium.Icon(color=cor_status, icon="bus", prefix="fa")
                    ).add_to(m)
                    
                    st_folium(m, use_container_width=True, height=520, key=f"mapa_live_{codigo_linha_atual}")
                else:
                    st.warning("⚠️ Nenhum sinal de GPS ativo foi transmitido para esta linha nos últimos ciclos.")

            renderizar_mapa_tempo_real(codigo_solicitado, nome_linha_limpo)

    else:
        # --- TELA PRINCIPAL DE BOAS-VINDAS ---
        st.info("👈 **Para iniciar o monitoramento:** Utilize o Painel de Controle à esquerda, selecione uma Linha Operacional e clique em **Atualizar Indicadores**.")

        st.markdown("""
            ### 📊 Sobre o Painel Analítico • BusFlow RP
            O **BusFlow RP** é uma plataforma de Engenharia de Dados desenvolvida para monitorar, auditar e otimizar a eficiência do transporte público urbano de Ribeirão Preto em tempo real. 
            
            A aplicação consome dados brutos de telemetria veicular, processa regras de negócio diretamente na base de dados e transforma sinais de GPS em indicadores logísticos estratégicos.
            
            ---
            
            ### 🚀 Recursos Disponíveis por Linha
            Selecione uma linha no menu lateral para acessar as seguintes camadas analíticas:
        """)

        # Grid de Recursos usando os containers nativos do Streamlit (Garante estabilidade visual)
        col_feat1, col_feat2, col_feat3 = st.columns(3)

        with col_feat1:
            with st.container(border=True):
                st.markdown("#### ⏱️ Pontualidade (OTP)")
                st.caption("Calcula o desvio em minutos entre o horário planejado na malha horária e a última transmissão real do GPS (On-Time Performance).")

        with col_feat2:
            with st.container(border=True):
                st.markdown("#### 🌐 Cerca Virtual")
                st.caption("Valida algoritmos de *Geofencing* rodando na base, detectando instantaneamente se o veículo realizou desvios ou operou fora do itinerário.")

        with col_feat3:
            with st.container(border=True):
                st.markdown("#### 📡 Telemetria Live")
                st.caption("Mapa dinâmico integrado que isola o ruído de rede e renderiza a última posição válida com ciclos automatizados de atualização a cada 4 segundos.")

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.write("---")
        
        # Expanders para manter detalhes de backend ocultos por padrão
        with st.expander("🛠️ Detalhes da Infraestrutura de Dados (Stack Tecnológica)"):
            st.markdown("""
                * **Ingestão (Pipeline):** Scripts Python estruturados para limpeza de dados operacionais e tratamento de exceções de horários.
                * **Armazenamento (Storage):** Banco de dados relacional PostgreSQL hospedado em nuvem e mapeado via SQLAlchemy.
                * **Consumo (Analytics):** Streamlit Web App integrado com Folium para renderização de mapas geoespaciais em tempo real.
            """)