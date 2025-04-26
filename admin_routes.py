"""
Módulo para gerenciar as rotas administrativas do sistema.
Permite adicionar, editar e remover médicos e equipes por unidade.
"""

import re
import functools
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask import current_app as app

# Configurar logging
logger = logging.getLogger(__name__)

# Criar um Blueprint para as rotas administrativas
admin_bp = Blueprint('admin', __name__)

# Decorator para verificar se o usuário está autenticado como administrador
def admin_required(func):
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        if 'admin_authenticated' not in session or not session['admin_authenticated']:
            flash('Você precisa fazer login como administrador para acessar esta página.', 'danger')
            return redirect(url_for('admin.login_page'))
        return func(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET'])
def login_page():
    """Página de login para administradores"""
    return render_template('admin_login.html')

@admin_bp.route('/login', methods=['POST'])
def login():
    """Processa o login de administrador"""
    senha = request.form.get('senha')
    
    if senha == app.config['ADMIN_PASSWORD']:
        session['admin_authenticated'] = True
        flash('Login realizado com sucesso!', 'success')
        return redirect(url_for('admin.dashboard'))
    else:
        flash('Senha incorreta!', 'danger')
        return redirect(url_for('admin.login_page'))

@admin_bp.route('/logout')
def logout():
    """Realiza o logout do administrador"""
    session.pop('admin_authenticated', None)
    flash('Você saiu do sistema com sucesso!', 'success')
    return redirect(url_for('index'))

@admin_bp.route('/')
@admin_required
def dashboard():
    """Dashboard administrativo"""
    unidades = ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro', 'São Paulo', 'Brasília']
    
    # Obter médicos por unidade
    medicos_por_unidade = {
        'Ribeirão Preto': ['Dr. Arthur', 'Dr. Daniel'],
        'Campinas': ['Dra. Adriana', 'Dra. Isadora'],
        'Rio de Janeiro': ['Dra. Ana Clara', 'Dra. Paula'],
        'São Paulo': ['Dr. Daniel', 'Dr. Renan', 'Dra. Ariane', 'Dra. Isabella', 'Dra. Talita', 'Dra. Thaiza'],
        'Brasília': ['Dra. Leticia', 'Dra. Natalia']
    }
    
    # Obter equipe por unidade
    equipe_por_unidade = {
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
    
    return render_template(
        'admin.html', 
        unidades=unidades, 
        medicos_por_unidade=medicos_por_unidade, 
        equipe_por_unidade=equipe_por_unidade
    )

@admin_bp.route('/add_medico', methods=['POST'])
@admin_required
def add_medico():
    """Adiciona um novo médico"""
    unidade = request.form.get('unidade')
    nome = request.form.get('nome')
    
    if not unidade or not nome:
        flash('Unidade e nome são campos obrigatórios!', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Obter médicos atuais
    medicos_por_unidade = {
        'Ribeirão Preto': ['Dr. Arthur', 'Dr. Daniel'],
        'Campinas': ['Dra. Adriana', 'Dra. Isadora'],
        'Rio de Janeiro': ['Dra. Ana Clara', 'Dra. Paula'],
        'São Paulo': ['Dr. Daniel', 'Dr. Renan', 'Dra. Ariane', 'Dra. Isabella', 'Dra. Talita', 'Dra. Thaiza'],
        'Brasília': ['Dra. Leticia', 'Dra. Natalia']
    }
    
    # Verificar se o médico já existe
    if unidade in medicos_por_unidade and nome in medicos_por_unidade[unidade]:
        flash(f'O médico {nome} já existe na unidade {unidade}!', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Adicionar novo médico
    if unidade not in medicos_por_unidade:
        medicos_por_unidade[unidade] = []
    
    medicos_por_unidade[unidade].append(nome)
    medicos_por_unidade[unidade].sort()  # Ordenar em ordem alfabética
    
    # Modificar a função get_medicos para refletir a alteração
    with open('app.py', 'r') as file:
        content = file.read()
    
    # Encontrar e substituir as definições de médicos
    pattern_start = r"medicos_por_unidade\s*=\s*\{"
    pattern_end = r"\s*\}"
    medicos_pattern = pattern_start + r"(.*?)" + pattern_end
    
    medicos_replacement = "medicos_por_unidade = {\n"
    for unit, medicos_list in medicos_por_unidade.items():
        medicos_replacement += f"        '{unit}': {str(medicos_list)},\n"
    medicos_replacement += "    }"
    
    updated_content = re.sub(medicos_pattern, medicos_replacement, content, flags=re.DOTALL)
    
    # Encontrar e substituir a segunda definição de médicos (se existir)
    pattern_start = r"doctors_by_unit\s*=\s*\{"
    pattern_end = r"\s*\}"
    doctors_pattern = pattern_start + r"(.*?)" + pattern_end
    
    doctors_replacement = "doctors_by_unit = {\n"
    for unit, medicos_list in medicos_por_unidade.items():
        doctors_replacement += f"            '{unit}': {str(medicos_list)},\n"
    doctors_replacement += "        }"
    
    if "doctors_by_unit" in content:
        updated_content = re.sub(doctors_pattern, doctors_replacement, updated_content, flags=re.DOTALL)
    
    # Salvar arquivo
    with open('app.py', 'w') as file:
        file.write(updated_content)
    
    flash(f'Médico {nome} adicionado com sucesso à unidade {unidade}!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete_medico', methods=['POST'])
@admin_required
def delete_medico():
    """Remove um médico"""
    unidade = request.form.get('unidade')
    nome = request.form.get('nome')
    
    if not unidade or not nome:
        flash('Unidade e nome são campos obrigatórios!', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Obter médicos atuais
    medicos_por_unidade = {
        'Ribeirão Preto': ['Dr. Arthur', 'Dr. Daniel'],
        'Campinas': ['Dra. Adriana', 'Dra. Isadora'],
        'Rio de Janeiro': ['Dra. Ana Clara', 'Dra. Paula'],
        'São Paulo': ['Dr. Daniel', 'Dr. Renan', 'Dra. Ariane', 'Dra. Isabella', 'Dra. Talita', 'Dra. Thaiza'],
        'Brasília': ['Dra. Leticia', 'Dra. Natalia']
    }
    
    # Verificar se o médico existe
    if unidade not in medicos_por_unidade or nome not in medicos_por_unidade[unidade]:
        flash(f'O médico {nome} não existe na unidade {unidade}!', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Remover médico
    medicos_por_unidade[unidade].remove(nome)
    
    # Modificar a função get_medicos para refletir a alteração
    with open('app.py', 'r') as file:
        content = file.read()
    
    # Encontrar e substituir as definições de médicos
    pattern_start = r"medicos_por_unidade\s*=\s*\{"
    pattern_end = r"\s*\}"
    medicos_pattern = pattern_start + r"(.*?)" + pattern_end
    
    medicos_replacement = "medicos_por_unidade = {\n"
    for unit, medicos_list in medicos_por_unidade.items():
        medicos_replacement += f"        '{unit}': {str(medicos_list)},\n"
    medicos_replacement += "    }"
    
    updated_content = re.sub(medicos_pattern, medicos_replacement, content, flags=re.DOTALL)
    
    # Encontrar e substituir a segunda definição de médicos (se existir)
    pattern_start = r"doctors_by_unit\s*=\s*\{"
    pattern_end = r"\s*\}"
    doctors_pattern = pattern_start + r"(.*?)" + pattern_end
    
    doctors_replacement = "doctors_by_unit = {\n"
    for unit, medicos_list in medicos_por_unidade.items():
        doctors_replacement += f"            '{unit}': {str(medicos_list)},\n"
    doctors_replacement += "        }"
    
    if "doctors_by_unit" in content:
        updated_content = re.sub(doctors_pattern, doctors_replacement, updated_content, flags=re.DOTALL)
    
    # Salvar arquivo
    with open('app.py', 'w') as file:
        file.write(updated_content)
    
    flash(f'Médico {nome} removido com sucesso da unidade {unidade}!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/add_equipe', methods=['POST'])
@admin_required
def add_equipe():
    """Adiciona um novo membro à equipe"""
    unidade = request.form.get('unidade')
    nome = request.form.get('nome')
    
    if not unidade or not nome:
        flash('Unidade e nome são campos obrigatórios!', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Obter equipe atual
    equipe_por_unidade = {
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
    
    # Verificar se o membro já existe
    if unidade in equipe_por_unidade and nome in equipe_por_unidade[unidade]:
        flash(f'O membro {nome} já existe na equipe da unidade {unidade}!', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Adicionar novo membro
    if unidade not in equipe_por_unidade:
        equipe_por_unidade[unidade] = []
    
    equipe_por_unidade[unidade].append(nome)
    equipe_por_unidade[unidade].sort()  # Ordenar em ordem alfabética
    
    # Modificar a função get_equipe para refletir a alteração
    with open('app.py', 'r') as file:
        content = file.read()
    
    # Encontrar e substituir as definições de equipe
    pattern_start = r"equipe_por_unidade\s*=\s*\{"
    pattern_end = r"\s*\}"
    equipe_pattern = pattern_start + r"(.*?)" + pattern_end
    
    equipe_replacement = "equipe_por_unidade = {\n"
    for unit, equipe_list in equipe_por_unidade.items():
        equipe_lines = str(equipe_list)
        if len(equipe_list) > 5:
            # Formatação com quebra de linhas para listas longas
            equipe_lines = "["
            for i, member in enumerate(equipe_list):
                if i % 3 == 0 and i > 0:
                    equipe_lines += "\n                  "
                equipe_lines += f"'{member}'"
                if i < len(equipe_list) - 1:
                    equipe_lines += ", "
            equipe_lines += "]"
        equipe_replacement += f"        '{unit}': {equipe_lines},\n"
    equipe_replacement += "    }"
    
    updated_content = re.sub(equipe_pattern, equipe_replacement, content, flags=re.DOTALL)
    
    # Encontrar e substituir a segunda definição de equipe (se existir)
    pattern_start = r"team_by_unit\s*=\s*\{"
    pattern_end = r"\s*\}"
    team_pattern = pattern_start + r"(.*?)" + pattern_end
    
    team_replacement = "team_by_unit = {\n"
    for unit, equipe_list in equipe_por_unidade.items():
        team_lines = str(equipe_list)
        if len(equipe_list) > 5:
            # Formatação com quebra de linhas para listas longas
            team_lines = "["
            for i, member in enumerate(equipe_list):
                if i % 3 == 0 and i > 0:
                    team_lines += "\n                      "
                team_lines += f"'{member}'"
                if i < len(equipe_list) - 1:
                    team_lines += ", "
            team_lines += "]"
        team_replacement += f"            '{unit}': {team_lines},\n"
    team_replacement += "        }"
    
    if "team_by_unit" in content:
        updated_content = re.sub(team_pattern, team_replacement, updated_content, flags=re.DOTALL)
    
    # Salvar arquivo
    with open('app.py', 'w') as file:
        file.write(updated_content)
    
    flash(f'Membro {nome} adicionado com sucesso à equipe da unidade {unidade}!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete_equipe', methods=['POST'])
@admin_required
def delete_equipe():
    """Remove um membro da equipe"""
    unidade = request.form.get('unidade')
    nome = request.form.get('nome')
    
    if not unidade or not nome:
        flash('Unidade e nome são campos obrigatórios!', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Obter equipe atual
    equipe_por_unidade = {
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
    
    # Verificar se o membro existe
    if unidade not in equipe_por_unidade or nome not in equipe_por_unidade[unidade]:
        flash(f'O membro {nome} não existe na equipe da unidade {unidade}!', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Remover membro
    equipe_por_unidade[unidade].remove(nome)
    
    # Modificar a função get_equipe para refletir a alteração
    with open('app.py', 'r') as file:
        content = file.read()
    
    # Encontrar e substituir as definições de equipe
    pattern_start = r"equipe_por_unidade\s*=\s*\{"
    pattern_end = r"\s*\}"
    equipe_pattern = pattern_start + r"(.*?)" + pattern_end
    
    equipe_replacement = "equipe_por_unidade = {\n"
    for unit, equipe_list in equipe_por_unidade.items():
        equipe_lines = str(equipe_list)
        if len(equipe_list) > 5:
            # Formatação com quebra de linhas para listas longas
            equipe_lines = "["
            for i, member in enumerate(equipe_list):
                if i % 3 == 0 and i > 0:
                    equipe_lines += "\n                  "
                equipe_lines += f"'{member}'"
                if i < len(equipe_list) - 1:
                    equipe_lines += ", "
            equipe_lines += "]"
        equipe_replacement += f"        '{unit}': {equipe_lines},\n"
    equipe_replacement += "    }"
    
    updated_content = re.sub(equipe_pattern, equipe_replacement, content, flags=re.DOTALL)
    
    # Encontrar e substituir a segunda definição de equipe (se existir)
    pattern_start = r"team_by_unit\s*=\s*\{"
    pattern_end = r"\s*\}"
    team_pattern = pattern_start + r"(.*?)" + pattern_end
    
    team_replacement = "team_by_unit = {\n"
    for unit, equipe_list in equipe_por_unidade.items():
        team_lines = str(equipe_list)
        if len(equipe_list) > 5:
            # Formatação com quebra de linhas para listas longas
            team_lines = "["
            for i, member in enumerate(equipe_list):
                if i % 3 == 0 and i > 0:
                    team_lines += "\n                      "
                team_lines += f"'{member}'"
                if i < len(equipe_list) - 1:
                    team_lines += ", "
            team_lines += "]"
        team_replacement += f"            '{unit}': {team_lines},\n"
    team_replacement += "        }"
    
    if "team_by_unit" in content:
        updated_content = re.sub(team_pattern, team_replacement, updated_content, flags=re.DOTALL)
    
    # Salvar arquivo
    with open('app.py', 'w') as file:
        file.write(updated_content)
    
    flash(f'Membro {nome} removido com sucesso da equipe da unidade {unidade}!', 'success')
    return redirect(url_for('admin.dashboard'))