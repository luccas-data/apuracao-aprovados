"""Gera os dados sintéticos do projeto.

Cria três listas de aprovados em PDF (cada instituição com um layout diferente), a base de
alunos de um cursinho fictício e um gabarito com a resposta certa do cruzamento.

Tudo é inventado: nomes sorteados de listas de nomes comuns e CPFs gerados com dígito
verificador propositalmente inválido, para que nenhum número corresponda a uma pessoa real.

Uso: uv run python scripts/gerar_dados.py
"""

import random
from pathlib import Path

import pandas as pd
from fpdf import FPDF
from fpdf.fonts import FontFace
from unidecode import unidecode

SEMENTE = 42
RAIZ = Path(__file__).resolve().parents[1]
PASTA_PDFS = RAIZ / "data" / "raw"
PASTA_GABARITO = RAIZ / "data" / "gabarito"

N_ALUNOS = 2000
N_HOMONIMOS = 15  # pares de alunos com exatamente o mesmo nome
N_ARMADILHAS = 25  # não alunos nas listas com o mesmo nome de um aluno

PRENOMES_F = [
    "Ana", "Maria", "Juliana", "Mariana", "Camila", "Beatriz", "Larissa", "Fernanda", "Gabriela",
    "Letícia", "Amanda", "Bruna", "Carolina", "Isabela", "Natália", "Rafaela", "Patrícia",
    "Vitória", "Luíza", "Débora",
]
PRENOMES_M = [
    "Lucas", "Gabriel", "Pedro", "João", "Rafael", "Gustavo", "Felipe", "Matheus", "Bruno",
    "Thiago", "Rodrigo", "André", "Leonardo", "Vinícius", "Eduardo", "Caio", "Henrique",
    "Marcelo", "Daniel", "Fábio",
]
NOMES_MEIO_F = ["Clara", "Luísa", "Cristina", "Aparecida", "Helena", "Beatriz", "Eduarda",
                "Fernanda", "Carolina", "Vitória"]
NOMES_MEIO_M = ["Henrique", "Augusto", "Eduardo", "Antônio", "Felipe", "Gabriel", "Luiz",
                "José", "Paulo", "Vinícius"]
SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima",
    "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes", "Soares",
    "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade", "Moreira",
    "Nunes", "Marques", "Machado", "Mendes", "Freitas", "Cardoso", "Ramos", "Gonçalves",
    "Santana", "Teixeira", "Araújo", "Monteiro", "Moura", "Cavalcanti", "Batista", "Conceição",
    "Assunção", "Magalhães", "Brandão", "Guimarães",
]
# partícula usada antes de cada sobrenome ("dos Santos", "da Silva"); o resto usa "de"
PARTICULA_DO_SOBRENOME = {"Santos": "dos", "Silva": "da", "Costa": "da", "Rocha": "da",
                          "Conceição": "da", "Assunção": "da"}
PARTICULAS = ["de", "da", "dos", "do"]

ESPECIALIDADES = [
    "Clínica Médica", "Cirurgia Geral", "Pediatria", "Ginecologia e Obstetrícia",
    "Medicina de Família e Comunidade", "Ortopedia e Traumatologia", "Psiquiatria",
    "Anestesiologia", "Radiologia", "Dermatologia", "Oftalmologia",
]
TURMAS = ["Extensivo 2026", "Intensivo 2026", "R+ Clínica 2026", "Extensivo 2025"]

# Instituições fictícias: (sigla, nome, total de aprovados, chance de um aluno ser aprovado nela)
INSTITUICOES = [
    ("IRP", "Instituto de Residência Paulista", 1200, 0.20),
    ("ENU", "Exame Nacional Unificado", 1500, 0.25),
    ("HES", "Hospital Escola do Sul", 800, 0.10),
]


def sortear_nome(rng: random.Random) -> str:
    """Monta um nome completo 'oficial', com acentos, como apareceria num documento."""
    if rng.random() < 0.5:
        prenomes, nomes_meio = PRENOMES_F, NOMES_MEIO_F
    else:
        prenomes, nomes_meio = PRENOMES_M, NOMES_MEIO_M
    partes = [rng.choice(prenomes)]
    if rng.random() < 0.6:
        partes.append(rng.choice(nomes_meio))
    n_sobrenomes = rng.choice([1, 2, 2, 3])
    for i, sobrenome in enumerate(rng.sample(SOBRENOMES, n_sobrenomes)):
        if i > 0 and rng.random() < 0.25:
            partes.append(PARTICULA_DO_SOBRENOME.get(sobrenome, "de"))
        partes.append(sobrenome)
    return " ".join(partes)


