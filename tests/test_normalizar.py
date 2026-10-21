from apuracao_aprovados.normalizar import normalizar_especialidade, normalizar_nome


def test_remove_acentos_e_maiusculas():
    assert normalizar_nome("JOÃO ANTÔNIO") == "joao antonio"


def test_remove_particulas():
    assert normalizar_nome("Ana Clara de Souza dos Santos") == "ana clara souza santos"


def test_espacos_repetidos_e_nas_pontas():
    assert normalizar_nome("  Ana   Clara  Souza ") == "ana clara souza"


def test_inicial_abreviada_vira_letra():
    assert normalizar_nome("Ana C. Souza") == "ana c souza"


def test_valor_vazio_nao_quebra():
    assert normalizar_nome(None) == ""


def test_especialidade_com_e_sem_acento_ficam_iguais():
    assert (normalizar_especialidade("Ginecologia e Obstetrícia")
            == normalizar_especialidade("GINECOLOGIA E OBSTETRICIA"))
