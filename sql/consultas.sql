-- Perguntas da apuração respondidas em SQL.
-- Cada consulta começa com "-- [n] título"; o notebook lê este arquivo e roda uma por uma.
-- Só contam como aprovação confirmada os casamentos com status 'automatico'.

-- [1] Resumo: quantos alunos passaram e quantas aprovações eles somam
SELECT
    COUNT(DISTINCT id_aluno) AS alunos_aprovados,
    COUNT(*)                 AS aprovacoes
FROM aprovacoes
WHERE status = 'automatico';

-- [2] Participação do cursinho em cada lista
SELECT
    instituicao,
    COUNT(*)                                              AS aprovados_na_lista,
    SUM(status = 'automatico')                            AS alunos_do_cursinho,
    ROUND(100.0 * SUM(status = 'automatico') / COUNT(*), 1) AS pct_da_lista,
    SUM(status = 'revisao')                               AS pendentes_de_revisao
FROM aprovacoes
GROUP BY instituicao
ORDER BY pct_da_lista DESC;

-- [3] Aprovações de alunos por especialidade
SELECT
    especialidade,
    COUNT(*) AS aprovacoes
FROM aprovacoes
WHERE status = 'automatico'
GROUP BY especialidade
ORDER BY aprovacoes DESC;

-- [4] Taxa de aprovação por turma (aluno aprovado em pelo menos uma instituição)
SELECT
    a.turma,
    COUNT(DISTINCT a.id_aluno)                                    AS alunos,
    COUNT(DISTINCT ap.id_aluno)                                   AS aprovados,
    ROUND(100.0 * COUNT(DISTINCT ap.id_aluno) / COUNT(DISTINCT a.id_aluno), 1) AS taxa_aprovacao
FROM alunos AS a
LEFT JOIN aprovacoes AS ap
    ON ap.id_aluno = a.id_aluno
   AND ap.status = 'automatico'
GROUP BY a.turma
ORDER BY taxa_aprovacao DESC;

-- [5] Alunos aprovados em mais de uma instituição
SELECT
    a.nome,
    a.turma,
    COUNT(DISTINCT ap.instituicao)          AS instituicoes,
    GROUP_CONCAT(DISTINCT ap.instituicao)   AS onde
FROM aprovacoes AS ap
JOIN alunos AS a ON a.id_aluno = ap.id_aluno
WHERE ap.status = 'automatico'
GROUP BY a.id_aluno
HAVING COUNT(DISTINCT ap.instituicao) > 1
ORDER BY instituicoes DESC, a.nome;

-- [6] Melhor classificação de cada aluno (função de janela) e quem ficou entre os 3 primeiros
-- O HES fica de fora: ele não publica classificação, só a ordem em que os nomes aparecem.
WITH ranking AS (
    SELECT
        ap.id_aluno,
        ap.instituicao,
        ap.especialidade,
        ap.classificacao,
        ROW_NUMBER() OVER (PARTITION BY ap.id_aluno ORDER BY ap.classificacao) AS ordem
    FROM aprovacoes AS ap
    WHERE ap.status = 'automatico'
      AND ap.instituicao <> 'HES'
)
SELECT
    a.nome,
    r.instituicao,
    r.especialidade,
    r.classificacao
FROM ranking AS r
JOIN alunos AS a ON a.id_aluno = r.id_aluno
WHERE r.ordem = 1
  AND r.classificacao <= 3
ORDER BY r.classificacao, a.nome;

-- [7] Fila de revisão manual: o que falta conferir e por quê
SELECT
    instituicao,
    motivo,
    COUNT(*) AS casos
FROM aprovacoes
WHERE status = 'revisao'
GROUP BY instituicao, motivo
ORDER BY casos DESC;
