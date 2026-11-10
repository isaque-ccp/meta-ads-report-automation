from dataclasses import dataclass, field

from app.parser import _norm


@dataclass
class Campo:
    rotulo: str
    chave: str       # chave logica (parser.valor / derivada) ou 'manual:<nome>'
    tipo: str        # 'moeda' | 'inteiro' | 'percentual'


@dataclass
class Bloco:
    titulo: str
    campos: list[Campo]
    criativo_rotulo: str = "Criativo:"   # "" = mostra so os links, sem rotulo
    mostra_criativo: bool = True
    mostra_publico: bool = False


@dataclass
class Cliente:
    nome_exibicao: str
    aliases: list[str]                   # casa com o nome do arquivo
    cabecalho: str                       # usa {nome} e {periodo}
    blocos: dict[str, Bloco]             # indicador -> Bloco
    negrito_titulo: bool = False         # *titulo* e linhas do cabecalho
    negrito_rotulo: bool = False         # *rotulo:* valor (CONSULTORIA)
    separador: str = "-" * 20
    agregar: bool = False                # soma campanhas do mesmo bloco num so
    criativo_no_fim: bool = False        # criativo depois do publico (Casa Móveis)
    marca_desativado: bool = False       # sufixo " (Desativado)" se campanha inativa
    intro_interativa: bool = False       # pede um resumo/intro digitado apos o titulo
    titulo_por_campanha: bool = False    # pede o titulo de cada campanha
    criativo_inline: bool = False        # "Criativo: <link>" na mesma linha do rotulo


# ---------------------------------------------------------------------------
# Cliente padrao (nao cadastrado): blocos genericos por objetivo
# ---------------------------------------------------------------------------
DEFAULT = Cliente(
    nome_exibicao="",
    aliases=[],
    cabecalho="📈 Relatório semanal - {nome}\nMétricas ({periodo}):",
    blocos={
        "actions:leadgen.other": Bloco(
            "Campanha de Leads",
            [
                Campo("Leads", "resultados", "inteiro"),
                Campo("Custo por lead", "custo_por_resultado", "moeda"),
                Campo("Investimento", "investimento", "moeda"),
            ],
            mostra_publico=True,
        ),
        "actions:onsite_conversion.messaging_conversation_started_7d": Bloco(
            "Campanha de Engajamento",
            [
                Campo("Investimento total", "investimento", "moeda"),
                Campo("Conversas", "resultados", "inteiro"),
                Campo("Custo por resultado", "custo_por_resultado", "moeda"),
                Campo("Taxa de interesse", "ctr_link", "percentual"),
            ],
            mostra_publico=True,
        ),
        "reach": Bloco(
            "Campanha de Alcance",
            [
                Campo("Alcance", "alcance", "inteiro"),
                Campo("CPM", "cpm", "moeda"),
                Campo("Investimento", "investimento", "moeda"),
            ],
            mostra_publico=True,
        ),
        "profile_visit_view": Bloco(
            "Campanha de Visitas ao Perfil",
            [
                Campo("Visitas ao perfil", "resultados", "inteiro"),
                Campo("Cliques no link", "cliques_link", "inteiro"),
                Campo("Novos seguidores", "seguidores", "inteiro"),
                Campo("Custo por seguidor", "custo_por_seguidor", "moeda"),
                Campo("Investimento", "investimento", "moeda"),
            ],
            mostra_publico=True,
        ),
        "actions:post_engagement": Bloco(
            "Campanha de Engajamento",
            [
                Campo("Investimento", "investimento", "moeda"),
                Campo("Alcance", "alcance", "inteiro"),
                Campo("Engajamento com o post", "resultados", "inteiro"),
            ],
            mostra_publico=True,
        ),
        "actions:offsite_conversion.fb_pixel_purchase": Bloco(
            "Campanha de Vendas",
            [
                Campo("Investimento Total", "investimento", "moeda"),
                Campo("Conversões", "resultados", "inteiro"),
                Campo("Custo por Conversão", "custo_por_resultado", "moeda"),
            ],
            mostra_publico=True,
        ),
    },
)
# post_interaction_gross usa o mesmo bloco de engajamento de publicacao
DEFAULT.blocos["actions:post_interaction_gross"] = DEFAULT.blocos["actions:post_engagement"]
# outros indicadores de compra reutilizam o bloco de Vendas
for _ind in ("actions:omni_purchase", "actions:onsite_web_purchase", "actions:purchase"):
    DEFAULT.blocos[_ind] = DEFAULT.blocos["actions:offsite_conversion.fb_pixel_purchase"]


