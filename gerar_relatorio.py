import os
import sys
from pathlib import Path

from app.clientes import Bloco, Campo, Cliente, detectar, grupos
from app.montagem import ItemRelatorio, montar_relatorio
from app.parser import extrair_cliente, parse_csv, tem_gasto


def _downloads() -> Path:
    """Pasta onde procurar o CSV exportado (sobrescreva com DOWNLOADS_DIR)."""
    return Path(os.environ.get("DOWNLOADS_DIR", Path.home() / "Downloads"))


DOWNLOADS = _downloads()
SAIDA = Path(__file__).parent / "relatorios"


def achar_csv() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    csvs = sorted(DOWNLOADS.glob("*.csv"), key=lambda p: p.stat().st_mtime)
    if not csvs:
        sys.exit(f"Nenhum CSV encontrado em {DOWNLOADS}. Passe o caminho como argumento.")
    print(f"Usando o CSV mais recente: {csvs[-1].name}")
    return csvs[-1]


def perguntar(rotulo: str, padrao: str = "") -> str:
    sufixo = f" [{padrao}]" if padrao else ""
    return input(f"{rotulo}{sufixo}: ").strip() or padrao


def confirmar(rotulo: str) -> bool:
    return input(f"{rotulo} [S/n]: ").strip().lower() not in ("n", "nao", "não")


def perguntar_varias(titulo: str) -> str:
    print(f"{titulo} (uma por linha, linha vazia para terminar):")
    linhas = []
    while True:
        linha = input("  ").strip()
        if not linha:
            break
        linhas.append(linha)
    return "\n".join(linhas)


def perguntar_intro() -> str:
    print("Resumo do topo (várias linhas; termine com uma linha só com '.'):")
    linhas = []
    while True:
        linha = input("  ")
        if linha.strip() == ".":
            break
        linhas.append(linha)
    return "\n".join(linhas)


def perguntar_numero(rotulo: str):
    while True:
        resp = input(f"{rotulo}: ").strip().replace(".", "").replace(",", ".")
        if not resp:
            return None
        try:
            return float(resp)
        except ValueError:
            print("  valor inválido, digite um número (ou Enter para pular)")


def bloco_interativo(indicador: str) -> Bloco:
    print(f"\nObjetivo desconhecido para '{indicador}'. Me ajude a rotular:")
    titulo = perguntar("Título da campanha", "Campanha")
    rotulo = perguntar("Rótulo do resultado (ex: Leads)")
    custo = perguntar("Rótulo do custo (vazio se não tiver)")
    campos = [Campo(rotulo, "resultados", "inteiro")]
    if custo:
        campos.append(Campo(custo, "custo_por_resultado", "moeda"))
    campos.append(Campo("Investimento", "investimento", "moeda"))
    return Bloco(titulo, campos, mostra_publico=True)


def escolher_cliente(detectado: Cliente, nome_detectado: str) -> tuple[Cliente, str]:
    from app.clientes import CLIENTES

    rotulo = detectado.nome_exibicao or nome_detectado
    print(f"\nCliente detectado: {rotulo}")
    print("Enter confirma, ou escolha: " + ", ".join(
        f"{i+1}) {c.nome_exibicao}" for i, c in enumerate(CLIENTES)
    ) + ", 0) genérico")
    esc = input("> ").strip()
    if esc == "0":
        return detectar("___inexistente___"), perguntar("Nome do cliente", nome_detectado)
    if esc.isdigit() and 1 <= int(esc) <= len(CLIENTES):
        cli = CLIENTES[int(esc) - 1]
        return cli, cli.nome_exibicao
    if detectado.nome_exibicao:
        return detectado, detectado.nome_exibicao
    return detectado, perguntar("Nome do cliente", nome_detectado)


def main():
    caminho = achar_csv()
    nome_detectado = extrair_cliente(caminho.name)
    cliente = detectar(caminho.name)
    cliente, nome = escolher_cliente(cliente, nome_detectado)
    intro = perguntar_intro() if cliente.intro_interativa else ""

    periodo, todas = parse_csv(caminho)
    ativas = [c for c in todas if tem_gasto(c)]
    ignoradas = len(todas) - len(ativas)
    if ignoradas:
        print(f"({ignoradas} campanhas sem gasto foram ignoradas)")

    itens = []
    for bloco, campanhas in grupos(cliente, ativas):
        if len(campanhas) == 1:
            print(f"\n--- Campanha: {campanhas[0].nome_csv}")
        else:
            print(f"\n--- {len(campanhas)} campanhas agregadas:")
            for c in campanhas:
                print(f"    • {c.nome_csv}")
        if not confirmar("Incluir no relatório?"):
            continue
        if bloco is None:
            bloco = bloco_interativo(campanhas[0].indicador)
        titulo = perguntar("Título da campanha", bloco.titulo) if cliente.titulo_por_campanha else ""
        criativo = perguntar_varias("Links do criativo") if bloco.mostra_criativo else ""
        publicos = perguntar_varias("Públicos") if bloco.mostra_publico else ""
        manuais = {}
        for campo in bloco.campos:
            if campo.chave.startswith("manual:"):
                manuais[campo.chave[len("manual:"):]] = perguntar_numero(campo.rotulo)
        itens.append(ItemRelatorio(campanhas, bloco, criativo, publicos, manuais, titulo))

    if not itens:
        sys.exit("Nenhuma campanha selecionada. Nada a gerar.")

    texto = montar_relatorio(cliente, nome, periodo, itens, intro)
    print("\n" + "=" * 50 + "\n")
    print(texto)

    SAIDA.mkdir(exist_ok=True)
    periodo_arq = periodo.replace("/", "").replace(" a ", "a").replace(" ", "")
    destino = SAIDA / f"Relatorio-{nome.replace(' ', '')}-{periodo_arq}.txt"
    destino.write_text(texto, encoding="utf-8")
    print(f"Salvo em: {destino}")


if __name__ == "__main__":
    main()
