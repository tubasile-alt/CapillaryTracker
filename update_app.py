import re

def update_app_py():
    with open('app.py', 'r') as file:
        content = file.read()
    
    # Adicionar Dra. Thaiza aos médicos de São Paulo
    pattern_medicos = r"'São Paulo':\s*\['Dr\. Renan', 'Dra\. Isabella', 'Dr\. Daniel', 'Dra\. Ariane', 'Dra\. Talita'\]"
    replacement_medicos = "'São Paulo': ['Dr. Renan', 'Dra. Isabella', 'Dr. Daniel', 'Dra. Ariane', 'Dra. Talita', 'Dra. Thaiza']"
    content = re.sub(pattern_medicos, replacement_medicos, content)
    
    # Adicionar Greice Barbosa à equipe de São Paulo
    pattern_equipe = r"'Adriana Almeida', 'Jaiza Valentim', 'Eliene Rodrigues', 'Thaís Paiva'\]"
    replacement_equipe = "'Adriana Almeida', 'Jaiza Valentim', 'Eliene Rodrigues', 'Thaís Paiva', 'Greice Barbosa']"
    content = re.sub(pattern_equipe, replacement_equipe, content)
    
    with open('app.py', 'w') as file:
        file.write(content)
    
    print("Arquivo app.py atualizado com sucesso!")

if __name__ == "__main__":
    update_app_py()
