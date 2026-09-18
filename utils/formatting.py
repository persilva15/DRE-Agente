from typing import Optional


def formatar_valor(valor: float, dividir_por_mil: bool = True) -> str:
    """
    Formata valor em R$.

    Args:
        valor: Valor a formatar
        dividir_por_mil: Se True, divide o valor por 1000 (padrão Power BI)
    """
    if valor is None:
        return "R$ -"

    if dividir_por_mil:
        valor = valor / 1000

    if abs(valor) >= 1_000_000:
        return f"R$ {valor/1_000_000:,.1f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
    elif abs(valor) >= 1_000:
        return f"R$ {valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_variacao_rs(valor: float, dividir_por_mil: bool = True) -> str:
    """
    Formata variação em R$.

    Args:
        valor: Valor da variação
        dividir_por_mil: Se True, divide o valor por 1000
    """
    if valor is None:
        return "-"

    if dividir_por_mil:
        valor = valor / 1000

    sinal = "+" if valor > 0 else ""
    return f"R$ {sinal}{valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_variacao_pct(valor: float) -> str:
    """
    Formata variação percentual.
    """
    if valor is None:
        return "-"

    sinal = "+" if valor > 0 else ""
    return f"{sinal}{valor:.1%}"


def formatar_indicador(valor: float, tipo: str = "receita") -> str:
    """
    Retorna indicador visual (emoji) para variação.

    Args:
        valor: Valor da variação percentual
        tipo: 'receita' (verde quando positivo) ou 'despesa' (verde quando negativo)
    """
    if valor is None:
        return "⚪"

    if tipo == "receita":
        return "🟢" if valor > 0 else "🔴" if valor < 0 else "⚪"
    else:  # despesa
        return "🟢" if valor < 0 else "🔴" if valor > 0 else "⚪"


def formatar_tabela_variacao(dados: list[dict]) -> str:
    """
    Formata uma tabela de variação.

    Args:
        dados: Lista de dicts com chaves 'linha', 'valor', 'variacao_rs', 'variacao_pct'
    """
    linhas = []
    linhas.append(f"{'Linha DRE':<35} {'Valor':>15} {'Var R$':>15} {'Var %':>10}")
    linhas.append("-" * 80)

    for item in dados:
        linha = item.get("linha", "")
        valor = item.get("valor", "")
        var_rs = item.get("variacao_rs", "")
        var_pct = item.get("variacao_pct", "")
        indicador = item.get("indicador", "")

        linhas.append(f"{linha:<35} {valor:>15} {var_rs:>15} {var_pct:>10} {indicador}")

    return "\n".join(linhas)
