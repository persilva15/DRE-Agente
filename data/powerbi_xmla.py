# -*- coding: utf-8 -*-
"""Modulo para extracao de dados do Power BI Desktop via XMLA/DAX.
Usa as mesmas medidas da pagina 'DRE vs Orcamento 26 (Visao Total)'.
"""
import subprocess
import re
import json
import os
import pandas as pd

try:
    import win32com.client as win32
    import pythoncom
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


def descobrir_porta_xmla() -> int:
    """Encontra a porta XMLA correta (testa todas e escolhe a que tem as medidas)."""
    ps = (
        "Get-NetTCPConnection -State Listen | Where-Object { $_.LocalAddress -eq '127.0.0.1' "
        "-and (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName -eq 'msmdsrv' } "
        "| Select-Object -ExpandProperty LocalPort"
    )
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                         capture_output=True, text=True, timeout=60)
    portas = re.findall(r"\d+", out.stdout)
    if not portas:
        raise RuntimeError("Power BI Desktop nao esta aberto.")
    # Testar cada porta e escolher a que tem as 4 medidas da Visão José Alberto
    medidas_necessarias = {"Valor Final Realizado 2025", "Valor Final Realizado 2026", "Valor Final Forecast 2026", "Valor Final Orçado"}
    for p in portas:
        try:
            pythoncom.CoInitialize()
            conn = win32.Dispatch("ADODB.Connection")
            conn.Open(f"Provider=MSOLAP;Data Source=localhost:{p}")
            rs = conn.OpenSchema(1)
            cat = None
            while not rs.EOF:
                try:
                    cat = rs.Fields("CATALOG_NAME").Value
                except Exception:
                    pass
                rs.MoveNext()
            rs.Close()
            conn.Close()
            conn2 = win32.Dispatch("ADODB.Connection")
            conn2.Open(f"Provider=MSOLAP;Data Source=localhost:{p};Initial Catalog={cat}")
            rs2 = conn2.OpenSchema(36)
            nomes = set()
            while not rs2.EOF:
                try:
                    nomes.add(rs2.Fields("MEASURE_NAME").Value)
                except Exception:
                    pass
                rs2.MoveNext()
            rs2.Close()
            conn2.Close()
            if medidas_necessarias.issubset(nomes):
                pythoncom.CoUninitialize()
                return int(p)
        except Exception:
            pass
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass
    # fallback: primeira porta
    return int(portas[0])


def abrir_conexao(porta: int):
    """Abre conexao XMLA com Power BI Desktop."""
    if not HAS_WIN32:
        raise RuntimeError("pywin32 nao instalado. Execute: pip install pywin32")
    
    try:
        pythoncom.CoInitialize()
    except Exception:
        pass
    
    conn = win32.Dispatch("ADODB.Connection")
    conn.Open(f"Provider=MSOLAP;Data Source=localhost:{porta}")
    rs = conn.OpenSchema(1)
    catalogo = None
    while not rs.EOF:
        try:
            catalogo = rs.Fields("CATALOG_NAME").Value
        except Exception:
            pass
        rs.MoveNext()
    rs.Close()
    if not catalogo:
        conn.Close()
        raise RuntimeError("Nao foi possivel identificar o catalogo.")
    conn.Close()
    
    conn = win32.Dispatch("ADODB.Connection")
    conn.Open(f"Provider=MSOLAP;Data Source=localhost:{porta};Initial Catalog={catalogo}")
    return conn


def consultar_dax(conn, dax: str) -> list:
    """Executa DAX e retorna lista de dicts."""
    rs, _ = conn.Execute(dax)
    cols = [rs.Fields(i).Name for i in range(rs.Fields.Count)]
    linhas = []
    while not rs.EOF:
        linhas.append({c: rs.Fields(i).Value for i, c in enumerate(cols)})
        rs.MoveNext()
    try:
        rs.Close()
    except Exception:
        pass
    return linhas


