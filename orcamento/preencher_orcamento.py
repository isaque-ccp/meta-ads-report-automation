"""Preenche o gasto diario (celulas laranja) na planilha de controle de
orcamento, puxando da Meta Marketing API."""
import os
import shutil
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string, get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from orcamento.meta_api import carregar_token, insights_diarios  # noqa: E402

# chave de conversao -> action_type da Meta ('leads' e 'thruplay' sao especiais)
CONV_ACTION = {
    "conversas": "onsite_conversion.messaging_conversation_started_7d",
    "visitas": "link_click",
    "engajamento": "post_engagement",
}

LARANJA = "FFFFF2CC"   # cor dos inputs diarios
MESES = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
LINHAS = range(15, 46)   # tabela diaria


@dataclass
class BlocoOrc:
    nome: str
    coluna: str          # coluna do CUSTO/DIA (ex 'F')
    objetivos: set       # objetivos da Meta que somam nesse bloco
    conversao: str = None  # conversas|leads|visitas|engajamento|thruplay|None


@dataclass
class ClienteOrc:
    chave: str
    act_id: str
    planilha: Path
    blocos: list


PLANILHAS = Path(os.environ.get("PLANILHAS_DIR", Path.home() / "Downloads"))

# Clientes de exemplo: troque act_id pelo ID real da conta de anuncios
# (sem o prefixo 'act_') e aponte para a planilha de cada cliente.
FESTA = ClienteOrc(
    chave="festa",
    act_id="000000000000001",
    planilha=PLANILHAS / "Controle de Orçamento - Espaço Festa.xlsx",
    blocos=[
        BlocoOrc("Campanha de Vendas", "F", {"OUTCOME_SALES"}, conversao="conversas"),
        BlocoOrc("Campanhas de Funil", "Q",
                 {"OUTCOME_ENGAGEMENT", "LINK_CLICKS", "OUTCOME_TRAFFIC",
                  "OUTCOME_AWARENESS"}, conversao="thruplay"),
    ],
)

CLARA = ClienteOrc(
    chave="clara",
    act_id="000000000000002",
    planilha=PLANILHAS / "Controle de Orçamento - Clara Modas.xlsx",
    blocos=[
        BlocoOrc("Seguidores", "F", {"LINK_CLICKS"}, conversao="visitas"),
        # objetivos vazios = bloco coringa (recebe o que nao foi mapeado)
        BlocoOrc("Outras (Engajamento + Alcance)", "Q", set(), conversao="engajamento"),
    ],
)

CASA = ClienteOrc(
    chave="casa_moveis",
    act_id="000000000000003",
    planilha=PLANILHAS / "Controle de Orçamento - Casa Móveis.xlsx",
    blocos=[
        BlocoOrc("Leads (mensagens/WhatsApp)", "F", set(), conversao="conversas"),
        BlocoOrc("Formulários", "Q", {"OUTCOME_LEADS"}, conversao="leads"),
    ],
)

CLIENTES = {c.chave: c for c in [FESTA, CLARA, CASA]}


def periodo_e_aba(hoje: date):
    """Aba do mes atual (mes civil). Retorna (inicio, fim, nome_da_aba)."""
    ini = date(hoje.year, hoje.month, 1)
    return ini, hoje, f"Meta ADS - {MESES[hoje.month]}"


def datas_das_linhas(ws, ini: date):
    """Mapeia cada linha da tabela diaria (linha 15 = dia 1) para a data.
    Dias que nao existem no mes (ex: 31 em junho) sao ignorados."""
    datas = {}
    for row in LINHAS:
        dia = ws[f"C{row}"].value
        if dia is None:
            continue
        try:
            datas[row] = date(ini.year, ini.month, int(dia))
        except ValueError:
            pass
    return datas


def _achar_aba(wb, alvo: str):
    """Acha a aba ignorando maiusculas/espacos (ex: 'Meta Ads - Junho')."""
    alvo_n = " ".join(alvo.lower().split())
    for s in wb.sheetnames:
        if " ".join(s.lower().split()) == alvo_n:
            return s
    return None


def _eh_laranja(cell) -> bool:
    f = cell.fill
    return bool(f and f.patternType == "solid" and f.fgColor.rgb == LARANJA)


