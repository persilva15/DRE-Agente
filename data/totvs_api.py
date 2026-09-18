"""Modulo para acesso a API TOTVS Cloud - Dados Realizados."""
import urllib.request
import json
import ssl
import base64
import pandas as pd
import os
from datetime import datetime


EXCLUIR_PATH = r"\\10.5.12.252\controladoria\25 - BI\DRE\Retirar_.xlsx"


CONTA_MAPPING = {
    "(-) ICMS CRED. S/ MERCADORIA": "Icms Credito S/Devolucao De Vendas",
    "ICMS OUTROS": "Icms Credito S/Devolucao De Vendas",
    "RECEITA FINANCEIRA ANTECIPACAO ED - COMISSAO BASPAG": "Outras Receitas Financeiras",
    "(-) SERVICO UTLIZADO NA PRESTACAO": "(-) Servicos Prestados Pj",
    "VENDAS DE MERCADORIAS": "Venda De Mercadoria",
    "(-) COFINS": "(-) Cofins",
    "(-) PIS": "(-) Pis",
    "MATERIAL UTLIZADO NA PRESTACAO": "(-) Material Utilizado Na Prestacao",
    "(-) LIMPEZA E CAPATAZIA EVENTOS": "(-) Servicos Prestados Pj",
    "SERVICOS PRESTADOS POR TERCEIROS": "(-) Servicos Prestados Pj",
    "(-) EVENTOS": "(-) Servicos Prestados Pj",
    "TELEFONES": "Telefone",
    "PUBLICIDADE E PROPRAGANDA": "Publicidades E Propagandas",
    "COMISSAO S/ VENDAS": "Comissoes S/ Vendas",
    "SOFTWARE/ LICENCA DE SISTEMA": "Sistema De Informatica",
    "(-) FREELANCER (C)": "(-) Freelancer",
    "EVENTOS E PRODUCOES": "Publicidades E Propagandas",
    "IMPOSTOS E TAXAS": "Impostos E Taxas Diversas",
    "ENTIDADES DE CLASSE E ASSOCIACOES": "Associacao De Classe",
    "MULTA": "Multa De Mora",
    "JUROS PASSIVOS": "Juros",
    "JUROS DE APLICACOES": "Aplicacoes Financeiras",
    "OUTRAS RECEITAS": "Outras Receitas Financeiras",
    "RPA": "Outras Despesas Com Pessoal",
    "PREMIOS E SEGUROS": "Seguros Diversos",
    "DSR": "Outras Despesas Com Pessoal",
    "(-) COMBUSTIVEL": "Manutencao E Conservacao",
    "ALUGUEIS DE IMOVEIS": "Alugueis",
    "COMBUSTIVEIS": "Manutencao E Conservacao",
    "(-) SERVICOS PJ INTERNOS": "(-) Servicos Prestados Pj",
    "ALUGUEL": "Alugueis",
    "EVENTOS": "Despesas Diversas",
    "(-) BONIFICACAO/COMISSAO": "Comissoes S/ Vendas",
    "ALOCACAO DE RATEIO  FOLHA DE PAGAMENTO": "Rateio",
    "ALOCACAO DE RATEIO DESPESAS GERAIS": "Rateio",
    "(-) TARIFA CARTAO - MDR": "(-) TARIFA CARTAO - MDR",
    "ADCIONAL NOTURNO": "Outras Despesas Com Pessoal",
    "(-) AJUDA DE CUSTO": "Ajuda De Custo",
    "ACADEMIA": "Outras Despesas Com Pessoal",
    "(-) ALOCACAO DE RATEIO  FOLHA DE PAGAMENTO": "Rateio",
    "(-) ALOCACAO DE RATEIO DESPESAS GERAIS": "Rateio",
    "ASSISTENCIA ODONTO E FARMACE": "Assistencia Medica, Odonto E Farmace",
    "(-) DEVOLUCAO DE VENDA DE SERVICOS": "(-) Devolucos",
    "CURSOS E TREINAMENTOS": "Outras Despesas Com Pessoal",
    "(-) INTERNET": "Internet",
    "(-) BRINDES E DOACOES": "Brindes E Bonificacoes",
    "FRETAMENTO": "Fretes",
    "SEGUROS": "Seguros Diversos",
    "(-) FRETES": "Fretes",
    "(-) ICMS": "(-) Icms S/ Vendas",
    "(-) IMPOSTOS E TAXAS": "Impostos E Taxas Diversas",
    "(-) SERVICO UTILIZADO NA PRESTACAO": "(-) Servicos Prestados Pj",
    "OUTRAS DESPESAS NAO OPERACIONAIS": "Despesas Diversas",
    "(-) MATERIAL UTLIZADO NA PRESTACAO": "(-) Material Utilizado Na Prestacao",
    "(-) DEVOLUCAO DE COMPRA": "Devolucao De Compra",
    "(-) ALUGUEL ESPACO": "(-) Locacao De Espaco, Maq. Equip/Estrut",
    "(-) CARTAO DE CREDITO": "Cartao De Credito Corporativo",
    "BENEFICIO LIVRE": "Outras Despesas Com Pessoal",
    "(-) INFRAESTRUTURA": "(-) Locacao De Espaco, Maq. Equip/Estrut",
    "(-) ALIMENTACAO E SERVICOS": "(-) Material Utilizado Na Prestacao",
    "(-) PALESTRANTE E TREINADOR": "(-) Servicos Prestados Pj",
    "(-) SERVICOS PRESTADOS POR TERCEIROS": "(-) Servicos Prestados Pj",
    "MEDICINA DO TRABALHO": "Despesas C/ Servicos Medicos",
    "(-) SEGUROS E TAXAS": "Seguros Diversos",
    "(-) INFRAESTRUTURA DE T.I": "(-) Locacao De Espaco, Maq. Equip/Estrut",
    "COMISSOES COLABORADORES": "Comissoes S/ Vendas",
    "CERTIFICADO DIGITAL": "Taxas Diversas",
    "(-) SERVICOS GRAFICOS": "(-) Material Didatico",
    "(-) EQUIPAMENTOS, MAQUINAS E INSTALACOES": "(-) Equipamentos, Maquinas e Instalacoes",
    "( - ) - SOFTWARE DE PROGRAMAS DE COMPUTADORES": "( - ) - Software de Programas de Computadores",
    "(-) VEICULOS": "Despesa C/ Veiculo",
    "DESPESAS COM ANTENACAO DE CARTAO DE CREDITO": "Despesas com Antecipacao de Cartao de Credito",
    "BONIFICACAO": "Bonificacoes Recebidas Em Mercadorias",
    "RECEITA VENDAS DE MERCADORIA INTERCOMPANY": "Venda De Mercadoria",
    "RECEITA VENDAS DE SERVICOS INTERCOMPANY": "Receita de Servicos Prestados",
    "MATERIAL DIDATICO - INTERCOMPANY": "(-) Material Didatico",
    "BAIXA DE ATIVO IMOBILIZADO": "Custo Na Venda De Imobilizado",
    "(-) CUSTO DA MERCADORIA INTERCOMPANY": "(-) Livros",
    "(-) MATERIAL DIDATICO - INTERCOMPANY": "(-) Material Didatico",
    "COFINS S/ FATURAMENTO - INTERCOMPANY": "(-) Cofins S/ Faturamento",
    "PIS S/ FATURAMENTO- INTERCOMPANY": "(-) Pis S/ Faturamento",
    "(-) COFINS S/ FATURAMENTO - INTERCOMPANY": "(-) Cofins S/ Faturamento",
    "(-) ISS S/ FATURAMENTO INTERCOMPANY": "(-) Iss S/ Faturamento",
    "(-) PIS S/ FATURAMENTO- INTERCOMPANY": "(-) Pis S/ Faturamento",
    "ICMS S/ FATURAMENTO - INTEMCOMPANY": "(-) Icms S/ Vendas",
    "(-) PUBLICIDADE E PROPAGANDA": "Publicidades E Propagandas",
    "(-) LOCACAO DE EQUIPAMENTO": "Locacao de Maquinas, Equipamentos",
    "VENDAS DE SERVICOS": "Receita de Servicos Prestados",
    "RECEITA DE SERVICOS PRESTADOS": "Receita de Servicos Prestados",
    "DESPESAS CARTORARIAS": "Despesas Diversas",
    "REFICOES": "Refeicoes",
    "VIAGENS AEREAS": "VIAGENS E HOSPEDAGENS",
    "IOF": "Impostos E Taxas Diversas",
    "BONIFICACOES CONCEDIDAS": "Brindes E Bonificacoes",
    "IRRF": "IR",
    "(-) KIT EVENTO E APOSTILA": "(-) Material Didatico",
    "(-) CAMPANHA DE MARKETING": "(-) Marketing",
}

