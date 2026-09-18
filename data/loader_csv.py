# -*- coding: utf-8 -*-
"""
Loader de dados via CSV (modo nuvem).
Lê CSVs do GitHub em vez de Excel da rede.
"""
import pandas as pd
import streamlit as st
import os
from datetime import datetime

from config import EMPRESAS_MAP


class DataLoaderCSV:
    """
    Carrega dados de CSVs para o modo nuvem (Streamlit Cloud).
    
    Compatível com a interface do DataLoader local.
    """

    def __init__(self, base_url: str = None):
        """
        Args:
            base_url: URL base dos CSVs.
                      - GitHub raw: https://raw.githubusercontent.com/user/repo/main/csv_data
                      - Local: csv_data (pasta local)
        """
        self.base_url = base_url or "csv_data"

    def _read_csv(self, filename: str) -> pd.DataFrame:
        """Lê um CSV ou CSV.gz do base_url."""
        import gzip
        
        try:
            if self.base_url.startswith("http"):
                # Tentar .gz primeiro, depois .csv
                for ext in [".gz", ""]:
                    url = f"{self.base_url}/{filename}{ext}"
                    try:
                        if ext == ".gz":
                            import urllib.request
                            import io
                            req = urllib.request.urlopen(url)
                            data = gzip.decompress(req.read())
                            df = pd.read_csv(io.BytesIO(data))
                        else:
                            df = pd.read_csv(url)
                        return df
                    except Exception:
                        continue
                st.error(f"Erro ao ler {filename}")
                return pd.DataFrame()
            else:
                # Local: tentar .gz primeiro, depois .csv
                gz_path = os.path.join(self.base_url, filename + ".gz")
                csv_path = os.path.join(self.base_url, filename)
                
                if os.path.exists(gz_path):
                    df = pd.read_csv(gz_path, compression="gzip")
                elif os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                else:
                    st.error(f"Arquivo não encontrado: {filename}")
                    return pd.DataFrame()
                
                return df
        except Exception as e:
            st.error(f"Erro ao ler {filename}: {e}")
            return pd.DataFrame()

    def load_base_dre(self) -> pd.DataFrame:
        """Carrega tabela Base (DRE original)."""
        df = self._read_csv("base_dre.csv")
        if not df.empty:
            if "data" in df.columns:
                df["data"] = pd.to_datetime(df["data"], errors="coerce")
            if "Valor" in df.columns:
                df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
        return df

    def load_plano_contas(self) -> pd.DataFrame:
        """Carrega tabela Plano de Contas (Dim)."""
        return self._read_csv("plano_contas.csv")

    def load_mascara_dre(self) -> pd.DataFrame:
        """Carrega tabela Mascara DRE."""
        return self._read_csv("mascara_dre.csv")

    def load_auxiliar(self) -> pd.DataFrame:
        """Carrega tabela Auxiliar (empresas)."""
        return self._read_csv("auxiliar.csv")

    def load_realizado_2025(self) -> pd.DataFrame:
        """Carrega Realizado 2025 (congelado)."""
        df = self._read_csv("real_2025.csv")
        if not df.empty and "DATA_EMISSAO" in df.columns:
            df["DATA_EMISSAO"] = pd.to_datetime(df["DATA_EMISSAO"], errors="coerce")
        return df

    def load_realizado_2026(self) -> pd.DataFrame:
        """Carrega Realizado 2026 (TOTVS)."""
        df = self._read_csv("real_2026.csv")
        if not df.empty and "DATA_EMISSAO" in df.columns:
            df["DATA_EMISSAO"] = pd.to_datetime(df["DATA_EMISSAO"], errors="coerce")
        return df

    def load_orcado_2026(self) -> pd.DataFrame:
        """Carrega Orçado 2026."""
        return self._read_csv("orcado_2026.csv")

    def load_forecast_2026(self) -> pd.DataFrame:
        """Carrega Forecast 2026."""
        return self._read_csv("forecast_2026.csv")

    def load_realizado_combinado(self) -> pd.DataFrame:
        """Combina Realizado 2025 + 2026 (compatibilidade com loader local)."""
        df_2025 = self.load_realizado_2025()
        df_2026 = self.load_realizado_2026()
        
        if df_2025.empty and df_2026.empty:
            return pd.DataFrame()
        
        frames = []
        if not df_2025.empty:
            frames.append(df_2025)
        if not df_2026.empty:
            frames.append(df_2026)
        
        if frames:
            return pd.concat(frames, ignore_index=True)
        return df_2025

    def load_retirar(self) -> pd.DataFrame:
        """Carrega lista de exclusão (Retirar_.xlsx)."""
        return self._read_csv("retirar.csv")

    def load_all(self) -> dict:
        """Carrega todas as tabelas e retorna um dicionário."""
        return {
            "base": self.load_base_dre(),
            "plano_contas": self.load_plano_contas(),
            "mascara_dre": self.load_mascara_dre(),
            "auxiliar": self.load_auxiliar(),
            "base_real_2025": self.load_realizado_combinado(),
            "base_orcado": self.load_orcado_2026(),
            "base_forecast": self.load_forecast_2026(),
        }

    def get_info(self) -> dict:
        """Retorna informações sobre os CSVs disponíveis."""
        info = {}
        
        if self.base_url.startswith("http"):
            base = self.base_url
        else:
            base = self.base_url
        
        csv_files = [
            "base_dre.csv", "plano_contas.csv", "mascara_dre.csv",
            "auxiliar.csv", "real_2025.csv", "real_2026.csv",
            "orcado_2026.csv", "forecast_2026.csv", "retirar.csv",
        ]
        
        for f in csv_files:
            try:
                if self.base_url.startswith("http"):
                    url = f"{base}/{f}"
                    df = pd.read_csv(url, nrows=0)
                    info[f] = {"status": "ok", "colunas": list(df.columns)}
                else:
                    path = os.path.join(base, f)
                    if os.path.exists(path):
                        df = pd.read_csv(path, nrows=0)
                        info[f] = {"status": "ok", "colunas": list(df.columns)}
                    else:
                        info[f] = {"status": "não encontrado"}
            except Exception as e:
                info[f] = {"status": f"erro: {e}"}
        
        return info
