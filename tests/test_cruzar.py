import pandas as pd
import pytest

from apuracao_aprovados.cruzar import avaliar, classificar, cruzar


@pytest.fixture
def alunos():
    return pd.DataFrame({
        "id_aluno": [1, 2, 3, 4],
        "nome": ["ana clara souza", "Pedro Henrique Lima", "Maria Silva", "Maria Silva"],
        "cpf": ["11122233344", "22233344455", "33344455566", "44455566677"],
        "turma": ["A", "A", "B", "B"],
    })


def aprovado(nome, cpf_parcial=None):
    return pd.DataFrame({"instituicao": ["X"], "inscricao": [1], "nome": [nome],
                         "especialidade": ["PEDIATRIA"], "classificacao": [1],
                         "cpf_parcial": [cpf_parcial]})


def test_nome_igual_sem_acento_casa_automatico(alunos):
    resultado = cruzar(aprovado("ANA CLARA SOUZA"), alunos)
    assert resultado.loc[0, "status"] == "automatico"
    assert resultado.loc[0, "id_aluno"] == 1


def test_uma_letra_faltando_casa_automatico(alunos):
    resultado = cruzar(aprovado("Pedro Henriqe Lima"), alunos)  # nota 97
    assert resultado.loc[0, "status"] == "automatico"
    assert resultado.loc[0, "id_aluno"] == 2


def test_letras_trocadas_vao_para_revisao(alunos):
    resultado = cruzar(aprovado("Pedro Henrique Lmia"), alunos)  # nota ~94,7
    assert resultado.loc[0, "status"] == "revisao"
    assert resultado.loc[0, "id_aluno"] == 2
    assert resultado.loc[0, "candidatos"].startswith("2 (")


def test_cpf_vazio_do_pandas_nao_conta_como_cpf(alunos):
    # lido de um CSV, o "sem CPF" vira NaN, e não None
    resultado = cruzar(aprovado("ANA CLARA SOUZA", cpf_parcial=float("nan")), alunos)
    assert resultado.loc[0, "status"] == "automatico"
    assert resultado.loc[0, "id_aluno"] == 1


def test_nome_desconhecido_nao_e_aluno(alunos):
    resultado = cruzar(aprovado("Gustavo Rocha Andrade"), alunos)
    assert resultado.loc[0, "status"] == "nao_aluno"
    assert pd.isna(resultado.loc[0, "id_aluno"])


def test_homonimos_vao_para_revisao_com_os_dois_candidatos(alunos):
    resultado = cruzar(aprovado("MARIA SILVA"), alunos)
    assert resultado.loc[0, "status"] == "revisao"
    assert resultado.loc[0, "motivo"] == "mais de um aluno com esse nome"
    assert sorted(resultado.loc[0, "candidatos"].split(", ")) == ["3 (100)", "4 (100)"]


def test_cpf_parcial_desempata_homonimos(alunos):
    # cpf do aluno 4 = 444 555666 77 -> os 6 do meio são 555666
    resultado = cruzar(aprovado("MARIA SILVA", cpf_parcial="555666"), alunos)
    assert resultado.loc[0, "status"] == "automatico"
    assert resultado.loc[0, "id_aluno"] == 4


def test_cpf_diferente_descarta_mesmo_com_nome_igual(alunos):
    resultado = cruzar(aprovado("Pedro Henrique Lima", cpf_parcial="999999"), alunos)
    assert resultado.loc[0, "status"] == "nao_aluno"


def test_avaliar_conta_acertos_e_erros():
    resultado = pd.DataFrame({
        "instituicao": ["X"] * 4, "inscricao": [1, 2, 3, 4],
        "id_aluno": pd.array([10, 20, None, None], dtype="Int64"),
        "status": ["automatico", "automatico", "revisao", "nao_aluno"],
    })
    gabarito = pd.DataFrame({
        "instituicao": ["X"] * 4, "inscricao": [1, 2, 3, 4],
        "id_aluno": pd.array([10, None, 30, 40], dtype="Int64"),
    })
    metricas = avaliar(resultado, gabarito)
    assert metricas["acertos"] == 1
    assert metricas["precisao"] == 0.5  # 1 certo em 2 automáticos
    assert metricas["recall"] == 1 / 3  # 1 encontrado de 3 alunos aprovados
    assert metricas["perdidos"] == 1  # o da inscrição 4


@pytest.mark.parametrize("nota, status", [
    (95, "automatico"),  # exatamente no limiar automático: aceita
    (94.9, "revisao"),
    (85, "revisao"),  # exatamente no limiar de revisão: ainda revisa
    (84.9, "nao_aluno"),
])
def test_limiares_nas_fronteiras(alunos, nota, status):
    candidatos = [("ana clara souza", nota, 0)]
    resultado = classificar(candidatos, usou_cpf=False, alunos=alunos,
                            limiar_auto=95, limiar_revisao=85)
    assert resultado["status"] == status
