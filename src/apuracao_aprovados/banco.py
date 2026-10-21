"""Gravação do resultado em SQLite e leitura das consultas de sql/consultas.sql."""

import re
import sqlite3
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
PASTA_SQL = RAIZ / "sql"


def salvar(caminho_banco: Path, alunos: pd.DataFrame, aprovacoes: pd.DataFrame) -> None:
    """Recria o banco do zero a cada execução: a fonte da verdade são os PDFs e o CSV."""
    caminho_banco.unlink(missing_ok=True)
    conexao = sqlite3.connect(caminho_banco)
    conexao.executescript((PASTA_SQL / "schema.sql").read_text(encoding="utf-8"))
    alunos[["id_aluno", "nome", "cpf", "turma"]].to_sql(
        "alunos", conexao, if_exists="append", index=False)
    colunas = ["instituicao", "inscricao", "nome", "especialidade", "classificacao",
               "cpf_parcial", "id_aluno", "score", "status", "motivo", "candidatos"]
    aprovacoes[colunas].to_sql("aprovacoes", conexao, if_exists="append", index=False)
    conexao.commit()
    conexao.close()  # o "with sqlite3.connect" só faz commit, não fecha a conexão


def ler_consultas(caminho: Path = PASTA_SQL / "consultas.sql") -> dict[str, str]:
    """Separa o arquivo em {título: consulta} usando os marcadores '-- [n] título'."""
    texto = caminho.read_text(encoding="utf-8")
    partes = re.split(r"^-- \[\d+\] (.+)$", texto, flags=re.MULTILINE)
    # partes = [cabeçalho, título1, sql1, título2, sql2, ...]
    return {titulo.strip(): sql.strip() for titulo, sql in zip(partes[1::2], partes[2::2])}


def consultar(caminho_banco: Path, sql: str) -> pd.DataFrame:
    conexao = sqlite3.connect(caminho_banco)
    resultado = pd.read_sql_query(sql, conexao)
    conexao.close()
    return resultado