COLIGADA_EMPRESA = {
    25: "CIS TREINAMENTO", 96: "PERSONALISSIMO", 85: "FEBRACIS SELECT",
    14: "CIS ASSESSMENT", 57: "CIS PAY", 2: "CP SERVICOS",
    8: "FEBRACIS TECNOLOGIA DA INFORMACAO", 63: "FEBRACIS PART. E GESTAO",
    6: "LIVRARIA FEBRACIS", 47: "FACULDADE FEBRACIS",
    46: "INSTITUTO PAULO VIEIRA", 101: "PERSONALISSIMO",
    103: "VERTUZ", 106: "SIMPLIFICA", 105: "SADI",
}

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")


def carregar_base_excluir() -> pd.DataFrame:
    """Carrega tabela dBase_Excluir de Retirar_.xlsx."""
    try:
        df = pd.read_excel(EXCLUIR_PATH, sheet_name="data")
        return df
    except Exception as e:
        print(f"[EXCLUIR] Erro ao carregar: {e}")
        return pd.DataFrame()


def calcular_concat_excluir(df: pd.DataFrame) -> pd.Series:
    """Calcula chave Concat_Excluir = CODCOLIGADA & CODFILIAL & CONTA_CONTABIL & DESCRICAO_CONTA & ORIGEM & DESC_CENTRO_CUSTO & DATA_EMISSAO & VALOR_CONTA."""
    col_valor = "VALOR_CONTA" if "VALOR_CONTA" in df.columns else "Real (R$)"
    
    # Normalizar CONTA_CONTABIL: remover prefixo "CREDITO - " ou "DEBITO - "
    conta = df["CONTA_CONTABIL"].astype(str).str.replace(r"^(CREDITO|DEBITO)\s*-\s*", "", regex=True)
    
    # Normalizar DATA_EMISSAO: remover timezone e hora
    data = pd.to_datetime(df["DATA_EMISSAO"], errors="coerce").dt.strftime("%Y-%m-%d")
    
    # Normalizar VALOR_CONTA: arredondar para 2 casas
    valor = pd.to_numeric(df[col_valor], errors="coerce").round(2).astype(str)
    
    return (
        df["CODCOLIGADA"].astype(str)
        + df["CODFILIAL"].astype(str)
        + conta
        + df["DESCRICAO_CONTA"].astype(str)
        + df["ORIGEM"].astype(str)
        + df["DESC_CENTRO_CUSTO"].astype(str)
        + data
        + valor
    )


