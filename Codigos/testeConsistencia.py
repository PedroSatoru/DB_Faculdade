from supabase import create_client, Client
import pandas as pd

# Configuração do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Função para carregar os dados das tabelas para o pandas
def carregarTabelas(table):
    print(f"🔄 Carregando dados da tabela {table}...")
    data = supabase.table(table).select("*").execute().data
    return pd.DataFrame(data)

# Função para checar a consistência das FKs
def checarFK(df_FK, coluna_FK, df_PK, coluna_PK, relacao=""):
    # Caso as colunas não sejam encontradas
    if coluna_FK not in df_FK.columns or coluna_PK not in df_PK.columns:
        print(f"⚠️ Coluna não encontrada: {coluna_FK} ou {coluna_PK}")
        return
    # ~ inverte o resultado, ou seja, inconsistencias recebe os valores de df_FK[coluna_FK] que não estão em df_PK[coluna_PK]
    inconsistencias = df_FK[~df_FK[coluna_FK].isin(df_PK[coluna_PK])]
    # Caso inconsistencias possua algum valor
    if not inconsistencias.empty:
        print(f"❌ Chave estrangeira inconssistente entre {coluna_FK} e {coluna_PK} na relação {relacao}: {len(inconsistencias)} erros.")
    # Caso inconsistencias esteja vazio
    else:
        print(f"✅ Relação {relacao}: FK({coluna_FK}) -> PK({coluna_PK}) OK")

# Função para checar a consistência dos chefes de departamento
def checarChefeDep(df_departamento, df_professor):
    # Criando um novo df com dados das duas tabelas
    dfMisto = df_departamento.merge(df_professor, left_on='chefe_id', right_on='id', suffixes=('_dep', '_prof'))
    # Criando um novo df apenas com dados inconsistentes (professor não pertence ao departamento do qual ele é chefe)
    inconsistencias = dfMisto[dfMisto['id_dep'] != dfMisto['departamento_id']]
    # Caso haja inconsistencias
    if not inconsistencias.empty:
        print(f"❌ Chefes de departamento inconsistentes!")
        # Mostrando quais são as inconsistencias
        print(f"{len(inconsistencias)} Inconstistencias:")
        print(inconsistencias[['id_dep', 'nome_dep', 'nome_prof', 'departamento_id']])
    # Caso não haja inconsistencias
    else:
        print("✅ Chefes de departamento consistentes!")

# Função para checar a consistência dos Coordenadores de Curso
def checarCoordCurso(df_curso, df_professor):
    # Criando um novo df com dados das duas tabelas
    df = df_curso.merge(df_professor, left_on='coordenador_id', right_on='id', suffixes=('_curso', '_prof'))
    # Criando um novo df apenas com dados inconsistentes (professor não pertence ao departamento do cuso que coordena)
    inconsistencias = df[df['departamento_id_curso'] != df['departamento_id_prof']]
    # Caso haja inconsistencias
    if not inconsistencias.empty:
        print(f"❌ Coordenadores de curso fora do departamento!")
        # Mostrando quais são as inconsistencias
        print(f"{len(inconsistencias)} Inconstistencias:")
        print(inconsistencias[['nome_curso','departamento_id_curso', 'nome_prof', 'departamento_id_prof',]])
    # Caso não haja inconsistencias
    else:
        print("✅ Coordenadores de curso Consistentes!")

# Função para checar a consistência das disciplinas do tipo tcc
def checarTipoTCC(df_tcc, df_lecionada):
    # Criando um novo df apenas com dados inconsistentes (tcc que não seja do tipo "tcc" na tabela lecionada)
    df = df_tcc.merge(df_lecionada, left_on='lecionada_id', right_on='id', suffixes=('_tcc', '_lec'))
    # Criando um novo df apenas com dados inconsistentes (professor não pertence ao departamento do cuso que coordena)
    inconsistencias = df[df['tipo'] != 'tcc']
    # Caso haja inconsistencias
    if not inconsistencias.empty:
        print(f"❌ TCCs com disciplina não marcada como tipo 'tcc'")
        # Mostrando quais são as inconsistencias
        print(f"{len(inconsistencias)} Inconstistencias:")
        print(inconsistencias[['id_tcc','titulo', 'id_lec', 'tipo',]])
        # Caso não haja inconsistencias
    else:
        print("✅ TCCs marcados corretamente com tipo 'tcc' em lecionadas.")

# Função para checar se há colunas com dados nulos
def checarNulos(df, colunas, nome=""):
    # Para cada coluna na lista de verificação
    print()
    print(f"🔄 verificando nulos na tabela {nome}...")
    for col in colunas:
        # Se a coluna pertencer ao df (tabela) a ser verificado
        if col in df.columns:
            # Criando um novo df apenas com dados inconsistentes (colunas com dados nulos)
            inconsistencias = df[df[col].isnull()]
            # Caso haja inconsistencias
            if not inconsistencias.empty:
                print(f"❌ Valores nulos encontrados em {col}")
                # Mostrando quais são as inconsistencias
                print(f"{len(inconsistencias)} Inconstistencias:")
                print(inconsistencias)
            # Caso não haja inconsistencias
            else:
                print(f"✅ {col} não possui valores nulos.")

