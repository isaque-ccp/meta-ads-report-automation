# Meta Ads Report Automation

Ferramentas em Python que automatizam duas rotinas semanais de uma agência de tráfego pago:

1. **Relatório semanal para WhatsApp**: lê o CSV exportado do Gerenciador de Anúncios da Meta e monta o texto do relatório de cada cliente, já formatado para colar no WhatsApp.
2. **Controle de orçamento**: busca o gasto e as conversões diárias pela Meta Marketing API e preenche a planilha de controle de orçamento do cliente.

Antes, os dois relatórios eram montados à mão a partir do Gerenciador de Anúncios. Agora cada um sai em poucos segundos.

> Os clientes e IDs de conta deste repositório são fictícios.

## 1. Relatório semanal (`gerar_relatorio.py`)

```
📈 Relatório semanal - Studio Aurora
Métricas (08/06 a 14/06):

Campanha de Visitas ao Perfil
Visitas ao perfil: 1.204
Cliques no link: 87
Novos seguidores: 152
Custo por seguidor: R$0,98
Investimento: R$149,84
--------------------------------------
```

- Identifica o cliente pelo nome do arquivo CSV (ex.: `CA---STUDIO-AURORA-Campanhas-....csv`).
- Ignora campanhas sem gasto no período.
- Cada cliente tem seu próprio modelo: cabeçalho, quais métricas mostrar em cada tipo de campanha, negrito do WhatsApp (`*...*`) e separadores.
- Clientes com `agregar=True` somam as campanhas de mesmo objetivo num único bloco. Métricas de razão (CPM, CTR, custo por resultado…) são **recalculadas a partir das somas**, nunca somadas.
- Modo interativo: pergunta, por campanha, se ela entra no relatório, o link do criativo, os públicos e os campos que não vêm no CSV.

### Arquitetura

| Módulo | Responsabilidade |
| --- | --- |
| `app/parser.py` | Lê o CSV da Meta, mapeia colunas lógicas (`investimento`, `alcance`, `thruplay`…) com busca tolerante a variações de nome |
| `app/clientes.py` | Modelos por cliente (`Cliente`, `Bloco`, `Campo`) e detecção do cliente pelo nome do arquivo |
| `app/montagem.py` | Agrega campanhas, deriva métricas e monta o texto final |
| `app/formatacao.py` | Formatação brasileira de moeda, inteiros e percentuais |
| `gerar_relatorio.py` | CLI interativa |

**Novo cliente** = uma nova instância de `Cliente` em `app/clientes.py`, adicionada à lista `CLIENTES`.

## 2. Controle de orçamento (`orcamento/`)

- `meta_api.py`: cliente mínimo da Graph API (só biblioteca padrão) que lê insights diários por campanha (`/act_<id>/insights`, `time_increment=1`), com paginação.
- `preencher_orcamento.py`: para cada cliente, agrupa as campanhas por objetivo em blocos da planilha, soma gasto e conversões por dia e grava **somente nas células de entrada** (identificadas pela cor). A planilha original não é alterada: o resultado vai para uma cópia `(preenchido)`.
- Blocos com `objetivos=set()` funcionam como coringa e recebem as campanhas não mapeadas.

## Como rodar

Requer Python 3.10+.

```bash
pip install -r requirements-dev.txt   # pytest (e openpyxl para o módulo de orçamento)

# relatório: usa o CSV mais recente da pasta Downloads, ou um caminho informado
python3 gerar_relatorio.py
python3 gerar_relatorio.py caminho/para/export.csv

# orçamento: token da Meta em ~/.meta_token (ou META_TOKEN_FILE)
python3 orcamento/preencher_orcamento.py festa
python3 orcamento/preencher_orcamento.py todos

# testes
python3 -m pytest
```

Variáveis de ambiente opcionais: `DOWNLOADS_DIR` (onde procurar o CSV), `PLANILHAS_DIR` (onde estão as planilhas) e `META_TOKEN_FILE` (arquivo do token).

## Testes

São 32 testes com `pytest`, cobrindo leitura do CSV, detecção de cliente, agregação de campanhas, métricas derivadas e formatação do texto.
