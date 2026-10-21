"""Extração das listas de aprovados a partir dos PDFs.

Cada instituição publica o resultado num layout diferente, então cada uma tem a sua função.
Todas devolvem um DataFrame com as mesmas colunas:
instituicao, inscricao, nome, especialidade, classificacao, cpf_parcial.
"""

import re
from pathlib import Path

import pandas as pd
import pdfplumber

COLUNAS = ["instituicao", "inscricao", "nome", "especialidade", "classificacao", "cpf_parcial"]


def _limpar_celula(texto: str | None) -> str:
    """Junta nomes quebrados em duas linhas e remove espaços repetidos."""
    if texto is None:
        return ""
    return re.sub(r"\s+", " ", texto).strip()


def _linhas_das_tabelas(caminho: Path) -> list[list[str]]:
    """Lê as tabelas de todas as páginas e descarta o cabeçalho repetido em cada página."""
    linhas = []
    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages:
            for tabela in pagina.extract_tables():
                for linha in tabela:
                    linha = [_limpar_celula(c) for c in linha]
                    if linha[0] == "Inscrição":  # cabeçalho
                        continue
                    linhas.append(linha)
    return linhas


def extrair_irp(caminho: Path) -> pd.DataFrame:
    """IRP: tabela com Inscrição, Nome, Especialidade, Classificação."""
    linhas = _linhas_das_tabelas(caminho)
    df = pd.DataFrame(linhas, columns=["inscricao", "nome", "especialidade", "classificacao"])
    df["instituicao"] = "IRP"
    df["cpf_parcial"] = None
    return df[COLUNAS]


# Ex.: "12º 470576 Fernanda Vitória Moura de Ramos Dias 94,69"
PADRAO_ENU = re.compile(r"^(\d+)º\s+(\d{6})\s+(.+?)\s+(\d{1,3},\d{2})$")


def extrair_enu(caminho: Path) -> pd.DataFrame:
    """ENU: texto corrido. A especialidade aparece num título antes de cada bloco de nomes."""
    registros = []
    especialidade = None
    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages:
            for linha in pagina.extract_text().splitlines():
                linha = linha.strip()
                if linha.startswith("ESPECIALIDADE:"):
                    especialidade = linha.removeprefix("ESPECIALIDADE:").strip()
                    continue
                encontrado = PADRAO_ENU.match(linha)
                if encontrado:  # linhas que não casam são título e rodapé da página
                    classificacao, inscricao, nome, _nota = encontrado.groups()
                    registros.append({
                        "inscricao": inscricao,
                        "nome": nome,
                        "especialidade": especialidade,
                        "classificacao": classificacao,
                    })
    df = pd.DataFrame(registros)
    df["instituicao"] = "ENU"
    df["cpf_parcial"] = None
    return df[COLUNAS]


def extrair_hes(caminho: Path) -> pd.DataFrame:
    """HES: tabela com CPF mascarado e situação. Só os aprovados entram (não a lista de espera)."""
    linhas = _linhas_das_tabelas(caminho)
    df = pd.DataFrame(linhas, columns=["inscricao", "nome", "cpf", "especialidade", "situacao"])
    df = df[df["situacao"] == "Aprovado"].copy()
    # "***.123.456-**" -> "123456" (os 6 dígitos do meio, que dá para comparar com a base)
    df["cpf_parcial"] = df["cpf"].str.replace(r"\D", "", regex=True)
    # o HES não publica classificação: fica a ordem em que o nome aparece no programa
    df["classificacao"] = df.groupby("especialidade").cumcount() + 1
    df["instituicao"] = "HES"
    return df[COLUNAS]


def extrair_todas(pasta: Path) -> pd.DataFrame:
    """Junta as três listas num único DataFrame."""
    df = pd.concat([
        extrair_irp(pasta / "resultado_irp.pdf"),
        extrair_enu(pasta / "resultado_enu.pdf"),
        extrair_hes(pasta / "resultado_hes.pdf"),
    ], ignore_index=True)
    df["inscricao"] = df["inscricao"].astype(int)
    df["classificacao"] = df["classificacao"].astype(int)
    return df