# Função para checar se há dados (que devem ser únicos) duplicados
def checarDuplicatas(df, colunas, nome):
    print()
    print(f"🔄 verificando duplicatas na tabela {nome}...")
    # Criando um novo df apenas com dados inconsistentes (dados duplicados)
    inconsistencias = df[df.duplicated(subset=colunas, keep=False)]
    # Caso haja inconsistencias
    if not inconsistencias.empty:
        print(f"❌ Duplicatas encontradas em {nome}")
        print(f"{len(inconsistencias)} Inconstistencias:")
        print(inconsistencias)
    # Caso não haja inconsistencias
    else:
        print(f"✅ Sem duplicatas em {nome}.")

# Função para checar a consistência de aprovação dos alunos
def checarAprovacao(df):
    # Criando um novo df somente com os alunos aprovados
    aprovados = df[df['status'] == 'aprovado']
    # Criando um novo df apenas com dados inconsistentes (alunos aprovados incorretamente)
    inconsistencias = aprovados[aprovados['nota'] < 5]
    # Caso haja inconsistencias
    if not inconsistencias.empty:
        print(f"❌ Alunos aprovados com nota insuficiente!")
        # Mostrando quais são as inconsistencias
        print(f"{len(inconsistencias)} Inconstistencias:")
        print(inconsistencias)
        # Caso não haja inconsistencias
    else:
        print("✅ Alunos aprovados corretamente")

# Função para checar a consistência de reprovação dos alunos
def checarReprovacao(df):
    # Criando um novo df somente com os alunos aprovados
    reprovados = df[df['status'] == 'reprovado']
    # Criando um novo df apenas com dados inconsistentes (alunos aprovados incorretamente)
    inconsistencias = reprovados[reprovados['nota'] >= 5]
    # Caso haja inconsistencias
    if not inconsistencias.empty:
        print(f"❌ Alunos reprovados com nota suficiente!")
        # Mostrando quais são as inconsistencias
        print(f"{len(inconsistencias)} Inconstistencias:")
        print(inconsistencias)
        # Caso não haja inconsistencias
    else:
        print("✅ Alunos reprovados corretamente")


# Carregar os dados das tabelas que serão utilizadas
print("----------------------------------------------")
print("Carregar Dados")
print("----------------------------------------------")
print()
df_aluno = carregarTabelas("aluno")
df_curso = carregarTabelas("curso")
df_professor = carregarTabelas("professor")
df_departamento = carregarTabelas("departamento")
df_disciplina = carregarTabelas("disciplina")
df_tcc = carregarTabelas("tcc")
df_lecionada = carregarTabelas("lecionada")
df_historico = carregarTabelas("historicoescolar")
print("✅ Tabelas carregadas!")
print()

# Testar consistência das chaves estrangeiras
print("----------------------------------------------")
print("Checar FK's")
print("----------------------------------------------")
print()
checarFK(df_aluno, "curso_id", df_curso, "id", "aluno/curso")
checarFK(df_professor, "departamento_id", df_departamento, "id", "professor/departamento")
checarFK(df_disciplina, "departamento_id", df_departamento, "id", "disciplina/departamento")
checarFK(df_tcc, "orientador_id", df_professor, "id", "tcc/orientador")
checarFK(df_lecionada, "professor_id", df_professor, "id", "lecionada/professor")
print()

# Testar consistência dos chefes de departamento
print("----------------------------------------------")
print("Checar Chefes de Departamento")
print("----------------------------------------------")
print()
checarChefeDep(df_departamento, df_professor)
print()

# Testar consistência dos coordenadores de curso
print("----------------------------------------------")
print("Checar Coordenadores de curso")
print("----------------------------------------------")
print()
checarCoordCurso(df_curso, df_professor)
print()

# Testar consistência de tipo dos tccs
print("----------------------------------------------")
print("Checar Tipo TCC's")
print("----------------------------------------------")
print()
checarTipoTCC(df_tcc, df_lecionada)
print()

# Testar se há dados nulos
print("----------------------------------------------")
print("Checar Nulos")
print("----------------------------------------------")
print()
checarNulos(df_tcc, ['id','titulo','orientador_id'], 'TCC')
checarNulos(df_aluno, list(df_aluno.columns), 'Aluno')
checarNulos(df_professor, list(df_professor.columns), 'Professor')
checarNulos(df_curso, list(df_curso.columns), 'Curso')
checarNulos(df_lecionada, ['id','disciplina_id','professor_id','semestre'], 'Lecionada')
checarNulos(df_disciplina, list(df_disciplina.columns), 'Disciplina')
checarNulos(df_departamento, ['id','nome'], 'Departamento')
print()

# Testar existência de duplicatas
print("----------------------------------------------")
print("Checar Duplicatas")
print("----------------------------------------------")
print()
checarDuplicatas(df_aluno, ['ra'], "aluno (ra)")
checarDuplicatas(df_disciplina, ['codigo'], "disciplina (codigo)")
checarDuplicatas(df_lecionada, ['disciplina_id', 'professor_id', 'semestre'], "lecionada (mesmo professor, disciplina e semestre)")
checarDuplicatas(df_tcc, ['titulo'], "tcc (titulo)")
print()

# Testar consistencia de aprovação/reprovação
print("----------------------------------------------")
print("Checar Consistencia de Aprovação/Reprovação")
print("----------------------------------------------")
print()
checarAprovacao(df_historico)
checarReprovacao(df_historico)
print()

