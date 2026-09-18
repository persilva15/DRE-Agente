import pandas as pd
from typing import Optional


class Measures:
    """
    Replica as principais medidas DAX do Power BI em Python.

    Referência: Medidas.tmdl do PBI -_OFICIAL_OK_V6
    """

    @staticmethod
    def calc_valor(df: pd.DataFrame, col_valor: str = "Valor") -> float:
        """Replica medida Valor = SUM(Base[Valor])."""
        return df[col_valor].sum()

    @staticmethod
    def calc_valor_final(
        df: pd.DataFrame,
        plano_contas: pd.DataFrame,
        mascara_dre: pd.DataFrame,
        col_valor: str = "Valor",
    ) -> float:
        """
        Replica a medida DAX 'Valor Final_'.

        Lógica:
        - Receita Bruta (Cod Conta < 13): exclui Receita Diferida
        - Receita Diferida (Cod Conta IN {14,15,16}): exibição separada
        - EBITDA (Ordem < 9): soma de valores até Despesas Operacionais
        - Subtotais: calcula valores acumulados
        """
        if df.empty:
            return 0.0

        # Merge com Plano de Contas para ter Cod Conta
        if "COD CONTA" in df.columns and "Cod Conta" not in df.columns:
            df = df.merge(
                plano_contas[["Cod Conta", "Nivel 1", "Nivel 2", "Nivel 3"]],
                left_on="COD CONTA",
                right_on="Cod Conta",
                how="left",
            )

        # Determinar qual linha estamos analisando
        if "Mascara DRE" in df.columns:
            mascara_dre_val = df["Mascara DRE"].max()
        elif "Cod Conta" in df.columns:
            # Lookup na mascara_dre baseado no Nivel 1
            nivel_1 = df["Nivel 1"].iloc[0] if "Nivel 1" in df.columns else None
            if nivel_1 and not mascara_dre.empty:
                match = mascara_dre[mascara_dre["Nivel 1"] == nivel_1]
                mascara_dre_val = match["Ordem"].iloc[0] if not match.empty else 0
            else:
                mascara_dre_val = 0
        else:
            mascara_dre_val = 0

        # Verificar se é nível 2
        n_2 = 1
        if "Coluna" in df.columns:
            n_2 = df["Coluna"].iloc[0]
        elif "Cod Conta" in df.columns:
            cod_conta = df["Cod Conta"].iloc[0]
            if cod_conta in [14, 15, 16]:
                n_2 = 2

        # Verificar se é subtotal
        subtotal = "N"
        if "Subtotal" in df.columns:
            subtotal = df["Subtotal"].iloc[0]
        elif not mascara_dre.empty and mascara_dre_val:
            match = mascara_dre[mascara_dre["Ordem"] == mascara_dre_val]
            if not match.empty:
                subtotal = match["Subtotal"].iloc[0]

        # Escopo Nivel 2
        escopo_nivel_2 = n_2 == 2

        # Receita Bruta sem Receita Diferida
        if "Cod Conta" in df.columns:
            receita_bruta_ajustada = df[df["Cod Conta"] < 13][col_valor].sum()

            # Receita Diferida separada
            receita_diferida = df[df["Cod Conta"].isin([14, 15, 16])][col_valor].sum()

            # Subtotal (valores abaixo da máscara atual, excluindo Receita Diferida)
            var_valor_subtotal = df[
                (df["Mascara DRE"] < mascara_dre_val if "Mascara DRE" in df.columns else True)
                & (~df["Cod Conta"].isin([14, 15, 16]))
            ][col_valor].sum()
        else:
            receita_bruta_ajustada = 0
            receita_diferida = 0
            var_valor_subtotal = 0

        # EBITDA (soma de valores com Ordem < 9)
        v_ebtid = 0
        if not mascara_dre.empty:
            ordens_ate_ebitda = mascara_dre[mascara_dre["Ordem"] < 9]["Ordem"].tolist()
            if "Mascara DRE" in df.columns:
                v_ebtid = df[df["Mascara DRE"].isin(ordens_ate_ebitda)][col_valor].sum()
            elif "Cod Conta" in df.columns:
                # Para dados do TOTVS, usar lógica diferente
                v_ebtid = var_valor_subtotal

        # SWITCH logic (replicado do DAX)
        if mascara_dre_val == 1 and n_2 == 2:
            return receita_diferida
        elif mascara_dre_val == 1:
            return receita_bruta_ajustada
        elif mascara_dre_val == 7 and not escopo_nivel_2:
            return var_valor_subtotal
        elif mascara_dre_val == 9:
            return v_ebtid
        elif subtotal == "S" and not escopo_nivel_2:
            return var_valor_subtotal
        else:
            return df[col_valor].sum()

    @staticmethod
    def calc_realizado(
        df: pd.DataFrame,
        plano_contas: pd.DataFrame,
        mascara_dre: pd.DataFrame,
        ano: int = 2025,
    ) -> float:
        """
        Replica a medida DAX 'Valor Final Realizado'.

        Filtra por ano e usa VALOR_CONTA_V2 com Inicio Conta = 3.
        """
        if df.empty:
            return 0.0

        # Filtrar por ano
        if "DATA_EMISSAO" in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df["DATA_EMISSAO"]):
                df["DATA_EMISSAO"] = pd.to_datetime(df["DATA_EMISSAO"], errors="coerce")
            df_ano = df[df["DATA_EMISSAO"].dt.year == ano]
        else:
            df_ano = df

        if df_ano.empty:
            return 0.0

        # Filtrar por Inicio Conta = 3
        if "Inicio Conta" in df_ano.columns:
            df_filtrado = df_ano[df_ano["Inicio Conta"] == 3]
        else:
            df_filtrado = df_ano

        if df_filtrado.empty:
            return 0.0

        # Usar VALOR_CONTA_V2 se disponível
        col_valor = "VALOR_CONTA_V2" if "VALOR_CONTA_V2" in df_filtrado.columns else "Valor"

        # Merge com Plano de Contas para ter Cod_conta_aux -> Cod Conta
        if "Cod_conta_aux" in df_filtrado.columns:
            df_filtrado = df_filtrado.merge(
                plano_contas[["Cod Conta", "Nivel 1", "Nivel 2", "Nivel 3"]],
                left_on="Cod_conta_aux",
                right_on="Cod Conta",
                how="left",
            )

        # Aplicar lógica similar ao Valor Final
        return Measures._aplicar_logica_dre(
            df_filtrado, plano_contas, mascara_dre, col_valor
        )

    @staticmethod
    def calc_orcado(
        df: pd.DataFrame,
        plano_contas: pd.DataFrame,
        mascara_dre: pd.DataFrame,
    ) -> float:
        """
        Replica a medida DAX 'Valor Final Orçado'.

        Usa Cod_conta_aux para lookup no Plano de Contas.
        """
        if df.empty:
            return 0.0

        col_valor = "Valor" if "Valor" in df.columns else "VALOR_CONTA_V2"

        # Merge com Plano de Contas
        if "Cod_conta_aux" in df.columns:
            df = df.merge(
                plano_contas[["Cod Conta", "Nivel 1", "Nivel 2", "Nivel 3"]],
                left_on="Cod_conta_aux",
                right_on="Cod Conta",
                how="left",
            )

        return Measures._aplicar_logica_dre(df, plano_contas, mascara_dre, col_valor)

    @staticmethod
    def calc_forecast(
        df: pd.DataFrame,
        plano_contas: pd.DataFrame,
        mascara_dre: pd.DataFrame,
    ) -> float:
        """
        Replica a medida DAX 'Valor Final Forecast'.
        """
        if df.empty:
            return 0.0

        col_valor = "Valor" if "Valor" in df.columns else "VALOR_CONTA_V2"

        # Merge com Plano de Contas
        if "Cod_conta_aux" in df.columns:
            df = df.merge(
                plano_contas[["Cod Conta", "Nivel 1", "Nivel 2", "Nivel 3"]],
                left_on="Cod_conta_aux",
                right_on="Cod Conta",
                how="left",
            )

        return Measures._aplicar_logica_dre(df, plano_contas, mascara_dre, col_valor)

    @staticmethod
    def _aplicar_logica_dre(
        df: pd.DataFrame,
        plano_contas: pd.DataFrame,
        mascara_dre: pd.DataFrame,
        col_valor: str,
    ) -> float:
        """
        Aplica a lógica comum do DRE (Receita Bruta, EBITDA, Subtotals).
        """
        if df.empty:
            return 0.0

        # Determinar a máscara DRE
        mascara_dre_val = 0
        if "Mascara DRE" in df.columns:
            mascara_dre_val = df["Mascara DRE"].max()
        elif "Nivel 1" in df.columns:
            nivel_1 = df["Nivel 1"].iloc[0]
            if nivel_1 and not mascara_dre.empty:
                match = mascara_dre[mascara_dre["Nivel 1"] == nivel_1]
                if not match.empty:
                    mascara_dre_val = match["Ordem"].iloc[0]

        # Determinar se é subtotal
        subtotal = "N"
        if not mascara_dre.empty and mascara_dre_val:
            match = mascara_dre[mascara_dre["Ordem"] == mascara_dre_val]
            if not match.empty:
                subtotal = match["Subtotal"].iloc[0]

        # Verificar nível 2
        n_2 = 1
        if "Coluna" in df.columns:
            n_2 = df["Coluna"].iloc[0]
        elif "Cod Conta" in df.columns:
            cod_conta = df["Cod Conta"].iloc[0] if not pd.isna(cod_conta) else 0
            if cod_conta in [14, 15, 16]:
                n_2 = 2

        escopo_nivel_2 = n_2 == 2

        # Lógica por tipo de linha
        if "Cod Conta" in df.columns:
            receita_bruta = df[df["Cod Conta"] < 13][col_valor].sum()
            receita_diferida = df[df["Cod Conta"].isin([14, 15, 16])][col_valor].sum()

            var_valor_subtotal = df[
                (~df["Cod Conta"].isin([14, 15, 16]))
            ][col_valor].sum()

            # EBITDA
            if not mascara_dre.empty:
                ordens_ate_ebitda = mascara_dre[mascara_dre["Ordem"] < 9]["Ordem"].tolist()
                if "Mascara DRE" in df.columns:
                    v_ebtid = df[df["Mascara DRE"].isin(ordens_ate_ebitda)][col_valor].sum()
                else:
                    v_ebtid = var_valor_subtotal
            else:
                v_ebtid = var_valor_subtotal
        else:
            receita_bruta = 0
            receita_diferida = 0
            var_valor_subtotal = 0
            v_ebtid = 0

        # SWITCH logic
        if mascara_dre_val == 1 and n_2 == 2:
            return receita_diferida
        elif mascara_dre_val == 1:
            return receita_bruta
        elif mascara_dre_val == 7 and not escopo_nivel_2:
            return var_valor_subtotal
        elif mascara_dre_val == 9:
            return v_ebtid
        elif subtotal == "S" and not escopo_nivel_2:
            return var_valor_subtotal
        else:
            return df[col_valor].sum()

    @staticmethod
    def calc_variacao(valor_a: float, valor_b: float) -> tuple[float, float]:
        """
        Calcula variação em R$ e %.

        Returns:
            (variacao_rs, variacao_pct)
        """
        var_rs = valor_a - valor_b
        var_pct = (var_rs / abs(valor_b)) if valor_b != 0 else 0
        return var_rs, var_pct

    @staticmethod
    def calc_av(
        df: pd.DataFrame,
        plano_contas: pd.DataFrame,
        mascara_dre: pd.DataFrame,
        col_valor: str,
        nivel_1_ref: str = "Receita Bruta",
    ) -> float:
        """
        Calcula Análise Vertical (% sobre Receita Bruta).
        """
        valor = Measures._aplicar_logica_dre(df, plano_contas, mascara_dre, col_valor)

        # Receita Bruta como referência
        if "Nivel 1" in df.columns:
            receita_bruta = df[df["Nivel 1"] == nivel_1_ref][col_valor].sum()
        elif "Cod Conta" in df.columns:
            receita_bruta = df[df["Cod Conta"] < 13][col_valor].sum()
        else:
            receita_bruta = 0

        return (valor / receita_bruta) if receita_bruta != 0 else 0

    @staticmethod
    def calc_ytd(
        df: pd.DataFrame,
        mes_ate: int,
        col_data: str = "data",
    ) -> pd.DataFrame:
        """
        Filtra dados até o mês especificado (Year-To-Date).
        """
        if df.empty or col_data not in df.columns:
            return df
        
        if not pd.api.types.is_datetime64_any_dtype(df[col_data]):
            df[col_data] = pd.to_datetime(df[col_data], errors="coerce")

        return df[df[col_data].dt.month <= mes_ate]