def aplicar_status_gerencial(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica Status Gerencial: 'Com Ajustes Gerenciais' se NAO esta na lista de exclusao."""
    if df.empty:
        return df

    df_excluir = carregar_base_excluir()
    if df_excluir.empty:
        print("[EXCLUIR] Lista vazia. Todos os dados serao considerados.")
        df["Status Gerencial"] = "Com Ajustes Gerenciais"
        return df

    df["Concat_Excluir"] = calcular_concat_excluir(df)
    df_excluir["Concat_Excluir"] = calcular_concat_excluir(df_excluir)

    chaves_excluir = set(df_excluir["Concat_Excluir"].unique())

    df["Status Gerencial"] = df["Concat_Excluir"].apply(
        lambda x: "Sem Ajustes Gerenciais" if x in chaves_excluir else "Com Ajustes Gerenciais"
    )

    total = len(df)
    excluidos = len(df[df["Status Gerencial"] == "Sem Ajustes Gerenciais"])
    print(f"[EXCLUIR] {excluidos}/{total} registros excluidos")

    df = df[df["Status Gerencial"] == "Com Ajustes Gerenciais"].copy()
    df.drop(columns=["Concat_Excluir"], inplace=True)

    return df


class TOTVSApi:

    def __init__(self, username: str, password: str):
        self.base_url = "https://cpservicos135751.rm.cloudtotvs.com.br:8051/api/framework/v1/consultaSQLServer/RealizaConsulta"
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.encoded_credentials = base64.b64encode(f"{username}:{password}".encode()).decode()

    def _fetch_json(self, query_id: str, dt_inicio: str, dt_fim: str) -> list:
        url = f"{self.base_url}/{query_id}/0/G/?parameters=DT_INICIO={dt_inicio};DT_FIM={dt_fim}"
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Basic {self.encoded_credentials}')
        req.add_header('User-Agent', 'Mozilla/5.0')
        resp = urllib.request.urlopen(req, timeout=120, context=self.ctx)
        return json.loads(resp.read().decode('utf-8'))

    def buscar_mes(self, query_id: str, ano: int, mes: int) -> pd.DataFrame:
        if mes == 12:
            dt_inicio = f"{ano}-12-01"
            dt_fim = f"{ano}-12-31"
        else:
            dt_inicio = f"{ano}-{mes:02d}-01"
            dt_fim = f"{ano}-{mes+1:02d}-01"
        
        dados = self._fetch_json(query_id, dt_inicio, dt_fim)
        return pd.DataFrame(dados)

    def buscar_por_meses(self, ano: int, meses: list, callback=None) -> pd.DataFrame:
        todos = []
        query_ids = ["TIC.034.8", "TIC.034.11"]
        
        for mes in meses:
            for qid in query_ids:
                if callback:
                    callback(f"Buscando {qid} - {mes}/{ano}...")
                try:
                    df = self.buscar_mes(qid, ano, mes)
                    if not df.empty:
                        todos.append(df)
                except Exception as e:
                    if callback:
                        callback(f"Erro {qid} {mes}/{ano}: {e}")
        
        if not todos:
            return pd.DataFrame()
        
        df = pd.concat(todos, ignore_index=True)
        return self._aplicar_transformacoes(df)

    def _aplicar_transformacoes(self, df: pd.DataFrame) -> pd.DataFrame:
        df["DATA_EMISSAO"] = pd.to_datetime(df["DATA_EMISSAO"], errors="coerce")
        df["VALOR_CONTA"] = pd.to_numeric(df["VALOR_CONTA"], errors="coerce").fillna(0)
        df["VALOR_CONTA_V2"] = df["VALOR_CONTA"] * -1

        split_desc = df["DESCRICAO_CONTA"].str.split(" - ", n=1, expand=True)
        df["DESCRICAO_CONTA - Copiar.1"] = pd.to_numeric(split_desc[0], errors="coerce").fillna(0).astype(int)
        df["DESCRICAO_CONTA - Copiar.2"] = split_desc[1].fillna("").str.strip()

        split_conta = df["CONTA_CONTABIL"].str.split(" - ", n=1, expand=True)
        df["CONTA_CONTABIL - Copiar.1"] = split_conta[0].fillna("").str.strip()
        df["CONTA_CONTABIL - Copiar.2"] = split_conta[1].fillna("").str.strip()

        df["Cod_conta_aux"] = df["CONTA_CONTABIL - Copiar.2"].apply(
            lambda x: int(str(x).split(".")[-1]) if pd.notna(x) and "." in str(x) else None
        )
        df["Inicio Conta"] = df["CONTA_CONTABIL - Copiar.2"].str[:1].fillna("0")
        df["Descricao Conta Final"] = df["NOME_CONTA_CONTABIL"].map(CONTA_MAPPING).fillna(df["NOME_CONTA_CONTABIL"])
        df["Empresa Final"] = df.apply(
            lambda r: COLIGADA_EMPRESA.get(r.get("CODCOLIGADA"), r.get("EMPRESA", "")), axis=1
        )
        df["EMPRESA"] = df["CODCOLIGADA"].map(COLIGADA_EMPRESA).fillna(df.get("EMPRESA", ""))

        for col in ["DESCRICAO_LANCAMENTO", "CENTRO_DE_CUSTO", "DESC_CENTRO_CUSTO"]:
            if col in df.columns:
                df[col] = df[col].fillna("").str.strip()

        return df


def buscar_realizado_totvs(username: str, password: str, ano: int = 2026, meses: list = None) -> pd.DataFrame:
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"realizado_totvs_{ano}.parquet")

    if os.path.exists(cache_file):
        mod_time = os.path.getmtime(cache_file)
        age_hours = (datetime.now() - datetime.fromtimestamp(mod_time)).total_seconds() / 3600
        if age_hours < 168:
            print(f"[TOTVS] Cache encontrado ({age_hours:.1f}h)")
            df = pd.read_parquet(cache_file)
            if "Status Gerencial" not in df.columns:
                df = aplicar_status_gerencial(df)
                df.to_parquet(cache_file, index=False)
            return df

    if meses is None:
        meses = list(range(1, 10))

    api = TOTVSApi(username, password)
    df = api.buscar_por_meses(ano, meses)

    if not df.empty:
        df = aplicar_status_gerencial(df)
        df.to_parquet(cache_file, index=False)
        print(f"[TOTVS] Cache salvo: {cache_file}")

    return df
