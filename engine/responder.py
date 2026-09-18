import pandas as pd
import re
from typing import Optional

from engine.dre_logic import DRELogic
from engine.parser import QuestionParser
from utils.formatting import (
    formatar_valor,
    formatar_variacao_rs,
    formatar_variacao_pct,
    formatar_indicador,
)
from config import MESES_NOMES, MES_CORRENTE, ANO_CORRENTE, DRE_COLUNAS


# =============================================================================
# PERSONALIDADE DO AGENTE
# =============================================================================

SYSTEM_PROMPT = """Você é um CFO Virtual e Especialista em Controladoria de Finanças Corporativas. Seu único propósito é analisar a DRE (Demonstração do Resultado do Exercício) apresentada na tela e fornecer respostas, análises e insights executivos.

SUA MISSÃO:
1. Responder a dúvidas pontuais sobre as linhas e variações da DRE (Receita Bruta, Deduções, Receita Líquida, CPV/CMV, Lucro Bruto, OPEX/Despesas Operacionais, EBITDA, Resultado Financeiro e Lucro Líquido).
2. Fornecer insights analíticos sobre a saúde financeira do período analisado (Análise Vertical e Análise Horizontal).
3. Comparar as margens e a estrutura de custos obtidas com as melhores práticas e benchmarks de mercado.

REGRAS DE ESCOPO E SEGURANÇA:
1. Responda EXCLUSIVAMENTE sobre os dados da DRE informada e tópicos de gestão financeira corporativa aplicáveis a esses resultados.
2. Se o usuário perguntar algo fora deste escopo (notícias gerais, suporte ao sistema, programação, receitas, piadas ou outros temas alheios ao DRE), recuse educadamente usando exatamente a mensagem abaixo:
"Desculpe, mas meu foco é exclusivamente a análise do DRE e estratégias financeiras para este painel. Como posso ajudar a interpretar os resultados atuais?"

COMO ESTRUTURAR OS INSIGHTS:
- Sempre relacione o resultado numérico com a causa e a consequência financeira.
- Para cada insight importante, destaque:
  * O Achado (O que aconteceu na DRE?)
  * Benchmark de Mercado (Como o mercado se comporta nesse cenário?)
  * Ação Recomendada (Qual alavanca financeira acionar?)

FORMATO DAS RESPOSTAS:
- Seja conciso, técnico e executivo.
- Use tópicos (bullet points) para destacar os principais achados.
- Ao apontar um problema ou variação nos dados, sempre sugira ações corretivas com base em benchmarks de mercado.
"""

# Mensagem para perguntas fora do escopo
MSG_FORA_ESCOPO = """Desculpe, mas meu foco é exclusivamente a análise do DRE e estratégias financeiras para este painel. Como posso ajudar a interpretar os resultados atuais?"""

# Palavras-chave que indicam perguntas FORA do escopo
OUT_OF_SCOPE_KEYWORDS = [
    r"\bpiada\b", r"\bengraçad", r"\brir\b",
    r"\bcódigo\b", r"\bprograma\b", r"\bpython\b", r"\bjavascript\b",
    r"\bnotícia\b", r"\bnoticias\b", r"\bfutebol\b", r"\besporte\b",
    r"\bculpa\b", r"\bresponsável\b", r"\bculpar\b",
    r"\bfeliz\b", r"\bamor\b", r"\bvida\b",
    r"\bmédico\b", r"\bdoença\b", r"\bsaúde\b",
    r"\bcomo\b.*\bcozinhar\b",
    r"\btempo\b.*\bclima\b",
    r"\bprevisão\b.*\btempo\b",
    r"\bfilme\b", r"\bmúsica\b",
    r"\bsuporte\b.*\btécnico\b", r"\bagente\b.*\bchu\b",
    r"\bcomo\b.*\binstalar\b",
    r"\bajuda\b(?!.*dados)",
    r"\bqual\b.*\bseu\b.*\bnome\b",
    r"\bquem\b.*\bvoce\b",
    r"\bobrigad\b", r"\bobrigado\b",
    r"\bpor\b.*\bfavor\b",
    r"\bdesculp\b",
    r"\bok\b", r"\bblz\b", r"\bvlw\b",
    r"\btchau\b", r"\bacabou\b",
    r"\bteste\b", r"\btest\b",
    r"\b1\b", r"\b2\b", r"\b3\b",
    r"\bai\b", r"\bhum\b", r"\beh\b",
    r"\bcerto\b", r"\bcerto\?\b",
    r"\be\b.*\bvoc[eê]\b",
    r"\bvoc[eê]\b.*\be\b",
    r"\bfala\b", r"\boi\b", r"\bolá\b", r"\bole\b",
]

