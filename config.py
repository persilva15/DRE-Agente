from pathlib import Path
from datetime import datetime

# =============================================================================
# CAMINHOS DOS ARQUIVOS EXCEL (conforme expressions.tmdl do Power BI)
# =============================================================================

NETWORK_BASE = r"\\10.5.12.252\controladoria"

PATHS = {
    "base_dre": rf"{NETWORK_BASE}\25 - BI\DRE\Base_DRE_v2.xlsx",
    "base_real_2025": rf"{NETWORK_BASE}\25 - BI\DRE\Base_Dre_2025_Congelada\Base_Real_2025.xlsx",
    "base_real_2024": rf"{NETWORK_BASE}\25 - BI\DRE\Base_DRE_v2_Real_24.xlsx",
    "orcado_2026": rf"{NETWORK_BASE}\24 - Orçamento\Orçamento 2026\ORCAMENTO_CONTABIL.xlsx",
    "forecast_2026": rf"{NETWORK_BASE}\24 - Orçamento\Orçamento 2026\Forecast 2026\FORECAST_CONTABIL.xlsx",
}

# =============================================================================
# ABAS DOS EXCEL (conforme partitions TMDL do Power BI)
# =============================================================================

SHEETS = {
    "base": "Base (2)",
    "plano_contas": "Dim (2)",
    "mascara_dre": "Mascara DRE",
    "auxiliar": "Auxiliar",
    "base_real_2025": "Base",
    "historica_2024": "Historica_2024",
    "orcado": "Base_Orcado",
    "forecast": "Plan. Forecast BI",
}

# =============================================================================
# MAPEAMENTO DE EMPRESAS (conforme DAX Empresa Final)
# =============================================================================

EMPRESAS_MAP = {
    25: "CIS TREINAMENTO",
    96: "PERSONALISSIMO",
    85: "FEBRACIS SELECT",
    14: "CIS ASSESSMENT",
    57: "CIS PAY",
    2: "CP SERVIÇOS",
    8: "FEBRACIS TECNOLOGIA DA INFORMAÇÃO",
    63: "FEBRACIS PART. E GESTÃO",
    6: "LIVRARIA FEBRACIS",
    47: "FACULDADE FEBRACIS",
    46: "INSTITUTO PAULO VIEIRA",
    101: "PERSONALISSIMO",
    103: "VERTUZ",
    106: "SIMPLIFICA",
    105: "SADI",
}

# Lista de nomes das empresas para busca
EMPRESAS_NOMES = sorted(set(EMPRESAS_MAP.values()))

# =============================================================================
# CLASSIFICAÇÃO DAS EMPRESAS (conforme tabela Auxiliar)
# =============================================================================

CLASSIFICACAO_MAP = {
    "CIS TREINAMENTO": "HOLDING",
    "PERSONALISSIMO": "HOLDING",
    "FEBRACIS SELECT": "HOLDING",
    "CIS ASSESSMENT": "COLIGADA",
    "CIS PAY": "COLIGADA",
    "CP SERVIÇOS": "HOLDING",
    "FEBRACIS TECNOLOGIA DA INFORMAÇÃO": "COLIGADA",
    "FEBRACIS PART. E GESTÃO": "HOLDING",
    "LIVRARIA FEBRACIS": "HOLDING",
    "FACULDADE FEBRACIS": "OUTROS",
    "INSTITUTO PAULO VIEIRA": "OUTROS",
    "VERTUZ": "COLIGADA",
    "SIMPLIFICA": "COLIGADA",
    "SADI": "COLIGADA",
}

# Lista de classificações disponíveis
CLASSIFICACOES = ["Consolidado", "HOLDING", "COLIGADA"]

# =============================================================================
# ESTRUTURA DRE (conforme tabela Mascara DRE)
# =============================================================================

MASCARA_DRE = [
    {"ordem": 1, "nivel_1": "Receita Bruta", "subtotal": "N"},
    {"ordem": 2, "nivel_1": "(-) Impostos", "subtotal": "N"},
    {"ordem": 2.5, "nivel_1": "(-) Devoluções e Descontos", "subtotal": "N"},
    {"ordem": 3, "nivel_1": "Receita Líquida", "subtotal": "S"},
    {"ordem": 4, "nivel_1": "(-) Custo Total", "subtotal": "N"},
    {"ordem": 5, "nivel_1": "Lucro Bruto (R$)", "subtotal": "S"},
    {"ordem": 6, "nivel_1": "(Despesas) Operacionais", "subtotal": "N"},
    {"ordem": 7, "nivel_1": "Ebitda", "subtotal": "N"},
    {"ordem": 8, "nivel_1": "(-) Depreciação, Amortização E Exaustão", "subtotal": "N"},
    {"ordem": 9, "nivel_1": "Ebit", "subtotal": "S"},
    {"ordem": 10, "nivel_1": "Receitas Financeiras", "subtotal": "N"},
    {"ordem": 10.5, "nivel_1": "(-) Despesas Financeiras", "subtotal": "N"},
    {"ordem": 11, "nivel_1": "Provisão Para Ir/Csll", "subtotal": "N"},
    {"ordem": 12, "nivel_1": "Lucro/Prejuízo Do Exercício", "subtotal": "S"},
]

# =============================================================================
# MESES
# =============================================================================

MESES_MAP = {
    "janeiro": 1, "jan": 1,
    "fevereiro": 2, "fev": 2,
    "março": 3, "marco": 3, "mar": 3,
    "abril": 4, "abr": 4,
    "maio": 5, "mai": 5,
    "junho": 6, "jun": 6,
    "julho": 7, "jul": 7,
    "agosto": 8, "ago": 8,
    "setembro": 9, "set": 9,
    "outubro": 10, "out": 10,
    "novembro": 11, "nov": 11,
    "dezembro": 12, "dez": 12,
}

MESES_NOMES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}

# =============================================================================
# MÊS CORRENTE (automático)
# =============================================================================

DATA_ATUAL = datetime.now()
MES_CORRENTE = DATA_ATUAL.month
ANO_CORRENTE = DATA_ATUAL.year

# =============================================================================
# COLUNAS DA TABELA DRE (conforme aba "DRE vs Orçamento 26 (Visão José Alberto)")
# =============================================================================

DRE_COLUNAS = [
    {"key": "r_2025", "label": "R 2025 (R$)", "tipo": "valor", "fonte": "realizado", "ano": 2025},
    {"key": "av_2025", "label": "AV 2025", "tipo": "av", "fonte": "realizado", "ano": 2025},
    {"key": "r_2026", "label": "R 2026 (R$)", "tipo": "valor", "fonte": "realizado", "ano": 2026},
    {"key": "av_2026", "label": "AV 2026", "tipo": "av", "fonte": "realizado", "ano": 2026},
    {"key": "var_r26_r25_pct", "label": "Var (%) R26/R25", "tipo": "var_pct", "fonte": "calculado"},
    {"key": "var_r26_r25_rs", "label": "Var (R$) R26/R25", "tipo": "var_rs", "fonte": "calculado"},
    {"key": "o_2026", "label": "O 2026 (R$)", "tipo": "valor", "fonte": "orcado", "ano": 2026},
    {"key": "av_o_2026", "label": "AV O 2026", "tipo": "av", "fonte": "orcado", "ano": 2026},
    {"key": "var_o26_r26_pct", "label": "Var (%) O26/R26", "tipo": "var_pct", "fonte": "calculado"},
    {"key": "var_o26_r26_rs", "label": "Var (R$) O26/R26", "tipo": "var_rs", "fonte": "calculado"},
]
