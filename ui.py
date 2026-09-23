import streamlit as st

# --- Paleta Febracis extraída da logo ---
FEB_GOLD = "#E8B23B"
FEB_GOLD_LIGHT = "#ECB63F"
FEB_GOLD_DARK = "#B88100"
FEB_GOLD_MID = "#C38A08"

EXECUTIVE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --gold: #E8B23B;
    --gold-light: #ECB63F;
    --gold-mid: #C38A08;
    --gold-dark: #B88100;
    --bg-deep: #0D1017;
    --bg-card: #11131A;
    --bg-surface: #171B25;
    --border-subtle: rgba(255,255,255,0.06);
    --border-card: rgba(232,178,59,0.08);
    --text-muted: #888;
    --text-dim: #666;
    --shadow-card: 0 8px 32px rgba(0,0,0,0.4), 0 1px 3px rgba(0,0,0,0.3);
    --shadow-hover: 0 12px 48px rgba(0,0,0,0.5), 0 2px 6px rgba(0,0,0,0.3);
    --radius: 12px;
    --radius-sm: 8px;
    --radius-lg: 16px;
}

/* --- BASE --- */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #0D1017 0%, #11131A 42%, #171B25 100%);
}
[data-testid="stHeader"] { background: transparent !important; }
.stApp, div.stText, p, span, li, label, .stMarkdown {
    color: #eee !important;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}
h1, h2, h3, h4, h5, h6 { font-family: 'Inter', sans-serif !important; }

/* --- SCROLLBAR --- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(232,178,59,0.2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(232,178,59,0.4); }

/* --- SIDEBAR --- */
[data-testid="stSidebar"] {
    background: #11131A !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
[data-testid="stSidebar"]::after { display: none; }
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--gold) !important;
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-weight: 600;
}

.nav-section-label {
    color: #8D92A0 !important;
    font-size: 0.62rem;
    letter-spacing: 2.3px;
    text-transform: uppercase;
    margin: 1.05rem 0 0.45rem 0.55rem;
    font-weight: 800;
}

/* --- HEADER --- */
.exec-header {
    background: linear-gradient(135deg, rgba(17,19,26,0.94) 0%, rgba(13,16,23,0.94) 100%);
    border: 1px solid var(--border-card);
    border-radius: var(--radius-lg);
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(20px);
}
.exec-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, var(--gold) 50%, transparent 100%);
}
.exec-header::after {
    content: '';
    position: absolute;
    top: -50%; right: -20%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(232,178,59,0.04) 0%, transparent 70%);
    pointer-events: none;
}
.exec-header h1 {
    color: var(--gold) !important;
    font-size: 1.6rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: 2px;
    position: relative;
}
.exec-header p {
    color: var(--text-muted) !important;
    margin: 0.3rem 0 0 0;
    font-size: 0.85rem;
    font-weight: 300;
    position: relative;
}

