import re

def sort_lists_in_app_py():
    with open('app.py', 'r') as file:
        content = file.read()
    
    # Ordenar médicos por unidade
    medicos = {
        'Ribeirão Preto': ['Dr. Arthur', 'Dr. Daniel'],
        'Campinas': ['Dra. Adriana', 'Dra. Isadora'],
        'Rio de Janeiro': ['Dra. Ana Clara', 'Dra. Paula'],
        'São Paulo': ['Dr. Daniel', 'Dr. Renan', 'Dra. Ariane', 'Dra. Isabella', 'Dra. Talita', 'Dra. Thaiza'],
        'Brasília': ['Dra. Leticia', 'Dra. Natalia']
    }
    
    for unidade, medicos_list in medicos.items():
        # Ordenar médicos em ordem alfabética
        medicos[unidade] = sorted(medicos_list)
    
    # Substituir médicos no arquivo
    pattern_start = r"medicos_por_unidade\s*=\s*\{"
    pattern_end = r"\s*\}"
    medicos_pattern = pattern_start + r"(.*?)" + pattern_end
    
    medicos_replacement = "medicos_por_unidade = {\n"
    for unidade, medicos_list in medicos.items():
        medicos_replacement += f"        '{unidade}': {str(medicos_list)},\n"
    medicos_replacement += "    }"
    
    content = re.sub(medicos_pattern, medicos_replacement, content, flags=re.DOTALL)
    
    # Ordenar equipe por unidade
    equipes = {
        'Ribeirão Preto': ['Aline', 'Ana', 'Natália'],
        'Campinas': ['Bruna Galhardo', 'Dayane Andrade', 'Eduarda de Sousa', 'Isabelle de Campos', 
                     'Juliana Nunes', 'Kesley Sabrina', 'Larissa Hellen', 'Thalita Corrêa', 'Vitória Delino'],
        'Rio de Janeiro': ['Assistente Extra', 'Dayane', 'Mariana Moro', 'Mariana Silva'],
        'São Paulo': ['Adriana Almeida', 'Ana Paula dos Santos', 'Dani Curti', 'Eliene Rodrigues', 
                      'Gabriela Cruz', 'Greice Barbosa', 'Jaiza Valentim', 'Joyce Eugênia Da Silva', 
                      'Josefa Wilma Vieira', 'Merielen Venâncio Oliveira', 'Rosana Pereira', 
                      'Sabrina Crott', 'Thaís Paiva', 'Thamiris Santos'],
        'Brasília': ['Angélica Sousa', 'Betânia Almeida', 'Dayse Fernandes', 'Layla Cardoso', 'Thamara Maciel']
    }
    
    for unidade, equipe_list in equipes.items():
        # Ordenar equipe em ordem alfabética
        equipes[unidade] = sorted(equipe_list)
    
    # Substituir equipe no arquivo
    pattern_start = r"equipe_por_unidade\s*=\s*\{"
    pattern_end = r"\s*\}"
    equipe_pattern = pattern_start + r"(.*?)" + pattern_end
    
    equipe_replacement = "equipe_por_unidade = {\n"
    for unidade, equipe_list in equipes.items():
        equipe_lines = str(equipe_list)
        if len(equipe_list) > 5:
            # Formatação com quebra de linhas
            equipe_lines = "["
            for i, member in enumerate(equipe_list):
                if i % 3 == 0 and i > 0:
                    equipe_lines += "\n                  "
                equipe_lines += f"'{member}'"
                if i < len(equipe_list) - 1:
                    equipe_lines += ", "
            equipe_lines += "]"
        equipe_replacement += f"        '{unidade}': {equipe_lines},\n"
    equipe_replacement += "    }"
    
    content = re.sub(equipe_pattern, equipe_replacement, content, flags=re.DOTALL)
    
    # Substituir também as segundas ocorrências (se houver)
    # Para médicos
    pattern_start = r"doctors_by_unit\s*=\s*\{"
    pattern_end = r"\s*\}"
    doctors_pattern = pattern_start + r"(.*?)" + pattern_end
    
    doctors_replacement = "doctors_by_unit = {\n"
    for unidade, medicos_list in medicos.items():
        doctors_replacement += f"            '{unidade}': {str(medicos_list)},\n"
    doctors_replacement += "        }"
    
    if "doctors_by_unit" in content:
        content = re.sub(doctors_pattern, doctors_replacement, content, flags=re.DOTALL)
    
    # Para equipe
    pattern_start = r"team_by_unit\s*=\s*\{"
    pattern_end = r"\s*\}"
    team_pattern = pattern_start + r"(.*?)" + pattern_end
    
    team_replacement = "team_by_unit = {\n"
    for unidade, equipe_list in equipes.items():
        team_lines = str(equipe_list)
        if len(equipe_list) > 5:
            # Formatação com quebra de linhas
            team_lines = "["
            for i, member in enumerate(equipe_list):
                if i % 3 == 0 and i > 0:
                    team_lines += "\n                      "
                team_lines += f"'{member}'"
                if i < len(equipe_list) - 1:
                    team_lines += ", "
            team_lines += "]"
        team_replacement += f"            '{unidade}': {team_lines},\n"
    team_replacement += "        }"
    
    if "team_by_unit" in content:
        content = re.sub(team_pattern, team_replacement, content, flags=re.DOTALL)
    
    with open('app.py', 'w') as file:
        file.write(content)

if __name__ == "__main__":
    sort_lists_in_app_py()
    print("Listas ordenadas com sucesso!")