# Palavras-chave que indicam perguntas SOBRE o painel (para diferenciar de fora do escopo)
DRE_KEYWORDS = [
    r"\bdre\b", r"\bresultado\b", r"\bexercício\b",
    r"\breceita\b", r"\bcusto\b", r"\bdespesa\b", r"\bdespesas\b",
    r"\beb\w*(?:da|ta)\b",
    r"\blucro\b", r"\bprejuízo\b", r"\bprejuizo\b",
    r"\bor[cç]ado\b", r"\bforecast\b", r"\brealizado\b",
    r"\bvariação\b", r"\bvaria[çc][ãa]o\b",
    r"\bimposto\b", r"\bimpostos\b",
    r"\bdepreciação\b", r"\bamortização\b",
    r"\bprovisão\b", r"\bprovisao\b",
    r"\bfinanceira\b", r"\bfinanceiras\b",
    r"\bempresa\b", r"\bconsolidado\b",
    r"\bholding\b", r"\bcoligada\b",
    r"\bcis\b", r"\bfebracis\b", r"\bpersonalissimo\b",
    r"\bvertuz\b", r"\bpay\b", r"\bassessment\b",
    r"\blivraria\b", r"\bcp\b", r"\bsadi\b", r"\bsimplifica\b",
    r"\bav\b", r"\banálise\s*vertical\b",
    r"\bytd\b", r"\bacumulado\b",
    r"\bmes\b", r"\bm[eê]s\b",
    r"\b202[0-9]\b",
]