/* --- CARDS --- */
.kpi-card {
    background: linear-gradient(145deg, var(--bg-card) 0%, var(--bg-surface) 100%);
    border: 1px solid var(--border-card);
    border-radius: var(--radius);
    padding: 1.3rem 1.5rem;
    min-height: 115px;
    box-shadow: var(--shadow-card);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: linear-gradient(145deg, rgba(232,178,59,0.02) 0%, transparent 60%);
    opacity: 0;
    transition: opacity 0.3s;
}
.kpi-card:hover {
    transform: translateY(-4px);
    border-color: rgba(232,178,59,0.25);
    box-shadow: var(--shadow-hover);
}
.kpi-card:hover::before { opacity: 1; }
.kpi-card .kpi-label {
    color: var(--text-muted);
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 0.6rem;
    font-weight: 500;
    position: relative;
}
.kpi-card .kpi-value {
    color: var(--gold);
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    position: relative;
}
.kpi-card .kpi-value.green { color: #4ade80; }
.kpi-card .kpi-value.red { color: #ef4444; }
.kpi-card .kpi-sub {
    color: var(--text-dim);
    font-size: 0.75rem;
    margin-top: 0.4rem;
    font-weight: 400;
    position: relative;
}

/* --- SECTION CARD --- */
.section-card {
    background: linear-gradient(145deg, var(--bg-card) 0%, var(--bg-surface) 100%);
    border: 1px solid var(--border-card);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow-card);
}
.section-card h3 {
    color: var(--gold) !important;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 1rem;
    font-weight: 600;
}

/* --- MÉTRICAS STREAMLIT --- */
[data-testid="metric-container"] {
    background: linear-gradient(145deg, var(--bg-card), var(--bg-surface));
    border: 1px solid var(--border-card);
    border-radius: var(--radius);
    padding: 15px;
    box-shadow: var(--shadow-card);
}
[data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 0.75rem !important; }
[data-testid="stMetricValue"] { color: var(--gold) !important; font-weight: 700 !important; }

/* --- BOTÕES --- */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--gold) 0%, var(--gold-dark) 100%) !important;
    color: #000 !important;
    border-radius: var(--radius-sm);
    border: none;
    font-weight: 600;
    transition: all 0.2s;
    box-shadow: 0 2px 12px rgba(232,178,59,0.2);
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(232,178,59,0.35);
}
div.stButton > button:not([kind]) {
    background: var(--bg-surface);
    color: #ccc !important;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    font-weight: 500;
    transition: all 0.2s;
}
div.stButton > button:not([kind]):hover {
    border-color: var(--gold-mid);
    color: var(--gold) !important;
}
[data-testid="stSidebar"] div.stButton > button {
    background: transparent !important;
    color: #9A9EA9 !important;
    border: none !important;
    border-left: 3px solid transparent !important;
    border-radius: 6px !important;
    text-align: left !important;
    justify-content: flex-start !important;
    height: 40px !important;
    padding: 0 0.9rem !important;
    font-size: 0.78rem !important;
    font-weight: 800 !important;
    box-shadow: none !important;
    transition: all 0.2s !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background: rgba(232,178,59,0.08) !important;
    color: var(--gold) !important;
    border-left-color: rgba(232,178,59,0.45) !important;
}
[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--gold) 0%, var(--gold-dark) 100%) !important;
    color: #000 !important;
    border-left: none !important;
    text-align: center !important;
    justify-content: center !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 12px rgba(232,178,59,0.15) !important;
}

/* --- DATAFRAME --- */
.stDataFrame {
    border-radius: var(--radius);
    border: 1px solid var(--border-card);
    overflow: hidden;
    box-shadow: var(--shadow-card);
}
.stDataFrame [data-testid="StyledDataFrameDataCell"] { font-size: 0.8rem; }
.stDataFrame thead tr th {
    background: var(--bg-deep) !important;
    color: var(--gold) !important;
    font-weight: 600;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--border-card);
}
.stDataFrame tbody tr { border-bottom: 1px solid rgba(255,255,255,0.03); transition: background 0.15s; }
.stDataFrame tbody tr:hover { background: rgba(23,27,37,0.85); }
.stDataFrame tbody tr:nth-child(even) { background: rgba(17,19,26,0.75); }

/* --- STREAMLIT COMPONENT BACKGROUNDS --- */
[data-testid="stAlert"],
[data-testid="stExpander"],
[data-testid="stStatusWidget"],
[data-testid="stForm"],
[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(145deg, var(--bg-card) 0%, var(--bg-surface) 100%) !important;
}
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
input,
textarea {
    background-color: var(--bg-card) !important;
}

.block-container { padding-bottom: 4rem; }

