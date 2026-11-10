import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Campanha:
    nome_csv: str
    veiculacao: str
    indicador: str
    investimento: float
    bruto: dict        # linha crua do CSV (coluna -> string)


# ---------------------------------------------------------------------------
# Extracao de cliente / periodo
# ---------------------------------------------------------------------------
def extrair_cliente(nome_arquivo: str) -> str:
    """'CA---STUDIO-AURORA-Campanhas-...' -> 'STUDIO AURORA'. Pode vir sujo; o
    usuario confirma/edita na hora."""
    base = Path(nome_arquivo).stem
    base = re.sub(r"\s*\(\d+\)$", "", base)    # remove sufixo ' (1)' de download
    base = re.sub(r"^CA-+", "", base)          # remove prefixo 'CA---'
    base = re.split(r"-Campanhas", base)[0]    # corta no '-Campanhas'
    return base.replace("-", " ").strip()


def formatar_periodo(inicio: str, fim: str) -> str:
    """'2026-06-08','2026-06-16' -> '08/06 a 16/06'."""
    _, mi, di = inicio.split("-")
    _, mf, df = fim.split("-")
    return f"{di}/{mi} a {df}/{mf}"


# ---------------------------------------------------------------------------
# Conversores
# ---------------------------------------------------------------------------
def _num(valor: str) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def _int_opt(valor: str):
    if valor in ("", None):
        return None
    try:
        return int(float(valor))
    except ValueError:
        return None


def _float_opt(valor: str):
    if valor in ("", None):
        return None
    try:
        return float(valor)
    except ValueError:
        return None


def calcular_resultados(investimento, custo_por_resultado):
    if not custo_por_resultado:
        return None
    return round(investimento / custo_por_resultado)


# ---------------------------------------------------------------------------
# Resolucao de valores logicos a partir das colunas do CSV
# ---------------------------------------------------------------------------
# chave logica -> (nome da coluna, tipo)
_COLUNAS = {
    "investimento": ("Valor usado (BRL)", "float"),
    "alcance": ("Alcance", "int"),
    "impressoes": ("Impressões", "int"),
    "cpm": ("CPM (custo por 1.000 impressões) (BRL)", "float"),
    "custo_por_resultado": ("Custo por resultados", "float"),
    "cliques_link": ("Cliques no link", "int"),
    "cliques_todos": ("Cliques (todos)", "int"),
    "cpc_link": ("CPC (custo por clique no link) (BRL)", "float"),
    "cpc_todos": ("CPC (todos) (BRL)", "float"),
    "ctr_link": ("CTR (taxa de cliques no link)", "float"),
    "ctr_todos": ("CTR (todos)", "float"),
    "seguidores": ("Seguidores no Instagram", "int"),
    "compartilhamentos": ("Compartilhamentos do post", "int"),
    "salvamentos": ("Salvamentos do post", "int"),
    "interacoes": ("Interações", "int"),
    "comentarios": ("Comentários no post", "int"),
    "visualizacoes_pagina": ("Visualizações da página de destino", "int"),
    "visitas_perfil_ig": ("Visitas ao perfil do Instagram", "int"),
}


def _norm(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower().strip()


def _busca_fuzzy(bruto: dict, alvo: str):
    """Procura uma coluna cujo nome contenha 'alvo' (sem acento/maiusculas)."""
    alvo = _norm(alvo)
    for coluna, valor in bruto.items():
        if alvo in _norm(coluna):
            return _int_opt(valor)
    return None


def valor(campanha: Campanha, chave: str):
    """Resolve uma chave logica em numero (ou None se ausente)."""
    b = campanha.bruto
    if chave == "resultados":
        r = _int_opt(b.get("Resultados", ""))
        if r is not None:
            return r
        return calcular_resultados(
            valor(campanha, "investimento"), valor(campanha, "custo_por_resultado")
        )
    if chave == "engajamento_pagina":
        return _busca_fuzzy(b, "engajamento com a pagina")
    if chave == "thruplay":
        return _busca_fuzzy(b, "thruplay")

    col_tipo = _COLUNAS.get(chave)
    if not col_tipo:
        return None
    coluna, tipo = col_tipo
    raw = b.get(coluna, "")
    return _float_opt(raw) if tipo == "float" else _int_opt(raw)


def tem_gasto(c: Campanha) -> bool:
    return c.investimento > 0


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------
def parse_csv(caminho):
    """Retorna (periodo, [Campanha]) com TODAS as linhas (ignora vazias)."""
    caminho = Path(caminho)
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        linhas = [row for row in csv.DictReader(f) if any(row.values())]

    periodo = ""
    campanhas = []
    for row in linhas:
        if not periodo:
            periodo = formatar_periodo(
                row["Início dos relatórios"], row["Encerramento dos relatórios"]
            )
        campanhas.append(
            Campanha(
                nome_csv=row["Nome da campanha"],
                veiculacao=row.get("Veiculação da campanha", "").strip(),
                indicador=row.get("Indicador de resultados", "").strip(),
                investimento=_num(row.get("Valor usado (BRL)", "")),
                bruto=row,
            )
        )
    return periodo, campanhas