class Responder:
    """
    Gera respostas formatadas para as perguntas do usuário.
    Age como especialista em análise de dados do painel DRE.
    """

    # Mapeamento de métricas para nomes de exibição
    METRICAS_DISPLAY = {
        "ebitda": "EBITDA",
        "ebit": "EBIT",
        "receita_bruta": "Receita Bruta",
        "receita_liquida": "Receita Líquida",
        "lucro_bruto": "Lucro Bruto",
        "despesas_operacionais": "Despesas Operacionais",
        "custo": "Custo Total",
        "impostos": "Impostos",
        "lucro": "Lucro/Prejuízo do Exercício",
        "receita_financeira": "Receitas Financeiras",
        "despesa_financeira": "Despesas Financeiras",
        "depreciacao": "Depreciação, Amortização e Exaustão",
        "provisao": "Provisão para IR/CSLL",
    }

    # Mapeamento de métricas para nomes na máscara DRE
    METRICAS_MASCARA = {
        "ebitda": "Ebitda",
        "ebit": "Ebit",
        "receita_bruta": "Receita Bruta",
        "receita_liquida": "Receita Líquida",
        "lucro_bruto": "Lucro Bruto (R$)",
        "despesas_operacionais": "(Despesas) Operacionais",
        "custo": "(-) Custo Total",
        "impostos": "(-) Impostos",
        "lucro": "Lucro/Prejuízo Do Exercício",
        "receita_financeira": "Receitas Financeiras",
        "despesa_financeira": "(-) Despesas Financeiras",
        "depreciacao": "(-) Depreciação, Amortização E Exaustão",
        "provisao": "Provisão Para Ir/Csll",
    }

    def __init__(self, dre_logic: DRELogic):
        self.dre_logic = dre_logic
        self.parser = QuestionParser()

    def _is_out_of_scope(self, pergunta: str) -> bool:
        """Verifica se a pergunta está fora do escopo do painel."""
        pergunta_lower = pergunta.lower().strip()

        # Perguntas muito curtas (< 5 caracteres) - fora do escopo
        if len(pergunta_lower) < 5:
            return True

        # Verificar padrões explicitamente fora do escopo
        for pattern in OUT_OF_SCOPE_KEYWORDS:
            if re.search(pattern, pergunta_lower, re.IGNORECASE):
                return True

        # Verificar se tem alguma palavra-chave do DRE
        for pattern in DRE_KEYWORDS:
            if re.search(pattern, pergunta_lower, re.IGNORECASE):
                return False  # Tem keyword DRE, NÃO está fora do escopo

        # Se não tem nenhuma palavra-chave do DRE, está fora do escopo
        return True

    def responder(self, pergunta: str, elementos: Optional[dict] = None) -> str:
        """
        Processa a pergunta e retorna a resposta formatada.
        """
        # Verificar se está fora do escopo (PRIMEIRO de tudo)
        if self._is_out_of_scope(pergunta):
            return MSG_FORA_ESCOPO

        # Parse da pergunta (usar elementos fornecidos ou re-parse)
        if elementos is None:
            elementos = self.parser.parse(pergunta)

        metrica = elementos["metrica"]
        empresa = elementos["empresa"]
        mes = elementos["mes"]
        ano = elementos["ano"]
        tipo_analise = elementos["tipo_analise"]

        # Determinar empresa para exibição
        empresa_display = empresa if empresa else "Consolidado"
        mes_display = MESES_NOMES.get(mes, "Corrente") if mes else "Corrente"
        ano_display = ano if ano else ANO_CORRENTE

        # Se tem tipo de análise, retornar comparação
        if tipo_analise:
            return self._responder_variacao(
                tipo_analise, empresa, mes, ano, empresa_display, mes_display, ano_display
            )

        # Se tem métrica, retornar valor específico
        if metrica:
            return self._responder_metrica(
                metrica, empresa, mes, ano, empresa_display, mes_display, ano_display
            )

        # Default: retornar DRE completo
        return self._responder_dre_completo(
            empresa, mes, ano, empresa_display, mes_display, ano_display
        )

    def _formatar_resposta(self, texto: str) -> str:
        """Formata a resposta como markdown puro."""
        return texto

    def _formatar_valor_rs(self, valor: float) -> str:
        """Formata valor em R$ mil."""
        if valor == 0:
            return "R$ -"
        return f"R$ {valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _formatar_pct(self, valor: float) -> str:
        """Formata percentual."""
        sinal = "+" if valor > 0 else ""
        return f"{sinal}{valor:.1%}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _responder_metrica(
        self,
        metrica: str,
        empresa: Optional[str],
        mes: Optional[int],
        ano: int,
        empresa_display: str,
        mes_display: str,
        ano_display: int,
    ) -> str:
        """Responde sobre uma métrica específica com insights usando dados XMLA."""
        nome_display = self.METRICAS_DISPLAY.get(metrica, metrica)
        nome_mascara = self.METRICAS_MASCARA.get(metrica, metrica)

        # Usar dados XMLA se disponíveis (mesma fonte da tabela principal)
        dre_xmla = self.dre_logic.data.get("dre_xmla", {})
        
        if dre_xmla and dre_xmla.get("real_2026"):
            r26 = dre_xmla.get("real_2026", {})
            f26 = dre_xmla.get("forecast_2026", {})
            o26 = dre_xmla.get("orcado_2026", {})
            r25 = dre_xmla.get("real_2025", {})
            
            valor = r26.get(nome_mascara, 0)
            valor_f = f26.get(nome_mascara, 0)
            valor_o = o26.get(nome_mascara, 0)
            valor_25 = r25.get(nome_mascara, 0)
            
            rb_r26 = r26.get("Receita Bruta", 0)
            rb_f26 = f26.get("Receita Bruta", 0)
            rb_o26 = o26.get("Receita Bruta", 0)
            rb_r25 = r25.get("Receita Bruta", 0)
            
            av_r26 = (valor / rb_r26) if rb_r26 != 0 else 0
            av_f26 = (valor_f / rb_f26) if rb_f26 != 0 else 0
            av_o26 = (valor_o / rb_o26) if rb_o26 != 0 else 0
            av_r25 = (valor_25 / rb_r25) if rb_r25 != 0 else 0
            
            var_r26_r25 = valor - valor_25
            var_f26_r26 = valor_f - valor
            var_f26_o26 = valor_f - valor_o
            
            var_r26_r25_pct = (var_r26_r25 / abs(valor_25)) if valor_25 != 0 else 0
            var_f26_r26_pct = (var_f26_r26 / abs(valor)) if valor != 0 else 0
            var_f26_o26_pct = (var_f26_o26 / abs(valor_o)) if valor_o != 0 else 0
            
            insight = self._gerar_insight_metrica(metrica, valor, rb_r26, empresa_display)
            
            linhas = [
                f"**{nome_display}** — {empresa_display}",
                f"",
                f"**R 2025:** {self._formatar_valor_rs(valor_25)} (AV: {self._formatar_pct(av_r25)})",
                f"**F 2026:** {self._formatar_valor_rs(valor_f)} (AV: {self._formatar_pct(av_f26)})",
                f"**R 2026:** {self._formatar_valor_rs(valor)} (AV: {self._formatar_pct(av_r26)})",
                f"**O 2026:** {self._formatar_valor_rs(valor_o)} (AV: {self._formatar_pct(av_o26)})",
                f"",
                f"**Variações:**",
                f"- R26 vs R25: **{self._formatar_valor_rs(var_r26_r25)}** ({self._formatar_pct(var_r26_r25_pct)})",
                f"- F26 vs R26: **{self._formatar_valor_rs(var_f26_r26)}** ({self._formatar_pct(var_f26_r26_pct)})",
                f"- F26 vs O26: **{self._formatar_valor_rs(var_f26_o26)}** ({self._formatar_pct(var_f26_o26_pct)})",
                f"",
                f"**Insight:** {insight}",
            ]
            
            return "\n".join(linhas)

        return self._formatar_resposta("\n".join(linhas))

    def _gerar_insight_metrica(self, metrica: str, valor: float, rb: float, empresa: str) -> str:
        """Gera insight no formato CFO: Achado → Benchmark → Ação Recomendada."""
        av = (valor / rb * 100) if rb != 0 else 0

        if metrica == "ebitda":
            if av > 15:
                return (
                    f"**Achado:** EBITDA de {av:.1f}% sobre a Receita Bruta, indicando solidez operacional.\n"
                    f"**Benchmark:** Margem EBITDA saudável está entre 15%-25% para empresas de serviços B2B.\n"
                    f"**Ação:** Manter disciplina de custos e investir em inovação para escalar resultado."
                )
            elif av > 5:
                return (
                    f"**Achado:** EBITDA de {av:.1f}% — margem moderada com potencial de melhoria.\n"
                    f"**Benchmark:** Empresas do setor de serviços premium buscam EBITDA acima de 15%.\n"
                    f"**Ação:** Revisar Despesas Operacionais (SG&A) e identificar itens fixos passíveis de redução."
                )
            else:
                return (
                    f"**Achado:** EBITDA de apenas {av:.1f}% — margem operacional comprometida.\n"
                    f"**Benchmark:** Margens abaixo de 5% são insustentáveis no médio prazo.\n"
                    f"**Ação:** Urgente: revisar estrutura de CPV/CMV e OPEX. Buscar eficiência operacional."
                )

        elif metrica == "receita_bruta":
            return (
                f"**Achado:** Receita Bruta de {self._formatar_valor_rs(valor)} como linha de partida do DRE.\n"
                f"**Benchmark:** Crescimento saudável de receita B2B deve ser ≥8% a.a. acima da inflação.\n"
                f"**Ação:** Monitorar composição de receita (recorrente vs. projetos) e sazonalidade."
            )

        elif metrica == "receita_liquida":
            if rb > 0:
                deducoes_pct = ((rb - valor) / rb * 100)
                return (
                    f"**Achado:** Receita Líquida de {self._formatar_valor_rs(valor)} (deduções de {deducoes_pct:.1f}% sobre a Bruta).\n"
                    f"**Benchmark:** Deduções sobre receita bruta acima de 15% indicam exposição a impostos ou devoluções elevadas.\n"
                    f"**Ação:** Analisar composição das deduções (impostos, devoluções, abatimentos) para otimizar carga tributária."
                )
            return f"**Achado:** Receita Líquida de {self._formatar_valor_rs(valor)}."

        elif metrica == "lucro":
            if valor > 0:
                return (
                    f"**Achado:** Lucro Líquido positivo de {self._formatar_valor_rs(valor)} ({av:.1f}% da Receita Bruta).\n"
                    f"**Benchmark:** Margem líquida saudável está entre 8%-15% para empresas maduras.\n"
                    f"**Ação:** Avaliar sustentabilidade do resultado e potencial de distribuição de dividendos."
                )
            else:
                return (
                    f"**Achado:** Prejuízo de {self._formatar_valor_rs(abs(valor))} ({av:.1f}% da Receita Bruta).\n"
                    f"**Benchmark:** Prejuízo operacional recorrente compromete a viabilidade do negócio.\n"
                    f"**Ação:** Análise de causa-raiz: custos acima do orçado, receitas abaixo da meta ou despesas financeiras elevadas."
                )

        elif metrica == "custo":
            if rb > 0:
                return (
                    f"**Achado:** Custo Total de {av:.1f}% sobre a Receita Bruta.\n"
                    f"**Benchmark:** Para serviços, CPV/CMV ideal deve estar entre 40%-60% da Receita Bruta.\n"
                    f"**Ação:** Decompor custos em fixos vs. variáveis e identificar alavancas de eficiência."
                )
            return f"**Achado:** Custo Total de {self._formatar_valor_rs(valor)}."

        elif metrica == "impostos":
            if rb > 0:
                return (
                    f"**Achado:** Impostos representam {av:.1f}% da Receita Bruta.\n"
                    f"**Benchmark:** Carga tributária eficiente para empresas de serviços está entre 8%-15%.\n"
                    f"**Ação:** Revisar planejamento tributário e regimes de tributação (Lucro Presumido vs. Real)."
                )
            return f"**Achado:** Impostos de {self._formatar_valor_rs(valor)}."

        elif metrica == "despesas_operacionais":
            if rb > 0:
                return (
                    f"**Achado:** Despesas Operacionais de {av:.1f}% da Receita Bruta impactam diretamente o EBITDA.\n"
                    f"**Benchmark:** SG&A saudável para B2B está entre 15%-25% da Receita Bruta.\n"
                    f"**Ação:** Identificar categorias de maior peso (Pessoal, Marketing, Administrativo) e otimizar."
                )
            return f"**Achado:** Despesas Operacionais de {self._formatar_valor_rs(valor)}."

        elif metrica == "receita_financeira":
            return (
                f"**Achado:** Receitas Financeiras de {self._formatar_valor_rs(valor)}.\n"
                f"**Benchmark:** Receitas financeiras devem ser complementares, não a fonte principal de resultado.\n"
                f"**Ação:** Avaliar política de caixa e investimentos de curtíssimo prazo."
            )

        elif metrica == "despesa_financeira":
            return (
                f"**Achado:** Despesas Financeiras de {self._formatar_valor_rs(valor)}.\n"
                f"**Benchmark:** Custo da dívida acima de CDI+2% indica necessidade de renegociação.\n"
                f"**Ação:** Revisar endividamento e custo de capital."
            )

        elif metrica == "depreciacao":
            return (
                f"**Achido:** Depreciação/Amortização de {self._formatar_valor_rs(valor)}.\n"
                f"**Benchmark:** DAE deve ser monitorado para manter EBITDA e EBIT alinhados.\n"
                f"**Ação:** Avaliar vida útil dos ativos e necessidade de atualização patrimonial."
            )

        elif metrica == "provisao":
            return (
                f"**Achado:** Provisão para IR/CSLL de {self._formatar_valor_rs(valor)}.\n"
                f"**Benchmark:** Provisão deve refletir efetiva expectativa de imposto a pagar.\n"
                f"**Ação:** Validar base de cálculo e planejamento tributário."
            )

        return f"Analisar a tendência desta métrica ao longo dos meses para identificar **padrões e anomalias**."

    def _responder_variacao(
        self,
        tipo: str,
        empresa: Optional[str],
        mes: Optional[int],
        ano: int,
        empresa_display: str,
        mes_display: str,
        ano_display: int,
    ) -> str:
        """Responde sobre variação entre cenários com insights."""
        nomes_tipo = {
            "real_vs_orcado": ("Realizado", "Orçado"),
            "real_vs_forecast": ("Realizado", "Forecast"),
            "forecast_vs_orcado": ("Forecast", "Orçado"),
        }
        nome_a, nome_b = nomes_tipo.get(tipo, ("A", "B"))

        variacao = self.dre_logic.calcular_variacao(tipo, empresa, mes, ano)

        if not variacao:
            return self._formatar_resposta("Não foi possível calcular a variação com os dados disponíveis.")

        # Identificar maiores variações
        maiores_variacoes = []
        for nivel_1, dados in variacao.items():
            if dados["ordem"] in [1, 3, 5, 7, 9, 12]:  # Linhas principais
                maiores_variacoes.append((nivel_1, dados))

        # Montar resposta
        linhas = [
            f"**Variação {nome_a} vs {nome_b}**",
            f"",
            f"- **Empresa:** {empresa_display}",
            f"- **Período:** Até {mes_display}/{ano_display}",
            f"",
        ]

        # Tabela resumida das linhas principais
        linhas.append(f"**Linha DRE | {nome_a} | {nome_b} | Var R$ | Var %**")
        linhas.append(f"---|---|---|---|---")

        for nivel_1, dados in sorted(variacao.items(), key=lambda x: x[1]["ordem"]):
            v_a = self._formatar_valor_rs(dados["valor_a"])
            v_b = self._formatar_valor_rs(dados["valor_b"])
            var_rs = formatar_variacao_rs(dados["variacao_rs"], dividir_por_mil=True)
            var_pct = formatar_variacao_pct(dados["variacao_pct"])

            if dados["subtotal"] == "S":
                linhas.append(f"**{nivel_1}** | **{v_a}** | **{v_b}** | **{var_rs}** | **{var_pct}**")
            else:
                linhas.append(f"{nivel_1} | {v_a} | {v_b} | {var_rs} | {var_pct}")

        # Insights
        linhas.append(f"")
        linhas.append(f"**Principais Achados:**")

        insights = self._gerar_insights_variacao(variacao, nome_a, nome_b)
        for insight in insights:
            linhas.append(f"- {insight}")

        return self._formatar_resposta("\n".join(linhas))

    def _gerar_insights_variacao(self, variacao: dict, nome_a: str, nome_b: str) -> list:
        """Gera insights no formato CFO: Achado → Benchmark → Ação para variações."""
        insights = []

        # Receita Bruta
        rb = variacao.get("Receita Bruta", {})
        if rb:
            var_pct = rb.get("variacao_pct", 0)
            if var_pct > 0.1:
                insights.append(
                    f"**Achado:** Receita Bruta cresceu {abs(var_pct):.1%} de {nome_b} para {nome_a}. "
                    f"**Benchmark:** Crescimento orgânico saudável está entre 8%-15% a.a. acima da inflação. "
                    f"**Ação:** Verificar se o crescimento é orgânico (cross-sell/upsell) ou por novos contratos."
                )
            elif var_pct < -0.1:
                insights.append(
                    f"**Achado:** Receita Bruta caiu {abs(var_pct):.1%} de {nome_b} para {nome_a}. "
                    f"**Benchmark:** Quedas acima de 5% em um período exigem ação imediata. "
                    f"**Ação:** Analisar churn de clientes, contratos perdidos ou sazonalidade."
                )
            else:
                insights.append(
                    f"**Achado:** Receita Bruta estável (variação de {var_pct:.1%}). "
                    f"**Benchmark:** Estabilidade pode indicar maturidade ou estagnação. "
                    f"**Ação:** Buscar oportunidades de crescimento em novos segmentos ou serviços."
                )

        # Custo Total
        ct = variacao.get("(-) Custo Total", {})
        if ct:
            var_pct = ct.get("variacao_pct", 0)
            if var_pct > 0.05:
                insights.append(
                    f"**Achado:** Custo Total aumentou {abs(var_pct):.1%} de {nome_b} para {nome_a}. "
                    f"**Benchmark:** Custos devem crescer abaixo da receita para melhorar margens. "
                    f"**Ação:** Avaliar se o aumento é justificado pelo crescimento da receita ou é arbítrio."
                )
            elif var_pct < -0.05:
                insights.append(
                    f"**Achido:** Custo Total reduziu {abs(var_pct):.1%}. "
                    f"**Benchmark:** Redução de custos sem impacto na receita é eficiência pura. "
                    f"**Ação:** Validar se a redução é sustentável ou foi pontual."
                )

        # Despesas Operacionais
        do = variacao.get("(Despesas) Operacionais", {})
        if do:
            var_pct = do.get("variacao_pct", 0)
            if abs(var_pct) > 0.1:
                sinal = "aumentaram" if var_pct > 0 else "reduziram"
                insights.append(
                    f"**Achado:** Despesas Operacionais {sinal} {abs(var_pct):.1%} de {nome_b} para {nome_a}. "
                    f"**Benchmark:** SG&A deve ser controlado e representar no máximo 25% da Receita Bruta. "
                    f"**Ação:** Identificar categorias de maior impacto (Pessoal, Marketing, Administrativo) e otimizar."
                )

        # EBITDA
        ebitda = variacao.get("Ebitda", {})
        if ebitda:
            var_rs = ebitda.get("variacao_rs", 0)
            var_pct = ebitda.get("variacao_pct", 0)
            if var_rs > 0:
                insights.append(
                    f"**Achado:** EBITDA melhorou R$ {var_rs:,.0f} mil (+{abs(var_pct):.1%}) de {nome_b} para {nome_a}. "
                    f"**Benchmark:** Melhoria de EBITDA indica ganho de eficiência operacional. "
                    f"**Ação:** Manter as alavancas de melhoria e monitorar sustentabilidade."
                )
            elif var_rs < 0:
                insights.append(
                    f"**Achado:** EBITDA piorou R$ {abs(var_rs):,.0f} mil ({var_pct:.1%}) de {nome_b} para {nome_a}. "
                    f"**Benchmark:** Queda de EBITDA requer ação imediata sobre custos e despesas. "
                    f"**Ação:** Revisar estrutura de CPV/CMV e OPEX para recuperar margem."
                )

        # Lucro
        lucro = variacao.get("Lucro/Prejuízo Do Exercício", {})
        if lucro:
            v_a = lucro.get("valor_a", 0)
            v_b = lucro.get("valor_b", 0)
            var_pct = lucro.get("variacao_pct", 0)
            if v_a > 0 and v_b < 0:
                insights.append(
                    f"**Achado:** Mudou de lucro para prejuízo entre {nome_b} e {nome_a}. "
                    f"**Benchmark:** Transição para prejuízo é sinal de alerta máximo. "
                    f"**Ação:** Análise de causa-raiz urgente: receitas, custos ou despesas financeiras."
                )
            elif v_a < 0 and v_b > 0:
                insights.append(
                    f"**Achado:** Mudou de prejuízo para lucro entre {nome_b} e {nome_a}. "
                    f"**Benchmark:** Recuperação é positiva, mas precisa ser sustentável. "
                    f"**Ação:** Validar se o lucro é operacional ou por itens não recorrentes."
                )
            elif abs(var_pct) > 0.1:
                sinal = "cresceu" if var_pct > 0 else "caiu"
                insights.append(
                    f"**Achado:** Lucro {sinal} {abs(var_pct):.1%} de {nome_b} para {nome_a}. "
                    f"**Benchmark:** Variação de Lucro Líquido acima de 10% requer análise detalhada. "
                    f"**Ação:** Decompor a variação por linha da DRE para identificar a causa principal."
                )

        if not insights:
            insights.append(
                "**Achado:** Variações dentro do esperado entre os cenários. "
                "**Benchmark:** Resultados estáveis indicam previsibilidade operacional. "
                "**Ação:** Monitorar tendência nos próximos períodos para confirmar estabilidade."
            )

        return insights

    def _responder_dre_completo(
        self,
        empresa: Optional[str],
        mes: Optional[int],
        ano: int,
        empresa_display: str,
        mes_display: str,
        ano_display: int,
    ) -> str:
        """Responde com o DRE completo formatado."""
        dre = self.dre_logic.calcular_valor_dre(empresa, mes, ano)

        # Se não há dados, retornar mensagem informativa
        if not dre:
            return self._formatar_resposta(
                f"**Dados não disponíveis**\n\n"
                f"- **Empresa:** {empresa_display}\n"
                f"- **Período:** {mes_display}/{ano_display}\n\n"
                f"Não foram encontrados dados para esta empresa/período. "
                f"Verifique se o Power BI Desktop está aberto e conectado."
            )

        linhas = [
            f"**DRE - Demonstração do Resultado do Exercício**",
            f"",
            f"- **Empresa:** {empresa_display}",
            f"- **Período:** Até {mes_display}/{ano_display}",
            f"",
        ]

        for nivel_1, dados in sorted(dre.items(), key=lambda x: x[1]["ordem"]):
            valor = self._formatar_valor_rs(dados["valor"])
            if dados["subtotal"] == "S":
                linhas.append(f"**{nivel_1}:** **{valor}**")
            else:
                linhas.append(f"- {nivel_1}: {valor}")

        # Insight rápido
        rb = 0
        ebitda = 0
        lucro = 0
        custo = 0
        despesas = 0
        for nivel_1, dados in dre.items():
            if "RECEITA BRUTA" in nivel_1.upper():
                rb = dados["valor"]
            if nivel_1.strip() == "Ebitda":
                ebitda = dados["valor"]
            if "LUCRO/PREJU" in nivel_1.upper():
                lucro = dados["valor"]
            if "CUSTO TOTAL" in nivel_1.upper():
                custo = dados["valor"]
            if "DESPESAS) OPERACIONAIS" in nivel_1.upper():
                despesas = dados["valor"]

        linhas.append(f"")
        linhas.append(f"**Resumo Executivo:**")

        if rb > 0:
            margem_ebitda = (ebitda / rb * 100) if rb else 0
            margem_liq = (lucro / rb * 100) if rb else 0
            margem_custos = (custo / rb * 100) if rb else 0
            margem_despesas = (despesas / rb * 100) if rb else 0

            linhas.append(f"- **Margem Bruta (após custos):** {100 - margem_custos:.1f}%")
            linhas.append(f"- **Margem EBITDA:** {margem_ebitda:.1f}%")
            linhas.append(f"- **Margem Líquida:** {margem_liq:.1f}%")
            linhas.append(f"")

            # Achado + Benchmark + Ação
            if margem_ebitda > 15:
                linhas.append(f"**Achado:** Margem EBITDA de {margem_ebitda:.1f}% — resultado operacional **forte**.")
                linhas.append(f"**Benchmark:** Margens acima de 15% estão dentro das melhores práticas para B2B.")
                linhas.append(f"**Ação:** Manter disciplina e investir em crescimento orgânico.")
            elif margem_ebitda > 5:
                linhas.append(f"**Achado:** Margem EBITDA de {margem_ebitda:.1f}% — resultado **moderado**.")
                linhas.append(f"**Benchmark:** Empresas maduras buscam EBITDA acima de 15%.")
                linhas.append(f"**Ação:** Revisar SG&A e buscar eficiência em custos fixos.")
            else:
                linhas.append(f"**Achado:** Margem EBITDA de {margem_ebitda:.1f}% — resultado **abaixo do desejado**.")
                linhas.append(f"**Benchmark:** Margens abaixo de 5% são insustentáveis no médio prazo.")
                linhas.append(f"**Ação:** Plano de redução de custos e renegociação de contratos.")

        return self._formatar_resposta("\n".join(linhas))

    def montar_tabela_dre_completa(
        self,
        empresa: Optional[str] = None,
        mes: Optional[int] = None,
        ano_ref: int = 2025,
    ) -> str:
        """Monta a tabela DRE completa com 10 colunas no formato markdown."""
        dados = self.dre_logic.calcular_dre_completo(empresa, mes, ano_ref)

        if not dados:
            return "Dados não disponíveis."

        colunas = [
            ("nivel_1", "Linha DRE"),
            ("r_2025", "R 2025"),
            ("av_2025", "AV 25"),
            ("r_2026", "R 2026"),
            ("av_2026", "AV 26"),
            ("var_r26_r25_pct", "Var% 26/25"),
            ("var_r26_r25_rs", "Var R$ 26/25"),
            ("o_2026", "O 2026"),
            ("av_o_2026", "AV O26"),
            ("var_o26_r26_pct", "Var% O/R"),
            ("var_o26_r26_rs", "Var R$ O/R"),
        ]

        header = "| " + " | ".join([c[1] for c in colunas]) + " |"
        separador = "|" + "|".join(["---"] * len(colunas)) + "|"

        linhas = [header, separador]

        for row in dados:
            valores = []
            for key, label in colunas:
                if key == "nivel_1":
                    valores.append(row["nivel_1"])
                elif row["subtotal"] == "S":
                    if "pct" in key or "av" in key:
                        valores.append(f"**{formatar_variacao_pct(row[key] / 100)}**")
                    elif "rs" in key:
                        valores.append(f"**{formatar_variacao_rs(row[key])}**")
                    else:
                        valores.append(f"**{formatar_valor(row[key])}**")
                else:
                    if "pct" in key or "av" in key:
                        valores.append(formatar_variacao_pct(row[key] / 100))
                    elif "rs" in key:
                        valores.append(formatar_variacao_rs(row[key]))
                    else:
                        valores.append(formatar_valor(row[key]))

            linhas.append("| " + " | ".join(valores) + " |")

        return "\n".join(linhas)