/* --- RESPOSTAS DO AGENTE --- */
[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdown"],
[data-testid="stSidebar"] [data-testid="stMarkdown"] > div,
[data-testid="stSidebar"] figure,
[data-testid="stSidebar"] figcaption,
[data-testid="stSidebar"] .stImage,
[data-testid="stSidebar"] .stImage > div,
[data-testid="stSidebar"] .stImage img,
[data-testid="stSidebar"] img {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stMarkdownContainer"] p strong { color: var(--gold) !important; }
div[data-testid="stMarkdownContainer"] ul { list-style-type: none; padding-left: 0; }
div[data-testid="stMarkdownContainer"] ul li::before { content: "▸ "; color: var(--gold); font-weight: 700; }
div[data-testid="stMarkdownContainer"] table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.82rem;
    margin: 0.8rem 0;
}
div[data-testid="stMarkdownContainer"] table th {
    background: var(--bg-deep);
    color: var(--gold);
    font-weight: 700;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 8px 10px;
    text-align: right;
    border-bottom: 2px solid rgba(232,178,59,0.2);
    white-space: nowrap;
}
div[data-testid="stMarkdownContainer"] table th:first-child { text-align: left; }
div[data-testid="stMarkdownContainer"] table td {
    padding: 6px 10px;
    text-align: right;
    color: #ddd;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
div[data-testid="stMarkdownContainer"] table td:first-child { text-align: left; color: #ccc; }
div[data-testid="stMarkdownContainer"] table tr:hover td { background: rgba(232,178,59,0.04); }

/* --- MULTISELECT --- */
div[data-baseweb="select"] > div {
    background-color: var(--bg-card) !important;
    border-color: var(--border-subtle) !important;
    border-radius: var(--radius-sm) !important;
    transition: border-color 0.2s;
}
div[data-baseweb="select"] > div:hover { border-color: var(--gold-mid) !important; }
div[data-baseweb="select"] span,
div[data-baseweb="select"] div { color: #ddd !important; }
div[data-baseweb="popover"] li,
div[data-baseweb="popover"] span {
    color: #ddd !important;
    background-color: var(--bg-card) !important;
}
div[data-baseweb="popover"] li:hover { background-color: var(--bg-surface) !important; }
div[data-baseweb="popover"] li[aria-selected="true"] {
    background-color: rgba(232,178,59,0.12) !important;
    color: var(--gold) !important;
}
div[data-baseweb="tag"] {
    background-color: rgba(232,178,59,0.1) !important;
    color: var(--gold) !important;
    border-radius: 6px !important;
}
div[data-baseweb="tag"] svg { fill: var(--gold) !important; }
div[data-baseweb="tag"]:hover { background-color: rgba(232,178,59,0.2) !important; }

/* --- TABS --- */
div[data-baseweb="tab-list"] { border-bottom: 1px solid var(--border-subtle); }
button[data-baseweb="tab"] { color: var(--text-muted) !important; font-size: 0.8rem; font-weight: 500; transition: color 0.2s; }
button[data-baseweb="tab"][aria-selected="true"] { color: var(--gold) !important; }

/* --- TABELA DRE EXECUTIVE --- */
.dre-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.82rem;
    position: relative;
}
.dre-table thead th {
    background: var(--bg-deep) !important;
    color: var(--gold);
    font-weight: 700;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 10px 8px;
    text-align: right;
    border-bottom: 2px solid rgba(232,178,59,0.2);
    white-space: nowrap;
    position: sticky;
    top: 0;
    z-index: 3;
}
.dre-table thead th:first-child {
    text-align: left;
    z-index: 10 !important;
    background: var(--bg-deep) !important;
    position: sticky;
    left: 0;
}
.dre-table tbody tr { transition: background 0.15s; position: relative; }
.dre-table tbody tr:hover td:not(:first-child) { background: rgba(232,178,59,0.06) !important; }
.dre-table tbody tr.subtotal:hover td:not(:first-child) { background: rgba(232,178,59,0.12) !important; }
.dre-table tbody td {
    padding: 8px;
    text-align: right;
    color: #ddd;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    background: var(--bg-card);
    white-space: nowrap;
    position: relative;
    z-index: 1;
}
.dre-table tbody td:first-child {
    text-align: left;
    color: #ccc;
    z-index: 5 !important;
}
.dre-table tbody tr.subtotal td { color: var(--gold); font-weight: 700; border-top: 1px solid rgba(232,178,59,0.15); }
.dre-table .val-positive { color: #4ade80; }
.dre-table .val-negative { color: #ef4444; }

/* --- FOOTER --- */
.exec-footer {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: linear-gradient(180deg, rgba(17,19,26,0.95) 0%, rgba(13,16,23,1) 100%);
    border-top: 1px solid var(--border-subtle);
    padding: 0.6rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 999;
    font-size: 0.78rem;
    backdrop-filter: blur(12px);
}
.exec-footer .user-info { color: var(--text-muted); }
.exec-footer .user-name { color: var(--gold); font-weight: 600; }

/* --- SIDEBAR FEHEADER --- */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 18px 16px 22px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 6px;
    position: sticky;
    top: 0;
    z-index: 100;
    background: #11131A;
}
.sidebar-brand img {
    border-radius: 4px;
    background: transparent !important;
}
[data-testid="stSidebar"] .sidebar-brand img {
    background: transparent !important;
    box-shadow: none !important;
}
.sidebar-brand-text h2 {
    color: #fff !important;
    font-size: 0.85rem !important;
    font-weight: 800 !important;
    letter-spacing: 2px !important;
    margin: 0 !important;
    line-height: 1.1 !important;
    text-transform: uppercase;
}
.sidebar-brand-text p {
    color: var(--text-muted) !important;
    font-size: 0.6rem !important;
    margin: 2px 0 0 0 !important;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-weight: 500;
}

/* --- SIDEBAR SECTION LABEL --- */
.sidebar-section {
    color: #555 !important;
    font-size: 0.58rem !important;
    letter-spacing: 2.5px !important;
    text-transform: uppercase;
    font-weight: 800 !important;
    margin: 16px 0 6px 16px !important;
    padding: 0;
}

.sidebar-examples {
    padding: 0 16px;
}
.sidebar-example-item {
    font-size: 0.7rem;
    color: #777;
    padding: 4px 0;
    line-height: 1.3;
}

/* --- SIDEBAR NAV ITEMS --- */
.sidebar-nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    margin: 1px 8px;
    border-radius: 8px;
    color: #9A9EA9 !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    cursor: pointer;
    transition: all 0.2s;
    border-left: 3px solid transparent;
}
.sidebar-nav-item:hover {
    background: rgba(232,178,59,0.06) !important;
    color: var(--gold) !important;
}
.sidebar-nav-item.active {
    background: rgba(232,178,59,0.1) !important;
    color: var(--gold) !important;
    border-left-color: var(--gold) !important;
    font-weight: 700 !important;
}
.sidebar-nav-item .nav-icon {
    font-size: 14px;
    width: 20px;
    text-align: center;
    flex-shrink: 0;
}

/* --- SIDEBAR FORM LABELS --- */
[data-testid="stSidebar"] label {
    color: #888 !important;
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 2px !important;
}

/* --- SIDEBAR SELECTBOX --- */
[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: var(--bg-card) !important;
    border-color: rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    min-height: 36px !important;
}
[data-testid="stSidebar"] div[data-baseweb="select"] > div:hover {
    border-color: rgba(232,178,59,0.3) !important;
}

/* --- SIDEBAR CHECKBOX --- */
[data-testid="stSidebar"] div[data-baseweb="checkbox"] {
    font-size: 0.75rem !important;
}
[data-testid="stSidebar"] div[data-baseweb="checkbox"] span {
    color: #aaa !important;
}

/* --- SIDEBAR RADIO (perguntas sugeridas) --- */
[data-testid="stSidebar"] div[data-baseweb="radio"] {
    font-size: 0.72rem !important;
}
[data-testid="stSidebar"] div[data-baseweb="radio"] span {
    color: #bbb !important;
}
[data-testid="stSidebar"] div[data-baseweb="radio"]:hover span {
    color: var(--gold) !important;
}

/* --- SIDEBAR DIVIDER --- */
.sidebar-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.06);
    margin: 10px 16px;
}
</style>
"""


def inject_styles():
    """Injeta o CSS executive no app."""
    st.markdown(EXECUTIVE_CSS, unsafe_allow_html=True)


def render_exec_header(subtitulo: str = ""):
    """Renderiza o header executivo com glow gold."""
    st.markdown(
        f"""
        <div class="exec-header">
            <h1>DRE AGENTE</h1>
            <p>{subtitulo or "Demonstração do Resultado do Exercício · Inteligência Financeira"}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, sub: str = "", css_class: str = ""):
    """Renderiza um card KPI no estilo executive."""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value {css_class}">{value}</div>
            {f'<div class="kpi-sub">{sub}</div>' if sub else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_card(title: str, content: str):
    """Renderiza um card de seção."""
    st.markdown(
        f"""
        <div class="section-card">
            <h3>{title}</h3>
            {content}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer(versao: str = "1.0"):
    """Renderiza o footer executive."""
    st.markdown(
        f"""
        <div class="exec-footer">
            <div class="user-info">
                <span class="user-name">DRE AGENTE</span>
                <span> · Power BI Integration</span>
            </div>
            <div style="color:#555;">Febracis · v{versao}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_real_brazilian(valor: float, dividir_por_mil: bool = True) -> str:
    """Formata valor em R$ no padrão brasileiro."""
    if valor is None:
        return "R$ -"
    if dividir_por_mil:
        valor = valor / 1000
    if abs(valor) >= 1_000_000:
        return f"R$ {valor/1_000_000:,.1f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
    elif abs(valor) >= 1:
        return f"R$ {valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_pct_brazilian(valor: float) -> str:
    """Formata percentual no padrão brasileiro."""
    if valor is None:
        return "-"
    sinal = "+" if valor > 0 else ""
    return f"{sinal}{valor:.1%}".replace(",", "X").replace(".", ",").replace("X", ".")
