"""
NOVA VERSÃO SIMPLIFICADA DO MÓDULO ADMINISTRATIVO
Sistema de administração reformulado do zero para usar banco de dados PostgreSQL
diretamente, garantindo persistência real dos dados.
"""

import logging
import traceback
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import functools

# Configurar logging
logger = logging.getLogger(__name__)

# Criar Blueprint para rotas administrativas
admin_bp = Blueprint('admin', __name__)

# Decorador para proteção de rotas administrativas
def admin_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"Verificando sessão admin: {session.get('admin_logged_in', 'Não encontrado')}")
        if 'admin_logged_in' not in session:
            logger.warning("Redirecionando para login - sessão não encontrada")
            return redirect(url_for('admin.login'))
        logger.info("Acesso administrativo autorizado")
        return f(*args, **kwargs)
    return decorated_function

# ROTAS DE AUTENTICAÇÃO
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login administrativo"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '12345':  # Senha simples para administração
            session['admin_logged_in'] = True
            logger.info("Admin login realizado com sucesso")
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Senha incorreta!', 'danger')
            logger.warning("Tentativa de login administrativo com senha incorreta")
    
    return render_template('admin_login.html')

@admin_bp.route('/logout')
def logout():
    """Logout administrativo"""
    session.pop('admin_logged_in', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))

# DASHBOARD PRINCIPAL
@admin_bp.route('/')
@admin_required 
def dashboard():
    """Dashboard administrativo principal"""
    try:
        logger.info("Carregando dashboard administrativo...")
        
        from app import load_admin_config
        
        # Carregar configuração atual do JSON
        config = load_admin_config()
        
        # Converter para formato compatível com o template
        units = []
        for unit_name in config.get('unidades', []):
            units.append({'name': unit_name, 'id': unit_name})
        
        doctors_by_unit = config.get('medicos_por_unidade', {})
        teams_by_unit = config.get('equipe_por_unidade', {})
        
        logger.info(f"Dashboard carregado com {len(units)} unidades")
        
        return render_template('admin_new.html', 
                             units=units,
                             doctors_by_unit=doctors_by_unit,
                             teams_by_unit=teams_by_unit)
        
    except Exception as e:
        logger.error(f"Erro ao carregar dashboard: {e}")
        # Retornar mensagem simples em caso de erro
        return f"<h1>Painel Administrativo</h1><p>Erro: {str(e)}</p><p>Unidades: {config.get('unidades', [])}</p>"

