from app.clientes import AURORA, CLARA, DEFAULT, detectar, bloco_para


def test_detectar_aurora():
    nome = "CA---STUDIO-AURORA-Campanhas-8-de-jun-de-2026-14-de-jun-de-2026.csv"
    assert detectar(nome) is AURORA


def test_detectar_clara_com_sufixo():
    nome = "Clara-Mo-as---Conta-03-Campanhas-8 (1).csv"
    assert detectar(nome) is CLARA


def test_detectar_desconhecido_cai_no_default():
    assert detectar("OutraMarca-Campanhas.csv") is DEFAULT


def test_bloco_do_cliente_tem_prioridade():
    # profile_visit_view: na Aurora e "Visitas ao Perfil", no DEFAULT idem,
    # mas na Clara e "Seguidores"
    assert bloco_para(CLARA, "profile_visit_view").titulo == "📈 Campanha de Seguidores"
    assert bloco_para(AURORA, "profile_visit_view").titulo == "Campanha de Visitas ao Perfil"


def test_bloco_cai_no_default_quando_cliente_nao_define():
    # Aurora nao define 'leadgen'; deve cair no bloco generico do DEFAULT
    bloco = bloco_para(AURORA, "actions:leadgen.other")
    assert bloco is not None
    assert bloco.titulo == "Campanha de Leads"


def test_bloco_desconhecido_retorna_none():
    assert bloco_para(AURORA, "actions:coisa_nova") is None
