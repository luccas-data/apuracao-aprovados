"""Padronização de nomes e especialidades para que possam ser comparados."""

import re

from unidecode import unidecode

# "de", "da", "dos"... aparecem em uns documentos e somem em outros
PARTICULAS = {"de", "da", "do", "das", "dos", "e"}


def normalizar_nome(nome: str) -> str:
    """'  Ana  Clara de SOUZA ' -> 'ana clara souza'.

    Tira acentos, deixa tudo minúsculo, remove pontuação, partículas e espaços extras.
    Iniciais abreviadas ("C.") viram só a letra ("c").
    """
    if not isinstance(nome, str):
        return ""
    nome = unidecode(nome).lower()
    nome = re.sub(r"[^a-z ]", " ", nome)
    palavras = [p for p in nome.split() if p not in PARTICULAS]
    return " ".join(palavras)


def normalizar_especialidade(especialidade: str) -> str:
    """'Ginecologia e Obstetrícia' -> 'GINECOLOGIA E OBSTETRICIA', o formato do IRP."""
    return re.sub(r"\s+", " ", unidecode(especialidade)).strip().upper()
