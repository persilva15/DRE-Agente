import re
from typing import Optional
from config import MESES_MAP, EMPRESAS_NOMES, MES_CORRENTE, ANO_CORRENTE


class QuestionParser:
    """
    Parser de perguntas em linguagem natural usando regex.

    Extrai: métrica, empresa, período, tipo de análise.
    """

    # =============================================================================
    # PADRÕES DE MÉTRICAS
    # =============================================================================

    METRICAS_PATTERNS = {
        "ebitda": r"\beb\w*(?:da|ta)\b",
        "ebit": r"\beb[ií]t\b|\bebit\b",
        "receita_bruta": r"\breceita\s*bruta\b",
        "receita_liquida": r"\breceita\s*l[ií]quida\b",
        "lucro_bruto": r"\blucro\s*bruto\b",
        "despesas_operacionais": r"\bdespesas?\s*operacionai[s]?\b|\b\(?despesas?\)?\s*operacionai[s]?\b",
        "custo": r"\bcusto\s*total\b|\bcusto\b",
        "impostos": r"\bimpostos?\b|\btributos?\b",
        "lucro": r"\blucro\s*(?:l[ií]quido)?\b|\bpreju[ií]zo\b",
        "receita_financeira": r"\breceitas?\s*financeiras?\b",
        "despesa_financeira": r"\bdespesas?\s*financeiras?\b",
        "depreciacao": r"\bdepreciação\b|\bdepreciacao\b|\bamortização\b|\bamortizacao\b|\bdae\b",
        "provisao": r"\bprovisão\b|\bprovisao\b|\bir\s*/?\s*csll\b",
    }

    # =============================================================================
    # PADRÕES DE TIPO DE ANÁLISE
    # =============================================================================

    ANALISE_PATTERNS = {
        "real_vs_orcado": [
            r"\breal\s*vs\s*[oó]rcado\b",
            r"\bor[cç]ado\s*vs\s*real\b",
            r"\brealizado\s*vs\s*or[cç]ado\b",
            r"\bor[cç]ado\s*vs\s*realizado\b",
            r"\bvariação\s*(?:entre\s*)?real\s*(?:e|vs)\s*or[cç]ado\b",
            r"\breal(?:izado)?\s*(?:e|vs)\s*or[cç]ado\b",
        ],
        "real_vs_forecast": [
            r"\breal\s*vs\s*forecast\b",
            r"\bforecast\s*vs\s*real\b",
            r"\brealizado\s*vs\s*forecast\b",
            r"\bforecast\s*vs\s*realizado\b",
            r"\bvariação\s*(?:entre\s*)?real\s*(?:e|vs)\s*forecast\b",
            r"\breal(?:izado)?\s*(?:e|vs)\s*forecast\b",
        ],
        "forecast_vs_orcado": [
            r"\bforecast\s*vs\s*[oó]rcado\b",
            r"\bor[cç]ado\s*vs\s*forecast\b",
            r"\bvariação\s*(?:entre\s*)?forecast\s*(?:e|vs)\s*or[cç]ado\b",
            r"\bforecast\s*(?:e|vs)\s*or[cç]ado\b",
        ],
        "av": [
            r"\banálise\s*vertical\b",
            r"\banalise\s*vertical\b",
            r"\bav\b",
        ],
        "ah": [
            r"\banálise\s*horizontal\b",
            r"\banalise\s*horizontal\b",
            r"\bah\b",
        ],
    }

    # =============================================================================
    # PADRÕES DE PERÍODO
    # =============================================================================

    PERIODO_PATTERNS = {
        "ytd": [
            r"\bytd\b",
            r"\bacumulado\b",
            r"\bat[eé]\s*agora\b",
            r"\bat[eé]\s*o\s*m[eê]s\s*corrente\b",
            r"\nm[eê]s\s*corrente\b",
            r"\nm[eê]s\s*atual\b",
        ],
        "mes_especifico": [
            r"(?:em|no|de|do)\s*(janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)",
            r"(?:em|no|de|do)\s*(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)",
            r"(janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)",
            r"(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)",
        ],
    }

    # =============================================================================
    # PADRÕES DE EMPRESA
    # =============================================================================

    EMPRESA_PATTERNS = {
        "consolidado": [
            r"\bconsolidado\b",
            r"\bconsolidad\b",
            r"\btotal\b",
            r"\bgeral\b",
            r"\btodas\b",
            r"\bholding\b",
        ],
        "cis_treinamento": [
            r"\bcis\s*treinamento\b",
            r"\bcis\b(?!.*(?:pay|assessment|select))",
        ],
        "personalissimo": [
            r"\bpersonal[ií]ssimo\b",
            r"\bpersonal\b",
        ],
        "febracis_select": [
            r"\bfebracis\s*select\b",
            r"\bselect\b",
        ],
        "cis_assessment": [
            r"\bcis\s*assessment\b",
            r"\bassessment\b",
        ],
        "cis_pay": [
            r"\bcis\s*pay\b",
            r"\bpay\b",
        ],
        "livraria": [
            r"\blivraria\b",
            r"\blivro\b",
        ],
        "faculdade": [
            r"\bfaculdade\b",
        ],
        "febracis_part": [
            r"\bfebracis\s*part\b",
            r"\bpart\.?\s*e\s*gestão\b",
        ],
        "cp_servicos": [
            r"\bcp\s*servi[cç]os\b",
        ],
        "vertuz": [
            r"\bvertuz\b",
        ],
        "simplifica": [
            r"\bsimplifica\b",
        ],
        "sadi": [
            r"\bsadi\b",
        ],
    }

    # Mapeamento de nomes das empresas
    EMPRESAS_MAP_REVERSE = {
        "consolidado": None,  # None = consolidado
        "cis_treinamento": "CIS TREINAMENTO",
        "personalissimo": "PERSONALISSIMO",
        "febracis_select": "FEBRACIS SELECT",
        "cis_assessment": "CIS ASSESSMENT",
        "cis_pay": "CIS PAY",
        "livraria": "LIVRARIA FEBRACIS",
        "faculdade": "FACULDADE FEBRACIS",
        "febracis_part": "FEBRACIS PART. E GESTÃO",
        "cp_servicos": "CP SERVIÇOS",
        "vertuz": "VERTUZ",
        "simplifica": "SIMPLIFICA",
        "sadi": "SADI",
    }

    # =============================================================================
    # PADRÕES DE ANO
    # =============================================================================

    ANO_PATTERN = r"\b(20\d{2})\b"

    def parse(self, pergunta: str) -> dict:
        """
        Analisa a pergunta e extrai elementos.

        Returns:
            Dict com: metrica, empresa, mes, ano, tipo_analise
        """
        pergunta_lower = pergunta.lower().strip()

        resultado = {
            "metrica": self._extrair_metrica(pergunta_lower),
            "empresa": self._extrair_empresa(pergunta_lower),
            "mes": self._extrair_mes(pergunta_lower),
            "ano": self._extrair_ano(pergunta_lower),
            "tipo_analise": self._extrair_tipo_analise(pergunta_lower),
            "pergunta_original": pergunta,
        }

        # Defaults
        if resultado["ano"] is None:
            resultado["ano"] = ANO_CORRENTE
        # Mês é opcional - None significa "todos os meses" (acumulado anual)
        # Só define mês default para perguntas que mencionam "até agora" ou "mês corrente"
        if resultado["mes"] is None and resultado["tipo_analise"] is None:
            # Verificar se a pergunta menciona período acumulado
            for pattern in self.PERIODO_PATTERNS["ytd"]:
                if re.search(pattern, pergunta, re.IGNORECASE):
                    resultado["mes"] = MES_CORRENTE
                    break

        return resultado

    def _extrair_metrica(self, pergunta: str) -> Optional[str]:
        """Extrai a métrica DRE da pergunta."""
        for metrica, pattern in self.METRICAS_PATTERNS.items():
            if re.search(pattern, pergunta, re.IGNORECASE):
                return metrica
        return None

    def _extrair_empresa(self, pergunta: str) -> Optional[str]:
        """Extrai a empresa da pergunta."""
        for empresa_key, patterns in self.EMPRESA_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, pergunta, re.IGNORECASE):
                    return self.EMPRESAS_MAP_REVERSE.get(empresa_key)

        # Tentar encontrar nomes de empresas diretamente
        for nome in EMPRESAS_NOMES:
            if nome.lower() in pergunta:
                return nome

        return None  # Default: consolidado

    def _extrair_mes(self, pergunta: str) -> Optional[int]:
        """Extrai o mês da pergunta."""
        # Verificar período YTD
        for pattern in self.PERIODO_PATTERNS["ytd"]:
            if re.search(pattern, pergunta, re.IGNORECASE):
                return MES_CORRENTE

        # Buscar mês específico
        for pattern in self.PERIODO_PATTERNS["mes_especifico"]:
            match = re.search(pattern, pergunta, re.IGNORECASE)
            if match:
                mes_str = match.group(1).lower()
                return MESES_MAP.get(mes_str)

        return None

    def _extrair_ano(self, pergunta: str) -> Optional[int]:
        """Extrai o ano da pergunta."""
        match = re.search(self.ANO_PATTERN, pergunta)
        if match:
            return int(match.group(1))
        return None

    def _extrair_tipo_analise(self, pergunta: str) -> Optional[str]:
        """Extrai o tipo de análise da pergunta."""
        for tipo, patterns in self.ANALISE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, pergunta, re.IGNORECASE):
                    return tipo
        return None