def _col_conv(col: str) -> str:
    """Coluna CONVERSÕES = coluna do CUSTO/DIA + 2 (F->H, Q->S, AA->AC...)."""
    return get_column_letter(column_index_from_string(col) + 2)


def _valor_conversao(r, chave: str) -> float:
    if chave == "thruplay":
        return r["thruplay"]
    if chave == "leads":
        a = r["acoes"]
        return a.get("onsite_conversion.lead_grouped", a.get("lead", 0.0))
    return r["acoes"].get(CONV_ACTION[chave], 0.0)


def _preenche_coluna(ws, col, datas, fim, valores, inteiro=False):
    """Escreve 'valores' (por data) nas celulas laranja da coluna; limpa futuro."""
    escritos = limpos = 0
    pulados = []
    for row in LINHAS:
        cell = ws[f"{col}{row}"]
        if not _eh_laranja(cell):
            pulados.append(cell.coordinate)
            continue
        dt = datas.get(row)
        if dt is None or dt > fim:
            if cell.value is not None:
                cell.value = None
                limpos += 1
        else:
            v = valores.get((dt.isoformat(), col), 0.0)
            cell.value = int(round(v)) if inteiro else round(v, 2)
            escritos += 1
    return escritos, limpos, pulados


def preencher(cli: ClienteOrc, hoje: date = None):
    hoje = hoje or date.today()
    token = carregar_token()
    ini, fim, aba = periodo_e_aba(hoje)

    registros = insights_diarios(cli.act_id, ini.isoformat(), fim.isoformat(), token)
    obj2bloco = {o: b for b in cli.blocos for o in b.objetivos}
    # bloco com objetivos vazios = coringa: recebe tudo que nao foi mapeado
    coringa = next((b for b in cli.blocos if not b.objetivos), None)
    gasto, conv, nao_mapeados = {}, {}, {}
    for r in registros:
        b = obj2bloco.get(r["objective"]) or coringa
        if not b:
            nao_mapeados[r["objective"]] = nao_mapeados.get(r["objective"], 0) + r["spend"]
            continue
        kg = (r["date"], b.coluna)
        gasto[kg] = gasto.get(kg, 0.0) + r["spend"]
        if b.conversao:
            kc = (r["date"], _col_conv(b.coluna))
            conv[kc] = conv.get(kc, 0.0) + _valor_conversao(r, b.conversao)

    origem = cli.planilha
    destino = origem.with_name(f"{origem.stem} (preenchido){origem.suffix}")
    shutil.copy(origem, destino)
    wb = load_workbook(destino)
    aba_real = _achar_aba(wb, aba)
    if aba_real is None:
        metas = [s for s in wb.sheetnames if "meta a" in s.lower()]
        sys.exit(f"Aba '{aba}' nao encontrada. Abas Meta: {metas}")
    aba = aba_real
    ws = wb[aba]

    datas = datas_das_linhas(ws, ini)
    escritos, limpos, pulados = 0, 0, []
    for b in cli.blocos:
        e, l, p = _preenche_coluna(ws, b.coluna, datas, fim, gasto)
        escritos += e; limpos += l; pulados += p
        if b.conversao:
            e, l, p = _preenche_coluna(ws, _col_conv(b.coluna), datas, fim, conv,
                                       inteiro=True)
            escritos += e; limpos += l; pulados += p
    wb.save(destino)
    return {
        "destino": destino, "aba": aba, "ini": ini, "fim": fim,
        "escritos": escritos, "limpos": limpos, "nao_mapeados": nao_mapeados,
        "pulados": pulados, "gasto": gasto, "conv": conv, "datas": datas,
    }


if __name__ == "__main__":
    chave = sys.argv[1] if len(sys.argv) > 1 else "todos"
    alvos = list(CLIENTES) if chave == "todos" else [chave]
    for k in alvos:
        try:
            res = preencher(CLIENTES[k])
            print(f"[{k:8}] {res['aba']}: {res['escritos']} preench / "
                  f"{res['limpos']} limpas -> {res['destino'].name}")
            if res["nao_mapeados"]:
                print(f"   AVISO sem bloco: {res['nao_mapeados']}")
        except Exception as e:
            print(f"[{k:8}] ERRO: {e}")
