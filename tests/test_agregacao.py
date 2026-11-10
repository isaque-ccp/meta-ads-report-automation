from app.clientes import FESTA, CONSULTORIA, grupos
from app.montagem import ItemRelatorio, montar_bloco, montar_relatorio
from app.parser import Campanha

_MSG = "actions:onsite_conversion.messaging_conversation_started_7d"


def _camp(indicador, **cols):
    return Campanha(
        nome_csv=cols.pop("nome", "x"),
        veiculacao="active",
        indicador=indicador,
        investimento=float(cols.get("Valor usado (BRL)", "0") or 0),
        bruto=cols,
    )


def test_grupos_agrega_mensagens_festa():
    c1 = _camp(_MSG, **{"Valor usado (BRL)": "177.45", "Resultados": "36",
                        "Cliques no link": "86", "Impressões": "8140"})
    c2 = _camp(_MSG, **{"Valor usado (BRL)": "211.26", "Resultados": "30",
                        "Cliques no link": "71", "Impressões": "9452"})
    video = _camp("video_thruplay_watched_actions",
                  **{"Valor usado (BRL)": "70.01", "ThruPlays": "1842",
                     "Alcance": "5340"})
    visitas = _camp("profile_visit_view",
                    **{"Valor usado (BRL)": "69.14", "ThruPlays": "265",
                       "Visitas ao perfil do Instagram": "29", "Alcance": "6049"})
    gs = grupos(FESTA, [c1, c2, video, visitas])
    # 2 grupos: vendas (2 mensagens) e distribuicao (video + visitas somados)
    titulos = {g[0].titulo: len(g[1]) for g in gs}
    assert titulos["💬 Campanha de Vendas – WhatsApp"] == 2
    assert titulos["📈 Campanha de Distribuição de Conteúdo"] == 2


def test_festa_distribuicao_soma_video_e_visitas():
    video = _camp("video_thruplay_watched_actions",
                  **{"Valor usado (BRL)": "70.01", "ThruPlays": "1842",
                     "Visitas ao perfil do Instagram": "2", "Alcance": "5340"})
    visitas = _camp("profile_visit_view",
                    **{"Valor usado (BRL)": "69.14", "ThruPlays": "265",
                       "Visitas ao perfil do Instagram": "29", "Alcance": "6049"})
    bloco = FESTA.blocos["video_thruplay_watched_actions"]
    texto = montar_bloco(ItemRelatorio([video, visitas], bloco), FESTA)
    assert "Vídeo assistido mais de 15s (Thruplay): 2.107" in texto  # 1842+265
    assert "Visitas ao perfil: 31" in texto                          # 2+29
    assert "Alcance: 11.389" in texto                                # 5340+6049
    assert "Investimento: R$139,15" in texto                         # 70.01+69.14
    assert "Custo por ThruPlay: R$0,07" in texto                     # 139.15/2107


def test_festa_vendas_soma_investimento_e_conversoes():
    c1 = _camp(_MSG, **{"Valor usado (BRL)": "177.45", "Resultados": "36"})
    c2 = _camp(_MSG, **{"Valor usado (BRL)": "211.26", "Resultados": "30"})
    bloco = FESTA.blocos[_MSG]
    texto = montar_bloco(ItemRelatorio([c1, c2], bloco), FESTA)
    assert "Investimento Total: R$388,71" in texto       # 177.45+211.26
    assert "Conversões: 66" in texto                       # 36+30
    assert "Custo por Resultado: R$5,89" in texto          # 388.71/66


def test_festa_distribuicao_thruplay():
    video = _camp("video_thruplay_watched_actions",
                  **{"Valor usado (BRL)": "70.01", "ThruPlays": "1842",
                     "Visitas ao perfil do Instagram": "39", "Alcance": "5340"})
    bloco = FESTA.blocos["video_thruplay_watched_actions"]
    texto = montar_bloco(ItemRelatorio([video], bloco), FESTA)
    assert "Vídeo assistido mais de 15s (Thruplay): 1.842" in texto
    assert "Visitas ao perfil: 39" in texto
    assert "Custo por ThruPlay: R$0,04" in texto           # 70.01/1842
    assert "Alcance: 5.340" in texto


def test_consultoria_negrito_e_agregacao_whatsapp():
    c1 = _camp(_MSG, **{"Valor usado (BRL)": "355.44", "Resultados": "29",
                        "Cliques no link": "78", "Impressões": "6133"})
    c2 = _camp(_MSG, **{"Valor usado (BRL)": "382.44", "Resultados": "27",
                        "Cliques no link": "164", "Impressões": "16983"})
    texto = montar_relatorio(CONSULTORIA, "Nova Consultoria", "17/05 a 15/06",
                             [ItemRelatorio([c1, c2], CONSULTORIA.blocos[_MSG])])
    assert texto.startswith("*📊 Relatório Semanal –17/05 a 15/06*")
    assert "*Meta ADS:*" in texto
    assert "*📲 Campanha de WhatsApp*" in texto
    assert "*Custo:* R$737,88" in texto                    # 355.44+382.44
    assert "*Lead:* 56" in texto                            # 29+27
