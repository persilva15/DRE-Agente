import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

from config import MES_CORRENTE, ANO_CORRENTE, MESES_NOMES, EMPRESAS_NOMES, CLASSIFICACAO_MAP, CLASSIFICACOES, MASCARA_DRE
from engine.dre_logic import DRELogic
from engine.parser import QuestionParser
from engine.responder import Responder
from ui import inject_styles, render_exec_header, render_kpi_card, render_footer, format_real_brazilian, format_pct_brazilian
from auth import login, logout, esta_logado, get_nome

# =============================================================================
# DETECTAR AMBIENTE (local vs nuvem)
# =============================================================================

IS_CLOUD = False
GITHUB_CSV_URL = ''

# Método 1: tentar st.secrets
try:
    GITHUB_CSV_URL = st.secrets.get("GITHUB_CSV_URL", "")
    if GITHUB_CSV_URL:
        IS_CLOUD = True
except Exception:
    pass

# Método 2: variável de ambiente
env_url = os.environ.get('GITHUB_CSV_URL', '')
if env_url:
    GITHUB_CSV_URL = env_url
    IS_CLOUD = True

# Método 3: verificar se rede local existe (timeout rápido)
if not IS_CLOUD:
    import socket
    try:
        socket.create_connection(("10.5.12.252", 443), timeout=2)
    except (OSError, socket.timeout):
        # Sem acesso à rede local → é cloud
        IS_CLOUD = True
        if not GITHUB_CSV_URL:
            GITHUB_CSV_URL = "https://raw.githubusercontent.com/persilva15/DRE-Agente/main/csv_data"

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="DRE - Agente Controller Febracis",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# AUTENTICAÇÃO
# =============================================================================

if not esta_logado():
    login()
    if not esta_logado():
        st.info('Insira suas credenciais para acessar')
        st.stop()

# =============================================================================
# INJETAR ESTILOS EXECUTIVE
# =============================================================================

inject_styles()

# =============================================================================
# HEADER EXECUTIVE
# =============================================================================

