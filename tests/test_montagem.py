from app.clientes import AURORA, CLARA, CONSULTORIA, DEFAULT, bloco_para
from app.montagem import ItemRelatorio, montar_bloco, montar_relatorio
from app.parser import Campanha


def _campanha(indicador, bruto):
    bruto = dict(bruto)
    return Campanha(
        nome_csv="x",
        veiculacao="active",
        indicador=indicador,
        investimento=float(bruto.get("Valor usado (BRL)", "0") or 0),
        bruto=bruto,
    )


def test_bloco_aurora_visitas():
    c = _campanha("profile_visit_view", {
        "Valor usado (BRL)": "244.95",
        "Resultados": "458",
        "Cliques no link": "567",
        "Seguidores no Instagram": "141",
    })
    item = ItemRelatorio([c],bloco_para(AURORA, "profile_visit_view"),
                         criativo="https://x", publicos="Lista 1%")
    bloco = montar_bloco(item, AURORA)
    assert "Visitas ao perfil: 458" in bloco
    assert "Cliques no link: 567" in bloco
    assert "Novos seguidores: 141" in bloco
    assert "Custo por seguidor: R$1,74" in bloco  # 244.95/141
    assert "Investimento: R$244,95" in bloco
    assert "Público:\nLista 1%" in bloco


def test_bloco_clara_engajamento_custo_por_interacao():
    c = _campanha("actions:post_interaction_gross", {
        "Valor usado (BRL)": "149.84",
        "Interações": "1539",
        "Comentários no post": "7",
        "Salvamentos do post": "34",
        "Compartilhamentos do post": "50",
        "Engajamento com a Página": "8472",
    })
    item = ItemRelatorio([c],bloco_para(CLARA, "actions:post_interaction_gross"),
                         criativo="https://a\nhttps://b")
    bloco = montar_bloco(item, CLARA)
    assert "🔹 Criativos\nhttps://a\nhttps://b" in bloco
    assert "Engajamento com a Página: 8.472" in bloco
    assert "Interações: 1.539" in bloco
    assert "Custo por Interação: R$0,10" in bloco  # 149.84/1539
    assert "Público" not in bloco


def test_bloco_clara_seguidores_sem_rotulo_criativo():
    c = _campanha("profile_visit_view", {
        "Valor usado (BRL)": "141.90",
        "Cliques no link": "286",
        "CPC (custo por clique no link) (BRL)": "0.496154",
        "Seguidores no Instagram": "102",
    })
    item = ItemRelatorio([c],bloco_para(CLARA, "profile_visit_view"),
                         criativo="https://link (Subimos sábado)")
    bloco = montar_bloco(item, CLARA)
    assert "Criativo:" not in bloco  # rotulo vazio -> so o link
    assert "https://link (Subimos sábado)" in bloco
    assert "Custo por clique: R$0,50" in bloco


def test_negrito_consultoria_titulo_e_rotulos():
    c = _campanha("actions:leadgen.other", {
        "Valor usado (BRL)": "51.76",
        "Resultados": "6",
        "Custo por resultados": "8.63",
        "Cliques no link": "19",
        "Impressões": "1000",
    })
    item = ItemRelatorio([c], bloco_para(CONSULTORIA, "actions:leadgen.other"))
    texto = montar_bloco(item, CONSULTORIA)
    assert "*⚙️ Formulário de Leads*" in texto   # titulo em negrito
    assert "*Custo:* R$51,76" in texto            # rotulo em negrito
    assert "*Lead:* 6" in texto


def test_casa_moveis_negrito_so_titulo_criativo_no_fim():
    from app.clientes import CASA
    c = _campanha("reach", {"Valor usado (BRL)": "68.73", "Alcance": "19152",
                            "Impressões": "19146"})
    c.veiculacao = "inactive"
    item = ItemRelatorio([c], bloco_para(CASA, "reach"),
                         criativo='"Similar"\nhttps://x', publicos="Bairros Alto",
                         titulo="Campanha Reconhecimento")
    texto = montar_bloco(item, CASA)
    assert "*Campanha Reconhecimento (Desativado)*" in texto  # titulo bold + sufixo
    assert "Investimento total: R$68,73" in texto             # rotulo SEM negrito
    assert "Alcance: 19.152" in texto
    # criativo vem depois do publico
    assert texto.index("Público:") < texto.index("Criativo:")


def test_relatorio_cabecalho_clara():
    c = _campanha("reach", {"Valor usado (BRL)": "49.34", "Alcance": "10855",
                            "Impressões": "19996"})
    item = ItemRelatorio([c],bloco_para(CLARA, "reach"), criativo="")
    texto = montar_relatorio(CLARA, "Clara Modas", "08/06 a 14/06", [item])
    assert texto.startswith("📊 Relatório Semanal Clara Modas - 08/06 a 14/06")
    assert "📈 Campanha de Alcance" in texto
