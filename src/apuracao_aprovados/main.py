"""Roda a apuração inteira: extrai os PDFs, cruza com os alunos e grava o resultado.

Uso: uv run python -m apuracao_aprovados.main
"""

import pandas as pd

from apuracao_aprovados.banco import RAIZ, salvar
from apuracao_aprovados.cruzar import cruzar
from apuracao_aprovados.extrair import extrair_todas
from apuracao_aprovados.normalizar import normalizar_especialidade

PASTA_RAW = RAIZ / "data" / "raw"
PASTA_PROCESSED = RAIZ / "data" / "processed"


def main() -> None:
    PASTA_PROCESSED.mkdir(parents=True, exist_ok=True)

    aprovados = extrair_todas(PASTA_RAW)
    aprovados["especialidade"] = aprovados["especialidade"].map(normalizar_especialidade)
    # CPF como texto: lido como número, perderia os zeros à esquerda
    alunos = pd.read_csv(PASTA_RAW / "alunos.csv", dtype={"cpf": str})

    resultado = cruzar(aprovados, alunos)

    resultado.to_csv(PASTA_PROCESSED / "resultado_cruzamento.csv", index=False)
    revisao = resultado[resultado["status"] == "revisao"].merge(
        alunos[["id_aluno", "nome", "turma"]].rename(columns={"nome": "nome_no_cadastro"}),
        on="id_aluno", how="left")
    revisao.to_csv(PASTA_PROCESSED / "revisao_manual.csv", index=False)
    salvar(PASTA_PROCESSED / "apuracao.sqlite", alunos, resultado)

    contagem = resultado["status"].value_counts()
    print(f"Nomes extraídos dos PDFs: {len(aprovados)}")
    print(f"  casados automaticamente: {contagem.get('automatico', 0)}")
    print(f"  para revisão manual:     {contagem.get('revisao', 0)}")
    print(f"  não são alunos:          {contagem.get('nao_aluno', 0)}")
    print(f"Alunos distintos aprovados: "
          f"{resultado.loc[resultado['status'] == 'automatico', 'id_aluno'].nunique()}")
    print(f"Arquivos gravados em {PASTA_PROCESSED.relative_to(RAIZ)}/")


if __name__ == "__main__":
    main()