# GESTÃO DE UNIDADES
@admin_bp.route('/add_unit', methods=['POST'])
@admin_required
def add_unit():
    """Adiciona nova unidade usando sistema JSON"""
    try:
        from app import load_admin_config
        import json
        
        name = request.form.get('name', '').strip()
        
        if not name:
            flash('Nome da unidade é obrigatório!', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        # Carregar configuração atual
        config = load_admin_config()
        
        # Verificar se unidade já existe
        if name in config.get('unidades', []):
            flash(f'A unidade "{name}" já existe!', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        # Adicionar nova unidade
        config['unidades'].append(name)
        config['medicos_por_unidade'][name] = []
        config['equipe_por_unidade'][name] = []
        
        # Salvar configuração
        with open('admin_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        flash(f'Unidade "{name}" criada com sucesso!', 'success')
        logger.info(f"Nova unidade criada: {name}")
        
    except Exception as e:
        logger.error(f"Erro ao adicionar unidade: {e}")
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        flash('Erro ao criar unidade. Tente novamente.', 'danger')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete_unit', methods=['POST'])
@admin_required
def delete_unit():
    """Remove unidade (desativa)"""
    try:
        from app import Unit, Doctor, TeamMember, db
        
        unit_id = request.form.get('unit_id')
        
        if not unit_id:
            flash('ID da unidade é obrigatório!', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        unit = Unit.query.get(unit_id)
        if not unit:
            flash('Unidade não encontrada!', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        # Desativar unidade e todos médicos/equipe relacionados
        unit.is_active = False
        unit.updated_at = datetime.utcnow()
        
        # Desativar médicos da unidade
        Doctor.query.filter_by(unit_id=unit_id).update({
            'is_active': False,
            'updated_at': datetime.utcnow()
        })
        
        # Desativar membros da equipe
        TeamMember.query.filter_by(unit_id=unit_id).update({
            'is_active': False,
            'updated_at': datetime.utcnow()
        })
        
        db.session.commit()
        
        flash(f'Unidade "{unit.name}" removida com sucesso!', 'success')
        logger.info(f"Unidade {unit.name} desativada")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao remover unidade: {e}")
        flash('Erro ao remover unidade. Tente novamente.', 'danger')
    
    return redirect(url_for('admin.dashboard'))

# GESTÃO DE MÉDICOS
@admin_bp.route('/add_doctor', methods=['POST'])
@admin_required
def add_doctor():
    """Adiciona novo médico"""
    try:
        from app import Unit, Doctor, db
        
        name = request.form.get('name', '').strip()
        unit_id = request.form.get('unit_id')
        
        if not name or not unit_id:
            flash('Nome do médico e unidade são obrigatórios!', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        # Verificar se unidade existe
        unit = Unit.query.get(unit_id)
        if not unit:
            flash('Unidade não encontrada!', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        # Verificar se médico já existe na unidade
        existing = Doctor.query.filter_by(name=name, unit_id=unit_id).first()
        if existing:
            if existing.is_active:
                flash(f'O médico "{name}" já existe na unidade "{unit.name}"!', 'danger')
            else:
                # Reativar médico
                existing.is_active = True
                existing.updated_at = datetime.utcnow()
                db.session.commit()
                flash(f'Médico "{name}" reativado na unidade "{unit.name}"!', 'success')
                logger.info(f"Médico {name} reativado na unidade {unit.name}")
            return redirect(url_for('admin.dashboard'))
        
        # Criar novo médico
        new_doctor = Doctor(name=name, unit_id=unit_id)
        db.session.add(new_doctor)
        db.session.commit()
        
        flash(f'Médico "{name}" adicionado à unidade "{unit.name}" com sucesso!', 'success')
        logger.info(f"Novo médico criado: {name} na unidade {unit.name}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao adicionar médico: {e}")
        flash('Erro ao adicionar médico. Tente novamente.', 'danger')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete_doctor', methods=['POST'])
@admin_required
def delete_doctor():
    """Remove médico (desativa)"""
    try:
        from app import Doctor, db
        
        doctor_id = request.form.get('doctor_id')
        
        if not doctor_id:
            flash('ID do médico é obrigatório!', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            flash('Médico não encontrado!', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        # Desativar médico
        doctor.is_active = False
        doctor.updated_at = datetime.utcnow()
        db.session.commit()
        
        unit_name = doctor.unit_obj.name if doctor.unit_obj else "Unidade desconhecida"
        flash(f'Médico "{doctor.name}" removido da unidade "{unit_name}" com sucesso!', 'success')
        logger.info(f"Médico {doctor.name} desativado da unidade {unit_name}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao remover médico: {e}")
        flash('Erro ao remover médico. Tente novamente.', 'danger')
    
    return redirect(url_for('admin.dashboard'))

# GESTÃO DE EQUIPE
@admin_bp.route('/add_team_member', methods=['POST'])
@admin_required
def add_team_member():
    """Adiciona novo membro da equipe"""
    try:
        from app import Unit, TeamMember, db
        
        name = request.form.get('name', '').strip()
        unit_id = request.form.get('unit_id')
        
        if not name or not unit_id:
            flash('Nome do membro da equipe e unidade são obrigatórios!', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        # Verificar se unidade existe
        unit = Unit.query.get(unit_id)
        if not unit:
            flash('Unidade não encontrada!', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        # Verificar se membro já existe na unidade
        existing = TeamMember.query.filter_by(name=name, unit_id=unit_id).first()
        if existing:
            if existing.is_active:
                flash(f'O membro "{name}" já existe na equipe da unidade "{unit.name}"!', 'danger')
            else:
                # Reativar membro
                existing.is_active = True
                existing.updated_at = datetime.utcnow()
                db.session.commit()
                flash(f'Membro "{name}" reativado na equipe da unidade "{unit.name}"!', 'success')
                logger.info(f"Membro {name} reativado na unidade {unit.name}")
            return redirect(url_for('admin.dashboard'))
        
        # Criar novo membro
        new_member = TeamMember(name=name, unit_id=unit_id)
        db.session.add(new_member)
        db.session.commit()
        
        flash(f'Membro "{name}" adicionado à equipe da unidade "{unit.name}" com sucesso!', 'success')
        logger.info(f"Novo membro criado: {name} na unidade {unit.name}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao adicionar membro da equipe: {e}")
        flash('Erro ao adicionar membro da equipe. Tente novamente.', 'danger')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete_team_member', methods=['POST'])
@admin_required
def delete_team_member():
    """Remove membro da equipe (desativa)"""
    try:
        from app import TeamMember, db
        
        member_id = request.form.get('member_id')
        
        if not member_id:
            flash('ID do membro da equipe é obrigatório!', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        member = TeamMember.query.get(member_id)
        if not member:
            flash('Membro da equipe não encontrado!', 'danger')
            return redirect(url_for('admin.dashboard'))
        
        # Desativar membro
        member.is_active = False
        member.updated_at = datetime.utcnow()
        db.session.commit()
        
        unit_name = member.unit_obj.name if member.unit_obj else "Unidade desconhecida"
        flash(f'Membro "{member.name}" removido da equipe da unidade "{unit_name}" com sucesso!', 'success')
        logger.info(f"Membro {member.name} desativado da unidade {unit_name}")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao remover membro da equipe: {e}")
        flash('Erro ao remover membro da equipe. Tente novamente.', 'danger')
    
    return redirect(url_for('admin.dashboard'))

# API PARA CARREGAR DADOS DINAMICAMENTE
@admin_bp.route('/api/units')
@admin_required
def api_units():
    """API para obter lista de unidades"""
    try:
        from app import Unit
        units = Unit.query.filter_by(is_active=True).order_by(Unit.name).all()
        return jsonify({
            'success': True,
            'units': [unit.to_dict() for unit in units]
        })
    except Exception as e:
        logger.error(f"Erro na API de unidades: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/doctors/<int:unit_id>')
@admin_required
def api_doctors(unit_id):
    """API para obter médicos de uma unidade"""
    try:
        from app import Doctor
        doctors = Doctor.query.filter_by(unit_id=unit_id, is_active=True).order_by(Doctor.name).all()
        return jsonify({
            'success': True,
            'doctors': [doctor.to_dict() for doctor in doctors]
        })
    except Exception as e:
        logger.error(f"Erro na API de médicos: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/api/team_members/<int:unit_id>')
@admin_required
def api_team_members(unit_id):
    """API para obter membros da equipe de uma unidade"""
    try:
        from app import TeamMember
        members = TeamMember.query.filter_by(unit_id=unit_id, is_active=True).order_by(TeamMember.name).all()
        return jsonify({
            'success': True,
            'team_members': [member.to_dict() for member in members]
        })
    except Exception as e:
        logger.error(f"Erro na API de membros da equipe: {e}")
        return jsonify({'success': False, 'error': str(e)})

# MIGRAÇÃO DE DADOS
@admin_bp.route('/migrate_data')
@admin_required
def migrate_data():
    """Migra dados do sistema JSON para o banco PostgreSQL"""
    try:
        from app import migrate_admin_data
        
        # Chama a função de migração do app principal
        result = migrate_admin_data()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro na migração de dados: {e}")
        return jsonify({
            'success': False,
            'error': f"Erro na migração: {str(e)}"
        })

# STATUS DO SISTEMA
@admin_bp.route('/status')
@admin_required
def system_status():
    """Status do sistema administrativo"""
    try:
        from app import Unit, Doctor, TeamMember, db
        
        # Estatísticas do sistema
        total_units = Unit.query.filter_by(is_active=True).count()
        total_doctors = Doctor.query.filter_by(is_active=True).count()
        total_members = TeamMember.query.filter_by(is_active=True).count()
        
        return jsonify({
            'success': True,
            'system_status': 'healthy',
            'database_status': 'connected',
            'statistics': {
                'total_units': total_units,
                'total_doctors': total_doctors,
                'total_team_members': total_members
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar status do sistema: {e}")
        return jsonify({
            'success': False,
            'system_status': 'error',
            'error': str(e)
        })