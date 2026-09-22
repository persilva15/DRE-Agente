import pandas as pd
from typing import Optional

from engine.measures import Measures
from config import MES_CORRENTE, ANO_CORRENTE


class DRELogic:
    """
    Orquestra os cálculos do DRE usando as medidades replicadas do Power BI.
    """

    def __init__(self, data: dict):
        """
        Args:
            data: Dicionário com todas as tabelas carregadas.
        """
        self.data = data
        self.measures = Measures()

    def _get_empresa_filter(self, empresa: Optional[str]) -> pd.Series:
        """Retorna filtro booleano para empresa."""
        if not empresa or empresa.upper() in ["CONSOLIDADO", "CONSOLIDAD", "TOTAL", "GERAL", "TODAS"]:
            return pd.Series([True] * len(self.data["base"]))

        base = self.data["base"]
        if "Empresa" in base.columns:
            return base["Empresa"].str.upper().str.contains(empresa.upper(), na=False)
        return pd.Series([True] * len(base))

    def _get_empresa_filter_totvs(self, empresa: Optional[str]) -> pd.Series:
        """Retorna filtro booleano para empresa nas tabelas TOTVS."""
        if not empresa or empresa.upper() in ["CONSOLIDADO", "CONSOLIDAD", "TOTAL", "GERAL", "TODAS"]:
            return pd.Series([True] * len(self.data["base_real_2025"]))

        df = self.data["base_real_2025"]
        if "Empresa Final" in df.columns:
            return df["Empresa Final"].str.upper().str.contains(empresa.upper(), na=False)
        elif "EMPRESA" in df.columns:
            return df["EMPRESA"].str.upper().str.contains(empresa.upper(), na=False)
        return pd.Series([True] * len(df))

    def _get_empresa_filter_orcado(self, empresa: Optional[str]) -> pd.Series:
        """Retorna filtro booleano para empresa nas tabelas de orçado/forecast."""
        if not empresa or empresa.upper() in ["CONSOLIDADO", "CONSOLIDAD", "TOTAL", "GERAL", "TODAS"]:
            return pd.Series([True] * len(self.data["base_orcado"]))

        df = self.data["base_orcado"]
        if "Empresa Final" in df.columns:
            return df["Empresa Final"].str.upper().str.contains(empresa.upper(), na=False)
        return pd.Series([True] * len(df))

    def calcular_valor_dre(
        self,
        empresa: Optional[str] = None,
        mes: Optional[int] = None,
        ano: int = 2025,
    ) -> dict:
        """
        Calcula o DRE consolidado ou por empresa.

        Returns:
            Dict com valores do DRE para cada linha da máscara.
        """
        base = self.data["base"]
        plano_contas = self.data["plano_contas"]
        mascara_dre = self.data["mascara_dre"]

        # Filtro de empresa
        filtro_empresa = self._get_empresa_filter(empresa)
        base_filtrado = base[filtro_empresa].copy()

        # Garantir que data e DATA_EMISSAO sao datetime
        for col in ["data", "DATA_EMISSAO"]:
            if col in base_filtrado.columns and not pd.api.types.is_datetime64_any_dtype(base_filtrado[col]):
                base_filtrado[col] = pd.to_datetime(base_filtrado[col], errors="coerce")

        # Filtro de data
        if mes and ano:
            if "data" in base_filtrado.columns:
                base_filtrado = base_filtrado[
                    (base_filtrado["data"].dt.month <= mes) & (base_filtrado["data"].dt.year == ano)
                ]
            elif "DATA_EMISSAO" in base_filtrado.columns:
                base_filtrado = base_filtrado[
                    (base_filtrado["DATA_EMISSAO"].dt.month <= mes) & (base_filtrado["DATA_EMISSAO"].dt.year == ano)
                ]
        elif ano:
            if "data" in base_filtrado.columns:
                base_filtrado = base_filtrado[base_filtrado["data"].dt.year == ano]
            elif "DATA_EMISSAO" in base_filtrado.columns:
                base_filtrado = base_filtrado[base_filtrado["DATA_EMISSAO"].dt.year == ano]

        # Merge com plano de contas para ter Nivel 1
        if "COD CONTA" in base_filtrado.columns:
            # Converter COD CONTA para int (removendo NaN)
            base_filtrado["COD CONTA"] = base_filtrado["COD CONTA"].fillna(0).astype(int)
            base_com_plano = base_filtrado.merge(
                plano_contas[["Cod Conta", "Nivel 1"]],
                left_on="COD CONTA",
                right_on="Cod Conta",
                how="left",
            )
        else:
            base_com_plano = base_filtrado.copy()

        # Ordenar máscara DRE por Ordem
        mascara_ordenada = mascara_dre.sort_values("Ordem")

        # Calcular para cada linha da máscara DRE
        resultado = {}
        for _, row_mascara in mascara_ordenada.iterrows():
            ordem = row_mascara["Ordem"]
            nivel_1 = row_mascara["Nivel 1"]
            subtotal = row_mascara["Subtotal"]

            # Filtrar base para este nível
            if "Nivel 1" in base_com_plano.columns:
                df_nivel = base_com_plano[base_com_plano["Nivel 1"] == nivel_1]
            else:
                df_nivel = base_com_plano

            # Calcular valor
            valor = 0
            nivel_1_lower = nivel_1.strip().lower()

            if subtotal == "S":
                if nivel_1_lower == "receita l\u00edquida":
                    receita_bruta = resultado.get("Receita Bruta", {}).get("valor", 0)
                    impostos = resultado.get("(-) Impostos", {}).get("valor", 0)
                    devolucoes = resultado.get("(-) Devolu\u00e7\u00f5es e Descontos", {}).get("valor", 0)
                    valor = receita_bruta + impostos + devolucoes
                elif nivel_1_lower == "lucro bruto (r$)":
                    receita_liquida = resultado.get("Receita L\u00edquida", {}).get("valor", 0)
                    custo = resultado.get("(-) Custo Total", {}).get("valor", 0)
                    valor = receita_liquida + custo
                elif nivel_1_lower == "ebit":
                    ebitda = resultado.get("Ebitda", {}).get("valor", 0)
                    depreciacao = resultado.get("(-) Deprecia\u00e7\u00e3o, Amortiza\u00e7\u00e3o E Exaust\u00e3o", {}).get("valor", 0)
                    valor = ebitda + depreciacao
                elif nivel_1_lower == "lucro/preju\u00edzo do exerc\u00edcio":
                    ebit = resultado.get("Ebit ", {}).get("valor", 0)
                    receitas_fin = resultado.get("Receitas Financeiras", {}).get("valor", 0)
                    despesas_fin = resultado.get("(-) Despesas Financeiras", {}).get("valor", 0)
                    provisao = resultado.get("Provis\u00e3o Para Ir/Csll", {}).get("valor", 0)
                    valor = ebit + receitas_fin + despesas_fin + provisao
                else:
                    valor = self.measures.calc_valor(df_nivel, col_valor="Valor")
            elif nivel_1_lower == "ebitda":
                lucro_bruto = resultado.get("Lucro Bruto (R$)", {}).get("valor", 0)
                despesas_op = resultado.get("(Despesas) Operacionais", {}).get("valor", 0)
                valor = lucro_bruto + despesas_op
            else:
                valor = self.measures.calc_valor(df_nivel, col_valor="Valor")

            resultado[nivel_1] = {
                "ordem": ordem,
                "subtotal": subtotal,
                "valor": valor,
            }

        return resultado

    def calcular_realizado(
        self,
        empresa: Optional[str] = None,
        mes: Optional[int] = None,
        ano: int = 2025,
    ) -> dict:
        """
        Calcula o DRE realizado (TOTVS).
        """
        df = self.data["base_real_2025"]

        # Retornar vazio se DataFrame vazio
        if df.empty:
            return {}

        plano_contas = self.data["plano_contas"]
        mascara_dre = self.data["mascara_dre"]

        # Filtro de empresa
        filtro_empresa = self._get_empresa_filter_totvs(empresa)
        df_filtrado = df[filtro_empresa].copy()

        # Garantir que DATA_EMISSAO e datetime (normalizar timezone)
        if "DATA_EMISSAO" in df_filtrado.columns:
            if not pd.api.types.is_datetime64_any_dtype(df_filtrado["DATA_EMISSAO"]):
                df_filtrado["DATA_EMISSAO"] = pd.to_datetime(df_filtrado["DATA_EMISSAO"], errors="coerce", utc=True)
                try:
                    df_filtrado["DATA_EMISSAO"] = df_filtrado["DATA_EMISSAO"].dt.tz_localize(None)
                except Exception:
                    pass
            elif pd.api.types.is_datetime64tz_dtype(df_filtrado["DATA_EMISSAO"].dtype):
                df_filtrado["DATA_EMISSAO"] = df_filtrado["DATA_EMISSAO"].dt.tz_localize(None)

        # Filtro de data
        if "DATA_EMISSAO" in df_filtrado.columns:
            if mes and ano:
                df_filtrado = df_filtrado[
                    (df_filtrado["DATA_EMISSAO"].dt.month <= mes) & (df_filtrado["DATA_EMISSAO"].dt.year == ano)
                ]
            elif ano:
                df_filtrado = df_filtrado[df_filtrado["DATA_EMISSAO"].dt.year == ano]

        # Filtrar Inicio Conta = 3
        if "Inicio Conta" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["Inicio Conta"].astype(str) == "3"]

        # Usar VALOR_CONTA_V2
        col_valor = "VALOR_CONTA_V2" if "VALOR_CONTA_V2" in df_filtrado.columns else "Valor"

        # Merge com plano de contas
        if "Cod_conta_aux" in df_filtrado.columns:
            df_filtrado = df_filtrado.merge(
                plano_contas[["Cod Conta", "Nivel 1", "Nivel 2", "Nivel 3"]],
                left_on="Cod_conta_aux",
                right_on="Cod Conta",
                how="left",
            )

        # Ordenar máscara DRE por Ordem
        mascara_ordenada = mascara_dre.sort_values("Ordem")

        # Calcular para cada linha da máscara DRE
        resultado = {}
        for _, row_mascara in mascara_ordenada.iterrows():
            ordem = row_mascara["Ordem"]
            nivel_1 = row_mascara["Nivel 1"]
            subtotal = row_mascara["Subtotal"]

            if "Nivel 1" in df_filtrado.columns:
                df_nivel = df_filtrado[df_filtrado["Nivel 1"] == nivel_1]
            else:
                df_nivel = df_filtrado

            # Calcular valor
            valor = 0
            nivel_1_lower = nivel_1.strip().lower()

            if subtotal == "S":
                if nivel_1_lower == "receita l\u00edquida":
                    receita_bruta = resultado.get("Receita Bruta", {}).get("valor", 0)
                    impostos = resultado.get("(-) Impostos", {}).get("valor", 0)
                    devolucoes = resultado.get("(-) Devolu\u00e7\u00f5es e Descontos", {}).get("valor", 0)
                    valor = receita_bruta + impostos + devolucoes
                elif nivel_1_lower == "lucro bruto (r$)":
                    receita_liquida = resultado.get("Receita L\u00edquida", {}).get("valor", 0)
                    custo = resultado.get("(-) Custo Total", {}).get("valor", 0)
                    valor = receita_liquida + custo
                elif nivel_1_lower == "ebit":
                    ebitda = resultado.get("Ebitda", {}).get("valor", 0)
                    depreciacao = resultado.get("(-) Deprecia\u00e7\u00e3o, Amortiza\u00e7\u00e3o E Exaust\u00e3o", {}).get("valor", 0)
                    valor = ebitda + depreciacao
                elif nivel_1_lower == "lucro/preju\u00edzo do exerc\u00edcio":
                    ebit = resultado.get("Ebit ", {}).get("valor", 0)
                    receitas_fin = resultado.get("Receitas Financeiras", {}).get("valor", 0)
                    despesas_fin = resultado.get("(-) Despesas Financeiras", {}).get("valor", 0)
                    provisao = resultado.get("Provis\u00e3o Para Ir/Csll", {}).get("valor", 0)
                    valor = ebit + receitas_fin + despesas_fin + provisao
                else:
                    valor = self.measures.calc_valor(df_nivel, col_valor=col_valor)
            elif nivel_1_lower == "ebitda":
                lucro_bruto = resultado.get("Lucro Bruto (R$)", {}).get("valor", 0)
                despesas_op = resultado.get("(Despesas) Operacionais", {}).get("valor", 0)
                valor = lucro_bruto + despesas_op
            else:
                valor = self.measures.calc_valor(df_nivel, col_valor=col_valor)

            resultado[nivel_1] = {
                "ordem": ordem,
                "subtotal": subtotal,
                "valor": valor,
            }

        return resultado

    def calcular_orcado(
        self,
        empresa: Optional[str] = None,
        mes: Optional[int] = None,
    ) -> dict:
        """
        Calcula o DRE orçado.
        """
        df = self.data["base_orcado"]

        # Retornar vazio se DataFrame vazio
        if df.empty:
            return {}

        plano_contas = self.data["plano_contas"]
        mascara_dre = self.data["mascara_dre"]

        # Filtro de empresa
        filtro_empresa = self._get_empresa_filter_orcado(empresa)
        df_filtrado = df[filtro_empresa].copy()

        # Garantir que Atributo e datetime
        if "Atributo" in df_filtrado.columns and not pd.api.types.is_datetime64_any_dtype(df_filtrado["Atributo"]):
            df_filtrado["Atributo"] = pd.to_datetime(df_filtrado["Atributo"], errors="coerce")

        # Filtro de data (por Atributo)
        if "Atributo" in df_filtrado.columns and mes:
            df_filtrado = df_filtrado[df_filtrado["Atributo"].dt.month <= mes]

        # Usar coluna Valor
        col_valor = "Valor" if "Valor" in df_filtrado.columns else "VALOR_CONTA_V2"

        if col_valor not in df_filtrado.columns:
            return {}

        # Merge com plano de contas
        if "Cod_conta_aux" in df_filtrado.columns:
            df_filtrado = df_filtrado.merge(
                plano_contas[["Cod Conta", "Nivel 1", "Nivel 2", "Nivel 3"]],
                left_on="Cod_conta_aux",
                right_on="Cod Conta",
                how="left",
            )

        # Ordenar máscara DRE por Ordem
        mascara_ordenada = mascara_dre.sort_values("Ordem")

        # Calcular para cada linha da máscara DRE
        resultado = {}
        for _, row_mascara in mascara_ordenada.iterrows():
            ordem = row_mascara["Ordem"]
            nivel_1 = row_mascara["Nivel 1"]
            subtotal = row_mascara["Subtotal"]

            if "Nivel 1" in df_filtrado.columns:
                df_nivel = df_filtrado[df_filtrado["Nivel 1"] == nivel_1]
            else:
                df_nivel = df_filtrado

            # Calcular valor
            valor = 0
            nivel_1_lower = nivel_1.strip().lower()

            if subtotal == "S":
                if nivel_1_lower == "receita l\u00edquida":
                    receita_bruta = resultado.get("Receita Bruta", {}).get("valor", 0)
                    impostos = resultado.get("(-) Impostos", {}).get("valor", 0)
                    devolucoes = resultado.get("(-) Devolu\u00e7\u00f5es e Descontos", {}).get("valor", 0)
                    valor = receita_bruta + impostos + devolucoes
                elif nivel_1_lower == "lucro bruto (r$)":
                    receita_liquida = resultado.get("Receita L\u00edquida", {}).get("valor", 0)
                    custo = resultado.get("(-) Custo Total", {}).get("valor", 0)
                    valor = receita_liquida + custo
                elif nivel_1_lower == "ebit":
                    ebitda = resultado.get("Ebitda", {}).get("valor", 0)
                    depreciacao = resultado.get("(-) Deprecia\u00e7\u00e3o, Amortiza\u00e7\u00e3o E Exaust\u00e3o", {}).get("valor", 0)
                    valor = ebitda + depreciacao
                elif nivel_1_lower == "lucro/preju\u00edzo do exerc\u00edcio":
                    ebit = resultado.get("Ebit ", {}).get("valor", 0)
                    receitas_fin = resultado.get("Receitas Financeiras", {}).get("valor", 0)
                    despesas_fin = resultado.get("(-) Despesas Financeiras", {}).get("valor", 0)
                    provisao = resultado.get("Provis\u00e3o Para Ir/Csll", {}).get("valor", 0)
                    valor = ebit + receitas_fin + despesas_fin + provisao
                else:
                    valor = self.measures.calc_valor(df_nivel, col_valor=col_valor)
            elif nivel_1_lower == "ebitda":
                lucro_bruto = resultado.get("Lucro Bruto (R$)", {}).get("valor", 0)
                despesas_op = resultado.get("(Despesas) Operacionais", {}).get("valor", 0)
                valor = lucro_bruto + despesas_op
            else:
                valor = self.measures.calc_valor(df_nivel, col_valor=col_valor)

            resultado[nivel_1] = {
                "ordem": ordem,
                "subtotal": subtotal,
                "valor": valor,
            }

        return resultado

    def calcular_forecast(
        self,
        empresa: Optional[str] = None,
        mes: Optional[int] = None,
    ) -> dict:
        """
        Calcula o DRE forecast.
        """
        df = self.data["base_forecast"]

        # Retornar vazio se DataFrame vazio
        if df.empty:
            return {}

        plano_contas = self.data["plano_contas"]
        mascara_dre = self.data["mascara_dre"]

        # Filtro de empresa
        filtro_empresa = self._get_empresa_filter_orcado(empresa)
        df_filtrado = df[filtro_empresa].copy()

        # Garantir que Atributo e datetime
        if "Atributo" in df_filtrado.columns and not pd.api.types.is_datetime64_any_dtype(df_filtrado["Atributo"]):
            df_filtrado["Atributo"] = pd.to_datetime(df_filtrado["Atributo"], errors="coerce")

        # Filtro de data (por Atributo)
        if "Atributo" in df_filtrado.columns and mes:
            df_filtrado = df_filtrado[df_filtrado["Atributo"].dt.month <= mes]

        # Usar coluna Valor
        col_valor = "Valor" if "Valor" in df_filtrado.columns else "VALOR_CONTA_V2"

        if col_valor not in df_filtrado.columns:
            return {}

        # Merge com plano de contas
        if "Cod_conta_aux" in df_filtrado.columns:
            df_filtrado = df_filtrado.merge(
                plano_contas[["Cod Conta", "Nivel 1", "Nivel 2", "Nivel 3"]],
                left_on="Cod_conta_aux",
                right_on="Cod Conta",
                how="left",
            )

        # Ordenar máscara DRE por Ordem
        mascara_ordenada = mascara_dre.sort_values("Ordem")

        # Calcular para cada linha da máscara DRE
        resultado = {}
        for _, row_mascara in mascara_ordenada.iterrows():
            ordem = row_mascara["Ordem"]
            nivel_1 = row_mascara["Nivel 1"]
            subtotal = row_mascara["Subtotal"]

            if "Nivel 1" in df_filtrado.columns:
                df_nivel = df_filtrado[df_filtrado["Nivel 1"] == nivel_1]
            else:
                df_nivel = df_filtrado

            # Calcular valor
            valor = 0
            nivel_1_lower = nivel_1.strip().lower()

            if subtotal == "S":
                if nivel_1_lower == "receita l\u00edquida":
                    receita_bruta = resultado.get("Receita Bruta", {}).get("valor", 0)
                    impostos = resultado.get("(-) Impostos", {}).get("valor", 0)
                    devolucoes = resultado.get("(-) Devolu\u00e7\u00f5es e Descontos", {}).get("valor", 0)
                    valor = receita_bruta + impostos + devolucoes
                elif nivel_1_lower == "lucro bruto (r$)":
                    receita_liquida = resultado.get("Receita L\u00edquida", {}).get("valor", 0)
                    custo = resultado.get("(-) Custo Total", {}).get("valor", 0)
                    valor = receita_liquida + custo
                elif nivel_1_lower == "ebit":
                    ebitda = resultado.get("Ebitda", {}).get("valor", 0)
                    depreciacao = resultado.get("(-) Deprecia\u00e7\u00e3o, Amortiza\u00e7\u00e3o E Exaust\u00e3o", {}).get("valor", 0)
                    valor = ebitda + depreciacao
                elif nivel_1_lower == "lucro/preju\u00edzo do exerc\u00edcio":
                    ebit = resultado.get("Ebit ", {}).get("valor", 0)
                    receitas_fin = resultado.get("Receitas Financeiras", {}).get("valor", 0)
                    despesas_fin = resultado.get("(-) Despesas Financeiras", {}).get("valor", 0)
                    provisao = resultado.get("Provis\u00e3o Para Ir/Csll", {}).get("valor", 0)
                    valor = ebit + receitas_fin + despesas_fin + provisao
                else:
                    valor = self.measures.calc_valor(df_nivel, col_valor=col_valor)
            elif nivel_1_lower == "ebitda":
                lucro_bruto = resultado.get("Lucro Bruto (R$)", {}).get("valor", 0)
                despesas_op = resultado.get("(Despesas) Operacionais", {}).get("valor", 0)
                valor = lucro_bruto + despesas_op
            else:
                valor = self.measures.calc_valor(df_nivel, col_valor=col_valor)

            resultado[nivel_1] = {
                "ordem": ordem,
                "subtotal": subtotal,
                "valor": valor,
            }

        return resultado

    def calcular_variacao(
        self,
        tipo: str,
        empresa: Optional[str] = None,
        mes: Optional[int] = None,
        ano: int = 2025,
    ) -> dict:
        """
        Calcula variação entre dois cenários.

        Args:
            tipo: 'real_vs_orcado', 'real_vs_forecast', 'forecast_vs_orcado'
            empresa: Nome da empresa (None = consolidado)
            mes: Mês limite
            ano: Ano de referência
        """
        if tipo == "real_vs_orcado":
            real = self.calcular_realizado(empresa, mes, ano)
            orcado = self.calcular_orcado(empresa, mes)
            return self._comparar_dre(real, orcado)
        elif tipo == "real_vs_forecast":
            real = self.calcular_realizado(empresa, mes, ano)
            forecast = self.calcular_forecast(empresa, mes)
            return self._comparar_dre(real, forecast)
        elif tipo == "forecast_vs_orcado":
            forecast = self.calcular_forecast(empresa, mes)
            orcado = self.calcular_orcado(empresa, mes)
            return self._comparar_dre(forecast, orcado)
        else:
            return {}

    def _comparar_dre(self, dre_a: dict, dre_b: dict) -> dict:
        """
        Compara dois DREs e retorna variações.
        """
        # Retornar vazio se ambos estiverem vazios
        if not dre_a and not dre_b:
            return {}

        # Se um estiver vazio, usar o outro como referência
        if not dre_a:
            dre_a = dre_b
        if not dre_b:
            dre_b = dre_a

        resultado = {}
        for nivel_1 in dre_a:
            valor_a = dre_a[nivel_1]["valor"]
            valor_b = dre_b.get(nivel_1, {}).get("valor", 0)
            var_rs, var_pct = Measures.calc_variacao(valor_a, valor_b)

            resultado[nivel_1] = {
                "ordem": dre_a[nivel_1]["ordem"],
                "subtotal": dre_a[nivel_1]["subtotal"],
                "valor_a": valor_a,
                "valor_b": valor_b,
                "variacao_rs": var_rs,
                "variacao_pct": var_pct,
            }

        return resultado

    def obter_ebitda(
        self,
        empresa: Optional[str] = None,
        mes: Optional[int] = None,
        ano: int = 2025,
        tipo: str = "base",
    ) -> float:
        """
        Retorna o valor do EBITDA.
        """
        if tipo == "realizado":
            dre = self.calcular_realizado(empresa, mes, ano)
        elif tipo == "orcado":
            dre = self.calcular_orcado(empresa, mes)
        elif tipo == "forecast":
            dre = self.calcular_forecast(empresa, mes)
        else:
            dre = self.calcular_valor_dre(empresa, mes, ano)

        # EBITDA está na linha com Ordem = 7
        for nivel_1, dados in dre.items():
            if dados["ordem"] == 7:
                return dados["valor"]
        return 0.0

    def obter_linha_dre(
        self,
        nivel_1: str,
        empresa: Optional[str] = None,
        mes: Optional[int] = None,
        ano: int = 2025,
        tipo: str = "base",
    ) -> float:
        """
        Retorna o valor de uma linha específica do DRE.
        """
        if tipo == "realizado":
            dre = self.calcular_realizado(empresa, mes, ano)
        elif tipo == "orcado":
            dre = self.calcular_orcado(empresa, mes)
        elif tipo == "forecast":
            dre = self.calcular_forecast(empresa, mes)
        else:
            dre = self.calcular_valor_dre(empresa, mes, ano)

        # Busca parcial
        for nivel, dados in dre.items():
            if nivel_1.upper() in nivel.upper():
                return dados["valor"]
        return 0.0

    def calcular_dre_completo(
        self,
        empresa: Optional[str] = None,
        mes: Optional[int] = None,
        ano_ref: int = 2025,
    ) -> list[dict]:
        """
        Calcula a tabela DRE completa com 10 colunas (conforme Power BI "Visão José Alberto").

        Returns:
            Lista de dicts, cada dict é uma linha da máscara DRE com as 10 colunas.
        """
        mascara_dre = self.data["mascara_dre"].sort_values("Ordem")

        # 1. Calcular Realizado 2025 e 2026
        r_2025 = self.calcular_realizado(empresa, mes, ano_ref)
        r_2026 = self.calcular_realizado(empresa, mes, 2026)

        # 2. Calcular Orçado 2026 e Forecast 2026
        o_2026 = self.calcular_orcado(empresa, mes)
        f_2026 = self.calcular_forecast(empresa, mes)

        # 3. Extrair Receita Bruta para AV
        rb_2025 = r_2025.get("Receita Bruta", {}).get("valor", 0)
        rb_2026 = r_2026.get("Receita Bruta", {}).get("valor", 0)
        rb_o26 = o_2026.get("Receita Bruta", {}).get("valor", 0)
        rb_f26 = f_2026.get("Receita Bruta", {}).get("valor", 0)

        # 4. Montar tabela
        resultado = []
        for _, row in mascara_dre.iterrows():
            nivel_1 = row["Nivel 1"]
            ordem = row["Ordem"]
            subtotal = row["Subtotal"]

            v_r25 = r_2025.get(nivel_1, {}).get("valor", 0)
            v_r26 = r_2026.get(nivel_1, {}).get("valor", 0)
            v_o26 = o_2026.get(nivel_1, {}).get("valor", 0)
            v_f26 = f_2026.get(nivel_1, {}).get("valor", 0)

            # Análise Vertical (valor / Receita Bruta * 100)
            av_2025 = (v_r25 / rb_2025 * 100) if rb_2025 != 0 else 0
            av_2026 = (v_r26 / rb_2026 * 100) if rb_2026 != 0 else 0
            av_o26 = (v_o26 / rb_o26 * 100) if rb_o26 != 0 else 0
            av_f26 = (v_f26 / rb_f26 * 100) if rb_f26 != 0 else 0

            # Inverter sinal para custos/despesas
            inverter = ordem in {2, 2.5, 4, 6, 8, 10.5}

            # F26 vs R25
            var_f26_r25_rs = v_f26 - v_r25
            var_f26_r25_pct = (var_f26_r25_rs / abs(v_r25)) if v_r25 != 0 else 0
            if inverter:
                var_f26_r25_pct = var_f26_r25_pct * -1

            # F26 vs R26
            var_f26_r26_rs = v_f26 - v_r26
            var_f26_r26_pct = (var_f26_r26_rs / abs(v_r26)) if v_r26 != 0 else 0
            if inverter:
                var_f26_r26_pct = var_f26_r26_pct * -1

            # F26 vs O26
            var_f26_o26_rs = v_f26 - v_o26
            var_f26_o26_pct = (var_f26_o26_rs / abs(v_o26)) if v_o26 != 0 else 0
            if inverter:
                var_f26_o26_pct = var_f26_o26_pct * -1

            resultado.append({
                "nivel_1": nivel_1,
                "ordem": ordem,
                "subtotal": subtotal,
                "r_2025": v_r25,
                "av_2025": av_2025,
                "f_2026": v_f26,
                "av_f26": av_f26,
                "r_2026": v_r26,
                "av_2026": av_2026,
                "var_f26_r25_pct": var_f26_r25_pct,
                "var_f26_r25_rs": var_f26_r25_rs,
                "var_f26_r26_pct": var_f26_r26_pct,
                "var_f26_r26_rs": var_f26_r26_rs,
                "o_2026": v_o26,
                "av_o_2026": av_o26,
                "var_f26_o26_pct": var_f26_o26_pct,
                "var_f26_o26_rs": var_f26_o26_rs,
            })

        return resultado

    # ------------------------------------------------------------------
    # Helpers para drill-down (retornam DataFrames já filtrados e com merge)
    # ------------------------------------------------------------------
    def _get_df_realizado_merged(self, empresa: Optional[str], mes: Optional[int], ano: int) -> pd.DataFrame:
        """Retorna DataFrame realizado filtrado e com Nivel 1/2/3 (para drill-down)."""
        df = self.data.get("base_real_2025")
        if df is None or df.empty:
            return pd.DataFrame()
        plano_contas = self.data.get("plano_contas")
        if plano_contas is None or plano_contas.empty:
            return pd.DataFrame()

        # Filtro de empresa
        filtro = self._get_empresa_filter_totvs(empresa)
        # Ajustar tamanho do filtro se df mudou (ex: base combinada tem real_2026 junto)
        if len(filtro) != len(df):
            if not empresa or empresa.upper() in ["CONSOLIDADO", "CONSOLIDAD", "TOTAL", "GERAL", "TODAS"]:
                df_f = df.copy()
            else:
                col_emp = "Empresa Final" if "Empresa Final" in df.columns else ("EMPRESA" if "EMPRESA" in df.columns else None)
                if col_emp:
                    df_f = df[df[col_emp].astype(str).str.upper().str.contains(empresa.upper(), na=False)].copy()
                else:
                    df_f = df.copy()
        else:
            df_f = df[filtro].copy()

        if "DATA_EMISSAO" in df_f.columns:
            if not pd.api.types.is_datetime64_any_dtype(df_f["DATA_EMISSAO"]):
                df_f["DATA_EMISSAO"] = pd.to_datetime(df_f["DATA_EMISSAO"], errors="coerce")
            if mes and ano:
                df_f = df_f[(df_f["DATA_EMISSAO"].dt.month <= mes) & (df_f["DATA_EMISSAO"].dt.year == ano)]
            elif ano:
                df_f = df_f[df_f["DATA_EMISSAO"].dt.year == ano]

        if "Inicio Conta" in df_f.columns:
            df_f = df_f[df_f["Inicio Conta"].astype(str) == "3"]

        # Garantir Cod_conta_aux int
        if "Cod_conta_aux" in df_f.columns:
            df_f["Cod_conta_aux"] = pd.to_numeric(df_f["Cod_conta_aux"], errors="coerce").fillna(0).astype(int)

        # Merge
        if "Cod_conta_aux" in df_f.columns and "Cod Conta" in plano_contas.columns:
            pc = plano_contas.copy()
            pc["Cod Conta"] = pd.to_numeric(pc["Cod Conta"], errors="coerce").fillna(0).astype(int)
            df_f = df_f.merge(
                pc[["Cod Conta", "Nivel 1", "Nivel 2", "Nivel 3"]],
                left_on="Cod_conta_aux", right_on="Cod Conta", how="left",
            )
        return df_f

    def _get_df_orcado_merged(self, empresa: Optional[str], mes: Optional[int]) -> pd.DataFrame:
        """Retorna DataFrame orçado filtrado e com Nivel 1/2/3."""
        df = self.data.get("base_orcado")
        if df is None or df.empty:
            return pd.DataFrame()
        plano_contas = self.data.get("plano_contas")
        if plano_contas is None or plano_contas.empty:
            return pd.DataFrame()

        filtro = self._get_empresa_filter_orcado(empresa)
        if len(filtro) != len(df):
            df_f = df.copy()
        else:
            df_f = df[filtro].copy()

        if "Atributo" in df_f.columns:
            if not pd.api.types.is_datetime64_any_dtype(df_f["Atributo"]):
                df_f["Atributo"] = pd.to_datetime(df_f["Atributo"], errors="coerce")
            if mes:
                df_f = df_f[df_f["Atributo"].dt.month <= mes]

        if "Cod_conta_aux" in df_f.columns:
            df_f["Cod_conta_aux"] = pd.to_numeric(df_f["Cod_conta_aux"], errors="coerce").fillna(0).astype(int)

        if "Cod_conta_aux" in df_f.columns and "Cod Conta" in plano_contas.columns:
            pc = plano_contas.copy()
            pc["Cod Conta"] = pd.to_numeric(pc["Cod Conta"], errors="coerce").fillna(0).astype(int)
            df_f = df_f.merge(
                pc[["Cod Conta", "Nivel 1", "Nivel 2", "Nivel 3"]],
                left_on="Cod_conta_aux", right_on="Cod Conta", how="left",
            )
        return df_f

    def _get_df_forecast_merged(self, empresa: Optional[str], mes: Optional[int]) -> pd.DataFrame:
        """Retorna DataFrame forecast filtrado e com Nivel 1/2/3."""
        df = self.data.get("base_forecast")
        if df is None or df.empty:
            return pd.DataFrame()
        plano_contas = self.data.get("plano_contas")
        if plano_contas is None or plano_contas.empty:
            return pd.DataFrame()

        # Reusar filtro de orçado (mesma estrutura)
        filtro = self._get_empresa_filter_orcado(empresa)
        if len(filtro) != len(df):
            df_f = df.copy()
        else:
            df_f = df[filtro].copy()

        if "Atributo" in df_f.columns:
            if not pd.api.types.is_datetime64_any_dtype(df_f["Atributo"]):
                df_f["Atributo"] = pd.to_datetime(df_f["Atributo"], errors="coerce")
            if mes:
                df_f = df_f[df_f["Atributo"].dt.month <= mes]

        if "Cod_conta_aux" in df_f.columns:
            df_f["Cod_conta_aux"] = pd.to_numeric(df_f["Cod_conta_aux"], errors="coerce").fillna(0).astype(int)

        if "Cod_conta_aux" in df_f.columns and "Cod Conta" in plano_contas.columns:
            pc = plano_contas.copy()
            pc["Cod Conta"] = pd.to_numeric(pc["Cod Conta"], errors="coerce").fillna(0).astype(int)
            df_f = df_f.merge(
                pc[["Cod Conta", "Nivel 1", "Nivel 2", "Nivel 3"]],
                left_on="Cod_conta_aux", right_on="Cod Conta", how="left",
            )
        return df_f

    def calcular_dre_hierarquico(
        self,
        empresa: Optional[str] = None,
        mes: Optional[int] = None,
        ano_ref: int = 2025,
    ) -> list[dict]:
        """
        Calcula DRE com hierarquia Nivel 1 -> Nivel 2 -> Nivel 3 para drill-down.

        Cada linha tem campos: nivel_1, nivel_2, nivel_3, nivel_label, level, parent, ordem, subtotal,
        r_2025, av_2025, f_2026, av_f26, r_2026, av_2026, o_2026, av_o_2026, variacoes...

        level 1 = linha da máscara (Nivel 1)
        level 2 = agrupado por Nivel 2 dentro de um Nivel 1
        level 3 = agrupado por Nivel 3 dentro de um Nivel 2
        """
        mascara_dre = self.data["mascara_dre"].sort_values("Ordem")
        plano_contas = self.data.get("plano_contas")

        # Totais Nivel 1 (reusa lógica existente)
        r_2025 = self.calcular_realizado(empresa, mes, ano_ref)
        r_2026 = self.calcular_realizado(empresa, mes, 2026)
        o_2026 = self.calcular_orcado(empresa, mes)
        f_2026 = self.calcular_forecast(empresa, mes)

        rb_2025 = r_2025.get("Receita Bruta", {}).get("valor", 0)
        rb_2026 = r_2026.get("Receita Bruta", {}).get("valor", 0)
        rb_o26 = o_2026.get("Receita Bruta", {}).get("valor", 0)
        rb_f26 = f_2026.get("Receita Bruta", {}).get("valor", 0)

        # DataFrames com merge para agregação Nivel 2/3
        df_r25 = self._get_df_realizado_merged(empresa, mes, ano_ref)
        df_r26 = self._get_df_realizado_merged(empresa, mes, 2026)
        df_f26 = self._get_df_forecast_merged(empresa, mes)
        df_o26 = self._get_df_orcado_merged(empresa, mes)

        # Coluna de valor por fonte
        def _col_valor(df: pd.DataFrame) -> str:
            if df is None or df.empty:
                return "Valor"
            if "VALOR_CONTA_V2" in df.columns:
                return "VALOR_CONTA_V2"
            return "Valor" if "Valor" in df.columns else df.columns[-1]

        col_r25 = _col_valor(df_r25) if not df_r25.empty else "VALOR_CONTA_V2"
        col_r26 = _col_valor(df_r26) if not df_r26.empty else "VALOR_CONTA_V2"
        col_f26 = _col_valor(df_f26) if not df_f26.empty else "Valor"
        col_o26 = _col_valor(df_o26) if not df_o26.empty else "Valor"

        resultado: list[dict] = []

        for idx1, (_, row_mascara) in enumerate(mascara_dre.iterrows()):
            nivel_1 = row_mascara["Nivel 1"]
            ordem = row_mascara["Ordem"]
            subtotal = row_mascara["Subtotal"]

            v_r25 = r_2025.get(nivel_1, {}).get("valor", 0)
            v_r26 = r_2026.get(nivel_1, {}).get("valor", 0)
            v_o26 = o_2026.get(nivel_1, {}).get("valor", 0)
            v_f26 = f_2026.get(nivel_1, {}).get("valor", 0)

            av_2025 = (v_r25 / rb_2025 * 100) if rb_2025 != 0 else 0
            av_2026 = (v_r26 / rb_2026 * 100) if rb_2026 != 0 else 0
            av_o26 = (v_o26 / rb_o26 * 100) if rb_o26 != 0 else 0
            av_f26 = (v_f26 / rb_f26 * 100) if rb_f26 != 0 else 0

            inverter = ordem in {2, 2.5, 4, 6, 8, 10.5}
            var_f26_r25_rs = v_f26 - v_r25
            var_f26_r25_pct = (var_f26_r25_rs / abs(v_r25)) if v_r25 != 0 else 0
            if inverter: var_f26_r25_pct *= -1
            var_f26_r26_rs = v_f26 - v_r26
            var_f26_r26_pct = (var_f26_r26_rs / abs(v_r26)) if v_r26 != 0 else 0
            if inverter: var_f26_r26_pct *= -1
            var_f26_o26_rs = v_f26 - v_o26
            var_f26_o26_pct = (var_f26_o26_rs / abs(v_o26)) if v_o26 != 0 else 0
            if inverter: var_f26_o26_pct *= -1

            nivel_1_lower = nivel_1.strip().lower()
            pode_expandir = (subtotal != "S" and nivel_1_lower != "ebitda")

            # Verificar se tem filhos de fato (pelo menos um Nivel 2 com dados)
            has_children = False
            if pode_expandir and plano_contas is not None and not plano_contas.empty:
                possiveis_n2 = plano_contas[plano_contas["Nivel 1"] == nivel_1]["Nivel 2"].dropna().unique()
                if len(possiveis_n2) > 0:
                    has_children = True

            row_id = f"n1-{idx1}"
            resultado.append({
                "nivel_1": nivel_1,
                "nivel_2": None,
                "nivel_3": None,
                "nivel_label": nivel_1,
                "level": 1,
                "parent": None,
                "_id": row_id,
                "_parent_id": "",
                "ordem": ordem,
                "subtotal": subtotal,
                "has_children": has_children,
                "r_2025": v_r25, "av_2025": av_2025,
                "f_2026": v_f26, "av_f26": av_f26,
                "r_2026": v_r26, "av_2026": av_2026,
                "var_f26_r25_pct": var_f26_r25_pct, "var_f26_r25_rs": var_f26_r25_rs,
                "var_f26_r26_pct": var_f26_r26_pct, "var_f26_r26_rs": var_f26_r26_rs,
                "o_2026": v_o26, "av_o_2026": av_o26,
                "var_f26_o26_pct": var_f26_o26_pct, "var_f26_o26_rs": var_f26_o26_rs,
            })

            if not pode_expandir or not has_children:
                continue

            # --- Nivel 2 ---
            # Usar plano_contas para listar Nivel 2 esperados, mas filtrar só os que têm algum valor
            pc_n2 = plano_contas[plano_contas["Nivel 1"] == nivel_1]
            nivel2_unicos = pc_n2["Nivel 2"].dropna().unique()
            for idx2, n2 in enumerate(nivel2_unicos):
                n2_str = str(n2).strip()
                if not n2_str:
                    continue

                def _sum_nivel2(df, col):
                    if df is None or df.empty or "Nivel 2" not in df.columns or "Nivel 1" not in df.columns:
                        return 0
                    m = df[(df["Nivel 1"] == nivel_1) & (df["Nivel 2"] == n2)]
                    if m.empty: return 0
                    return pd.to_numeric(m[col], errors="coerce").fillna(0).sum()

                v2_r25 = _sum_nivel2(df_r25, col_r25)
                v2_r26 = _sum_nivel2(df_r26, col_r26)
                v2_f26 = _sum_nivel2(df_f26, col_f26)
                v2_o26 = _sum_nivel2(df_o26, col_o26)

                # Pular Nivel 2 sem nenhum dado em nenhuma coluna
                if v2_r25 == 0 and v2_r26 == 0 and v2_f26 == 0 and v2_o26 == 0:
                    continue

                av2_2025 = (v2_r25 / rb_2025 * 100) if rb_2025 != 0 else 0
                av2_2026 = (v2_r26 / rb_2026 * 100) if rb_2026 != 0 else 0
                av2_o26 = (v2_o26 / rb_o26 * 100) if rb_o26 != 0 else 0
                av2_f26 = (v2_f26 / rb_f26 * 100) if rb_f26 != 0 else 0

                var2_f26_r25_rs = v2_f26 - v2_r25
                var2_f26_r25_pct = (var2_f26_r25_rs / abs(v2_r25)) if v2_r25 != 0 else 0
                if inverter: var2_f26_r25_pct *= -1
                var2_f26_r26_rs = v2_f26 - v2_r26
                var2_f26_r26_pct = (var2_f26_r26_rs / abs(v2_r26)) if v2_r26 != 0 else 0
                if inverter: var2_f26_r26_pct *= -1
                var2_f26_o26_rs = v2_f26 - v2_o26
                var2_f26_o26_pct = (var2_f26_o26_rs / abs(v2_o26)) if v2_o26 != 0 else 0
                if inverter: var2_f26_o26_pct *= -1

                # Verificar se este Nivel 2 tem Nivel 3
                pc_n3_check = plano_contas[(plano_contas["Nivel 1"] == nivel_1) & (plano_contas["Nivel 2"] == n2)]
                has_n3 = pc_n3_check["Nivel 3"].dropna().nunique() > 0

                n2_id = f"n2-{idx1}-{idx2}"
                resultado.append({
                    "nivel_1": nivel_1,
                    "nivel_2": n2,
                    "nivel_3": None,
                    "nivel_label": n2,
                    "level": 2,
                    "parent": nivel_1,
                    "_id": n2_id,
                    "_parent_id": row_id,
                    "ordem": ordem,
                    "subtotal": "N",
                    "has_children": has_n3,
                    "r_2025": v2_r25, "av_2025": av2_2025,
                    "f_2026": v2_f26, "av_f26": av2_f26,
                    "r_2026": v2_r26, "av_2026": av2_2026,
                    "var_f26_r25_pct": var2_f26_r25_pct, "var_f26_r25_rs": var2_f26_r25_rs,
                    "var_f26_r26_pct": var2_f26_r26_pct, "var_f26_r26_rs": var2_f26_r26_rs,
                    "o_2026": v2_o26, "av_o_2026": av2_o26,
                    "var_f26_o26_pct": var2_f26_o26_pct, "var_f26_o26_rs": var2_f26_o26_rs,
                })

                # --- Nivel 3 ---
                pc_n3 = plano_contas[(plano_contas["Nivel 1"] == nivel_1) & (plano_contas["Nivel 2"] == n2)]
                nivel3_unicos = pc_n3["Nivel 3"].dropna().unique()
                for idx3, n3 in enumerate(nivel3_unicos):
                    n3_str = str(n3).strip()
                    if not n3_str:
                        continue

                    def _sum_nivel3(df, col):
                        if df is None or df.empty or "Nivel 3" not in df.columns or "Nivel 2" not in df.columns:
                            return 0
                        m = df[(df["Nivel 1"] == nivel_1) & (df["Nivel 2"] == n2) & (df["Nivel 3"] == n3)]
                        if m.empty: return 0
                        return pd.to_numeric(m[col], errors="coerce").fillna(0).sum()

                    v3_r25 = _sum_nivel3(df_r25, col_r25)
                    v3_r26 = _sum_nivel3(df_r26, col_r26)
                    v3_f26 = _sum_nivel3(df_f26, col_f26)
                    v3_o26 = _sum_nivel3(df_o26, col_o26)

                    if v3_r25 == 0 and v3_r26 == 0 and v3_f26 == 0 and v3_o26 == 0:
                        continue

                    av3_2025 = (v3_r25 / rb_2025 * 100) if rb_2025 != 0 else 0
                    av3_2026 = (v3_r26 / rb_2026 * 100) if rb_2026 != 0 else 0
                    av3_o26 = (v3_o26 / rb_o26 * 100) if rb_o26 != 0 else 0
                    av3_f26 = (v3_f26 / rb_f26 * 100) if rb_f26 != 0 else 0

                    var3_f26_r25_rs = v3_f26 - v3_r25
                    var3_f26_r25_pct = (var3_f26_r25_rs / abs(v3_r25)) if v3_r25 != 0 else 0
                    if inverter: var3_f26_r25_pct *= -1
                    var3_f26_r26_rs = v3_f26 - v3_r26
                    var3_f26_r26_pct = (var3_f26_r26_rs / abs(v3_r26)) if v3_r26 != 0 else 0
                    if inverter: var3_f26_r26_pct *= -1
                    var3_f26_o26_rs = v3_f26 - v3_o26
                    var3_f26_o26_pct = (var3_f26_o26_rs / abs(v3_o26)) if v3_o26 != 0 else 0
                    if inverter: var3_f26_o26_pct *= -1

                    n3_id = f"n3-{idx1}-{idx2}-{idx3}"
                    resultado.append({
                        "nivel_1": nivel_1,
                        "nivel_2": n2,
                        "nivel_3": n3,
                        "nivel_label": n3,
                        "level": 3,
                        "parent": n2,
                        "_id": n3_id,
                        "_parent_id": n2_id,
                        "ordem": ordem,
                        "subtotal": "N",
                        "has_children": False,
                        "r_2025": v3_r25, "av_2025": av3_2025,
                        "f_2026": v3_f26, "av_f26": av3_f26,
                        "r_2026": v3_r26, "av_2026": av3_2026,
                        "var_f26_r25_pct": var3_f26_r25_pct, "var_f26_r25_rs": var3_f26_r25_rs,
                        "var_f26_r26_pct": var3_f26_r26_pct, "var_f26_r26_rs": var3_f26_r26_rs,
                        "o_2026": v3_o26, "av_o_2026": av3_o26,
                        "var_f26_o26_pct": var3_f26_o26_pct, "var_f26_o26_rs": var3_f26_o26_rs,
                    })

        return resultado

    def calcular_dre_luciana(
        self,
        empresa: str = None,
        meses_ate: int = 9,
        ano: int = 2026,
    ) -> list[dict]:
        """
        Calcula DRE usando dados extraídos via XMLA (Visão José Alberto).
        
        Medidas: R25, F26, R26, O26
        
        Returns:
            Lista de dicts, cada dict é uma linha da máscara DRE.
        """
        dre_xmla = self.data.get("dre_xmla", {})
        if not dre_xmla or not dre_xmla.get("real_2026"):
            return []
        
        r25 = dre_xmla["real_2025"]
        r26 = dre_xmla["real_2026"]
        f26 = dre_xmla["forecast_2026"]
        o26 = dre_xmla["orcado_2026"]
        
        mascara_dre = self.data["mascara_dre"].sort_values("Ordem")
        
        # Receita Bruta para AV (já vem como total do Nivel 1)
        rb_r25 = r25.get("Receita Bruta", 0)
        rb_r26 = r26.get("Receita Bruta", 0)
        rb_f26 = f26.get("Receita Bruta", 0)
        rb_o26 = o26.get("Receita Bruta", 0)
        
        # Montar tabela - apenas linhas que existem nos dados XMLA
        resultado = []
        for _, row in mascara_dre.iterrows():
            nivel_1 = row["Nivel 1"]
            ordem = row["Ordem"]
            subtotal = row["Subtotal"]
            
            nivel_1_key = nivel_1.strip()
            
            # Pular linhas que não existem nos dados XMLA (ex: "Ebit" filtrado)
            if nivel_1_key not in r25 and nivel_1_key not in r26 and nivel_1_key not in f26 and nivel_1_key not in o26:
                continue
            
            v_r25 = r25.get(nivel_1_key, 0)
            v_r26 = r26.get(nivel_1_key, 0)
            v_f26 = f26.get(nivel_1_key, 0)
            v_o26 = o26.get(nivel_1_key, 0)
            
            # Análise Vertical (valor / Receita Bruta)
            av_r25 = (v_r25 / rb_r25) if rb_r25 != 0 else 0
            av_r26 = (v_r26 / rb_r26) if rb_r26 != 0 else 0
            av_f26 = (v_f26 / rb_f26) if rb_f26 != 0 else 0
            av_o26 = (v_o26 / rb_o26) if rb_o26 != 0 else 0
            
            # Variações (conforme DAX do Power BI - inverte sinal para custos/despesas)
            # Ordem {2,2.5,4,6,8,10.5} são custos/despesas - inverter sinal do Var %
            inverter = ordem in {2, 2.5, 4, 6, 8, 10.5}
            
            # F26 vs R25
            var_f26_r25_rs = v_f26 - v_r25
            var_f26_r25_pct = (var_f26_r25_rs / abs(v_r25)) if v_r25 != 0 else 0
            if inverter:
                var_f26_r25_pct = var_f26_r25_pct * -1
            
            # F26 vs R26
            var_f26_r26_rs = v_f26 - v_r26
            var_f26_r26_pct = (var_f26_r26_rs / abs(v_r26)) if v_r26 != 0 else 0
            if inverter:
                var_f26_r26_pct = var_f26_r26_pct * -1
            
            # F26 vs O26
            var_f26_o26_rs = v_f26 - v_o26
            var_f26_o26_pct = (var_f26_o26_rs / abs(v_o26)) if v_o26 != 0 else 0
            if inverter:
                var_f26_o26_pct = var_f26_o26_pct * -1
            
            resultado.append({
                "nivel_1": nivel_1,
                "ordem": ordem,
                "subtotal": subtotal,
                "r_2025": v_r25,
                "av_2025": av_r25,
                "f_2026": v_f26,
                "av_f26": av_f26,
                "r_2026": v_r26,
                "av_2026": av_r26,
                "var_f26_r25_pct": var_f26_r25_pct,
                "var_f26_r25_rs": var_f26_r25_rs,
                "var_f26_r26_pct": var_f26_r26_pct,
                "var_f26_r26_rs": var_f26_r26_rs,
                "o_2026": v_o26,
                "av_o_2026": av_o26,
                "var_f26_o26_pct": var_f26_o26_pct,
                "var_f26_o26_rs": var_f26_o26_rs,
            })
        
        return resultado