def gerar_cpf(rng: random.Random) -> str:
    """CPF de 11 dígitos com o primeiro dígito verificador errado de propósito."""
    base = [rng.randint(0, 9) for _ in range(9)]
    soma = sum(d * p for d, p in zip(base, range(10, 1, -1)))
    dv1_correto = 0 if soma % 11 < 2 else 11 - soma % 11
    dv1 = (dv1_correto + 1) % 10  # nunca bate com o dígito válido
    dv2 = rng.randint(0, 9)
    return "".join(map(str, base + [dv1, dv2]))


def sujar_nome(nome: str, rng: random.Random) -> str:
    """Simula o nome como o aluno digitou no cadastro: sem acento, abreviado, com erro..."""
    partes = nome.split()
    if len(partes) > 3 and rng.random() < 0.10:  # abrevia um nome do meio: "Ana C. Souza"
        i = rng.randint(1, len(partes) - 2)
        if partes[i] not in PARTICULAS:
            partes[i] = partes[i][0] + "."
    if len(partes) > 3 and rng.random() < 0.10:  # esquece um sobrenome do meio
        i = rng.randint(1, len(partes) - 2)
        partes.pop(i)
    novo = " ".join(partes)
    if rng.random() < 0.08:  # erro de digitação: troca, apaga ou duplica uma letra
        i = rng.randint(1, len(novo) - 2)
        tipo = rng.choice(["troca", "apaga", "duplica"])
        if tipo == "troca":
            novo = novo[:i] + novo[i + 1] + novo[i] + novo[i + 2:]
        elif tipo == "apaga":
            novo = novo[:i] + novo[i + 1:]
        else:
            novo = novo[:i] + novo[i] + novo[i:]
    if rng.random() < 0.40:
        novo = unidecode(novo)
    if rng.random() < 0.20:
        novo = novo.lower()
    if rng.random() < 0.10:
        novo = novo.replace(" ", "  ", 1) + " "
    return novo


def gerar_alunos(rng: random.Random) -> pd.DataFrame:
    nomes = set()
    while len(nomes) < N_ALUNOS - N_HOMONIMOS:
        nomes.add(sortear_nome(rng))
    nomes = sorted(nomes)
    # homônimos: alguns nomes aparecem duas vezes (pessoas diferentes, CPFs diferentes)
    nomes += rng.sample(nomes, N_HOMONIMOS)
    rng.shuffle(nomes)

    linhas = []
    for i, nome in enumerate(nomes, start=1):
        linhas.append({
            "id_aluno": i,
            "nome_oficial": nome,  # só vai para o gabarito, não para a base
            "nome": sujar_nome(nome, rng),
            "cpf": gerar_cpf(rng),
            "turma": rng.choice(TURMAS),
        })
    return pd.DataFrame(linhas)


def gerar_lista(sigla: str, total: int, chance: float, alunos: pd.DataFrame,
                rng: random.Random) -> pd.DataFrame:
    """Lista de aprovados de uma instituição: alguns alunos do cursinho + outros candidatos."""
    aprovados_alunos = alunos[[rng.random() < chance for _ in range(len(alunos))]]
    linhas = []
    for _, aluno in aprovados_alunos.iterrows():
        linhas.append({"nome": aluno["nome_oficial"], "cpf": aluno["cpf"],
                       "id_aluno": aluno["id_aluno"]})

    nomes_alunos = set(alunos["nome_oficial"])
    # armadilhas: candidatos de fora com nome igual ao de algum aluno
    for nome in rng.sample(sorted(nomes_alunos), N_ARMADILHAS):
        linhas.append({"nome": nome, "cpf": gerar_cpf(rng), "id_aluno": None})
    while len(linhas) < total:
        nome = sortear_nome(rng)
        if nome not in nomes_alunos:
            linhas.append({"nome": nome, "cpf": gerar_cpf(rng), "id_aluno": None})

    lista = pd.DataFrame(linhas)
    lista["especialidade"] = [rng.choice(ESPECIALIDADES) for _ in range(len(lista))]
    lista["nota"] = [round(rng.uniform(60, 95), 2) for _ in range(len(lista))]
    lista = lista.sample(frac=1, random_state=rng.randint(0, 10_000)).reset_index(drop=True)
    lista["inscricao"] = rng.sample(range(100_000, 999_999), len(lista))
    lista["instituicao"] = sigla
    # classificação dentro de cada especialidade, pela nota
    lista = lista.sort_values(["especialidade", "nota"], ascending=[True, False])
    lista["classificacao"] = lista.groupby("especialidade").cumcount() + 1
    return lista.reset_index(drop=True)


