import os
from dotenv import load_dotenv
load_dotenv('chaves.env')
from supabase import create_client, Client
import random
from faker import Faker

# Gerar nomes e frases em português
fake = Faker('pt_BR')
fake.seed_instance(42)  

# Configuração do Supabase (SUA URL E KEY AQUI)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================================================
# Função gerar_ra() melhorada para evitar colisões
# ================================================
def gerar_ra(existing_ra=None):
    """Gera RA único no formato AA.MM.NN-C (10 caracteres)"""
    while True:
        ano = str(random.randint(15, 25)).zfill(2)   # Ano entre 15 (2015) e 25 (2025)
        mes = random.choice(['01', '08'])            # Janeiro ou Agosto
        numero = f"{random.randint(10, 99):02}"     # 2 dígitos (10-99)
        curso_id = random.randint(1, 5)              # ID do curso (1-5)
        novo_ra = f"{ano}.{mes}.{numero}-{curso_id}" # Total: 10 caracteres
        
        # Verifica unicidade
        if existing_ra is None or novo_ra not in existing_ra:
            return novo_ra


def obter_disciplinas_por_curso(curso_id):
    """Obtém disciplinas da matriz curricular do curso"""
    response = supabase.table("curso_disciplina")\
                    .select("disciplina_id")\
                    .eq("curso_id", curso_id)\
                    .execute()
    return [d['disciplina_id'] for d in response.data]

# ================================================
# Funções para criação de entidades
# ================================================

def criar_alunos(quantidade=20):
    """Cria alunos com RAs únicos"""
    try:
        alunos = []
        ras_gerados = set()
        
        # Obter RAs existentes no banco
        existing = supabase.table("aluno").select("ra").execute()
        ras_existentes = {a['ra'] for a in existing.data}
        
        for _ in range(quantidade):
            tentativas = 0
            while True:
                ra = gerar_ra(ras_gerados.union(ras_existentes))
                if ra not in ras_gerados:
                    ras_gerados.add(ra)
                    break
                tentativas += 1
                # Prevenir loop infinito
                if tentativas > 100:
                    raise Exception("Não foi possível gerar RA único após 100 tentativas")
                    
            curso_id = int(ra.split('-')[-1])
            
            alunos.append({
                "ra": ra,
                "nome": fake.name()[:100],  # Limite de 100 caracteres
                "curso_id": curso_id
            })
        
        # Inserção em lotes sem duplicatas
        if alunos:
            supabase.table("aluno").insert(alunos).execute()
            print(f"✓ {len(alunos)} alunos criados")
        
        return alunos
    
    except Exception as e:
        print(f"✗ Erro ao criar alunos: {str(e)}")
        return []


def criar_turma(disciplina_id, semestre, tipo='regular'):
    """Cria ou obtém turma existente com tipo específico"""
    try:
        # Verificar se a disciplina é um TCC
        if disciplina_id in [9, 10]:  # IDs das disciplinas de TCC
            tipo = 'tcc'

        # Verificar se turma já existe
        existing = supabase.table("lecionada")\
                        .select("*")\
                        .eq("disciplina_id", disciplina_id)\
                        .eq("semestre", semestre)\
                        .eq("tipo", tipo)\
                        .execute()
        
        if existing.data:
            return existing.data[0]
        
        # Obter professor adequado
        if tipo == 'tcc':
            # Para TCC, professores podem ser de qualquer departamento
            professores = supabase.table("professor").select("id").execute().data
        else:
            # Para turmas regulares, professores do departamento da disciplina
            departamento_id = supabase.table("disciplina")\
                                    .select("departamento_id")\
                                    .eq("id", disciplina_id)\
                                    .execute().data[0]['departamento_id']
            
            professores = supabase.table("professor")\
                               .select("id")\
                               .eq("departamento_id", departamento_id)\
                               .execute().data
        
        if not professores:
            raise Exception("Nenhum professor disponível")
        
        # Criar nova turma
        nova_turma = supabase.table("lecionada").insert({
            "disciplina_id": disciplina_id,
            "professor_id": random.choice(professores)['id'],
            "semestre": semestre,
            "tipo": tipo
        }).execute()
        
        return nova_turma.data[0]
    
    except Exception as e:
        print(f"✗ Erro ao criar turma {tipo}: {str(e)}")
        return None

