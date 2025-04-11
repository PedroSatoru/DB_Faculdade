

#Todas as querrys que serão utilizadas no projeto estão aqui, para facilitar a manutenção e o uso.
#As querrys principais estão no começo do arquivo, e as querrys extras estão no final do arquivo.


#Querrys principais:
#Mostre todo o histórico escolar de um aluno que teve reprovação em uma disciplina, retornando inclusive a reprovação em um semestre e a aprovação no semestre seguinte;
#Mostre todos os TCCs orientados por um professor junto com os nomes dos alunos que fizeram o projeto;
#Mostre a matriz curicular de pelo menos 2 cursos diferentes que possuem disciplinas em comum (e.g., Ciência da Computação e Ciência de Dados). Este exercício deve ser dividido em 2 queries sendo uma para cada curso;
#Para um determinado aluno, mostre os códigos e nomes das diciplinas já cursadas junto com os nomes dos professores que lecionaram a disciplina para o aluno;
#Liste todos os chefes de departamento e coordenadores de curso em apenas uma query de forma que a primeira coluna seja o nome do professor, a segunda o nome do departamento coordena e a terceira o nome do curso que coordena. Substitua os campos em branco do resultado da query pelo texto "nenhum"

#Querrys extras:
#01. Encontre os nomes de todos os estudantes.
#02. Liste os IDs e nomes de todos os professores
#07. Encontre os nomes de todos os estudantes que cursaram "Banco de Dados" (course_id = 'CS-101').
#09. Encontre o número total de estudantes que cursaram "Inteligência Artificial" (course_id = 'CS-102').
#10. Recupere os nomes e IDs dos estudantes que são orientados por um professor específico (ID = 'I001').
#22. Encontre os estudantes que estão matriculados em cursos oferecidos pelo departamento de "Ciência da Computação".
#31. Encontre os nomes dos estudantes que cursaram um curso em todos os departamentos.
#34. Liste os cursos que foram ministrados por mais de um professor em semestres diferentes.
#42. Encontre o número de alunos matriculados em cada curso e liste-os por título de curso.
#50. Liste os nomes dos estudantes que não cursaram nenhum curso no departamento de "Engenharia".


# querrys principais#

#Querry 1, aluno e reprovações#
"""
SELECT 
    a.ra AS "RA do Aluno",
    a.nome AS "Nome do Aluno",
    c.nome AS "Curso",
    he.semestre AS "Semestre",
    CASE 
        WHEN he.lecionada_id IS NOT NULL THEN d.nome
        WHEN he.tcc_id IS NOT NULL THEN 'TCC: ' || t.titulo
    END AS "Disciplina/TCC",
    CASE 
        WHEN he.lecionada_id IS NOT NULL THEN d.codigo
        WHEN he.tcc_id IS NOT NULL THEN 'TCC-' || t.id::text
    END AS "Código",
    he.nota AS "Nota",
    he.status AS "Status",
    CASE 
        WHEN he.lecionada_id IS NOT NULL THEN p.nome
        WHEN he.tcc_id IS NOT NULL THEN prof_orientador.nome
    END AS "Professor/Orientador",
    CASE 
        WHEN he.lecionada_id IS NOT NULL THEN 'Disciplina'
        WHEN he.tcc_id IS NOT NULL THEN 'TCC'
    END AS "Tipo"
FROM 
    aluno a
JOIN 
    curso c ON a.curso_id = c.id
LEFT JOIN 
    historicoescolar he ON a.ra = he.aluno_ra
LEFT JOIN 
    lecionada l ON he.lecionada_id = l.id
LEFT JOIN 
    disciplina d ON l.disciplina_id = d.id
LEFT JOIN 
    professor p ON l.professor_id = p.id
LEFT JOIN 
    tcc t ON he.tcc_id = t.id
LEFT JOIN 
    professor prof_orientador ON t.orientador_id = prof_orientador.id
WHERE 
    a.ra = '25.01.71-4'  -- Substitua pelo RA do aluno desejado
    -- Ou use: a.nome = 'Nome do Aluno' para buscar por nome
ORDER BY 
    he.semestre, 
    CASE WHEN he.lecionada_id IS NOT NULL THEN 1 ELSE 2 END,
    "Disciplina/TCC";
"""