render_exec_header("DRE vs Orçamento 26 · Inteligência Financeira")

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    # --- HEADER MARCA ---
    col_logo, col_text = st.columns([1, 3])
    with col_logo:
        # Caminho relativo para funcionar local e na nuvem
        logo_path = os.path.join(os.path.dirname(__file__), "logo_cor.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=64)
        else:
            st.markdown(" ", unsafe_allow_html=True)
    with col_text:
        st.markdown(
            '<div style="padding-top:4px;">'
            '<div style="color:#fff;font-size:1.1rem;font-weight:800;letter-spacing:2px;text-transform:uppercase;margin:0;line-height:1.1;">FEBRACIS</div>'
            '<div style="color:#aaa;font-size:0.75rem;margin:2px 0 0 0;letter-spacing:1px;text-transform:uppercase;font-weight:500;">AGENTE DRE</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    
    # --- USUÁRIO LOGADO ---
    st.markdown(f'<p style="color:#888;font-size:0.7rem;margin:0;">Logado como: <b>{get_nome()}</b></p>', unsafe_allow_html=True)
    if st.button("Sair", key="btn_logout"):
        logout()
    
    # --- SEÇÃO: FILTROS ---
    st.markdown('<p class="sidebar-section">Filtros</p>', unsafe_allow_html=True)
    
    classificacao_selecionada = st.selectbox(
        "Classificação",
        options=["Todos", "HOLDING", "COLIGADA"],
        index=0,
        label_visibility="collapsed",
    )
    
    if classificacao_selecionada == "HOLDING":
        empresas_disponiveis = [emp for emp, cls in CLASSIFICACAO_MAP.items() if cls == "HOLDING"]
    elif classificacao_selecionada == "COLIGADA":
        empresas_disponiveis = [emp for emp, cls in CLASSIFICACAO_MAP.items() if cls == "COLIGADA"]
    else:
        empresas_disponiveis = sorted(EMPRESAS_NOMES)
    
    empresa_selecionada = st.selectbox(
        "Empresa",
        options=["Consolidado"] + sorted(empresas_disponiveis),
        index=0,
        label_visibility="collapsed",
    )
    
    col_ano, col_mes = st.columns([1, 1])
    with col_ano:
        ano_selecionado = st.selectbox(
            "Ano",
            options=[2024, 2025, 2026],
            index=2,
            label_visibility="collapsed",
        )
    with col_mes:
        filtrar_mes = st.checkbox("Mês", value=False)
    
    if filtrar_mes:
        mes_opcoes = [MESES_NOMES[i] for i in range(1, 13)]
        mes_selecionado_str = st.selectbox(
            "Mês",
            options=mes_opcoes,
            index=MES_CORRENTE - 1 if MES_CORRENTE <= 12 else 0,
            label_visibility="collapsed",
        )
        mes_atual = next(k for k, v in MESES_NOMES.items() if v == mes_selecionado_str)
    else:
        mes_atual = None
    
    empresa_filtro = None if empresa_selecionada == "Consolidado" else empresa_selecionada
    classificacao_filtro = None if classificacao_selecionada == "Todos" else classificacao_selecionada
    
    # --- DIVIDER ---
    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    
    # --- SEÇÃO: PERGUNTAS SUGERIDAS ---
    st.markdown('<p class="sidebar-section">Exemplos de Perguntas</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-examples">'
        '<div class="sidebar-example-item">   Qual o EBITDA consolidado?</div>'
        '<div class="sidebar-example-item">   Receita Bruta da CIS TREINAMENTO</div>'
        '<div class="sidebar-example-item">   Variação Real vs Orçado consolidado</div>'
        '<div class="sidebar-example-item">   Lucro líquido da PERSONALISSIMO</div>'
        '<div class="sidebar-example-item">   DRE consolidado até dezembro</div>'
        '<div class="sidebar-example-item">   Custo Total da CIS ASSESSMENT</div>'
        '</div>',
        unsafe_allow_html=True,
    )

# =============================================================================
# CARREGAR DADOS
# =============================================================================

@st.cache_data(ttl=3600, show_spinner="Carregando dados...")
def carregar_dados_base():
    """Carrega dados baseado no ambiente (local ou nuvem)."""
    if IS_CLOUD and GITHUB_CSV_URL:
        # Modo nuvem: ler CSVs do GitHub
        from data.loader_csv import DataLoaderCSV
        loader = DataLoaderCSV(GITHUB_CSV_URL)
        data = loader.load_all()
    else:
        # Modo local: ler Excel da rede
        from data.loader import DataLoader
        loader = DataLoader()
        data = {
            "base": loader.load_base_dre(),
            "plano_contas": loader.load_plano_contas(),
            "mascara_dre": loader.load_mascara_dre(),
            "auxiliar": loader.load_auxiliar(),
            "base_real_2025": loader.load_realizado_combinado(),
            "base_real_2024": loader.load_base_real_2024(),
            "base_orcado": loader.load_base_orcado(),
            "base_forecast": loader.load_base_forecast(),
        }
    return data

def carregar_dados_xmla(empresa: str = None, classificacao: str = None):
    """Carrega dados XMLA (apenas modo local)."""
    if IS_CLOUD:
        return {}
    from data.powerbi_xmla import extrair_dre_jose_alberto
    return extrair_dre_jose_alberto(empresa=empresa, classificacao=classificacao)

try:
    data = carregar_dados_base()
    
    # XMLA apenas no modo local
    if not IS_CLOUD:
        try:
            with st.spinner("Carregando dados XMLA do Power BI..."):
                dre_xmla = carregar_dados_xmla(empresa_filtro, classificacao_filtro)
            data["dre_xmla"] = dre_xmla
        except Exception as e:
            st.warning(f"XMLA não disponível: {e}")
            data["dre_xmla"] = {}
    else:
        data["dre_xmla"] = {}
    
    dre_logic = DRELogic(data)
    responder = Responder(dre_logic)
    parser = QuestionParser()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# =============================================================================
# KPI CARDS
# =============================================================================

# Tentar usar XMLA primeiro (dados idênticos ao Power BI - Visão Total)
dre_completo = dre_logic.calcular_dre_luciana(empresa_filtro, meses_ate=mes_atual or 9, ano=ano_selecionado)

# Se XMLA não retornou dados, usar método antigo
if not dre_completo:
    dre_completo = dre_logic.calcular_dre_completo(empresa_filtro, mes_atual, ano_selecionado)

# Receita Bruta para KPIs
rb_r25 = 0
rb_f26 = 0
rb_r26 = 0
rb_o26 = 0
for row in dre_completo:
    if row["nivel_1"] == "Receita Bruta":
        rb_r25 = row["r_2025"]
        rb_f26 = row["f_2026"]
        rb_r26 = row["r_2026"]
        rb_o26 = row["o_2026"]
        break

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    render_kpi_card(
        "R 2025 (R$ mil)",
        format_real_brazilian(rb_r25),
        sub="Realizado 2025"
    )

with kpi_col2:
    render_kpi_card(
        "F 2026 (R$ mil)",
        format_real_brazilian(rb_f26),
        sub="Forecast 2026"
    )

with kpi_col3:
    render_kpi_card(
        "R 2026 (R$ mil)",
        format_real_brazilian(rb_r26),
        sub="Realizado 2026"
    )

with kpi_col4:
    render_kpi_card(
        "O 2026 (R$ mil)",
        format_real_brazilian(rb_o26),
        sub="Orçado 2026"
    )

st.markdown("---")

# =============================================================================
# TABELA DRE COMPLETA (10 COLUNAS)
# =============================================================================

st.markdown("""
<div style="padding: 10px 0;">
    <h2 style="color: #E8B23B; margin: 0; font-size: 1.1rem; font-weight: 700; letter-spacing: 1px;">
        DRE vs ORÇAMENTO 26
    </h2>
    <p style="color: #888; margin: 5px 0 0 0; font-size: 0.85rem;">
        Visão Total · {empresa} · {periodo}
    </p>
</div>
""".format(
    empresa=empresa_selecionada,
    periodo=f"Até {MESES_NOMES[mes_atual]}/{ano_selecionado}" if mes_atual else f"Ano {ano_selecionado}"
), unsafe_allow_html=True)

# Converter para DataFrame para exibição estilizada
rows = []
for row in dre_completo:
    rows.append({
        "Linha DRE": row["nivel_1"],
        "R 2025 (R$)": row["r_2025"],
        "AV 25": row["av_2025"],
        "F 2026 (R$)": row["f_2026"],
        "AV F26": row["av_f26"],
        "R 2026 (R$)": row["r_2026"],
        "AV R26": row["av_2026"],
        "Var F26 vs R26 %": row["var_f26_r26_pct"],
        "Var F26 vs R26 R$": row["var_f26_r26_rs"],
        "Var F26 vs R25 %": row["var_f26_r25_pct"],
        "Var F26 vs R25 R$": row["var_f26_r25_rs"],
        "O 2026 (R$)": row["o_2026"],
        "AV O26": row["av_o_2026"],
        "Var F26 vs O26 %": row["var_f26_o26_pct"],
        "Var F26 vs O26 R$": row["var_f26_o26_rs"],
        "_subtotal": row["subtotal"] == "S",
    })

df_dre = pd.DataFrame(rows)

# Estilizar tabela
def style_dre_table(df):
    """Aplica estilo executive à tabela DRE."""
    styled = df.style
    
    # Formatar colunas de valores
    styled = styled.format({
        "R 2025 (R$)": "R$ {:,.0f}",
        "AV 25": "{:.1f}%",
        "F 2026 (R$)": "R$ {:,.0f}",
        "AV F26": "{:.1f}%",
        "R 2026 (R$)": "R$ {:,.0f}",
        "AV R26": "{:.1f}%",
        "Var F26 vs R26 %": "{:+.1%}",
        "Var F26 vs R26 R$": "R$ {:,.0f}",
        "Var F26 vs R25 %": "{:+.1%}",
        "Var F26 vs R25 R$": "R$ {:,.0f}",
        "O 2026 (R$)": "R$ {:,.0f}",
        "AV O26": "{:.1f}%",
        "Var F26 vs O26 %": "{:+.1%}",
        "Var F26 vs O26 R$": "R$ {:,.0f}",
    })
    
    return styled

# Exibir tabela com coluna Linha DRE congelada
def render_dre_table_html(df):
    """Renderiza tabela DRE como HTML com coluna A congelada."""
    
    def fmt_rs(v):
        if v == 0: return "R$ -"
        return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    def fmt_pct(v):
        sinal = "+" if v > 0 else ""
        return f"{sinal}{v:.1%}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    def fmt_av(v):
        return f"{v:.1%}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    cols = [
        ("Linha DRE", "text"),
        ("R 2025 (R$)", "rs"), ("AV 25", "av"),
        ("F 2026 (R$)", "rs"), ("AV F26", "av"),
        ("R 2026 (R$)", "rs"), ("AV R26", "av"),
        ("Var F26 vs R26 %", "pct"), ("Var F26 vs R26 R$", "rs"),
        ("Var F26 vs R25 %", "pct"), ("Var F26 vs R25 R$", "rs"),
        ("O 2026 (R$)", "rs"), ("AV O26", "av"),
        ("Var F26 vs O26 %", "pct"), ("Var F26 vs O26 R$", "rs"),
    ]
    
    header_html = "".join(
        f'<th style="white-space:nowrap;{"text-align:left;min-width:220px;position:sticky;left:0;z-index:5;background:var(--bg-deep);box-shadow:2px 0 5px rgba(0,0,0,0.5);" if i==0 else ""}">{c[0]}</th>'
        for i, c in enumerate(cols)
    )
    
    rows_html = ""
    linhas_destaque = {"Receita Bruta", "Receita Líquida", "Lucro Bruto (R$)", "Ebitda", "Lucro/Prejuízo Do Exercício"}
    for _, row in df.iterrows():
        nivel_1 = str(row.get("Linha DRE", "")).strip()
        is_sub = row.get("_subtotal", False) or nivel_1 in linhas_destaque
        cls = ' class="subtotal"' if is_sub else ""
        cells = ""
        for i, (col_name, tipo) in enumerate(cols):
            val = row[col_name]
            if tipo == "text":
                cell_val = str(val)
                if is_sub:
                    style = 'text-align:left;min-width:220px;position:sticky;left:0;z-index:3;background:rgba(180,140,30,0.25) !important;box-shadow:4px 0 10px rgba(0,0,0,0.9);color:var(--gold);font-weight:700;white-space:nowrap;'
                else:
                    bg = "#080a10" if row.name % 2 == 0 else "#0b0e16"
                    style = f'text-align:left;min-width:220px;position:sticky;left:0;z-index:3;background:{bg} !important;box-shadow:4px 0 10px rgba(0,0,0,0.9);white-space:nowrap;'
            elif tipo == "rs":
                cell_val = fmt_rs(val)
                style = "text-align:right;white-space:nowrap;"
                if is_sub:
                    style += "color:var(--gold);font-weight:700;"
            elif tipo == "av":
                cell_val = fmt_av(val)
                style = "text-align:right;white-space:nowrap;"
            elif tipo == "pct":
                cell_val = fmt_pct(val)
                style = "text-align:right;white-space:nowrap;"
                if val > 0:
                    style += "color:#4ade80;"
                elif val < 0:
                    style += "color:#ef4444;"
            else:
                cell_val = str(val)
                style = "white-space:nowrap;"
            cells += f'<td style="{style}">{cell_val}</td>'
        rows_html += f'<tr{cls}>{cells}</tr>\n'
    
    html = f"""
    <div style="overflow-x:auto;border-radius:var(--radius);border:1px solid var(--border-card);box-shadow:var(--shadow-card);max-height:500px;">
        <table class="dre-table">
            <thead><tr>{header_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """
    return html

st.markdown(render_dre_table_html(df_dre), unsafe_allow_html=True)

# =============================================================================
# PERGUNTA DO USUÁRIO
# =============================================================================

st.markdown("---")

st.markdown("""
<div style="padding: 10px 0;">
    <p class="nav-section-label">Pergunte ao Agente</p>
</div>
""", unsafe_allow_html=True)

pergunta = st.text_input(
    " ",
    placeholder="Digite sua pergunta sobre o DRE... (Ex: Qual o EBITDA da CIS TREINAMENTO em março?)",
    label_visibility="collapsed",
)

if pergunta:
    with st.spinner("Processando..."):
        elementos = parser.parse(pergunta)
        
        # Aplicar filtros da sidebar
        if empresa_selecionada != "Consolidado":
            elementos["empresa"] = empresa_filtro
        if filtrar_mes and mes_atual:
            elementos["mes"] = mes_atual
        if ano_selecionado:
            elementos["ano"] = ano_selecionado
        
    resposta = responder.responder(pergunta, elementos)
    st.markdown(resposta)

# =============================================================================
# RODAPÉ
# =============================================================================

render_footer()