# ---------------------------------------------------------------------------
# Studio Aurora
# ---------------------------------------------------------------------------
AURORA = Cliente(
    nome_exibicao="Studio Aurora",
    aliases=["studio aurora", "aurora"],
    cabecalho="📈 Relatório semanal - {nome}\nMétricas ({periodo}):",
    separador="-" * 38,
    blocos={
        "profile_visit_view": Bloco(
            "Campanha de Visitas ao Perfil",
            [
                Campo("Visitas ao perfil", "resultados", "inteiro"),
                Campo("Cliques no link", "cliques_link", "inteiro"),
                Campo("Novos seguidores", "seguidores", "inteiro"),
                Campo("Custo por seguidor", "custo_por_seguidor", "moeda"),
                Campo("Investimento", "investimento", "moeda"),
            ],
            mostra_publico=True,
        ),
        "reach": Bloco(
            "Campanha de Alcance",
            [
                Campo("Alcance", "alcance", "inteiro"),
                Campo("CPM", "cpm", "moeda"),
                Campo("Investimento", "investimento", "moeda"),
            ],
        ),
    },
)


# ---------------------------------------------------------------------------
# Clara Modas
# ---------------------------------------------------------------------------
CLARA = Cliente(
    nome_exibicao="Clara Modas",
    aliases=["clara"],
    cabecalho="📊 Relatório Semanal {nome} - {periodo}",
    separador="-" * 19,
    blocos={
        "actions:post_interaction_gross": Bloco(
            "📈 Campanha de Engajamento/Novos Seguidores + Engajados",
            [
                Campo("Investimento total", "investimento", "moeda"),
                Campo("Engajamento com a Página", "engajamento_pagina", "inteiro"),
                Campo("Interações", "interacoes", "inteiro"),
                Campo("Comentários", "comentarios", "inteiro"),
                Campo("Salvamentos", "salvamentos", "inteiro"),
                Campo("Compartilhamentos", "compartilhamentos", "inteiro"),
                Campo("Custo por Interação", "custo_por_interacao", "moeda"),
            ],
            criativo_rotulo="🔹 Criativos",
        ),
        "profile_visit_view": Bloco(
            "📈 Campanha de Seguidores",
            [
                Campo("Investimento total", "investimento", "moeda"),
                Campo("Cliques", "cliques_link", "inteiro"),
                Campo("Custo por clique", "custo_por_clique", "moeda"),
                Campo("Novos seguidores", "seguidores", "inteiro"),
                Campo("Custo por seguidor", "custo_por_seguidor", "moeda"),
            ],
            criativo_rotulo="",
        ),
        "reach": Bloco(
            "📈 Campanha de Alcance",
            [
                Campo("Investimento total", "investimento", "moeda"),
                Campo("Impressões", "impressoes", "inteiro"),
                Campo("Alcance", "alcance", "inteiro"),
            ],
            criativo_rotulo="",
        ),
    },
)
# o post_engagement "comum" tambem cai no bloco de engajamento da Clara
CLARA.blocos["actions:post_engagement"] = CLARA.blocos["actions:post_interaction_gross"]


# ---------------------------------------------------------------------------
# Espaço Festa  (agrega campanhas do mesmo objetivo)
# ---------------------------------------------------------------------------
_MSG = "actions:onsite_conversion.messaging_conversation_started_7d"

# Distribuicao de Conteudo soma a campanha de video view E a de visitas
_FESTA_DISTRIB = Bloco(
    "📈 Campanha de Distribuição de Conteúdo",
    [
        Campo("Vídeo assistido mais de 15s (Thruplay)", "thruplay", "inteiro"),
        Campo("Visitas ao perfil", "visitas_perfil_ig", "inteiro"),
        Campo("Custo por ThruPlay", "custo_por_thruplay", "moeda"),
        Campo("Alcance", "alcance", "inteiro"),
        Campo("Investimento", "investimento", "moeda"),
    ],
    mostra_criativo=False,
)

FESTA = Cliente(
    nome_exibicao="Espaço Festa",
    aliases=["festa"],
    cabecalho="📊 Relatório Semanal – {periodo}\n\n📱 META ADS",
    agregar=True,
    blocos={
        _MSG: Bloco(
            "💬 Campanha de Vendas – WhatsApp",
            [
                Campo("Investimento Total", "investimento", "moeda"),
                Campo("Conversões", "resultados", "inteiro"),
                Campo("Custo por Resultado", "custo_por_resultado", "moeda"),
            ],
            mostra_criativo=False,
        ),
        "video_thruplay_watched_actions": _FESTA_DISTRIB,
        "profile_visit_view": _FESTA_DISTRIB,
    },
)


