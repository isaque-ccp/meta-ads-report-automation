"""Cliente minimo da Meta Marketing API (somente leitura de gasto)."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://graph.facebook.com/v23.0/"
# arquivo com o token de acesso (fora do repositorio); sobrescreva com META_TOKEN_FILE
TOKEN_PADRAO = Path(os.environ.get("META_TOKEN_FILE", Path.home() / ".meta_token"))


def carregar_token(caminho: Path = TOKEN_PADRAO) -> str:
    return Path(caminho).read_text(encoding="utf-8-sig").strip()


def _get(path: str, token: str, **params):
    params["access_token"] = token
    url = API + path + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Meta API {e.code}: {e.read().decode()[:400]}")


def listar_contas(token: str):
    """[(nome, act_id)] de todas as contas que o token enxerga."""
    dados = _get("me/adaccounts", token, fields="name,account_id", limit=200)
    return [(d.get("name"), d.get("account_id")) for d in dados.get("data", [])]


def insights_diarios(act_id: str, since: str, until: str, token: str):
    """Por campanha/dia: {date, objective, spend, acoes(dict), thruplay}."""
    tr = json.dumps({"since": since, "until": until})
    saida, path = [], f"act_{act_id}/insights"
    params = dict(
        fields="spend,objective,actions,video_thruplay_watched_actions",
        level="campaign",
        time_increment="1",
        time_range=tr,
        limit="500",
    )
    while True:
        resp = _get(path, token, **params)
        for d in resp.get("data", []):
            acoes = {a["action_type"]: float(a["value"]) for a in d.get("actions", [])}
            tp = sum(float(a["value"])
                     for a in d.get("video_thruplay_watched_actions", []))
            saida.append(
                {
                    "date": d.get("date_start"),
                    "objective": d.get("objective", ""),
                    "spend": float(d.get("spend", 0) or 0),
                    "acoes": acoes,
                    "thruplay": tp,
                }
            )
        prox = resp.get("paging", {}).get("next")
        if not prox:
            return saida
        path, params = prox[len(API):].split("?", 1)[0], dict(
            urllib.parse.parse_qsl(prox.split("?", 1)[1])
        )


# alias retrocompativel (so gasto)
def gasto_diario(act_id, since, until, token):
    return [
        {"date": r["date"], "objective": r["objective"], "spend": r["spend"]}
        for r in insights_diarios(act_id, since, until, token)
    ]
