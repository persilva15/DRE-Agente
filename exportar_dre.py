# -*- coding: utf-8 -*-
"""
Script de exportação de dados DRE para CSV.
Executa no servidor local, exporta CSVs e faz git push para nuvem.

Uso:
    python exportar_dre.py              # Exporta tudo
    python exportar_dre.py --totvs      # Exporta apenas TOTVS (diário)
    python exportar_dre.py --validate   # Valida XMLA vs CSV
"""
import os
import sys
import pandas as pd
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# =============================================================================
# CAMINHOS EXCEL (local)
# =============================================================================

NETWORK_BASE = "//10.5.12.252/controladoria"

EXCEL_PATHS = {
    "base_dre": f"{NETWORK_BASE}/25 - BI/DRE/Base_DRE_v2.xlsx",
    "base_real_2025": f"{NETWORK_BASE}/25 - BI/DRE/Base_Dre_2025_Congelada/Base_Real_2025.xlsx",
    "orcado_2026": f"{NETWORK_BASE}/24 - Orçamento/Orçamento 2026/ORCAMENTO_CONTABIL.xlsx",
    "forecast_2026": f"{NETWORK_BASE}/24 - Orçamento/Orçamento 2026/Forecast 2026/FORECAST_CONTABIL.xlsx",
    "retirar": f"{NETWORK_BASE}/25 - BI/DRE/Retirar_.xlsx",
}

SHEETS = {
    "base": "Base (2)",
    "plano_contas": "Dim (2)",
    "mascara_dre": "Mascara DRE",
    "auxiliar": "Auxiliar",
    "real_2025": "Base",
    "orcado": "Base_Orcado",
    "forecast": "Plan. Forecast BI",
    "retirar": "data",
}

CSV_DIR = "csv_data"

# =============================================================================
# FUNÇÕES DE EXPORTAÇÃO
# =============================================================================

def exportar_excel_para_csv(nome: str, path_excel: str, sheet: str, path_csv: str) -> bool:
    """Exporta uma aba do Excel para CSV."""
    try:
        if not os.path.exists(path_excel):
            print(f"[AVISO] Arquivo nao encontrado: {path_excel}")
            return False
        
        df = pd.read_excel(path_excel, sheet_name=sheet, engine="openpyxl")
        os.makedirs(os.path.dirname(path_csv) if os.path.dirname(path_csv) else ".", exist_ok=True)
        df.to_csv(path_csv, index=False, encoding="utf-8-sig")
        print(f"[OK] {nome}: {len(df)} linhas -> {os.path.basename(path_csv)}")
        return True
    except Exception as e:
        print(f"[ERRO] {nome}: {e}")
        return False


def exportar_totvs() -> bool:
    """Exporta dados TOTVS via API (Realizado 2026)."""
    try:
        from data.totvs_api import buscar_realizado_totvs
        
        username = os.environ.get("TOTVS_USER", "")
        password = os.environ.get("TOTVS_PASS", "")
        
        if not username or not password:
            print("[AVISO] Credenciais TOTVS não encontradas no .env")
            print("        Defina TOTVS_USER e TOTVS_PASS no arquivo .env")
            return False
        
        df = buscar_realizado_totvs(username, password, ano=2026)
        if df.empty:
            print("[AVISO] TOTVS retornou dados vazios")
            return False
        
        path_csv = os.path.join(CSV_DIR, "real_2026.csv")
        df.to_csv(path_csv, index=False, encoding="utf-8-sig")
        print(f"[OK] TOTVS R2026: {len(df)} linhas -> {os.path.basename(path_csv)}")
        return True
    except Exception as e:
        print(f"[ERRO] TOTVS: {e}")
        return False


def git_push(mensagem: str = None):
    """Faz git add, commit e push."""
    try:
        if mensagem is None:
            mensagem = f"Atualização DRE {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        subprocess.run(["git", "add", CSV_DIR], check=True, capture_output=True)
        result = subprocess.run(["git", "status", "--porcelain", CSV_DIR], capture_output=True, text=True)
        
        if not result.stdout.strip():
            print("[INFO] Nenhuma alteração para commitar")
            return
        
        subprocess.run(["git", "commit", "-m", mensagem], check=True, capture_output=True)
        subprocess.run(["git", "push"], check=True, capture_output=True)
        print(f"[OK] Git push: {mensagem}")
    except subprocess.CalledProcessError as e:
        print(f"[ERRO] Git: {e}")
    except FileNotFoundError:
        print("[AVISO] Git não encontrado. Pulando push.")