#Querry 2, tccs, alunos e professores#
query2 = """
SELECT t.titulo, p.nome AS orientador, a.nome AS aluno
FROM tcc t
JOIN professor p ON t.orientador_id = p.id
JOIN tcc_aluno ta ON t.id = ta.tcc_id
JOIN aluno a ON ta.aluno_ra = a.ra
WHERE p.id = 2;
"""
#Querry 3, aulas em comum#
query3 = """
SELECT d.codigo, d.nome AS disciplina, p.nome AS professor_responsavel
FROM curso_disciplina cd
JOIN disciplina d ON cd.disciplina_id = d.id
JOIN professor p ON cd.professor_responsavel_id = p.id
WHERE cd.curso_id = 4
ORDER BY d.codigo;"""
"""""
SELECT d.codigo, d.nome AS disciplina, p.nome AS professor_responsavel
FROM curso_disciplina cd
JOIN disciplina d ON cd.disciplina_id = d.id
JOIN professor p ON cd.professor_responsavel_id = p.id
WHERE cd.curso_id = 1
ORDER BY d.codigo;"""""

#Querry 4, aluno, disciplina e professor responsável#

query4 = """
SELECT d.codigo, d.nome AS disciplina, p.nome AS professor
FROM historicoescolar h
JOIN lecionada l ON h.lecionada_id = l.id
JOIN disciplina d ON l.disciplina_id = d.id
JOIN professor p ON l.professor_id = p.id
WHERE h.aluno_ra = '17.08.80-3'
AND h.status = 'aprovado'
ORDER BY h.semestre;"""

#Querry 5, coordenador e chefe de departamento#
query5= """
SELECT 
    p.nome AS professor,
    COALESCE(d.nome, 'nenhum') AS departamento_chefiado,
    COALESCE(c.nome, 'nenhum') AS curso_coordenado
FROM professor p
LEFT JOIN departamento d ON p.id = d.chefe_id
LEFT JOIN curso c ON p.id = c.coordenador_id
WHERE d.chefe_id IS NOT NULL OR c.coordenador_id IS NOT NULL
ORDER BY p.nome;
"""


#Querrys extras#
#Querry 6, nomes de todos os estudantes
query6 = """
SELECT nome FROM aluno ORDER BY nome;
"""
#Querry 7, IDs e nomes de todos os professores

query7 = """
-- Query básica: IDs e nomes de todos os professores
SELECT 
    id AS "ID",
    nome AS "Nome do Professor"
FROM 
    professor
ORDER BY 
    id;;
"""

#Querry 8, nomes de todos os estudantes que cursaram "Banco de Dados" (course_id = 'CC-201')

query8 = """
SELECT DISTINCT
    a.nome AS "Nome do Estudante",
    a.ra AS "RA",
    c.nome AS "Curso",
    h.nota AS "Nota",
    h.status AS "Status",
    h.semestre AS "Semestre"
FROM
    aluno a
JOIN historicoescolar h ON a.ra = h.aluno_ra
JOIN lecionada l ON h.lecionada_id = l.id
JOIN disciplina d ON l.disciplina_id = d.id
JOIN curso c ON a.curso_id = c.id
WHERE
    d.id = 3
ORDER BY
    a.nome, h.semestre;
    """
#Querry 9, número total de estudantes que cursaram "Estrutura de Dados" (course_id = 'CC-102').

query9 = """
SELECT COUNT(DISTINCT a.ra) AS "Total de Estudantes que Cursaram Estruturas de Dados"
FROM aluno a
JOIN historicoescolar h ON a.ra = h.aluno_ra
JOIN lecionada l ON h.lecionada_id = l.id
JOIN disciplina d ON l.disciplina_id = d.id
WHERE d.nome = 'Estruturas de Dados';
"""

#Querry 10, nomes e IDs dos estudantes que são orientados por um professor específico).

