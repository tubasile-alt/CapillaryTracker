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
import uuid
from datetime import datetime
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
    """Salva a configuração de médicos e equipe com backup automático e verificação de integridade"""
    start_time = datetime.now()
    operation_id = str(uuid.uuid4())[:8]
    logger.info(f"🔄 [{operation_id}] Iniciando salvamento de configuração...")
    
    try:
        # Log estado inicial
        original_units = len(config.get('unidades', []))
        original_doctors = sum(len(docs) for docs in config.get('medicos_por_unidade', {}).values())
        original_team = sum(len(team) for team in config.get('equipe_por_unidade', {}).values())
        
        logger.info(f"📋 [{operation_id}] Estado inicial: {original_units} unidades, {original_doctors} médicos, {original_team} membros equipe")
        
        # Sempre sincronizar Uberlândia antes de salvar
        config = sync_uberlandia_teams(config)
        
        # Criar backup com timestamp
        backup_file = CONFIG_FILE.replace('.json', '_backup.json')
        timestamped_backup = CONFIG_FILE.replace('.json', f'_backup_{start_time.strftime("%Y%m%d_%H%M%S")}.json')
        
        if os.path.exists(CONFIG_FILE):
            try:
                # Backup principal
                shutil.copy2(CONFIG_FILE, backup_file)
                # Backup com timestamp
                shutil.copy2(CONFIG_FILE, timestamped_backup)
                logger.info(f"✅ [{operation_id}] Backups criados: {backup_file} e {timestamped_backup}")
            except Exception as e:
                logger.error(f"⚠️ [{operation_id}] Erro ao criar backup: {e}")
        
        # Salvar em arquivo temporário primeiro
        temp_file = CONFIG_FILE + '.tmp'
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # Verificar integridade do arquivo temporário
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 10:  # Pelo menos 10 bytes
                # Validar JSON
                with open(temp_file, 'r', encoding='utf-8') as f:
                    test_config = json.load(f)
                
                # Verificar se tem as estruturas necessárias
                if not all(key in test_config for key in ['unidades', 'medicos_por_unidade', 'equipe_por_unidade']):
                    raise ValueError("Estrutura JSON inválida")
                
                # Mover arquivo temporário para o arquivo final
                shutil.move(temp_file, CONFIG_FILE)
                
                # Verificar se o arquivo final foi criado corretamente
                final_size = os.path.getsize(CONFIG_FILE)
                logger.info(f"✅ [{operation_id}] Configuração salva: {CONFIG_FILE} ({final_size} bytes)")
                
                # Log estado final
                final_units = len(config.get('unidades', []))
                final_doctors = sum(len(docs) for docs in config.get('medicos_por_unidade', {}).values())
                final_team = sum(len(team) for team in config.get('equipe_por_unidade', {}).values())
                
                logger.info(f"📊 [{operation_id}] Estado final: {final_units} unidades, {final_doctors} médicos, {final_team} membros equipe")
                
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"⏱️ [{operation_id}] Salvamento concluído em {elapsed:.2f}s")
                
            else:
                raise Exception(f"Arquivo temporário inválido: {temp_file}")
                
        except Exception as temp_error:
            # Limpar arquivo temporário se existir
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            raise temp_error
            
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ [{operation_id}] ERRO CRÍTICO ao salvar configuração após {elapsed:.2f}s: {e}")
        logger.error(f"Traceback completo:\n{traceback.format_exc()}")
        
        # Tentar restaurar do backup se existir
        backup_file = CONFIG_FILE.replace('.json', '_backup.json')
        if os.path.exists(backup_file):
            try:
                shutil.copy2(backup_file, CONFIG_FILE)
                logger.info(f"🔄 [{operation_id}] Configuração restaurada do backup: {backup_file}")
            except Exception as restore_error:
                logger.error(f"❌ [{operation_id}] ERRO DUPLO - Falha ao restaurar backup: {restore_error}")
        
        # Re-raise para que a aplicação saiba que houve erro
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

    # Salvar configuração com verificação
    try:
        save_config(config)
        logger.info(f"✅ Configuração salva ao adicionar médico {nome}")
        
        # Atualizar app.py
        if update_app_py(config):
            flash(f'✅ DADOS SALVOS COM SUCESSO! Médico {nome} foi adicionado à unidade {unidade} e já está disponível no sistema.', 'success')
            logger.info(f"🎯 Médico {nome} adicionado e sistema atualizado")
        else:
            flash(f'⚠️ SALVAMENTO PARCIAL: Médico {nome} foi salvo no arquivo mas pode não aparecer imediatamente no sistema. Recarregue a página ou reinicie se necessário.', 'warning')
            logger.warning(f"⚠️ Médico {nome} salvo mas app.py não foi atualizado")
    except Exception as save_error:
        logger.error(f"❌ ERRO CRÍTICO ao salvar médico {nome}: {save_error}")
        flash(f'❌ DADOS NÃO FORAM SALVOS! Não foi possível adicionar o médico {nome}. Tente novamente. Erro técnico: {str(save_error)}', 'danger')

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

    # Salvar configuração com verificação
    try:
        save_config(config)
        logger.info(f"✅ Configuração salva ao remover médico {nome}")
        
        # Atualizar app.py
        if update_app_py(config):
            flash(f'✅ DADOS SALVOS COM SUCESSO! Médico {nome} foi removido da unidade {unidade} e a mudança já está ativa.', 'success')
            logger.info(f"🎯 Médico {nome} removido e sistema atualizado")
        else:
            flash(f'⚠️ SALVAMENTO PARCIAL: Médico {nome} foi removido do arquivo mas pode ainda aparecer temporariamente no sistema. Recarregue a página.', 'warning')
            logger.warning(f"⚠️ Médico {nome} removido mas app.py não foi atualizado")
    except Exception as save_error:
        logger.error(f"❌ ERRO CRÍTICO ao remover médico {nome}: {save_error}")
        flash(f'❌ DADOS NÃO FORAM SALVOS! Não foi possível remover o médico {nome}. O médico permanece no sistema. Tente novamente.', 'danger')

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

    # Salvar configuração com verificação
    try:
        save_config(config)
        logger.info(f"✅ Configuração salva ao adicionar membro {nome}")
        
        # Atualizar app.py
        if update_app_py(config):
            flash(f'✅ DADOS SALVOS COM SUCESSO! Membro {nome} foi adicionado à equipe da unidade {unidade} e já está disponível.', 'success')
            logger.info(f"🎯 Membro {nome} adicionado e sistema atualizado")
        else:
            flash(f'⚠️ SALVAMENTO PARCIAL: Membro {nome} foi salvo no arquivo mas pode não aparecer imediatamente na lista. Recarregue a página.', 'warning')
            logger.warning(f"⚠️ Membro {nome} salvo mas app.py não foi atualizado")
    except Exception as save_error:
        logger.error(f"❌ ERRO CRÍTICO ao salvar membro {nome}: {save_error}")
        flash(f'❌ DADOS NÃO FORAM SALVOS! Não foi possível adicionar {nome} à equipe. Tente novamente.', 'danger')

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

    # Salvar configuração com verificação
    try:
        save_config(config)
        logger.info(f"✅ Configuração salva ao remover membro {nome}")
        
        # Atualizar app.py
        if update_app_py(config):
            flash(f'✅ DADOS SALVOS COM SUCESSO! Membro {nome} foi removido da equipe da unidade {unidade}.', 'success')
            logger.info(f"🎯 Membro {nome} removido e sistema atualizado")
        else:
            flash(f'⚠️ SALVAMENTO PARCIAL: Membro {nome} foi removido do arquivo mas pode ainda aparecer temporariamente. Recarregue a página.', 'warning')
            logger.warning(f"⚠️ Membro {nome} removido mas app.py não foi atualizado")
    except Exception as save_error:
        logger.error(f"❌ ERRO CRÍTICO ao remover membro {nome}: {save_error}")
        flash(f'❌ DADOS NÃO FORAM SALVOS! Não foi possível remover {nome} da equipe. O membro permanece na lista. Tente novamente.', 'danger')

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
    
    # Salvar configuração com verificação
    try:
        save_config(config)
        logger.info(f"✅ Configuração salva ao adicionar unidade {nome}")
        
        # Atualizar app.py
        if update_app_py(config):
            flash(f'✅ DADOS SALVOS COM SUCESSO! Unidade {nome} foi criada e já está disponível no sistema.', 'success')
            logger.info(f"🎯 Unidade {nome} adicionada e sistema atualizado")
        else:
            flash(f'⚠️ SALVAMENTO PARCIAL: Unidade {nome} foi salva no arquivo mas pode não aparecer imediatamente nas listas. Recarregue a página.', 'warning')
            logger.warning(f"⚠️ Unidade {nome} salva mas app.py não foi atualizado")
    except Exception as save_error:
        logger.error(f"❌ ERRO CRÍTICO ao salvar unidade {nome}: {save_error}")
        flash(f'❌ DADOS NÃO FORAM SALVOS! Não foi possível criar a unidade {nome}. Tente novamente.', 'danger')
    
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
    
    # Salvar configuração com verificação
    try:
        save_config(config)
        logger.info(f"✅ Configuração salva ao remover unidade {nome}")
        
        # Atualizar app.py
        if update_app_py(config):
            flash(f'✅ DADOS SALVOS COM SUCESSO! Unidade {nome} foi removida completamente do sistema.', 'success')
            logger.info(f"🎯 Unidade {nome} removida e sistema atualizado")
        else:
            flash(f'⚠️ SALVAMENTO PARCIAL: Unidade {nome} foi removida do arquivo mas pode ainda aparecer temporariamente. Recarregue a página.', 'warning')
            logger.warning(f"⚠️ Unidade {nome} removida mas app.py não foi atualizado")
    except Exception as save_error:
        logger.error(f"❌ ERRO CRÍTICO ao remover unidade {nome}: {save_error}")
        flash(f'❌ DADOS NÃO FORAM SALVOS! Não foi possível remover a unidade {nome}. A unidade permanece no sistema. Tente novamente.', 'danger')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/monitor_changes')
