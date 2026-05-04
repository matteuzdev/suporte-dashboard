import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da Página - Suporte Dashboard
st.set_page_config(page_title="Suporte Dashboard", layout="wide", initial_sidebar_state="expanded")


# --- SISTEMA DE SEGURANÇA ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True

    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown("<h1 style='text-align: center; color: #20435C;'>SUPORTE N2</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Painel de Gestão de Tickets</p>", unsafe_allow_html=True)
        password = st.text_input("Senha de acesso:", type="password")
        if st.button("ENTRAR NO SISTEMA"):
            if password == "suporten2":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta.")
    return False


if not check_password():
    st.stop()


# --- CONFIGURAÇÕES ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1LWuWM2iEPz-3f3qvXaaokiNrnLafjPP43LIAKz5tcoA/export?format=csv&gid=1321610989"

# CSS Customizado (Paleta Officecom preservada)
st.markdown(
    """
    <style>
    .main { background-color: #F4F7F9; }
    .stMetric { background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #E0E4E8; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    [data-testid="stMetricLabel"] {
        background-color: #F4F7F9 !important;
        border-radius: 6px !important;
        padding: 4px 8px !important;
    }
    [data-testid="stMetricLabel"] p { color: #20435C !important; font-weight: 700 !important; }
    [data-testid="stMetricValue"] { color: #20435C !important; font-weight: bold; }
    [data-testid="stSidebar"] { background-color: #20435C; border-right: 1px solid #1a364a; }
    [data-testid="stSidebar"] * { color: white !important; }
    h1, h2, h3 { color: #20435C !important; font-family: 'Inter', sans-serif; }
    .stButton>button {
        background-color: #EA465E !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        border: none !important;
        padding: 10px !important;
    }
    .stButton>button:hover { background-color: #d63f56 !important; }
    th { background-color: #20435C !important; color: white !important; text-align: center !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL, encoding="utf-8")
        expected = ["ID", "Titulo", "Solicitante", "Criacao", "Status", "Casas", "Atualizacao", "Leitura", "Mesclado", "Link"]
        if len(df.columns) >= len(expected):
            df.columns = expected + list(df.columns[len(expected):])

        for col in ["Status", "Casas", "Criacao", "Atualizacao", "Link", "Titulo", "Solicitante", "ID"]:
            if col not in df.columns:
                df[col] = ""

        df["Criacao"] = pd.to_datetime(df["Criacao"], format="%d/%m/%Y", errors="coerce")
        df["Atualizacao"] = pd.to_datetime(df["Atualizacao"], dayfirst=True, errors="coerce")
        df["Status"] = df["Status"].fillna("Sem Status")
        df["Casas"] = df["Casas"].fillna("Sem brand")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>SUPORTE N2</h2>", unsafe_allow_html=True)
    if st.button("🚪 LOGOUT"):
        st.session_state.authenticated = False
        st.rerun()
    st.markdown("---")
    if st.button("🔄 ATUALIZAR DADOS"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.subheader("Filtros")
    df_raw = load_data()
    if not df_raw.empty:
        status_list = ["Todos"] + sorted(df_raw["Status"].unique().tolist())
        selected_status = st.selectbox("Status do Ticket", status_list)
        casa_list = ["Todas"] + sorted(df_raw["Casas"].str.split(", ").explode().unique().tolist())
        selected_casa = st.selectbox("Brands", casa_list)

if "filtros" not in st.session_state:
    st.session_state.filtros = {"Status": None, "Casas": None}

if not df_raw.empty:
    df = df_raw.copy()
    if selected_status != "Todos":
        df = df[df["Status"] == selected_status]
    if selected_casa != "Todas":
        df = df[df["Casas"].str.contains(selected_casa, na=False)]
    if st.session_state.filtros["Status"]:
        df = df[df["Status"] == st.session_state.filtros["Status"]]
    if st.session_state.filtros["Casas"]:
        df = df[df["Casas"].str.contains(st.session_state.filtros["Casas"], na=False)]

    # --- MÉTRICAS ---
    st.title("🛡️ Suporte Dashboard")
    st.markdown("Interface de monitoramento de tickets enviados para **Cactus**.")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total de Tickets", len(df))
    with m2:
        dev = len(df[df["Status"] == "Devolutiva"])
        st.metric("Devolutivas", dev, delta=f"{(dev / len(df) * 100):.1f}%" if len(df) > 0 else "0%")
    with m3:
        aguardando_fornecedor = len(df[df["Status"].str.strip().str.lower() == "aguardando fornecedor"])
        st.metric("Aguardando Fornecedor", aguardando_fornecedor)
    with m4:
        aguardando_cliente = len(df[df["Status"].str.strip().str.lower() == "aguardando cliente"])
        st.metric("Aguardando Cliente", aguardando_cliente)

    st.markdown("---")

    # --- GRÁFICOS ---
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Situação dos Chamados")
        status_counts = df["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Quantidade"]
        fig_status = px.pie(
            status_counts,
            values="Quantidade",
            names="Status",
            hole=0.4,
            color_discrete_sequence=["#EA465E", "#20435C", "#6C757D", "#ADB5BD"],
        )
        fig_status.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_status, use_container_width=True)

    with c2:
        st.subheader("Tickets por Brand")
        df_casas = df.assign(Casas=df["Casas"].str.split(", ")).explode("Casas")
        casa_counts = df_casas["Casas"].value_counts().reset_index().head(10)
        casa_counts.columns = ["Brand", "Tickets"]
        fig_casas = px.bar(casa_counts, x="Tickets", y="Brand", orientation="h", color_discrete_sequence=["#20435C"])
        fig_casas.update_layout(margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_casas, use_container_width=True)

    st.subheader("Criados vs Atualizados por Data")
    created_daily = (
        df.dropna(subset=["Criacao"])
        .groupby(df["Criacao"].dt.date)
        .size()
        .reset_index(name="Quantidade")
        .rename(columns={"Criacao": "Data"})
    )
    created_daily["Tipo"] = "Criados"

    updated_daily = (
        df.dropna(subset=["Atualizacao"])
        .groupby(df["Atualizacao"].dt.date)
        .size()
        .reset_index(name="Quantidade")
        .rename(columns={"Atualizacao": "Data"})
    )
    updated_daily["Tipo"] = "Atualizados"

    trend_df = pd.concat([created_daily, updated_daily], ignore_index=True).sort_values("Data")
    if not trend_df.empty:
        fig_trend = px.line(
            trend_df,
            x="Data",
            y="Quantidade",
            color="Tipo",
            markers=True,
            color_discrete_map={"Criados": "#20435C", "Atualizados": "#EA465E"},
        )
        fig_trend.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=320, legend_title_text="")
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Sem dados válidos de criação/atualização para exibir o gráfico por data.")

    # --- TABELA ---
    st.markdown("---")
    st.subheader("📋 Detalhamento")
    df_display = df.copy()
    df_display["Link"] = df_display["Link"].apply(
        lambda x: f'<a href="{x}" target="_blank" style="color: #EA465E; font-weight: bold;">Ver Ticket</a>'
    )
    df_display = df_display.rename(columns={"Casas": "Brands"})
    st.write(
        df_display[["ID", "Criacao", "Solicitante", "Status", "Brands", "Titulo", "Link"]].to_html(escape=False, index=False),
        unsafe_allow_html=True,
    )

    st.markdown("<br><p style='text-align: center; color: #888;'>Suporte Dashboard | Conexão Cactus Ativa</p>", unsafe_allow_html=True)
else:
    st.error("Sem dados para exibir.")