query10 = """
SELECT DISTINCT 
    a.ra AS "RA",
    a.nome AS "Aluno",
    p.nome AS "Professor"
FROM 
    aluno a
JOIN 
    historicoescolar h ON a.ra = h.aluno_ra
JOIN 
    lecionada l ON h.lecionada_id = l.id
JOIN 
    professor p ON l.professor_id = p.id
WHERE 
    p.id = 1  
ORDER BY 
    a.nome;
    """
#Querry 11, estudantes que estão matriculados em cursos oferecidos pelo departamento de TI
query11 = """
SELECT 
    a.ra AS "RA",
    a.nome AS "Nome do Aluno",
    c.nome AS "Curso",
    d.nome AS "Departamento"
FROM 
    aluno a
JOIN 
    curso c ON a.curso_id = c.id
JOIN 
    departamento d ON c.departamento_id = d.id
WHERE 
    d.id = 2  -- Substitua pelo ID do departamento desejado
ORDER BY 
    a.nome;
    """
#Querry 12, nomes dos estudantes que cursaram um curso em todos os departamentos.

query12 = """
SELECT 
    a.nome AS "Estudante",
    a.ra AS "RA",
    STRING_AGG(DISTINCT d.nome, ', ' ORDER BY d.nome) AS "Departamentos Cursados"
FROM aluno a
JOIN historicoescolar h ON a.ra = h.aluno_ra
JOIN lecionada l ON h.lecionada_id = l.id
JOIN disciplina di ON l.disciplina_id = di.id
JOIN departamento d ON di.departamento_id = d.id
GROUP BY a.ra, a.nome
HAVING COUNT(DISTINCT d.id) = (SELECT COUNT(*) FROM departamento)
ORDER BY a.nome;
"""

#Querry 13,  Liste os cursos que foram ministrados por mais de um professor em semestres diferentes.

query13 = """
SELECT 
    c.nome AS "Curso",
    d.nome AS "Disciplina",
    COUNT(DISTINCT l.professor_id) AS "Quantidade de Professores",
    COUNT(DISTINCT l.semestre) AS "Quantidade de Semestres",
    STRING_AGG(DISTINCT p.nome, ', ' ORDER BY p.nome) AS "Professores"
FROM 
    curso c
JOIN curso_disciplina cd ON c.id = cd.curso_id
JOIN disciplina d ON cd.disciplina_id = d.id
JOIN lecionada l ON d.id = l.disciplina_id
JOIN professor p ON l.professor_id = p.id
GROUP BY 
    c.id, c.nome, d.id, d.nome
HAVING 
    COUNT(DISTINCT l.professor_id) > 1
ORDER BY 
    c.nome, d.nome;
"""
#Querry 14, Encontre o número de alunos matriculados em cada curso e liste-os por título de curso

query14 = """
SELECT 
    c.nome AS "Curso",
    COUNT(a.ra) AS "Número de Alunos Matriculados"
FROM 
    curso c
LEFT JOIN 
    aluno a ON c.id = a.curso_id
GROUP BY 
    c.id, c.nome
ORDER BY 
    COUNT(a.ra) DESC, c.nome;
"""
#Querry 15, nomes dos estudantes que não cursaram nenhum curso no departamento de "Matematica".

query15 = """
SELECT
    a.nome AS "Estudante",
    STRING_AGG(DISTINCT di.nome, ', ' ORDER BY di.nome) AS "Disciplinas Cursadas"
FROM
    aluno a
JOIN historicoescolar h ON a.ra = h.aluno_ra
JOIN lecionada l ON h.lecionada_id = l.id
JOIN disciplina di ON l.disciplina_id = di.id
JOIN departamento dep ON di.departamento_id = dep.id
WHERE a.ra NOT IN (
    SELECT h.aluno_ra
    FROM historicoescolar h
    JOIN lecionada l ON h.lecionada_id = l.id
    JOIN disciplina d ON l.disciplina_id = d.id
    JOIN departamento mat ON d.departamento_id = mat.id
    WHERE mat.nome = 'Matemática'
)
GROUP BY a.ra, a.nome
ORDER BY a.nome;
"""