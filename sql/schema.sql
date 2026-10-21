-- Banco da apuração: a base de alunos e o resultado do cruzamento com as listas.

CREATE TABLE IF NOT EXISTS alunos (
    id_aluno INTEGER PRIMARY KEY,
    nome     TEXT NOT NULL,
    cpf      TEXT NOT NULL,
    turma    TEXT NOT NULL
);

-- Uma linha por nome publicado numa lista de aprovados.
-- id_aluno só é preenchido quando o cruzamento achou um aluno (automático ou em revisão).
CREATE TABLE IF NOT EXISTS aprovacoes (
    instituicao   TEXT NOT NULL,
    inscricao     INTEGER NOT NULL,
    nome          TEXT NOT NULL,
    especialidade TEXT NOT NULL,
    classificacao INTEGER NOT NULL,
    cpf_parcial   TEXT,
    id_aluno      INTEGER REFERENCES alunos (id_aluno),
    score         REAL,
    status        TEXT NOT NULL CHECK (status IN ('automatico', 'revisao', 'nao_aluno')),
    motivo        TEXT,
    candidatos    TEXT,  -- alunos parecidos, para quem for revisar: "id (nota)"
    PRIMARY KEY (instituicao, inscricao)
);
