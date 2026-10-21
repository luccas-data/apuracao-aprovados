import pandas as pd

from apuracao_aprovados.banco import consultar, ler_consultas, salvar


def test_arquivo_de_consultas_tem_todas_as_perguntas():
    consultas = ler_consultas()
    assert len(consultas) == 7
    assert all("SELECT" in sql.upper() for sql in consultas.values())


def test_consultas_rodam_num_banco_pequeno(tmp_path):
    alunos = pd.DataFrame({"id_aluno": [1, 2], "nome": ["Ana", "Bia"],
                           "cpf": ["1", "2"], "turma": ["A", "B"]})
    aprovacoes = pd.DataFrame({
        "instituicao": ["IRP", "ENU"], "inscricao": [10, 20], "nome": ["ANA", "Ana"],
        "especialidade": ["PEDIATRIA", "PEDIATRIA"], "classificacao": [1, 5],
        "cpf_parcial": [None, None], "id_aluno": [1, 1], "score": [100.0, 100.0],
        "status": ["automatico", "automatico"], "motivo": ["", ""], "candidatos": ["1 (100)"] * 2,
    })
    banco = tmp_path / "teste.sqlite"
    salvar(banco, alunos, aprovacoes)
    for sql in ler_consultas().values():
        consultar(banco, sql)  # não pode dar erro
    resumo = consultar(banco, ler_consultas()["Resumo: quantos alunos passaram e quantas aprovações eles somam"])
    assert resumo.loc[0, "alunos_aprovados"] == 1
    assert resumo.loc[0, "aprovacoes"] == 2
