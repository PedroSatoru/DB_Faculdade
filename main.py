import os
from supabase import create_client, Client
import random
from faker import Faker

fake = Faker('pt_BR')

# Configuração do Supabase (SUA URL E KEY AQUI)
SUPABASE_URL = "https://brehfssbmphoqgmmckrr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJyZWhmc3NibXBob3FnbW1ja3JyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI5NDIxMzgsImV4cCI6MjA1ODUxODEzOH0.g7EPcTSKw5froygzwKFKGh7ktYaEcBVFotK5MJMp0Qo"
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
    """Gera histórico acadêmico com tratamento completo de reprovações e semestres adicionais"""
    try:
        historico = []
        ano_base = 2000 + int(aluno_ra[:2])  # Extrai ano do RA
        disciplinas_curso = obter_disciplinas_por_curso(curso_id)
        disciplinas_pendentes = disciplinas_curso.copy()
        disciplinas_cursadas = []
        disciplinas_reprovadas = []
        semestre_atual = 1
        max_semestres = 8  # Limite máximo de semestres (4 anos)
        
        while semestre_atual <= max_semestres:
            # Calcula ano e período
            ano = ano_base + ((semestre_atual - 1) // 2)
            periodo = 1 if semestre_atual % 2 == 1 else 2
            semestre = f"{ano}.{periodo}"
            
            try:
                # Verifica se pode fazer TCC (último semestre regular ou adicional)
                pode_fazer_tcc = (not disciplinas_pendentes and not disciplinas_reprovadas)
                
                # Se é o 4º semestre ou posterior E pode fazer TCC
                if semestre_atual >= 4 and pode_fazer_tcc:
                    # Verifica se já tem TCC no histórico
                    tem_tcc = any(h.get('tcc_id') for h in historico)
                    
                    if not tem_tcc or any(h.get('tcc_id') and h['status'] == 'reprovado' for h in historico):
                        # Cria ou repete TCC
                        tcc_data = criar_tcc(aluno_ra, semestre)
                        if not tcc_data:
                            raise Exception("Falha ao criar TCC")
                        
                        # Gera nota para TCC (mais rigoroso)
                        nota = round(random.triangular(4, 10, 6.5), 1) if tem_tcc else round(random.triangular(5, 10, 7), 1)
                        status = "aprovado" if nota >= 5 else "reprovado"
                        
                        historico.append({
                            "aluno_ra": aluno_ra,
                            "semestre": semestre,
                            "nota": nota,
                            "status": status,
                            "tcc_id": tcc_data['tcc_id'],
                            "lecionada_id": tcc_data['lecionada_id']
                        })
                        
                        if status == "reprovado":
                            # Remove TCC aprovado anterior se existir (para recálculo)
                            historico = [h for h in historico if not (h.get('tcc_id') and h['status'] == 'aprovado')]
                            
                        semestre_atual += 1
                        continue
                
                # Se não pode fazer TCC ou precisa repetir disciplina
                disciplina_id = None
                
                # 1. Prioriza disciplinas reprovadas
                if disciplinas_reprovadas:
                    disciplina_id = disciplinas_reprovadas.pop(0)
                # 2. Disciplinas pendentes
                elif disciplinas_pendentes:
                    disciplina_id = random.choice(disciplinas_pendentes)
                    disciplinas_pendentes.remove(disciplina_id)
                # 3. Todas disciplinas cursadas, mas TCC não liberado
                else:
                    # Pode acontecer se reprovou em TCC mas não tem disciplinas pendentes
                    semestre_atual += 1
                    continue
                
                # Cria turma para a disciplina
                turma = criar_turma(disciplina_id, semestre)
                if not turma:
                    raise Exception(f"Turma não criada para disciplina {disciplina_id}")
                
                # Gera nota com distribuição adequada
                ja_cursou = any(h.get('disciplina_id') == disciplina_id for h in historico)
                
                if ja_cursou:
                    # Segunda tentativa - aumenta chance de aprovação
                    nota = round(random.triangular(4, 10, 6.5), 1)
                else:
                    # Primeira tentativa
                    nota = round(random.triangular(0, 10, 5.5), 1)
                
                status = "aprovado" if nota >= 5 else "reprovado"
                
                # Adiciona ao histórico
                historico.append({
                    "aluno_ra": aluno_ra,
                    "semestre": semestre,
                    "nota": nota,
                    "status": status,
                    "lecionada_id": turma['id'],
                    "disciplina_id": disciplina_id
                })
                
                # Atualiza listas de controle
                if status == "aprovado":
                    if disciplina_id not in disciplinas_cursadas:
                        disciplinas_cursadas.append(disciplina_id)
                else:
                    if disciplina_id not in disciplinas_reprovadas:
                        disciplinas_reprovadas.append(disciplina_id)
                
                semestre_atual += 1

            except Exception as e:
                print(f"✗ Erro no semestre {semestre_atual} de {aluno_ra}: {str(e)}")
                semestre_atual += 1
                continue

        # Insere histórico no banco de dados
        registros_validos = 0
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
                registros_validos += 1
                
            except Exception as e:
                print(f"✗ Falha ao inserir registro de {aluno_ra}: {str(e)}")
                continue

        print(f"✓ Histórico de {aluno_ra} criado: {registros_validos}/{len(historico)} registros")
        return historico
    
    except Exception as e:
        print(f"✗ Erro fatal no histórico de {aluno_ra}: {str(e)}")
        return []
    
def criar_tcc(aluno_ra, semestre):
    """Cria registro completo de TCC com turma específica"""
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
        
        # Criar registro do TCC
        tcc = supabase.table("tcc").insert({
            "titulo": fake.catch_phrase()[:200],
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
        alunos = criar_alunos(10)
        
        # Gerar histórico para cada aluno
        for aluno in alunos:
            gerar_historico_aluno(aluno['ra'], aluno['curso_id'])
        
        print("✅ Base de dados populada com sucesso!")
        print("Alunos criados:", len(alunos))
        
    except Exception as e:
        print(f"❌ Erro crítico: {str(e)}")

if __name__ == "__main__":
    main()
