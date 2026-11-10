from app.formatacao import formatar_moeda, formatar_inteiro, formatar_percentual


def test_moeda_simples():
    assert formatar_moeda(1.64) == "R$1,64"


def test_moeda_arredonda_duas_casas():
    assert formatar_moeda(8.68615385) == "R$8,69"


def test_moeda_com_milhar():
    assert formatar_moeda(1145.37) == "R$1.145,37"


def test_inteiro_com_milhar():
    assert formatar_inteiro(55706) == "55.706"


def test_inteiro_pequeno():
    assert formatar_inteiro(290) == "290"


def test_percentual():
    assert formatar_percentual(1.06) == "1,06%"
    assert formatar_percentual(0.304621) == "0,30%"