@admin_required
def monitor_changes():
    """Monitora mudanças e verifica integridade dos dados"""
    try:
        # Verificar integridade dos arquivos
        results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'files_check': {},
            'app_sync': {},
            'recommendations': []
        }
        
        # 1. Verificar arquivo principal
        if os.path.exists(CONFIG_FILE):
            size = os.path.getsize(CONFIG_FILE)
            results['files_check']['main_file'] = {
                'exists': True,
                'size': size,
                'status': 'OK' if size > 50 else 'PROBLEMA - Arquivo muito pequeno'
            }
        else:
            results['files_check']['main_file'] = {
                'exists': False,
                'status': 'CRÍTICO - Arquivo não encontrado'
            }
            results['recommendations'].append('Arquivo de configuração principal não encontrado!')
        
        # 2. Verificar backup
        backup_file = CONFIG_FILE.replace('.json', '_backup.json')
        if os.path.exists(backup_file):
            backup_size = os.path.getsize(backup_file)
            results['files_check']['backup_file'] = {
                'exists': True,
                'size': backup_size,
                'status': 'OK' if backup_size > 50 else 'PROBLEMA'
            }
        else:
            results['files_check']['backup_file'] = {
                'exists': False,
                'status': 'AVISO - Sem backup recente'
            }
        
        # 3. Verificar sincronização com app
        try:
            file_config = load_config()
            from app import UNIDADES, MEDICOS_POR_UNIDADE, EQUIPE_POR_UNIDADE
            
            file_units = set(file_config.get('unidades', []))
            app_units = set(UNIDADES)
            
            results['app_sync'] = {
                'file_units': len(file_units),
                'app_units': len(app_units),
                'synchronized': file_units == app_units,
                'missing_in_app': list(file_units - app_units),
                'extra_in_app': list(app_units - file_units)
            }
            
            if not results['app_sync']['synchronized']:
                results['recommendations'].append('Dados do arquivo e aplicação não estão sincronizados!')
                
        except Exception as sync_error:
            results['app_sync']['error'] = str(sync_error)
            results['recommendations'].append(f'Erro na verificação de sincronização: {sync_error}')
        
        # 4. Recomendações finais
        if not results['recommendations']:
            results['recommendations'].append('✅ Todos os sistemas estão funcionando corretamente')
        
        return jsonify({
            'status': 'success',
            'data': results
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no monitoramento: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@admin_bp.route('/health_check')
def health_check():
    """Verificação rápida de saúde do sistema"""
    try:
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'config_file': os.path.exists(CONFIG_FILE),
            'backup_file': os.path.exists(CONFIG_FILE.replace('.json', '_backup.json')),
            'can_load_config': False,
            'app_responsive': True
        }
        
        # Tentar carregar configuração
        try:
            config = load_config()
            health_status['can_load_config'] = bool(config and len(config.get('unidades', [])) > 0)
            health_status['units_count'] = len(config.get('unidades', []))
        except:
            health_status['can_load_config'] = False
            
        overall_health = all([
            health_status['config_file'],
            health_status['can_load_config'],
            health_status['app_responsive']
        ])
        
        return jsonify({
            'status': 'healthy' if overall_health else 'unhealthy',
            'details': health_status
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@admin_bp.route('/verify_config', methods=['GET'])
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