# ---------------------------------------------------------------------------
# Nova Consultoria  (negrito em tudo + agrega)
# ---------------------------------------------------------------------------
def _bloco_consultoria(titulo: str) -> Bloco:
    return Bloco(
        titulo,
        [
            Campo("CTR% (Taxa de interesse)", "ctr_link", "percentual"),
            Campo("Custo", "investimento", "moeda"),
            Campo("Cliques", "cliques_link", "inteiro"),
            Campo("Custo por clique", "custo_por_clique", "moeda"),
            Campo("Lead", "resultados", "inteiro"),
            Campo("Custo por lead", "custo_por_resultado", "moeda"),
        ],
        mostra_criativo=False,
    )


CONSULTORIA = Cliente(
    nome_exibicao="Nova Consultoria",
    aliases=["consultoria"],
    cabecalho="📊 Relatório Semanal –{periodo}\n\nMeta ADS:",
    negrito_titulo=True,
    negrito_rotulo=True,
    agregar=True,
    separador="-" * 56,
    blocos={
        "actions:leadgen.other": _bloco_consultoria("⚙️ Formulário de Leads"),
        _MSG: _bloco_consultoria("📲 Campanha de WhatsApp"),
    },
)


# ---------------------------------------------------------------------------
# Casa Móveis (negrito so no titulo, criativo no fim, titulo por campanha,
# resumo digitado, sufixo Desativado; 1 bloco por campanha)
# ---------------------------------------------------------------------------
CASA = Cliente(
    nome_exibicao="Casa Móveis",
    aliases=["casa moveis"],
    cabecalho="📊 Relatório Semanal - {periodo}",
    negrito_titulo=True,
    criativo_no_fim=True,
    marca_desativado=True,
    intro_interativa=True,
    titulo_por_campanha=True,
    criativo_inline=True,
    separador="-" * 46,
    blocos={
        "reach": Bloco(
            "Campanha Reconhecimento",
            [
                Campo("Investimento total", "investimento", "moeda"),
                Campo("Alcance", "alcance", "inteiro"),
                Campo("Custo por 1.000 impressões", "cpm", "moeda"),
            ],
            mostra_publico=True,
        ),
        "actions:onsite_conversion.messaging_conversation_started_7d": Bloco(
            "Campanha Vendas",
            [
                Campo("Investimento total", "investimento", "moeda"),
                Campo("Conversas", "resultados", "inteiro"),
                Campo("Custo por resultado", "custo_por_resultado", "moeda"),
                Campo("Taxa de interesse", "ctr_link", "percentual"),
            ],
            mostra_publico=True,
        ),
        "actions:leadgen.other": Bloco(
            "Formulário",
            [
                Campo("Investimento total", "investimento", "moeda"),
                Campo("Leads", "resultados", "inteiro"),
                Campo("Custo por resultado", "custo_por_resultado", "moeda"),
                Campo("Taxa de interesse", "ctr_link", "percentual"),
            ],
            mostra_publico=True,
        ),
    },
)


CLIENTES = [AURORA, CLARA, FESTA, CONSULTORIA, CASA]


def detectar(nome_arquivo: str) -> Cliente:
    """Identifica o cliente pelo nome do arquivo; cai no DEFAULT se nao casar."""
    alvo = _norm(nome_arquivo)
    for cli in CLIENTES:
        if any(_norm(a) in alvo for a in cli.aliases):
            return cli
    return DEFAULT


def bloco_para(cliente: Cliente, indicador: str) -> Bloco | None:
    """Bloco do cliente para o objetivo; cai no DEFAULT; None se desconhecido."""
    return cliente.blocos.get(indicador) or DEFAULT.blocos.get(indicador)


def _blocos_unicos(cliente: Cliente):
    vistos, ordem = set(), []
    for b in cliente.blocos.values():
        if id(b) not in vistos:
            vistos.add(id(b))
            ordem.append(b)
    return ordem


def grupos(cliente: Cliente, ativas):
    """Lista de (bloco, [campanhas]).

    Cliente com agregar=True junta todas as campanhas do mesmo bloco (e ignora
    objetivos que ele nao define). Caso contrario, cada campanha vira um grupo
    proprio (bloco pode ser None -> o chamador pergunta na hora).
    """
    if cliente.agregar:
        ordem = [[b, []] for b in _blocos_unicos(cliente)]
        for c in ativas:
            alvo = cliente.blocos.get(c.indicador)
            if alvo is None:
                continue
            for par in ordem:
                if par[0] is alvo:
                    par[1].append(c)
                    break
        return [(b, lst) for b, lst in ordem if lst]
    return [(bloco_para(cliente, c.indicador), [c]) for c in ativas]