class PDFResultado(FPDF):
    """PDF com cabeçalho e rodapé repetidos em todas as páginas, como os editais reais."""

    def __init__(self, titulo: str):
        super().__init__()
        self.titulo = titulo
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 8, self.titulo, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.cell(0, 8, f"Página {self.page_no()} de {{nb}}", align="C")


def pdf_irp(lista: pd.DataFrame, caminho: Path) -> None:
    """IRP: tabela única, nomes em maiúsculas e sem acento."""
    pdf = PDFResultado("INSTITUTO DE RESIDENCIA PAULISTA - RESULTADO FINAL 2027")
    pdf.add_page()
    pdf.set_font("Helvetica", size=8)
    with pdf.table(col_widths=(20, 85, 60, 25), headings_style=FontFace(emphasis="BOLD")) as tabela:
        tabela.row(["Inscrição", "Nome", "Especialidade", "Classif."])
        for _, r in lista.iterrows():
            tabela.row([str(r["inscricao"]), unidecode(r["nome"]).upper(),
                        unidecode(r["especialidade"]).upper(), str(r["classificacao"])])
    pdf.output(caminho)


def pdf_enu(lista: pd.DataFrame, caminho: Path) -> None:
    """ENU: texto corrido, agrupado por especialidade, com nota em formato brasileiro."""
    pdf = PDFResultado("Exame Nacional Unificado - Resultado Final - Residência Médica 2027")
    pdf.add_page()
    for especialidade, grupo in lista.groupby("especialidade"):
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 8, f"ESPECIALIDADE: {especialidade.upper()}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=9)
        for _, r in grupo.iterrows():
            nota = f"{r['nota']:.2f}".replace(".", ",")
            pdf.cell(12, 5, f"{r['classificacao']}º")
            pdf.cell(20, 5, f"{r['inscricao']}")
            pdf.cell(130, 5, r["nome"])
            pdf.cell(0, 5, nota, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
    pdf.output(caminho)


def pdf_hes(lista: pd.DataFrame, caminho: Path, rng: random.Random) -> pd.DataFrame:
    """HES: tabela com CPF mascarado e situação (aprovado ou lista de espera)."""
    lista = lista.copy()
    lista["situacao"] = ["Aprovado" if rng.random() < 0.7 else "Lista de espera"
                         for _ in range(len(lista))]
    pdf = PDFResultado("HOSPITAL ESCOLA DO SUL - PROCESSO SELETIVO RESIDÊNCIA MÉDICA 2027")
    pdf.add_page()
    pdf.set_font("Helvetica", size=8)
    with pdf.table(col_widths=(18, 70, 30, 50, 25),
                   headings_style=FontFace(emphasis="BOLD")) as tabela:
        tabela.row(["Inscrição", "Candidato", "CPF", "Programa", "Situação"])
        for _, r in lista.iterrows():
            cpf = r["cpf"]
            cpf_mascarado = f"***.{cpf[3:6]}.{cpf[6:9]}-**"
            tabela.row([str(r["inscricao"]), r["nome"].upper(), cpf_mascarado,
                        r["especialidade"], r["situacao"]])
    pdf.output(caminho)
    return lista


def main() -> None:
    rng = random.Random(SEMENTE)
    PASTA_PDFS.mkdir(parents=True, exist_ok=True)
    PASTA_GABARITO.mkdir(parents=True, exist_ok=True)

    alunos = gerar_alunos(rng)
    alunos[["id_aluno", "nome", "cpf", "turma"]].to_csv(
        PASTA_PDFS / "alunos.csv", index=False)

    gabaritos = []
    for sigla, _, total, chance in INSTITUICOES:
        lista = gerar_lista(sigla, total, chance, alunos, rng)
        caminho = PASTA_PDFS / f"resultado_{sigla.lower()}.pdf"
        if sigla == "IRP":
            pdf_irp(lista, caminho)
        elif sigla == "ENU":
            pdf_enu(lista, caminho)
        else:
            lista = pdf_hes(lista, caminho, rng)
            lista = lista[lista["situacao"] == "Aprovado"]  # lista de espera não conta
        gabaritos.append(lista[["instituicao", "inscricao", "id_aluno"]])
        print(f"{sigla}: {len(lista)} aprovados, {lista['id_aluno'].notna().sum()} alunos")

    gabarito = pd.concat(gabaritos)
    gabarito["id_aluno"] = gabarito["id_aluno"].astype("Int64")
    gabarito.to_csv(PASTA_GABARITO / "gabarito.csv", index=False)
    print(f"{len(alunos)} alunos na base; gabarito com {len(gabarito)} linhas")


if __name__ == "__main__":
    main()
