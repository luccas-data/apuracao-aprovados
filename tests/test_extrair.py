from pathlib import Path

import pandas as pd

from apuracao_aprovados.extrair import PADRAO_ENU, _limpar_celula, extrair_todas

RAIZ = Path(__file__).resolve().parents[1]


def test_nome_quebrado_em_duas_linhas_e_juntado():
    assert _limpar_celula("FABIO JOSE ANDRADE DA ASSUNCAO\nDE BARBOSA") == (
        "FABIO JOSE ANDRADE DA ASSUNCAO DE BARBOSA")


def test_celula_vazia():
    assert _limpar_celula(None) == ""


def test_linha_do_enu_e_reconhecida():
    encontrado = PADRAO_ENU.match("12º 470576 Fernanda Vitória Moura de Ramos Dias 94,69")
    assert encontrado.groups() == ("12", "470576", "Fernanda Vitória Moura de Ramos Dias", "94,69")


def test_rodape_do_enu_e_ignorado():
    assert PADRAO_ENU.match("Página 3 de 20") is None


def test_pdfs_extraidos_batem_com_o_gabarito():
    """Toda inscrição do gabarito sai dos PDFs, e nada além disso (lista de espera fica fora)."""
    extraidos = extrair_todas(RAIZ / "data" / "raw")
    gabarito = pd.read_csv(RAIZ / "data" / "gabarito" / "gabarito.csv")
    chaves = ["instituicao", "inscricao"]
    assert len(extraidos) == len(gabarito)
    assert (extraidos[chaves].sort_values(chaves).values
            == gabarito[chaves].sort_values(chaves).values).all()
