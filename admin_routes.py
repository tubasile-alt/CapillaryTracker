"""
Módulo para gerenciar as rotas administrativas do sistema.
Permite adicionar, editar e remover médicos e equipes por unidade.
"""
import re
import functools
import logging
import json
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask import current_app as app

# Configurar logging
logger = logging.getLogger(__name__)

# Criar um Blueprint para as rotas administrativas
admin_bp = Blueprint('admin', __name__)

# Arquivo para salvar as configurações
CONFIG_FILE = 'admin_config.json'

def load_config():
    """Carrega a configuração de médicos e equipe"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    # Configuração padrão
    return {
        'unidades': ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro', 'São Paulo', 'Brasília'],
        'medicos_por_unidade': {
            'Ribeirão Preto': ['Dr. Arthur', 'Dr. Daniel'],
            'Campinas': ['Dra. Adriana', 'Dra. Isadora'],
            'Rio de Janeiro': ['Dra. Ana Clara', 'Dra. Paula'],
            'São Paulo': ['Dr. Daniel', 'Dr. Renan', 'Dra. Ariane', 'Dra. Isabella', 'Dra. Talita', 'Dra. Thaiza'],
            'Brasília': ['Dra. Leticia', 'Dra. Natalia']
        },
        'equipe_por_unidade': {
            'Ribeirão Preto': ['Aline', 'Ana', 'Lavinia', 'Natália'],
            'Campinas': ['Bruna Galhardo', 'Dayane Andrade', 'Eduarda de Sousa', 'Isabelle de Campos', 
                         'Juliana Nunes', 'Kesley Sabrina', 'Larissa Hellen', 'Thalita Corrêa', 'Vitória Delino'],
            'Rio de Janeiro': ['Assistente Extra', 'Dayane', 'Mariana Moro', 'Mariana Silva'],
            'São Paulo': ['Adriana Almeida', 'Ana Paula dos Santos', 'Dani Curti', 'Eliene Rodrigues', 
                          'Gabriela Cruz', 'Greice Barbosa', 'Jaiza Valentim', 'Joyce Eugênia Da Silva', 
                          'Josefa Wilma Vieira', 'Merielen Venâncio Oliveira', 'Rosana Pereira', 
                          'Sabrina Crott', 'Thaís Paiva', 'Thamiris Santos'],
            'Brasília': ['Angélica Sousa', 'Betânia Almeida', 'Dayse Fernandes', 'Layla Cardoso', 'Thamara Maciel']
        }
    }

def save_config(config):
    """Salva a configuração de médicos e equipe"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def update_app_py(config):
    """Atualiza o arquivo app.py com as novas configurações"""
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # Atualizar UNIDADES
        unidades_list = config.get('unidades', ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro', 'São Paulo', 'Brasília'])
        unidades_str = f"UNIDADES = {unidades_list}"
        
        # Encontrar e substituir a definição de UNIDADES
        unidades_pattern = r"UNIDADES\s*=\s*\[[\s\S]*?\]"
        if re.search(unidades_pattern, content):
            content = re.sub(unidades_pattern, unidades_str, content, flags=re.DOTALL)
        else:
            # Adicionar UNIDADES se não existir
            content = content.replace('MEDICOS_POR_UNIDADE', f'{unidades_str}\n\nMEDICOS_POR_UNIDADE')

        # Atualizar MEDICOS_POR_UNIDADE
        medicos_str = f"MEDICOS_POR_UNIDADE = {config.get('medicos_por_unidade', {})}"
        medicos_pattern = r"MEDICOS_POR_UNIDADE\s*=\s*\{[\s\S]*?\n\}"
        content = re.sub(medicos_pattern, medicos_str, content, flags=re.DOTALL)

        # Atualizar EQUIPE_POR_UNIDADE
        equipe_str = f"EQUIPE_POR_UNIDADE = {config.get('equipe_por_unidade', {})}"
        equipe_pattern = r"EQUIPE_POR_UNIDADE\s*=\s*\{[\s\S]*?\n\}"
        content = re.sub(equipe_pattern, equipe_str, content, flags=re.DOTALL)

        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info("Arquivo app.py atualizado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar app.py: {str(e)}")
        return False

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
    # Carregar configuração atual
    config = load_config()
    
    # Usar unidades da configuração ou lista padrão
    unidades = config.get('unidades', ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro', 'São Paulo', 'Brasília'])

    return render_template(
        'admin.html', 
        config=config,
        unidades=unidades, 
        medicos_por_unidade=config['medicos_por_unidade'], 
        equipe_por_unidade=config['equipe_por_unidade']
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

    # Carregar configuração atual
    config = load_config()

    # Verificar se o médico já existe
    if unidade in config['medicos_por_unidade'] and nome in config['medicos_por_unidade'][unidade]:
        flash(f'O médico {nome} já existe na unidade {unidade}!', 'danger')
        return redirect(url_for('admin.dashboard'))

    # Adicionar novo médico
    if unidade not in config['medicos_por_unidade']:
        config['medicos_por_unidade'][unidade] = []

    config['medicos_por_unidade'][unidade].append(nome)
    config['medicos_por_unidade'][unidade].sort()  # Ordenar em ordem alfabética

    # Salvar configuração
    save_config(config)

    # Atualizar app.py
    if update_app_py(config):
        flash(f'Médico {nome} adicionado com sucesso à unidade {unidade}!', 'success')
    else:
        flash(f'Médico adicionado, mas houve erro ao atualizar o sistema. Reinicie a aplicação.', 'warning')

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

    # Carregar configuração atual
    config = load_config()

    # Verificar se o médico existe
    if unidade not in config['medicos_por_unidade'] or nome not in config['medicos_por_unidade'][unidade]:
        flash(f'O médico {nome} não existe na unidade {unidade}!', 'danger')
        return redirect(url_for('admin.dashboard'))

    # Remover médico
    config['medicos_por_unidade'][unidade].remove(nome)

    # Salvar configuração
    save_config(config)

    # Atualizar app.py
    if update_app_py(config):
        flash(f'Médico {nome} removido com sucesso da unidade {unidade}!', 'success')
    else:
        flash(f'Médico removido, mas houve erro ao atualizar o sistema. Reinicie a aplicação.', 'warning')

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

    # Carregar configuração atual
    config = load_config()

    # Verificar se o membro já existe
    if unidade in config['equipe_por_unidade'] and nome in config['equipe_por_unidade'][unidade]:
        flash(f'O membro {nome} já existe na equipe da unidade {unidade}!', 'danger')
        return redirect(url_for('admin.dashboard'))

    # Adicionar novo membro
    if unidade not in config['equipe_por_unidade']:
        config['equipe_por_unidade'][unidade] = []

    config['equipe_por_unidade'][unidade].append(nome)
    config['equipe_por_unidade'][unidade].sort()  # Ordenar em ordem alfabética

    # Salvar configuração
    save_config(config)

    # Atualizar app.py
    if update_app_py(config):
        flash(f'Membro {nome} adicionado com sucesso à equipe da unidade {unidade}!', 'success')
    else:
        flash(f'Membro adicionado, mas houve erro ao atualizar o sistema. Reinicie a aplicação.', 'warning')

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

    # Carregar configuração atual
    config = load_config()

    # Verificar se o membro existe
    if unidade not in config['equipe_por_unidade'] or nome not in config['equipe_por_unidade'][unidade]:
        flash(f'O membro {nome} não existe na equipe da unidade {unidade}!', 'danger')
        return redirect(url_for('admin.dashboard'))

    # Remover membro
    config['equipe_por_unidade'][unidade].remove(nome)

    # Salvar configuração
    save_config(config)

    # Atualizar app.py
    if update_app_py(config):
        flash(f'Membro {nome} removido com sucesso da equipe da unidade {unidade}!', 'success')
    else:
        flash(f'Membro removido, mas houve erro ao atualizar o sistema. Reinicie a aplicação.', 'warning')

    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/add_unidade', methods=['POST'])
@admin_required
def add_unidade():
    """Adiciona uma nova unidade"""
    nome = request.form.get('nome')
    
    if not nome:
        flash('Nome da unidade é obrigatório!', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Carregar configuração atual
    config = load_config()
    
    # Verificar se a unidade já existe
    if 'unidades' not in config:
        config['unidades'] = []
    
    if nome in config['unidades']:
        flash(f'A unidade {nome} já existe!', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Adicionar nova unidade
    config['unidades'].append(nome)
    config['unidades'].sort()  # Ordenar em ordem alfabética
    
    # Inicializar listas vazias para médicos e equipe
    if 'medicos_por_unidade' not in config:
        config['medicos_por_unidade'] = {}
    if 'equipe_por_unidade' not in config:
        config['equipe_por_unidade'] = {}
        
    config['medicos_por_unidade'][nome] = []
    config['equipe_por_unidade'][nome] = []
    
    # Salvar configuração
    save_config(config)
    
    # Atualizar app.py
    if update_app_py(config):
        flash(f'Unidade {nome} adicionada com sucesso!', 'success')
    else:
        flash(f'Unidade adicionada, mas houve erro ao atualizar o sistema. Reinicie a aplicação.', 'warning')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete_unidade', methods=['POST'])
@admin_required
def delete_unidade():
    """Remove uma unidade"""
    nome = request.form.get('nome')
    
    if not nome:
        flash('Nome da unidade é obrigatório!', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Carregar configuração atual
    config = load_config()
    
    # Verificar se a unidade existe
    if 'unidades' not in config or nome not in config['unidades']:
        flash(f'A unidade {nome} não existe!', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Remover unidade
    config['unidades'].remove(nome)
    
    # Remover médicos e equipe da unidade
    if nome in config.get('medicos_por_unidade', {}):
        del config['medicos_por_unidade'][nome]
    if nome in config.get('equipe_por_unidade', {}):
        del config['equipe_por_unidade'][nome]
    
    # Salvar configuração
    save_config(config)
    
    # Atualizar app.py
    if update_app_py(config):
        flash(f'Unidade {nome} removida com sucesso!', 'success')
    else:
        flash(f'Unidade removida, mas houve erro ao atualizar o sistema. Reinicie a aplicação.', 'warning')
    
    return redirect(url_for('admin.dashboard'))