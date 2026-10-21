"""Cruzamento das listas de aprovados com a base de alunos.

Os nomes nunca são iguais letra por letra (acento, abreviação, erro de digitação), então a
comparação é por similaridade (rapidfuzz). Cada aprovado recebe um de três status:

- automatico: casou com um aluno com segurança;
- revisao:    parecido o bastante para desconfiar, mas precisa de uma pessoa conferir;
- nao_aluno:  nenhum aluno parecido.
"""

import pandas as pd
from rapidfuzz import fuzz, process

from apuracao_aprovados.normalizar import normalizar_nome

LIMIAR_AUTOMATICO = 95  # a partir daqui o casamento é aceito sem revisão
LIMIAR_REVISAO = 85  # entre os dois limiares, vai para a revisão manual (ver notebook)


def tem_cpf(cpf_parcial) -> bool:
    """None e NaN (o 'vazio' do pandas) contam como sem CPF."""
    return isinstance(cpf_parcial, str) and cpf_parcial != ""


def classificar(candidatos: list[tuple], usou_cpf: bool, alunos: pd.DataFrame,
                limiar_auto: float, limiar_revisao: float) -> dict:
    """Decide o status de UM aprovado a partir dos alunos mais parecidos com ele.

    `candidatos` vem do rapidfuzz: lista de (nome, nota, índice) da maior para a menor nota.
    `usou_cpf` indica que os candidatos já foram filtrados pelo CPF parcial.
    """
    if not candidatos or candidatos[0][1] < limiar_revisao:
        motivo = "CPF de aluno, mas nome diferente" if candidatos and usou_cpf else "sem nome parecido"
        if usou_cpf and not candidatos:
            motivo = "nenhum aluno com esse CPF"
        return {"id_aluno": None, "score": candidatos[0][1] if candidatos else 0.0,
                "status": "nao_aluno", "motivo": motivo, "candidatos": None}

    _, melhor_score, melhor_indice = candidatos[0]
    resultado = {"id_aluno": alunos.loc[melhor_indice, "id_aluno"], "score": melhor_score,
                 # lista para quem for revisar: "id (nota)" dos alunos mais parecidos
                 "candidatos": ", ".join(f"{alunos.loc[i, 'id_aluno']} ({s:.0f})"
                                         for _, s, i in candidatos if s >= limiar_revisao)}

    # Com CPF parcial igual e nome parecido, não há dúvida de quem é.
    if usou_cpf:
        return {**resultado, "status": "automatico", "motivo": "CPF confere e nome parecido"}

    # Dois alunos diferentes com nota alta = homônimos; não dá para escolher sozinho.
    if len(candidatos) > 1 and candidatos[1][1] >= limiar_auto:
        return {**resultado, "status": "revisao", "motivo": "mais de um aluno com esse nome"}
    if melhor_score >= limiar_auto:
        return {**resultado, "status": "automatico", "motivo": "nome praticamente igual"}
    return {**resultado, "status": "revisao", "motivo": "nome parecido, mas não igual"}


def cruzar(aprovados: pd.DataFrame, alunos: pd.DataFrame,
           limiar_auto: float = LIMIAR_AUTOMATICO,
           limiar_revisao: float = LIMIAR_REVISAO) -> pd.DataFrame:
    """Devolve os aprovados com as colunas id_aluno, score, status, motivo e candidatos."""
    alunos = alunos.reset_index(drop=True)
    nomes_alunos = alunos["nome"].map(normalizar_nome)
    cpf_do_meio = alunos["cpf"].str[3:9]  # os 6 dígitos que o HES deixa à mostra

    linhas = []
    for _, aprovado in aprovados.iterrows():
        usou_cpf = tem_cpf(aprovado["cpf_parcial"])
        # Quando a lista publica parte do CPF, só compara o nome com os alunos daquele CPF.
        opcoes = nomes_alunos[cpf_do_meio == aprovado["cpf_parcial"]] if usou_cpf else nomes_alunos
        # token_sort_ratio ordena as palavras antes de comparar: a ordem dos sobrenomes não importa
        candidatos = process.extract(normalizar_nome(aprovado["nome"]), opcoes,
                                     scorer=fuzz.token_sort_ratio, limit=3)
        linhas.append(classificar(candidatos, usou_cpf, alunos, limiar_auto, limiar_revisao))

    resultado = pd.concat([aprovados.reset_index(drop=True), pd.DataFrame(linhas)], axis=1)
    resultado["id_aluno"] = resultado["id_aluno"].astype("Int64")
    return resultado


def avaliar(resultado: pd.DataFrame, gabarito: pd.DataFrame) -> dict:
    """Compara o cruzamento com a resposta certa (só existe porque os dados são sintéticos).

    As contas são por APROVAÇÃO (linha das listas): um aluno aprovado em 3 lugares conta 3 vezes.
    Precisão: dos casamentos automáticos, quantos ligaram o nome ao aluno certo.
    Recall:   das aprovações de alunos, quantas o automático encontrou.
    """
    df = resultado.merge(gabarito.rename(columns={"id_aluno": "id_certo"}),
                         on=["instituicao", "inscricao"], how="left")
    automaticos = df[df["status"] == "automatico"]
    # onde não há aluno no gabarito a comparação dá <NA>, e o sum() ignora: conta só os acertos
    acertos = (automaticos["id_aluno"] == automaticos["id_certo"]).sum()
    aprovacoes_de_alunos = df["id_certo"].notna().sum()
    return {
        "automaticos": len(automaticos),
        "acertos": int(acertos),
        "precisao": acertos / len(automaticos) if len(automaticos) else 0.0,
        "recall": acertos / aprovacoes_de_alunos if aprovacoes_de_alunos else 0.0,
        "em_revisao": int((df["status"] == "revisao").sum()),
        # aprovações de alunos que ficaram como "nao_aluno": essas ninguém vai olhar de novo
        "perdidos": int(((df["status"] == "nao_aluno") & df["id_certo"].notna()).sum()),
    }