def exportar_todos():
    """Exporta todos os arquivos Excel para CSV."""
    print("=" * 50)
    print("  EXPORTAÇÃO DRE FEBRACIS")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 50)
    print()
    
    os.makedirs(CSV_DIR, exist_ok=True)
    
    sucesso = 0
    total = 0
    
    # 1. Base DRE (4 abas)
    abas_base = [
        ("Base DRE", EXCEL_PATHS["base_dre"], SHEETS["base"], "base_dre.csv"),
        ("Plano de Contas", EXCEL_PATHS["base_dre"], SHEETS["plano_contas"], "plano_contas.csv"),
        ("Mascara DRE", EXCEL_PATHS["base_dre"], SHEETS["mascara_dre"], "mascara_dre.csv"),
        ("Auxiliar", EXCEL_PATHS["base_dre"], SHEETS["auxiliar"], "auxiliar.csv"),
    ]
    
    for nome, path_excel, sheet, csv_file in abas_base:
        total += 1
        path_csv = os.path.join(CSV_DIR, csv_file)
        if exportar_excel_para_csv(nome, path_excel, sheet, path_csv):
            sucesso += 1
    
    print()
    
    # 2. Realizado 2025 (congelado)
    total += 1
    if exportar_excel_para_csv(
        "Realizado 2025",
        EXCEL_PATHS["base_real_2025"],
        SHEETS["real_2025"],
        os.path.join(CSV_DIR, "real_2025.csv")
    ):
        sucesso += 1
    
    # 3. Orçado 2026
    total += 1
    if exportar_excel_para_csv(
        "Orçado 2026",
        EXCEL_PATHS["orcado_2026"],
        SHEETS["orcado"],
        os.path.join(CSV_DIR, "orcado_2026.csv")
    ):
        sucesso += 1
    
    # 4. Forecast 2026
    total += 1
    if exportar_excel_para_csv(
        "Forecast 2026",
        EXCEL_PATHS["forecast_2026"],
        SHEETS["forecast"],
        os.path.join(CSV_DIR, "forecast_2026.csv")
    ):
        sucesso += 1
    
    # 5. Retirar (lista de exclusão)
    total += 1
    if exportar_excel_para_csv(
        "Retirar",
        EXCEL_PATHS["retirar"],
        SHEETS["retirar"],
        os.path.join(CSV_DIR, "retirar.csv")
    ):
        sucesso += 1
    
    print()
    
    # 6. TOTVS API (diário)
    total += 1
    if exportar_totvs():
        sucesso += 1
    
    print()
    print("=" * 50)
    print(f"  RESULTADO: {sucesso}/{total} arquivos exportados")
    print("=" * 50)
    
    return sucesso == total


def exportar_apenas_totvs():
    """Exporta apenas dados TOTVS (atualização diária)."""
    print("=" * 50)
    print("  EXPORTAÇÃO TOTVS (diário)")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 50)
    print()
    
    os.makedirs(CSV_DIR, exist_ok=True)
    
    if exportar_totvs():
        print()
        print("[OK] Dados TOTVS exportados com sucesso")
        return True
    else:
        print()
        print("[ERRO] Falha na exportação TOTVS")
        return False


def listar_csvs():
    """Lista todos os CSVs exportados."""
    if not os.path.exists(CSV_DIR):
        print("Nenhum CSV encontrado")
        return
    
    print(f"\nCSVs em {CSV_DIR}:")
    print("-" * 40)
    
    for f in sorted(os.listdir(CSV_DIR)):
        if f.endswith(".csv"):
            path = os.path.join(CSV_DIR, f)
            tamanho = os.path.getsize(path) / 1024
            modificado = datetime.fromtimestamp(os.path.getmtime(path))
            print(f"  {f:<25} {tamanho:>6.1f} KB  {modificado.strftime('%d/%m/%Y %H:%M')}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    if "--totvs" in sys.argv:
        ok = exportar_apenas_totvs()
    elif "--list" in sys.argv:
        listar_csvs()
        ok = True
    else:
        ok = exportar_todos()
    
    if ok:
        print("\n[OK] Exportação concluída")
    else:
        print("\n[AVISO] Exportação concluída com erros")
    
    sys.exit(0 if ok else 1)
