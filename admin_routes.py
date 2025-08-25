"""
Módulo para gerenciar as rotas administrativas do sistema.
Permite adicionar, editar e remover médicos e equipes por unidade.
"""
import re
import functools
import logging
import json
import os
import shutil
import traceback
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask import current_app as app

# Configurar logging
logger = logging.getLogger(__name__)

# Criar um Blueprint para as rotas administrativas
admin_bp = Blueprint('admin', __name__)

# Arquivo para salvar as configurações
CONFIG_FILE = 'admin_config.json'

def load_config():
    """Carrega a configuração de médicos e equipe com tratamento robusto de erros"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"✅ Configuração carregada: {len(config.get('unidades', []))} unidades")
                return config
        else:
            logger.warning(f"⚠️ Arquivo {CONFIG_FILE} não encontrado, usando configuração padrão")
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"❌ Erro ao carregar {CONFIG_FILE}: {e}")
        
        # Tentar carregar do backup
        backup_file = CONFIG_FILE.replace('.json', '_backup.json')
        if os.path.exists(backup_file):
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info(f"🔄 Configuração carregada do backup: {len(config.get('unidades', []))} unidades")
                    # Restaurar o arquivo principal
                    shutil.copy2(backup_file, CONFIG_FILE)
                    logger.info(f"✅ Arquivo principal restaurado do backup")
                    return config
            except Exception as backup_error:
                logger.error(f"❌ Erro ao carregar backup: {backup_error}")
        
        logger.warning("🔄 Usando configuração padrão devido a erros")

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

def sync_uberlandia_teams(config):
    """Sincroniza automaticamente a equipe de Uberlândia com São Paulo, Goiânia, Ribeirão Preto e Brasília"""
    source_units = ["São Paulo", "Goiania", "Ribeirão Preto", "Brasília"]
    uberlandia_team = []
    
    for unit in source_units:
        if unit in config['equipe_por_unidade']:
            uberlandia_team.extend(config['equipe_por_unidade'][unit])
    
    # Remover duplicatas e ordenar
    uberlandia_team = sorted(list(set(uberlandia_team)))
    
    # Atualizar Uberlândia
    config['equipe_por_unidade']['Uberlândia'] = uberlandia_team
    
    print(f"✅ Uberlândia sincronizada com {len(uberlandia_team)} membros das equipes de: {', '.join(source_units)}")
    return config

def save_config(config):
    """Salva a configuração de médicos e equipe com backup automático"""
    try:
        # Sempre sincronizar Uberlândia antes de salvar
        config = sync_uberlandia_teams(config)
        
        # Criar backup do arquivo atual antes de salvar
        backup_file = CONFIG_FILE.replace('.json', '_backup.json')
        if os.path.exists(CONFIG_FILE):
            try:
                shutil.copy2(CONFIG_FILE, backup_file)
                logger.info(f"✅ Backup criado: {backup_file}")
            except Exception as e:
                logger.error(f"⚠️ Erro ao criar backup: {e}")
        
        # Salvar em arquivo temporário primeiro
        temp_file = CONFIG_FILE + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # Verificar se o arquivo temporário foi criado corretamente
        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
            # Mover arquivo temporário para o arquivo final
            shutil.move(temp_file, CONFIG_FILE)
            logger.info(f"✅ Configuração salva com sucesso em {CONFIG_FILE}")
            logger.info(f"📊 Dados salvos: {len(config.get('unidades', []))} unidades, {len(config.get('medicos_por_unidade', {}))} grupos de médicos")
        else:
            logger.error(f"❌ Erro: arquivo temporário {temp_file} não foi criado corretamente")
            raise Exception("Falha ao criar arquivo temporário")
            
    except Exception as e:
        logger.error(f"❌ Erro ao salvar configuração: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Tentar restaurar do backup se existir
        backup_file = CONFIG_FILE.replace('.json', '_backup.json')
        if os.path.exists(backup_file):
            try:
                shutil.copy2(backup_file, CONFIG_FILE)
                logger.info(f"🔄 Configuração restaurada do backup: {backup_file}")
            except Exception as restore_error:
                logger.error(f"❌ Erro ao restaurar backup: {restore_error}")
        raise e

def update_app_py(config):
    """Atualiza o arquivo app.py com as novas configurações e verifica integridade"""
    try:
        # Importar a função de recarregamento do app.py
        from app import reload_admin_config
        reload_admin_config()
        
        # Verificar se as configurações foram realmente atualizadas
        from app import UNIDADES, MEDICOS_POR_UNIDADE, EQUIPE_POR_UNIDADE
        
        # Verificar integridade dos dados carregados
        expected_units = set(config.get('unidades', []))
        actual_units = set(UNIDADES)
        
        if expected_units == actual_units:
            logger.info("✅ Configurações recarregadas e verificadas no app.py com sucesso.")
            logger.info(f"📊 Unidades sincronizadas: {len(UNIDADES)} unidades")
            return True
        else:
            missing_units = expected_units - actual_units
            extra_units = actual_units - expected_units
            logger.warning(f"⚠️ Inconsistência detectada:")
            if missing_units:
                logger.warning(f"   Unidades faltando: {missing_units}")
            if extra_units:
                logger.warning(f"   Unidades extras: {extra_units}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao recarregar configurações no app.py: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
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
    # Forçar recarregamento das configurações
    config = load_config()
    
    # Log para debug
    logger.info(f"Dashboard carregado com {len(config.get('unidades', []))} unidades")
    
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

@admin_bp.route('/verify_config')
@admin_required
def verify_config():
    """Endpoint para verificar a integridade da configuração"""
    try:
        # Carregar configuração do arquivo
        file_config = load_config()
        
        # Importar configuração atual do app
        from app import UNIDADES, MEDICOS_POR_UNIDADE, EQUIPE_POR_UNIDADE
        app_config = {
            'unidades': UNIDADES,
            'medicos_por_unidade': MEDICOS_POR_UNIDADE,
            'equipe_por_unidade': EQUIPE_POR_UNIDADE
        }
        
        # Verificar se estão sincronizados
        file_units = set(file_config.get('unidades', []))
        app_units = set(app_config.get('unidades', []))
        
        is_synced = file_units == app_units
        
        response = {
            'status': 'success' if is_synced else 'warning',
            'is_synced': is_synced,
            'file_config': {
                'units_count': len(file_config.get('unidades', [])),
                'doctors_count': sum(len(docs) for docs in file_config.get('medicos_por_unidade', {}).values()),
                'team_count': sum(len(team) for team in file_config.get('equipe_por_unidade', {}).values())
            },
            'app_config': {
                'units_count': len(app_config.get('unidades', [])),
                'doctors_count': sum(len(docs) for docs in app_config.get('medicos_por_unidade', {}).values()),
                'team_count': sum(len(team) for team in app_config.get('equipe_por_unidade', {}).values())
            },
            'file_units': sorted(list(file_units)),
            'app_units': sorted(list(app_units))
        }
        
        if not is_synced:
            response['missing_in_app'] = sorted(list(file_units - app_units))
            response['extra_in_app'] = sorted(list(app_units - file_units))
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar configuração: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@admin_bp.route('/force_reload')
@admin_required
def force_reload():
    """Força o recarregamento das configurações"""
    try:
        config = load_config()
        if update_app_py(config):
            flash('✅ Configurações recarregadas com sucesso!', 'success')
        else:
            flash('⚠️ Houve problemas ao recarregar as configurações. Verifique os logs.', 'warning')
    except Exception as e:
        logger.error(f"❌ Erro ao forçar recarregamento: {e}")
        flash(f'❌ Erro ao recarregar configurações: {str(e)}', 'danger')
    
    return redirect(url_for('admin.dashboard'))