# ================================================
# Geração de histórico acadêmico e TCC
# ================================================
def gerar_historico_aluno(aluno_ra, curso_id):
    """Gera histórico com 3 disciplinas regulares + TCC"""
    try:
        historico = []
        ano_base = 2000 + int(aluno_ra[:2])
        disciplinas_curso = obter_disciplinas_por_curso(curso_id)
        
        # Obter o id da disciplina de TCC para filtragem
        tcc_data = supabase.table("disciplina")\
                           .select("id")\
                           .eq("codigo", "TCC001")\
                           .execute().data
        if not tcc_data:
            raise Exception("Disciplina de TCC não encontrada")
        tcc_disciplina_id = tcc_data[0]['id']
        
        # Filtrar para obter apenas disciplinas regulares (excluindo o TCC)
        disciplinas_regulares_ids = [d for d in disciplinas_curso if d != tcc_disciplina_id]
        if not disciplinas_regulares_ids:
            raise Exception("Nenhuma disciplina regular encontrada para o curso")
        
        # Seleciona 3 disciplinas regulares
        disciplinas_regulares = random.sample(disciplinas_regulares_ids, min(3, len(disciplinas_regulares_ids)))
        disciplinas_pendentes = disciplinas_regulares.copy()
        disciplinas_reprovadas = []
        semestre_atual = 1
        max_semestres = 6  # Limite de 3 anos (6 semestres)
        tcc_realizado = False

        while semestre_atual <= max_semestres and (disciplinas_pendentes or disciplinas_reprovadas or not tcc_realizado):
            ano = ano_base + ((semestre_atual - 1) // 2)
            periodo = 1 if semestre_atual % 2 == 1 else 2
            semestre = f"{ano}.{periodo}"
            
            # Verifica se pode fazer o TCC (após aprovar todas as disciplinas regulares)
            pode_fazer_tcc = not disciplinas_pendentes and not disciplinas_reprovadas

            if pode_fazer_tcc and not tcc_realizado:
                # Criar e registrar o TCC
                tcc_info = criar_tcc(aluno_ra, semestre)
                if not tcc_info:
                    raise Exception("Falha ao criar TCC")
                
                # 30% de chance de reprovação no TCC
                if random.random() < 0.3:
                    nota = round(random.uniform(0, 4.9), 1)
                    status = "reprovado"
                    max_semestres += 1  # Semestre extra para refazer o TCC
                else:
                    nota = round(random.uniform(5, 10), 1)
                    status = "aprovado"
                    tcc_realizado = True
                
                historico.append({
                    "aluno_ra": aluno_ra,
                    "semestre": semestre,
                    "nota": nota,
                    "status": status,
                    "tcc_id": tcc_info['tcc_id'],
                    "lecionada_id": tcc_info['lecionada_id'],
                    "tipo": "TCC"
                })
                semestre_atual += 1
                continue

            # Lógica para disciplinas regulares
            disciplina_id = None
            if disciplinas_reprovadas:
                disciplina_id = disciplinas_reprovadas.pop(0)
            elif disciplinas_pendentes:
                disciplina_id = disciplinas_pendentes.pop(0)
            else:
                semestre_atual += 1
                continue
            
            turma = criar_turma(disciplina_id, semestre)
            if not turma:
                raise Exception(f"Turma não criada para disciplina {disciplina_id}")
            
            # 10% de chance de reprovação em disciplinas regulares
            if random.random() < 0.1:
                nota = round(random.uniform(0, 4.9), 1)
                status = "reprovado"
                disciplinas_reprovadas.append(disciplina_id)
            else:
                nota = round(random.uniform(5, 10), 1)
                status = "aprovado"
            
            historico.append({
                "aluno_ra": aluno_ra,
                "semestre": semestre,
                "nota": nota,
                "status": status,
                "lecionada_id": turma['id'],
                "disciplina_id": disciplina_id,
                "tipo": "Disciplina"
            })
            semestre_atual += 1

        # Insere histórico no banco
        for registro in historico:
            try:
                data = {
                    "aluno_ra": registro['aluno_ra'],
                    "lecionada_id": registro.get('lecionada_id'),
                    "nota": registro['nota'],
                    "status": registro['status'],
                    "semestre": registro['semestre']
                }
                if 'tcc_id' in registro:
                    data["tcc_id"] = registro['tcc_id']
                supabase.table("historicoescolar").insert(data).execute()
            except Exception as e:
                print(f"✗ Falha ao inserir registro de {aluno_ra}: {str(e)}")
                continue

        print(f"✓ Histórico de {aluno_ra} criado: {len(historico)} registros")
        return historico

    except Exception as e:
        print(f"✗ Erro fatal no histórico de {aluno_ra}: {str(e)}")
        return []

def criar_tcc(aluno_ra, semestre):
    """Cria registro único de TCC com turma específica"""
    try:
        # Obter disciplina de TCC
        disciplina_tcc = supabase.table("disciplina")\
                               .select("id")\
                               .eq("codigo", "TCC001")\
                               .execute().data
        
        if not disciplina_tcc:
            raise Exception("Disciplina de TCC não encontrada")
        
        disciplina_id = disciplina_tcc[0]['id']
        
        # Criar turma de TCC
        turma_tcc = criar_turma(disciplina_id, semestre, tipo='tcc')
        if not turma_tcc:
            raise Exception("Falha ao criar turma de TCC")
        
        # Criar registro do TCC (único por aluno)
        tcc = supabase.table("tcc").insert({
            "titulo": f"TCC - {fake.catch_phrase()[:150]}",
            "orientador_id": turma_tcc['professor_id'],
            "semestre": semestre,
            "lecionada_id": turma_tcc['id']
        }).execute().data[0]
        
        # Vincular aluno
        supabase.table("tcc_aluno").insert({
            "tcc_id": tcc['id'],
            "aluno_ra": aluno_ra
        }).execute()
        
        return {
            'tcc_id': tcc['id'],
            'lecionada_id': turma_tcc['id']
        }
        
    except Exception as e:
        print(f"✗ Erro ao criar TCC: {str(e)}")
        return None
# ================================================
# Execução principal
# ================================================

def main():
    try:
        # Criar alunos
        alunos = criar_alunos(1)
        
        # Gerar histórico para cada aluno
        for aluno in alunos:
            gerar_historico_aluno(aluno['ra'], aluno['curso_id'])
        
        print("✅ Base de dados populada com sucesso!")
        print("Alunos criados:", len(alunos))
        
    except Exception as e:
        print(f"❌ Erro crítico: {str(e)}")

if __name__ == "__main__":
    main()
