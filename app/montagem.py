from dataclasses import dataclass, field

from app.clientes import Bloco, Cliente
from app.formatacao import formatar_inteiro, formatar_moeda, formatar_percentual
from app.parser import Campanha, valor


@dataclass
class ItemRelatorio:
    campanhas: list          # 1 campanha (normal) ou N (bloco agregado)
    bloco: Bloco
    criativo: str = ""
    publicos: str = ""
    manuais: dict = field(default_factory=dict)   # nome -> numero digitado
    titulo: str = ""         # sobrescreve o titulo do bloco (titulo por campanha)


# Chaves de razao: sempre recalculadas a partir das somas (valem para 1 ou N
# campanhas — numa campanha unica o resultado bate com a coluna do CSV).
def _soma(item: ItemRelatorio, chave: str):
    vals = [valor(c, chave) for c in item.campanhas]
    vals = [v for v in vals if v is not None]
    return sum(vals) if vals else None


def _div(a, b):
    return a / b if (a is not None and b) else None


def _resolver(item: ItemRelatorio, chave: str):
    if chave.startswith("manual:"):
        return item.manuais.get(chave[len("manual:"):])

    inv = _soma(item, "investimento")
    if chave == "custo_por_resultado":
        return _div(inv, _soma(item, "resultados"))
    if chave == "cpm":
        r = _div(inv, _soma(item, "impressoes"))
        return r * 1000 if r is not None else None
    if chave in ("ctr_link", "ctr"):
        r = _div(_soma(item, "cliques_link"), _soma(item, "impressoes"))
        return r * 100 if r is not None else None
    if chave in ("cpc_link", "custo_por_clique"):
        return _div(inv, _soma(item, "cliques_link"))
    if chave == "custo_por_seguidor":
        return _div(inv, _soma(item, "seguidores"))
    if chave == "custo_por_interacao":
        return _div(inv, _soma(item, "interacoes"))
    if chave == "custo_por_thruplay":
        return _div(inv, _soma(item, "thruplay"))
    return _soma(item, chave)


def _fmt(v, tipo: str) -> str:
    if tipo == "moeda":
        return formatar_moeda(v)
    if tipo == "percentual":
        return formatar_percentual(v)
    return formatar_inteiro(v)


def _linha(rotulo: str, texto: str, negrito: bool) -> str:
    return f"*{rotulo}:* {texto}" if negrito else f"{rotulo}: {texto}"


def _inativa(item: ItemRelatorio) -> bool:
    return any(c.veiculacao.lower() != "active" for c in item.campanhas)


def _linhas_criativo(item: ItemRelatorio, cliente: Cliente):
    b = item.bloco
    if not (b.mostra_criativo and item.criativo.strip()):
        return []
    crv = item.criativo.split("\n")
    if not b.criativo_rotulo:
        return crv
    if cliente.criativo_inline:
        return [f"{b.criativo_rotulo} {crv[0]}"] + crv[1:]
    return [b.criativo_rotulo] + crv


def montar_bloco(item: ItemRelatorio, cliente: Cliente) -> str:
    b = item.bloco
    titulo = item.titulo or b.titulo
    if cliente.marca_desativado and _inativa(item):
        titulo += " (Desativado)"
    linhas = [f"*{titulo}*" if cliente.negrito_titulo else titulo, ""]

    if not cliente.criativo_no_fim:
        cr = _linhas_criativo(item, cliente)
        if cr:
            linhas += cr + [""]

    for campo in b.campos:
        v = _resolver(item, campo.chave)
        if v is None:
            continue
        linhas.append(_linha(campo.rotulo, _fmt(v, campo.tipo), cliente.negrito_rotulo))

    if b.mostra_publico and item.publicos.strip():
        linhas.append("Público:")
        linhas.append(item.publicos)

    if cliente.criativo_no_fim:
        cr = _linhas_criativo(item, cliente)
        if cr:
            linhas += [""] + cr

    return "\n".join(linhas)


def montar_relatorio(cliente: Cliente, nome: str, periodo: str, itens,
                     intro: str = "") -> str:
    cabecalho = cliente.cabecalho.format(nome=nome, periodo=periodo)
    if cliente.negrito_titulo:
        cabecalho = "\n".join(
            f"*{l}*" if l.strip() else l for l in cabecalho.split("\n")
        )
    partes = [cabecalho]
    if intro.strip():
        partes.append(intro.strip())
    blocos = [montar_bloco(it, cliente) for it in itens]
    partes.append(f"\n{cliente.separador}\n".join(blocos))
    return "\n\n".join(partes) + "\n"