def extrair_dre_jose_alberto(empresa: str = None, meses_ate: int = 9, ano: int = 2026, classificacao: str = None) -> dict:
    """
    Extrai DRE completo da pagina 'Visao Jose Alberto' via XMLA.
    
    Agrupamento por 'Mascara DRE'[Nivel 1] para que SELECTEDVALUE('Plano de Contas'[Mascara DRE])
    funcione corretamente (Plano de Contas filtrado via relationship Mascara DRE -> Plano de Contas).
    
    Filtros visuais da pagina Power BI (José Alberto):
      - EMPRESA IN {lista de 11 empresas HOLDING+COLIGADA}
      - Status Gerencial = "Com Ajustes Gerenciais" (apenas R26 via fTotvs_Final)
      - Mascara DRE[Nivel 1] <> "Ebit" AND NOT(ISBLANK(...))
    
    Returns:
        dict com keys: real_2025, forecast_2026, real_2026, orcado_2026, all_keys
    """
    porta = descobrir_porta_xmla()
    conn = abrir_conexao(porta)
    
    try:
        # Filtro de EMPRESA (Auxiliar) - baseado na classificacao selecionada
        empresas_holding = [
            "CIS TREINAMENTO", "PERSONALISSIMO", "FEBRACIS SELECT",
            "CP SERVIÇOS", "FEBRACIS PART. E GESTÃO", "LIVRARIA FEBRACIS", "VX"
        ]
        empresas_coligada = [
            "CIS ASSESSMENT", "CIS PAY", "FEBRACIS TECNOLOGIA DA INFORMAÇÃO", "VERTUZ"
        ]
        empresas_todas = empresas_holding + empresas_coligada
        
        # Se empresa individual foi selecionada, filtrar apenas ela
        if empresa:
            empresas_filtro = [empresa]
        elif classificacao == "HOLDING":
            empresas_filtro = empresas_holding
        elif classificacao == "COLIGADA":
            empresas_filtro = empresas_coligada
        else:
            empresas_filtro = empresas_todas
        
        filtro_empresa = ", FILTER('Auxiliar', 'Auxiliar'[Empresa] IN {" + ", ".join('"' + e + '"' for e in empresas_filtro) + "})"
        
        # Filtro de Status Gerencial para realizado (exclui linhas com Retirar nao vazio)
        # Deve ser aplicado via CALCULATE dentro da medida, nao como filtro do SUMMARIZECOLUMNS
        calc_status_real = "CALCULATE([Valor Final Realizado 2025], 'fTotvs_Final'[Status Gerencial] = \"Com Ajustes Gerenciais\")"
        calc_status_real_2026 = "CALCULATE([Valor Final Realizado 2026], 'fTotvs_Final'[Status Gerencial] = \"Com Ajustes Gerenciais\")"
        
        # Filtro de Mascara DRE Nivel 1 nao nulo e nao "Ebit"
        filtro_mascara = ", FILTER('Mascara DRE', 'Mascara DRE'[Nivel 1] <> \"Ebit\" && NOT(ISBLANK('Mascara DRE'[Nivel 1])))"
        
        # Usar 'Mascara DRE'[Nivel 1] como agrupamento
        # Isso filtra Plano de Contas via relationship, garantindo que
        # SELECTEDVALUE('Plano de Contas'[Mascara DRE]) retorna um valor unico
        
        dax_real_2025 = """
EVALUATE
SUMMARIZECOLUMNS(
    'Mascara DRE'[Nivel 1]""" + filtro_empresa + filtro_mascara + """,
    "R25", """ + calc_status_real + """
)
ORDER BY 'Mascara DRE'[Nivel 1]
"""
        
        dax_real_2026 = """
EVALUATE
SUMMARIZECOLUMNS(
    'Mascara DRE'[Nivel 1]""" + filtro_empresa + filtro_mascara + """,
    "R26", """ + calc_status_real_2026 + """
)
ORDER BY 'Mascara DRE'[Nivel 1]
"""
        
        dax_forecast = """
EVALUATE
SUMMARIZECOLUMNS(
    'Mascara DRE'[Nivel 1]""" + filtro_empresa + filtro_mascara + """,
    "F26", [Valor Final Forecast 2026]
)
ORDER BY 'Mascara DRE'[Nivel 1]
"""
        
        dax_orcado = """
EVALUATE
SUMMARIZECOLUMNS(
    'Mascara DRE'[Nivel 1]""" + filtro_empresa + filtro_mascara + """,
    "O26", [Valor Final Or\u00e7ado]
)
ORDER BY 'Mascara DRE'[Nivel 1]
"""
        
        print("[XMLA] Extraindo DRE Jose Alberto " + str(ano) + " (empresa=" + str(empresa) + ", classificacao=" + str(classificacao) + ")...")
        
        real_2025_rows = consultar_dax(conn, dax_real_2025)
        print("[XMLA] Realizado 2025: " + str(len(real_2025_rows)) + " linhas")
        
        real_2026_rows = consultar_dax(conn, dax_real_2026)
        print("[XMLA] Realizado 2026: " + str(len(real_2026_rows)) + " linhas")
        
        forecast_rows = consultar_dax(conn, dax_forecast)
        print("[XMLA] Forecast 2026: " + str(len(forecast_rows)) + " linhas")
        
        orcado_rows = consultar_dax(conn, dax_orcado)
        print("[XMLA] Orcado 2026: " + str(len(orcado_rows)) + " linhas")
        
        # Montar estruturas - chave = Mascara DRE[Nivel 1] (strip whitespace)
        def montar_dict(rows, chave):
            d = {}
            for r in rows:
                n1 = r.get("Mascara DRE[Nivel 1]", r.get("[Nivel 1]"))
                if n1 is None:
                    continue
                n1 = n1.strip()
                val = r.get("[" + chave + "]") if "[" + chave + "]" in r else r.get(chave)
                d[n1] = float(val) if val is not None else 0.0
            return d
        
        real_2025 = montar_dict(real_2025_rows, "R25")
        real_2026 = montar_dict(real_2026_rows, "R26")
        forecast_2026 = montar_dict(forecast_rows, "F26")
        orcado_2026 = montar_dict(orcado_rows, "O26")
        
        # Todas as chaves
        all_keys = set(real_2025.keys()) | set(real_2026.keys()) | set(forecast_2026.keys()) | set(orcado_2026.keys())
        
    except Exception as e:
        raise e
    finally:
        try:
            conn.Close()
        except Exception:
            pass
        if HAS_WIN32:
            pythoncom.CoUninitialize()
    
    return {
        "real_2025": real_2025,
        "real_2026": real_2026,
        "forecast_2026": forecast_2026,
        "orcado_2026": orcado_2026,
        "all_keys": all_keys,
    }
