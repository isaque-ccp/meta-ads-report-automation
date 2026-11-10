from app.parser import (
    Campanha,
    extrair_cliente,
    formatar_periodo,
    calcular_resultados,
    valor,
    tem_gasto,
)


def _campanha(bruto):
    return Campanha(
        nome_csv=bruto.get("Nome da campanha", "x"),
        veiculacao=bruto.get("Veiculação da campanha", "active"),
        indicador=bruto.get("Indicador de resultados", ""),
        investimento=float(bruto.get("Valor usado (BRL)", "0") or 0),
        bruto=bruto,
    )


def test_extrair_cliente_simples():
    nome = "CA---Casa-Móveis-Campanhas-8-de-jun-de-2026-16-de-jun-de-2026.csv"
    assert extrair_cliente(nome) == "Casa Móveis"


def test_extrair_cliente_ignora_sufixo_download():
    nome = "Clara-Campanhas-8-de-jun-de-2026-14-de-jun-de-2026 (1).csv"
    assert extrair_cliente(nome) == "Clara"


def test_formatar_periodo():
    assert formatar_periodo("2026-06-08", "2026-06-16") == "08/06 a 16/06"


def test_calcular_resultados():
    assert calcular_resultados(112.92, 8.68615385) == 13
    assert calcular_resultados(100.0, 0) is None


def test_valor_resolve_colunas():
    c = _campanha({
        "Valor usado (BRL)": "149.84",
        "Alcance": "17872",
        "Interações": "1539",
        "Comentários no post": "7",
        "Salvamentos do post": "34",
        "Compartilhamentos do post": "50",
        "Resultados": "1539",
    })
    assert valor(c, "investimento") == 149.84
    assert valor(c, "alcance") == 17872
    assert valor(c, "interacoes") == 1539
    assert valor(c, "comentarios") == 7
    assert valor(c, "salvamentos") == 34
    assert valor(c, "compartilhamentos") == 50
    assert valor(c, "resultados") == 1539


def test_valor_coluna_ausente_retorna_none():
    c = _campanha({"Valor usado (BRL)": "10"})
    assert valor(c, "seguidores") is None
    assert valor(c, "interacoes") is None


def test_valor_engajamento_pagina_fuzzy():
    c = _campanha({"Engajamento com a Página": "8472"})
    assert valor(c, "engajamento_pagina") == 8472


def test_resultados_deriva_quando_sem_coluna():
    c = _campanha({"Valor usado (BRL)": "112.92", "Custo por resultados": "8.68615385"})
    assert valor(c, "resultados") == 13


def test_tem_gasto():
    assert tem_gasto(_campanha({"Valor usado (BRL)": "10"})) is True
    assert tem_gasto(_campanha({"Valor usado (BRL)": "0"})) is False
