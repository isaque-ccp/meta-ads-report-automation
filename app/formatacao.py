def formatar_inteiro(valor: int) -> str:
    """55706 -> '55.706' (milhar com ponto)."""
    return f"{int(round(valor)):,}".replace(",", ".")


def formatar_moeda(valor: float) -> str:
    """1.64 -> 'R$1,64' (milhar com ponto, decimal com vírgula)."""
    texto = f"{valor:,.2f}"            # '1,145.37'
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R${texto}"


def formatar_percentual(valor: float) -> str:
    """0.304621 -> '0,30%' (a coluna de CTR ja vem em pontos percentuais)."""
    return f"{valor:.2f}".replace(".", ",") + "%"
