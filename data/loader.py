import pandas as pd
import streamlit as st
from datetime import datetime
import os

from config import PATHS, SHEETS, EMPRESAS_MAP


class DataLoader:
    """Carrega e cacheia todas as tabelas do Power BI."""

    def __init__(self):
        self._data = {}

    def _read_excel(self, path: str, sheet: str) -> pd.DataFrame:
        """Lê uma aba específica de um arquivo Excel."""
        try:
            df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
            return df
        except Exception as e:
            st.error(f"Erro ao ler {path} - {sheet}: {e}")
            return pd.DataFrame()

    @st.cache_data(ttl=3600, show_spinner="Carregando dados do Power BI...")
    def load_base_dre(_self) -> pd.DataFrame:
        """Carrega tabela Base (DRE original)."""
        df = _self._read_excel(PATHS["base_dre"], SHEETS["base"])
        if not df.empty:
            df["data"] = pd.to_datetime(df["data"], errors="coerce")
            df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
        return df

    @st.cache_data(ttl=3600, show_spinner="Carregando plano de contas...")
    def load_plano_contas(_self) -> pd.DataFrame:
        """Carrega tabela Plano de Contas (Dim)."""
        df = _self._read_excel(PATHS["base_dre"], SHEETS["plano_contas"])
        return df

    @st.cache_data(ttl=3600, show_spinner="Carregando máscara DRE...")
    def load_mascara_dre(_self) -> pd.DataFrame:
        """Carrega tabela Mascara DRE."""
        df = _self._read_excel(PATHS["base_dre"], SHEETS["mascara_dre"])
        return df

    @st.cache_data(ttl=3600, show_spinner="Carregando empresas...")
    def load_auxiliar(_self) -> pd.DataFrame:
        """Carrega tabela Auxiliar (empresas)."""
        df = _self._read_excel(PATHS["base_dre"], SHEETS["auxiliar"])
        return df

    @st.cache_data(ttl=3600, show_spinner="Carregando realizado 2025...")
    def load_base_real_2025(_self) -> pd.DataFrame:
        """Carrega tabela Base_Real_2025 (realizado via TOTVS)."""
        df = _self._read_excel(PATHS["base_real_2025"], SHEETS["base_real_2025"])
        if not df.empty:
            df["DATA_EMISSAO"] = pd.to_datetime(df["DATA_EMISSAO"], errors="coerce")
        return df

    @st.cache_data(ttl=3600, show_spinner="Carregando realizado 2024...")
    def load_base_real_2024(_self) -> pd.DataFrame:
        """Carrega tabela Base_Real_2024 (histórico)."""
        df = _self._read_excel(PATHS["base_real_2024"], SHEETS["historica_2024"])
        if not df.empty:
            df["data"] = pd.to_datetime(df["data"], errors="coerce")
        return df

    def load_realizado_totvs(_self) -> pd.DataFrame:
        username = os.environ.get("TOTVS_USER", "")
        password = os.environ.get("TOTVS_PASS", "")
        
        if not username or not password:
            print("[TOTVS] Credenciais nao encontradas.")
            return pd.DataFrame()
        
        try:
            from data.totvs_api import buscar_realizado_totvs
            df = buscar_realizado_totvs(username, password, ano=2026)
            if not df.empty and "DATA_EMISSAO" in df.columns:
                df["DATA_EMISSAO"] = pd.to_datetime(df["DATA_EMISSAO"], errors="coerce")
            return df
        except Exception as e:
            print(f"[TOTVS] Erro: {e}")
            return pd.DataFrame()

    def load_realizado_combinado(_self) -> pd.DataFrame:
        df_excel = _self.load_base_real_2025()
        df_totvs = _self.load_realizado_totvs()
        
        if df_totvs.empty:
            return df_excel
        
        if not df_excel.empty and "DATA_EMISSAO" in df_excel.columns:
            df_excel["DATA_EMISSAO"] = pd.to_datetime(df_excel["DATA_EMISSAO"], errors="coerce")
            df_excel_2025 = df_excel[df_excel["DATA_EMISSAO"].dt.year == 2025].copy()
        else:
            df_excel_2025 = df_excel
        
        if not df_totvs.empty and "DATA_EMISSAO" in df_totvs.columns:
            df_totvs["DATA_EMISSAO"] = pd.to_datetime(df_totvs["DATA_EMISSAO"], errors="coerce")
            df_totvs_2026 = df_totvs[df_totvs["DATA_EMISSAO"].dt.year == 2026].copy()
        else:
            df_totvs_2026 = pd.DataFrame()
        
        frames = []
        if not df_excel_2025.empty:
            frames.append(df_excel_2025)
        if not df_totvs_2026.empty:
            frames.append(df_totvs_2026)
        
        if frames:
            return pd.concat(frames, ignore_index=True)
        else:
            return df_excel

    @st.cache_data(ttl=3600, show_spinner="Carregando orçado 2026...")
    def load_base_orcado(_self) -> pd.DataFrame:
        """Carrega e transforma tabela fBase_Orcado para formato compatível."""
        df = _self._read_excel(PATHS["orcado_2026"], SHEETS["orcado"])
        if df.empty:
            return df
        
        # Identificar colunas mensais (datetime)
        monthly_cols = [col for col in df.columns if isinstance(col, datetime)]
        
        if not monthly_cols:
            return df
        
        # Extrair CODCONTA_last para mapear com Dim
        df["Cod_conta_aux"] = df["CODCONTA"].apply(
            lambda x: int(str(x).split(".")[-1]) if pd.notna(x) and "." in str(x) else None
        )
        
        # Mapear CODCOLIGADA para nome da empresa
        df["Empresa"] = df["CODCOLIGADA"].map(EMPRESAS_MAP)
        
        # Melt: transformar colunas mensais em linhas
        id_cols = ["CODCOLIGADA", "CODFILIAL", "CODCONTA", "CODCCUSTO", "ANO", "Cod_conta_aux", "Empresa"]
        df_melted = df.melt(
            id_vars=[c for c in id_cols if c in df.columns],
            value_vars=monthly_cols,
            var_name="Atributo",
            value_name="Valor",
        )
        
        # Converter Atributo para datetime
        df_melted["Atributo"] = pd.to_datetime(df_melted["Atributo"], errors="coerce")
        
        # Converter Valor para numérico
        df_melted["Valor"] = pd.to_numeric(df_melted["Valor"], errors="coerce").fillna(0)
        
        return df_melted

    @st.cache_data(ttl=3600, show_spinner="Carregando forecast 2026...")
    def load_base_forecast(_self) -> pd.DataFrame:
        """Carrega e transforma tabela fBase_Forecast_2026 para formato compatível."""
        df = _self._read_excel(PATHS["forecast_2026"], SHEETS["forecast"])
        if df.empty:
            return df
        
        # Identificar colunas mensais (datetime)
        monthly_cols = [col for col in df.columns if isinstance(col, datetime)]
        
        if not monthly_cols:
            return df
        
        # Extrair CODCONTA_last para mapear com Dim
        df["Cod_conta_aux"] = df["CODCONTA"].apply(
            lambda x: int(str(x).split(".")[-1]) if pd.notna(x) and "." in str(x) else None
        )
        
        # Mapear CODCOLIGADA para nome da empresa
        df["Empresa"] = df["CODCOLIGADA"].map(EMPRESAS_MAP)
        
        # Melt: transformar colunas mensais em linhas
        id_cols = ["CODCOLIGADA", "CODFILIAL", "CODCONTA", "CODCCUSTO", "ANO", "Cod_conta_aux", "Empresa"]
        df_melted = df.melt(
            id_vars=[c for c in id_cols if c in df.columns],
            value_vars=monthly_cols,
            var_name="Atributo",
            value_name="Valor",
        )
        
        # Converter Atributo para datetime
        df_melted["Atributo"] = pd.to_datetime(df_melted["Atributo"], errors="coerce")
        
        # Converter Valor para numérico
        df_melted["Valor"] = pd.to_numeric(df_melted["Valor"], errors="coerce").fillna(0)
        
        return df_melted

    @st.cache_data(ttl=3600, show_spinner="Carregando realizado via Power BI...")
    def load_dre_realizado_xmla(_self, empresa: str = None, meses_ate: int = 9, ano: int = 2026, classificacao: str = None) -> dict:
        """Extrai DRE completo via XMLA (Visão José Alberto)."""
        try:
            from data.powerbi_xmla import extrair_dre_jose_alberto
            dados = extrair_dre_jose_alberto(empresa, meses_ate, ano, classificacao)
            return dados
        except Exception as e:
            print(f"[XMLA] Erro: {e}")
            return {"real_2025": {}, "real_2026": {}, "forecast_2026": {}, "orcado_2026": {}, "all_keys": set()}

    def load_all(self) -> dict:
        """Carrega todas as tabelas e retorna um dicionário."""
        self._data = {
            "base": self.load_base_dre(),
            "plano_contas": self.load_plano_contas(),
            "mascara_dre": self.load_mascara_dre(),
            "auxiliar": self.load_auxiliar(),
            "base_real_2025": self.load_realizado_combinado(),
            "base_real_2024": self.load_base_real_2024(),
            "base_orcado": self.load_base_orcado(),
            "base_forecast": self.load_base_forecast(),
            "dre_xmla": self.load_dre_realizado_xmla(),
        }
        return self._data

    def get(self, key: str) -> pd.DataFrame:
        """Retorna uma tabela pelo nome."""
        if not self._data:
            self.load_all()
        return self._data.get(key, pd.DataFrame())


def load_all_data() -> dict:
    """Função auxiliar para carregar todas as tabelas."""
    loader = DataLoader()
    return loader.load_all()
