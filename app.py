import os
import logging
import traceback
import re
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
import functools
import pandas as pd
from openpyxl.utils.dataframe import dataframe_to_rows
import numpy as np
from datetime import datetime, date
from fuzzywuzzy import fuzz
import json
from flask_sqlalchemy import SQLAlchemy
import shutil
from sqlalchemy import text, extract
import dropbox
import io
from werkzeug.utils import secure_filename
import uuid
import mimetypes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting Flask application...")

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['ADMIN_PASSWORD'] = '12345'
app.config['UPLOAD_FOLDER'] = 'static/uploads/necrose_photos'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Função para carregar configurações do arquivo JSON
def load_admin_config():
    """Carrega configurações de unidades, médicos e equipe do arquivo admin_config.json"""
    config_file = 'admin_config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except Exception as e:
            logger.error(f"Erro ao carregar admin_config.json: {e}")
    
    # Configuração padrão se o arquivo não existir
    return {
        'unidades': ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro', 'São Paulo', 'Brasília', 'Goiania'],
        'medicos_por_unidade': {
            'Ribeirão Preto': ['Dr. Arthur', 'Dr. Daniel'],
            'Campinas': ['Dra. Adriana', 'Dra. Isadora'],
            'Rio de Janeiro': ['Dra. Ana Clara', 'Dra. Paula'],
            'São Paulo': ['Dr. Daniel', 'Dr. Renan', 'Dra. Ariane', 'Dra. Isabella', 'Dra. Talita', 'Dra. Thaiza'],
            'Brasília': ['Dra. Leticia', 'Dra. Natalia'],
            'Goiania': []
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
            'Brasília': ['Angélica Sousa', 'Betânia Almeida', 'Dayse Fernandes', 'Layla Cardoso', 'Thamara Maciel'],
            'Goiania': []
        }
    }

# Carregar configurações dinamicamente
def reload_admin_config():
    """Recarrega as configurações administrativas"""
    global UNIDADES, MEDICOS_POR_UNIDADE, EQUIPE_POR_UNIDADE
    admin_config = load_admin_config()
    UNIDADES = admin_config.get('unidades', ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro', 'São Paulo', 'Brasília'])
    MEDICOS_POR_UNIDADE = admin_config.get('medicos_por_unidade', {})
    EQUIPE_POR_UNIDADE = admin_config.get('equipe_por_unidade', {})
    logger.info(f"Configurações recarregadas: {len(UNIDADES)} unidades, {len(MEDICOS_POR_UNIDADE)} grupos de médicos")

# Inicializar configurações
reload_admin_config()

# Importar e registrar blueprints após as configurações da app
from admin_routes import admin_bp
app.register_blueprint(admin_bp, url_prefix='/admin')

# Configure SQLAlchemy with detailed logging and connection settings
database_url = os.environ.get('DATABASE_URL', None)

# Se estamos em ambiente de deploy e não temos DATABASE_URL, use a conexão Neon
if database_url is None:
    # Configuração padrão para ambiente de deploy
    database_url = 'postgresql://neondb_owner:npg_BoiquUY6v8CN@ep-flat-salad-a4j7rvot.us-east-1.aws.neon.tech/neondb?sslmode=require'
    logger.info(f"⚠️ DATABASE_URL não encontrada. Usando configuração padrão para deploy.")

# Transformar URLs postgres:// em postgresql://
if database_url and database_url.startswith('postgres://'):
    # Handle Heroku-style PostgreSQL URLs
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 299
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 20
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 299,
    'pool_timeout': 20,
    'pool_size': 5,
    'max_overflow': 10
}

# Log database connection info
logger.info(f"📌 Database URL in use: {app.config['SQLALCHEMY_DATABASE_URI']}")
if database_url and database_url.startswith('postgres://'):
    logger.warning("Converting postgres:// to postgresql:// in database URL")
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 30,
    'pool_size': 5,
    'max_overflow': 10,
    'connect_args': {}
}

db = SQLAlchemy(app)

# Define models
class Surgery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date)
    nome = db.Column(db.String(255))
    unidade = db.Column(db.String(100))
    medico = db.Column(db.String(100))
    equipe = db.Column(db.String(255))
    hora_cirurgia = db.Column(db.String(5))
    tempo_cirurgia = db.Column(db.Float)
    total_foliculos = db.Column(db.Integer)
    frente = db.Column(db.Integer)
    densidade_scketh = db.Column(db.Float)
    coroa = db.Column(db.Integer)
    scalpe = db.Column(db.Integer)
    peninsula_direita = db.Column(db.Integer)
    peninsula_esquerda = db.Column(db.Integer)
    # Campos de quadrantes
    q1_area = db.Column(db.Float)
    q1_furos = db.Column(db.Integer)
    q1_fios = db.Column(db.Integer)
    q1_densidade = db.Column(db.Float)
    q1_taxa_quebra = db.Column(db.Float)
    q2_area = db.Column(db.Float)
    q2_furos = db.Column(db.Integer)
    q2_fios = db.Column(db.Integer)
    q2_densidade = db.Column(db.Float)
    q2_taxa_quebra = db.Column(db.Float)
    q3_area = db.Column(db.Float)
    q3_furos = db.Column(db.Integer)
    q3_fios = db.Column(db.Integer)
    q3_densidade = db.Column(db.Float)
    q3_taxa_quebra = db.Column(db.Float)
    q4_area = db.Column(db.Float)
    q4_furos = db.Column(db.Integer)
    q4_fios = db.Column(db.Integer)
    q4_densidade = db.Column(db.Float)
    q4_taxa_quebra = db.Column(db.Float)
    densidade_extracao = db.Column(db.Float)
    # Campos da segunda página do formulário
    infiltracao = db.Column(db.String(255))
    sedacao = db.Column(db.String(255))
    sangramento = db.Column(db.String(255))
    tadalafila = db.Column(db.String(255))
    bloqueio_seringas = db.Column(db.String(255))
    fonte_1 = db.Column(db.String(255))
    fonte_2 = db.Column(db.String(255))
    fonte_3 = db.Column(db.String(255))
    fonte_4 = db.Column(db.String(255))
    fonte_5 = db.Column(db.String(255))
    pelos_corporais = db.Column(db.String(255))
    # Body hair detailed fields
    barba_furos = db.Column(db.Integer, default=0)
    barba_fios = db.Column(db.Integer, default=0)
    barba_comentarios = db.Column(db.Text, default='')
    peitoral_furos = db.Column(db.Integer, default=0)
    peitoral_fios = db.Column(db.Integer, default=0)
    peitoral_comentarios = db.Column(db.Text, default='')
    abdome_furos = db.Column(db.Integer, default=0)
    abdome_fios = db.Column(db.Integer, default=0)
    abdome_comentarios = db.Column(db.Text, default='')
    pernas_furos = db.Column(db.Integer, default=0)
    pernas_fios = db.Column(db.Integer, default=0)
    pernas_comentarios = db.Column(db.Text, default='')
    tecnica = db.Column(db.String(255))
    solucao_frente = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UnitProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unidade = db.Column(db.String(100), unique=True)
    meta = db.Column(db.Integer)

class Necrose(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    surgery_id = db.Column(db.Integer, db.ForeignKey('surgery.id'), nullable=False)
    unidade = db.Column(db.String(100), nullable=False)
    paciente_nome = db.Column(db.String(255), nullable=False)
    data_cirurgia = db.Column(db.Date, nullable=False)
    data_avaliacao = db.Column(db.Date, nullable=False)
    medico_responsavel = db.Column(db.String(100))
    
    # Dados de necrose
    tem_necrose = db.Column(db.Boolean, default=False)
    grau_necrose = db.Column(db.String(50))  # Leve, Moderada, Severa
    localizacao = db.Column(db.Text)  # Área afetada
    numero_necroses = db.Column(db.Integer, default=1)  # Número de necroses
    tamanho_1_cm = db.Column(db.Float)  # Tamanho da 1ª necrose em cm
    tamanho_2_cm = db.Column(db.Float)  # Tamanho da 2ª necrose em cm (se houver)
    tamanho_3_cm = db.Column(db.Float)  # Tamanho da 3ª necrose em cm (se houver)
    tamanho_4_cm = db.Column(db.Float)  # Tamanho da 4ª necrose em cm (se houver)
    
    # Regiões acometidas (múltiplas possíveis)
    primeira_faixa = db.Column(db.Boolean, default=False)
    segunda_faixa = db.Column(db.Boolean, default=False)
    terceira_faixa = db.Column(db.Boolean, default=False)
    coroa = db.Column(db.Boolean, default=False)
    descricao = db.Column(db.Text)
    tratamento_aplicado = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    
    # Campos de acompanhamento
    status = db.Column(db.String(50), default='Em acompanhamento')  # Em acompanhamento, Resolvida, etc.
    data_resolucao = db.Column(db.Date)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento
    surgery = db.relationship('Surgery', backref='necroses')

class NecrosePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    necrose_id = db.Column(db.Integer, db.ForeignKey('necrose.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    necrose = db.relationship('Necrose', backref='photos')

# Configure Flask-Migrate
from flask_migrate import Migrate

# Initialize Flask-Migrate with app and db
migrate = Migrate(app, db)
logger.info("✅ Flask-Migrate initialized")

# ===============================
# DROPBOX BACKUP FUNCTIONALITY
# ===============================

def trigger_automatic_backup():
    """
    Dispara backup automático com múltiplas estratégias (Dropbox + local)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        logger.info("🔄 Iniciando backup automático multicanal...")
        
        # Buscar todos os dados para backup
        surgeries = Surgery.query.order_by(Surgery.data.desc()).all()
        necroses = Necrose.query.order_by(Necrose.data_avaliacao.desc()).all()
        
        if not surgeries:
            return False, "Nenhum dado de cirurgia encontrado para backup"
        
        # Criar DataFrame com dados de cirurgias
        surgery_data = []
        for surgery in surgeries:
            surgery_dict = {
                'ID': surgery.id,
                'Data': surgery.data.strftime('%d/%m/%Y') if surgery.data else '',
                'Nome': surgery.nome,
                'Unidade': surgery.unidade,
                'Médico': surgery.medico,
                'Equipe': surgery.equipe,
                'Total_Folículos': surgery.total_foliculos,
                'Densidade_Extração': getattr(surgery, 'densidade_extracao', ''),
                'Densidade_Sketch': getattr(surgery, 'densidade_scketh', ''),
                'Sangramento': surgery.sangramento,
                'Infiltração': surgery.infiltracao,
                'Técnica': surgery.tecnica,
                'Tempo_Cirurgia': surgery.tempo_cirurgia,
                'Q1_Fios': getattr(surgery, 'q1_fios', ''),
                'Q1_Furos': getattr(surgery, 'q1_furos', ''),
                'Q2_Fios': getattr(surgery, 'q2_fios', ''),
                'Q2_Furos': getattr(surgery, 'q2_furos', ''),
                'Q3_Fios': getattr(surgery, 'q3_fios', ''),
                'Q3_Furos': getattr(surgery, 'q3_furos', ''),
                'Q4_Fios': getattr(surgery, 'q4_fios', ''),
                'Q4_Furos': getattr(surgery, 'q4_furos', ''),
                'Tadalafila': surgery.tadalafila,
                'Solução_Frente': surgery.solucao_frente,
                'Pelos_Corporais': getattr(surgery, 'pelos_corporais', ''),
                'Created_At': surgery.created_at.strftime('%d/%m/%Y %H:%M') if surgery.created_at else ''
            }
            surgery_data.append(surgery_dict)
        
        # Criar DataFrame com dados de necroses
        necrose_data = []
        for necrose in necroses:
            necrose_dict = {
                'ID': necrose.id,
                'Surgery_ID': necrose.surgery_id,
                'Paciente': necrose.paciente_nome,
                'Unidade': necrose.unidade,
                'Data_Cirurgia': necrose.data_cirurgia.strftime('%d/%m/%Y') if necrose.data_cirurgia else '',
                'Data_Avaliação': necrose.data_avaliacao.strftime('%d/%m/%Y') if necrose.data_avaliacao else '',
                'Médico_Responsável': necrose.medico_responsavel,
                'Tem_Necrose': necrose.tem_necrose,
                'Número_Necroses': necrose.numero_necroses,
                'Grau_Necrose': necrose.grau_necrose,
                'Primeira_Faixa': necrose.primeira_faixa,
                'Segunda_Faixa': necrose.segunda_faixa,
                'Terceira_Faixa': necrose.terceira_faixa,
                'Coroa': necrose.coroa,
                'Tamanho_1_cm': necrose.tamanho_1_cm,
                'Tamanho_2_cm': necrose.tamanho_2_cm,
                'Tamanho_3_cm': necrose.tamanho_3_cm,
                'Tamanho_4_cm': necrose.tamanho_4_cm,
                'Status': necrose.status,
                'Created_At': necrose.created_at.strftime('%d/%m/%Y %H:%M') if necrose.created_at else '',
                'Updated_At': necrose.updated_at.strftime('%d/%m/%Y %H:%M') if necrose.updated_at else ''
            }
            necrose_data.append(necrose_dict)
        
        # Criar timestamp para backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # ESTRATÉGIA 1: Backup Local (sempre funciona)
        local_backup_success = create_local_backup(surgery_data, necrose_data, timestamp)
        
        # ESTRATÉGIA 2: Backup Dropbox (se token válido)
        dropbox_backup_success = create_dropbox_backup(surgery_data, necrose_data, timestamp)
        
        # Resultado final
        if local_backup_success and dropbox_backup_success:
            return True, f"Backup completo (Local + Dropbox) - {timestamp}"
        elif local_backup_success:
            return True, f"Backup local realizado - {timestamp} (Dropbox indisponível)"
        elif dropbox_backup_success:
            return True, f"Backup Dropbox realizado - {timestamp} (Local falhou)"
        else:
            return False, "Falha em todos os backups"
            
    except Exception as e:
        logger.error(f"Erro no backup automático: {e}")
        return False, f"Erro: {str(e)}"

def create_local_backup(surgery_data, necrose_data, timestamp):
    """Criar backup local em Excel"""
    try:
        # Garantir que diretório existe
        backup_dir = 'data_backup'
        os.makedirs(backup_dir, exist_ok=True)
        
        # Nome do arquivo local
        local_filename = f"{backup_dir}/backup_automatico_{timestamp}.xlsx"
        
        # Criar arquivo Excel com múltiplas planilhas
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        # Usar openpyxl para criar múltiplas planilhas
        from openpyxl import Workbook
        wb = Workbook()
        
        # Planilha de pacientes (dados de cirurgia)
        ws_pacientes = wb.active
        ws_pacientes.title = "Pacientes"
        if surgery_data:
            surgery_df = pd.DataFrame(surgery_data)
            for row in dataframe_to_rows(surgery_df, index=False, header=True):
                ws_pacientes.append(row)
        
        # Planilha de necroses
        if necrose_data:
            ws_necroses = wb.create_sheet(title="Necroses")
            necrose_df = pd.DataFrame(necrose_data)
            for row in dataframe_to_rows(necrose_df, index=False, header=True):
                ws_necroses.append(row)
        
        # Salvar arquivo
        wb.save(local_filename)
        
        logger.info(f"💾 Backup local criado: {local_filename}")
        return True
        
    except Exception as e:
        logger.error(f"Erro no backup local: {e}")
        return False

def create_dropbox_backup(surgery_data, necrose_data, timestamp):
    """Criar backup no Dropbox"""
    try:
        # Verificar token
        dropbox_token = os.environ.get('DROPBOX_ACCESS_TOKEN')
        if not dropbox_token:
            logger.warning("Token Dropbox não configurado")
            return False
        
        # Criar arquivo Excel temporário
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        # Criar workbook
        from openpyxl import Workbook
        wb = Workbook()
        
        # Planilha de pacientes (dados de cirurgia)
        ws_pacientes = wb.active
        ws_pacientes.title = "Pacientes"
        if surgery_data:
            surgery_df = pd.DataFrame(surgery_data)
            for row in dataframe_to_rows(surgery_df, index=False, header=True):
                ws_pacientes.append(row)
        
        # Planilha de necroses
        if necrose_data:
            ws_necroses = wb.create_sheet(title="Necroses")
            necrose_df = pd.DataFrame(necrose_data)
            for row in dataframe_to_rows(necrose_df, index=False, header=True):
                ws_necroses.append(row)
        
        # Salvar arquivo temporário
        wb.save(temp_filename)
        
        # Upload para Dropbox
        dbx = dropbox.Dropbox(dropbox_token)
        
        with open(temp_filename, 'rb') as f:
            excel_content = f.read()
        
        # Nome do arquivo no Dropbox
        dropbox_path = f"/backup_automatico_{timestamp}.xlsx"
        
        dbx.files_upload(
            excel_content,
            dropbox_path,
            mode=dropbox.files.WriteMode.overwrite
        )
        
        # Limpar arquivo temporário
        os.unlink(temp_filename)
        
        logger.info(f"☁️ Backup Dropbox criado: {dropbox_path}")
        return True
        
    except Exception as e:
        logger.error(f"Erro no backup Dropbox: {e}")
        return False

def export_and_backup(df=None):
    """
    Exporta DataFrame para Excel e faz backup automático no Dropbox.
    
    Args:
        df: DataFrame para backup. Se None, busca todos os dados do banco.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Verificar se o token do Dropbox está configurado
        dropbox_token = os.environ.get('DROPBOX_ACCESS_TOKEN')
        if not dropbox_token:
            logger.warning("DROPBOX_ACCESS_TOKEN não configurado - backup desabilitado")
            return False, "Token do Dropbox não configurado"
        
        # Limpar e validar o token
        dropbox_token = dropbox_token.strip().replace('\\t', '').replace('\t', '').replace('\n', '').replace('\r', '').replace(' ', '')
        
        # Validação básica do comprimento do token
        if len(dropbox_token) < 10:
            logger.error(f"Token do Dropbox muito curto - comprimento: {len(dropbox_token)}")
            return False, "Token do Dropbox muito curto"
        
        logger.info(f"Token validado - comprimento: {len(dropbox_token)}, inicia com: {dropbox_token[:4]}...")
        
        # Se não foi fornecido DataFrame, buscar todos os dados do banco
        if df is None:
            logger.info("Buscando dados do banco para backup...")
            surgeries = Surgery.query.order_by(Surgery.data.desc()).all()
            
            if not surgeries:
                logger.info("Nenhum dado encontrado no banco para backup")
                return False, "Nenhum dado encontrado para backup"
            
            # Converter dados do banco para DataFrame usando EXATAMENTE o mesmo formato do download_complete_data
            data_list = []
            for surgery in surgeries:
                surgery_dict = {
                    'ID': surgery.id,
                    'Data': surgery.data.strftime('%d/%m/%Y') if surgery.data else '',
                    'Paciente': surgery.nome or '',
                    'Unidade': surgery.unidade or '',
                    'Médico': surgery.medico or '',
                    'Equipe': surgery.equipe or '',
                    'Hora da Cirurgia': surgery.hora_cirurgia or '',
                    'Tempo de Cirurgia (horas)': surgery.tempo_cirurgia or 0,
                    'Total de Folículos': surgery.total_foliculos or 0,
                    'Frente': surgery.frente or 0,
                    'Densidade Scketh': surgery.densidade_scketh or 0,
                    'Coroa': surgery.coroa or 0,
                    'Scalpe': surgery.scalpe or 0,
                    'Península Direita': surgery.peninsula_direita or 0,
                    'Península Esquerda': surgery.peninsula_esquerda or 0,
                    'Infiltração': surgery.infiltracao or '',
                    'Sedação': getattr(surgery, 'sedacao', '') or '',
                    'Sangramento': getattr(surgery, 'sangramento', '') or '',
                    'Tadalafila': surgery.tadalafila or '',
                    'Bloqueio de Seringas': surgery.bloqueio_seringas or '',
                    'Fonte 1': surgery.fonte_1 or '',
                    'Fonte 2': surgery.fonte_2 or '',
                    'Fonte 3': surgery.fonte_3 or '',
                    'Fonte 4': surgery.fonte_4 or '',
                    'Fonte 5': surgery.fonte_5 or '',
                    'Pelos Corporais': surgery.pelos_corporais or '',
                    # Body hair detailed fields
                    'Barba Furos': getattr(surgery, 'barba_furos', 0) or 0,
                    'Barba Fios': getattr(surgery, 'barba_fios', 0) or 0,
                    'Barba Comentários': getattr(surgery, 'barba_comentarios', '') or '',
                    'Peitoral Furos': getattr(surgery, 'peitoral_furos', 0) or 0,
                    'Peitoral Fios': getattr(surgery, 'peitoral_fios', 0) or 0,
                    'Peitoral Comentários': getattr(surgery, 'peitoral_comentarios', '') or '',
                    'Abdome Furos': getattr(surgery, 'abdome_furos', 0) or 0,
                    'Abdome Fios': getattr(surgery, 'abdome_fios', 0) or 0,
                    'Abdome Comentários': getattr(surgery, 'abdome_comentarios', '') or '',
                    'Pernas Furos': getattr(surgery, 'pernas_furos', 0) or 0,
                    'Pernas Fios': getattr(surgery, 'pernas_fios', 0) or 0,
                    'Pernas Comentários': getattr(surgery, 'pernas_comentarios', '') or '',
                    'Técnica': surgery.tecnica or '',
                    'Solução Frente (ml)': surgery.solucao_frente or 0,
                    'Q1 Área': surgery.q1_area or 0,
                    'Q1 Furos': surgery.q1_furos or 0,
                    'Q1 Fios': surgery.q1_fios or 0,
                    'Q1 Densidade': surgery.q1_densidade or 0,
                    'Q1 Taxa Quebra': surgery.q1_taxa_quebra or 0,
                    'Q2 Área': surgery.q2_area or 0,
                    'Q2 Furos': surgery.q2_furos or 0,
                    'Q2 Fios': surgery.q2_fios or 0,
                    'Q2 Densidade': surgery.q2_densidade or 0,
                    'Q2 Taxa Quebra': surgery.q2_taxa_quebra or 0,
                    'Q3 Área': surgery.q3_area or 0,
                    'Q3 Furos': surgery.q3_furos or 0,
                    'Q3 Fios': surgery.q3_fios or 0,
                    'Q3 Densidade': surgery.q3_densidade or 0,
                    'Q3 Taxa Quebra': surgery.q3_taxa_quebra or 0,
                    'Q4 Área': surgery.q4_area or 0,
                    'Q4 Furos': surgery.q4_furos or 0,
                    'Q4 Fios': surgery.q4_fios or 0,
                    'Q4 Densidade': surgery.q4_densidade or 0,
                    'Q4 Taxa Quebra': surgery.q4_taxa_quebra or 0,
                    'Densidade Extração': surgery.densidade_extracao or 0,
                    'Data de Criação': surgery.created_at.strftime('%d/%m/%Y %H:%M:%S') if surgery.created_at else ''
                }
                data_list.append(surgery_dict)
            
            df = pd.DataFrame(data_list)
        
        # Criar arquivo temporário no disco para gerar o Excel
        import tempfile
        logger.info("Criando arquivo Excel temporário para backup...")
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_filename = temp_file.name
            df.to_excel(temp_filename, sheet_name='Cirurgias', index=False, engine='openpyxl')
        
        # Ler o arquivo Excel como bytes
        with open(temp_filename, 'rb') as f:
            excel_content = f.read()
        
        # Remover arquivo temporário
        os.unlink(temp_filename)
        
        # Conectar ao Dropbox
        logger.info("Conectando ao Dropbox...")
        dbx = dropbox.Dropbox(dropbox_token)
        
        # Nome fixo do arquivo (sempre o mesmo)
        filename = "relatorio_cirurgias_backup.xlsx"
        dropbox_path = f"/{filename}"
        
        # Upload para o Dropbox (sobrescrever se existir)
        logger.info(f"Fazendo upload para Dropbox: {dropbox_path}")
        dbx.files_upload(
            excel_content,
            dropbox_path,
            mode=dropbox.files.WriteMode.overwrite,
            autorename=False
        )
        
        logger.info(f"✅ Backup realizado com sucesso no Dropbox: {filename}")
        return True, f"Arquivo '{filename}' atualizado com sucesso no Dropbox"
        
    except dropbox.exceptions.AuthError as e:
        if 'expired_access_token' in str(e):
            logger.error("Token do Dropbox expirado")
            return False, "Token do Dropbox expirado. Gere um novo token no console do Dropbox."
        else:
            logger.error(f"Erro de autenticação Dropbox: {e}")
            return False, f"Erro de autenticação: {e}"
    except Exception as e:
        logger.error(f"Erro no backup para Dropbox: {str(e)}")
        logger.error(traceback.format_exc())
        return False, f"Erro no backup: {str(e)}"

# Load models and set up tables only once
with app.app_context():
    # Não usamos db.create_all() em produção com migrações
    # O Flask-Migrate deve gerenciar todas as alterações de tabela
    # Este código permanece apenas para compatibilidade retroativa
    if os.environ.get("FLASK_ENV") == "development" and not os.environ.get("USE_MIGRATIONS"):
        db.create_all()
        logger.info("✅ Database tables created in development mode")

    # Initialize test data in development environment
    if os.environ.get("FLASK_ENV") == "development":
        if Surgery.query.count() == 0:
            logger.info("Inserindo dados de teste no ambiente de desenvolvimento...")
            test_data = [
                Surgery(
                    data=datetime.now().date(),
                    nome="Paciente Teste Dev",
                    unidade="Ribeirão Preto",
                    medico="Dr. Arthur",
                    equipe="Aline",
                    hora_cirurgia="08:00",
                    tempo_cirurgia=2.5,
                    total_foliculos=3500,
                    frente=1000,
                    densidade_scketh=85,
                    coroa=800,
                    scalpe=500,
                    peninsula_direita=600,
                    peninsula_esquerda=600
                )
            ]
            db.session.bulk_save_objects(test_data)
            db.session.commit()
            logger.info("✅ Dados de teste inseridos com sucesso")

    # Check if database needs initial data for production
    try:
        count = Surgery.query.count()
        if count == 0:
            logger.info("Database is empty, inserting test data...")
            test_data = [
                Surgery(
                    data=datetime.now().date(),
                    nome="Paciente Teste",
                    unidade="Ribeirão Preto",
                    medico="Dr. Arthur",
                    equipe="Aline",
                    hora_cirurgia="08:00",
                    tempo_cirurgia=2.5,
                    total_foliculos=3500,
                    frente=1000,
                    densidade_scketh=85,
                    coroa=800,
                    scalpe=500,
                    peninsula_direita=600,
                    peninsula_esquerda=600
                )
            ]
            db.session.bulk_save_objects(test_data)
            db.session.commit()
            logger.info("✅ Test data inserted successfully")
    except Exception as e:
        logger.error(f"Error inserting test data: {str(e)}")
        db.session.rollback()

# Modificar a rota do dashboard para processar os dados corretamente
@app.route('/dashboard')
def dashboard():
    logger.info("Accessing dashboard route")
    try:
        with app.app_context():
            # Check record counts
            replit_count = Surgery.query.count()
            deploy_count = db.session.query(Surgery).count()
            logger.info(f"📌 Registros no Replit: {replit_count}")
            logger.info(f"📌 Registros no deploy: {deploy_count}")

            if replit_count != deploy_count:
                logger.warning(f"⚠️ Diferença de registros detectada: Replit={replit_count}, Deploy={deploy_count}")
            # Usar consulta SQL direta para debugging
            sql = text("""
                SELECT count(*) AS total, 
                       COALESCE(avg(total_foliculos), 0) as avg_foliculos,
                       COALESCE(avg(densidade_scketh), 0) as avg_densidade
                FROM surgery;
            """)
            result = db.session.execute(sql)
            stats = result.fetchone()
            logger.info(f"Database stats: {stats}")

            if not stats or stats.total == 0:
                logger.warning("No records found in database")
                return render_template('dashboard.html', data={
                    'total_surgeries': 0,
                    'avg_follicles': 0,
                    'avg_density': 0,
                    'labels': [],
                    'datasets': [],
                    'has_follicle_data': False,
                    'follicles_data': {'labels': [], 'averages': [], 'le_density': []},
                    'version': '2.4'
                }, error="Nenhum registro encontrado no banco de dados.")

            # Buscar dados detalhados
            sql = text("""
                SELECT 
                    data, 
                    unidade,
                    total_foliculos,
                    densidade_scketh
                FROM surgery
                ORDER BY data ASC;
            """)

            result = db.session.execute(sql)
            rows = result.fetchall()

            # Criar DataFrame e tratar valores nulos
            df = pd.DataFrame(rows, columns=['data', 'unidade', 'total_foliculos', 'densidade_scketh'])
            df['total_foliculos'] = pd.to_numeric(df['total_foliculos'], errors='coerce').fillna(0)
            df['densidade_scketh'] = pd.to_numeric(df['densidade_scketh'], errors='coerce').fillna(0)

            logger.info(f"Data summary:\n{df.describe()}")

            # Inicializar dados do dashboard
            dashboard_data = {
                'total_surgeries': int(stats.total),
                'avg_follicles': int(round(stats.avg_foliculos or 0)),
                'avg_density': int(round(stats.avg_densidade or 0)),
                'labels': [],
                'datasets': [],
                'has_follicle_data': True,
                'follicles_data': {'labels': [], 'averages': [], 'le_density': []},
                'update_time': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'version': '2.4'
            }

            if not df.empty:
                # Filtrar datas válidas (remover datas muito antigas que causam overflow)
                try:
                    # Converter data e filtrar apenas datas válidas (anos >= 1900)
                    df['data_parsed'] = pd.to_datetime(df['data'], errors='coerce')
                    df = df[df['data_parsed'].notna()]
                    df = df[df['data_parsed'].dt.year >= 1900]
                    
                    if df.empty:
                        logger.warning("Nenhuma data válida encontrada após filtro")
                        dashboard_data['has_follicle_data'] = False
                    else:
                        # Processar dados por mês
                        df['mes_ano'] = df['data_parsed'].dt.strftime('%m/%Y')

                        # Agrupar por mês
                        monthly_data = df.groupby('mes_ano').agg({
                            'data': 'count',  # contagem de cirurgias
                            'total_foliculos': 'mean',  # média de folículos
                            'densidade_scketh': 'mean'   # média de densidade
                        }).round(2)

                        # Dados gerais por mês
                        dashboard_data['labels'] = monthly_data.index.tolist()
                        dashboard_data['datasets'].append({
                            'label': 'Total de Cirurgias',
                            'data': monthly_data['data'].tolist()
                        })

                        # Dados por unidade
                        for unidade in df['unidade'].unique():
                            df_unit = df[df['unidade'] == unidade]
                            unit_data = df_unit.groupby('mes_ano')['data'].count()

                            # Preencher meses faltantes com zero
                            unit_data = unit_data.reindex(monthly_data.index, fill_value=0)

                            dashboard_data['datasets'].append({
                                'label': f'Cirurgias - {unidade}',
                                'data': unit_data.tolist()
                            })

                        # Dados de folículos e densidade por mês
                        dashboard_data['follicles_data']['labels'] = monthly_data.index.tolist()
                        dashboard_data['follicles_data']['averages'] = monthly_data['total_foliculos'].round().astype(int).tolist()
                        dashboard_data['follicles_data']['le_density'] = monthly_data['densidade_scketh'].round().astype(int).tolist()
                        
                except Exception as e:
                    logger.error(f"Erro ao processar datas no dashboard: {str(e)}")
                    dashboard_data['has_follicle_data'] = False

            logger.info(f"Processed dashboard data: {dashboard_data}")
            return render_template('dashboard.html', data=dashboard_data)

    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}\n{traceback.format_exc()}")
        return render_template('dashboard.html', data={
            'total_surgeries': 0,
            'avg_follicles': 0,
            'avg_density': 0,
            'labels': [],
            'datasets': [{'label': 'Cirurgias', 'data': []}],
            'has_follicle_data': False,
            'follicles_data': {'labels': [], 'averages': [], 'le_density': []},
            'version': '2.4'
        }, error=f"Erro ao carregar dashboard: {str(e)}")

def backup_excel_file(source_file):
    """Create a backup of the Excel file with timestamp"""
    if os.path.exists(source_file):
        backup_dir = "data_backup"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/{os.path.splitext(os.path.basename(source_file))[0]}_{timestamp}.xlsx"
        shutil.copy2(source_file, backup_file)
        logger.info(f"Created backup: {backup_file}")
        return backup_file
    return None

def save_to_excel(data):
    """Save data to Excel and database with improved error handling"""
    try:
        logging.info("Starting data save process...")
        logger.info(f"Received data: {data}")
        filename = "cirurgias.xlsx"

        # Create backup before modifying
        backup_excel_file(filename)
        logger.info(f"Backup created successfully")

        # Save to database first
        try:
            logger.info(f"Preparing data for database insertion")

            # Convert to DataFrame and handle NaN values
            dados = pd.DataFrame([data])
            dados = dados.fillna(0)
            data = dados.iloc[0].to_dict()
            logger.info(f"Data processed with fillna: {data}")

            # Convert date string to date object
            try:
                # Verificar se o campo data está presente ou usar o campo formatado
                logger.info(f"Data keys available: {list(data.keys())}")
                
                if 'data' in data and data['data']:
                    logger.info(f"Using 'data' field: {data['data']}")
                    try:
                        data_date = datetime.strptime(data['data'], '%Y-%m-%d').date()
                        logger.info(f"Parsed date (YYYY-MM-DD): {data_date}")
                    except ValueError:
                        # Tentativa de parsing no formato DD/MM/YYYY
                        data_date = datetime.strptime(data['data'], '%d/%m/%Y').date()
                        logger.info(f"Parsed date (DD/MM/YYYY): {data_date}")
                elif 'Data (DD/MM/AAAA)' in data and data['Data (DD/MM/AAAA)']:
                    logger.info(f"Using 'Data (DD/MM/AAAA)' field: {data['Data (DD/MM/AAAA)']}")
                    data_date = datetime.strptime(data['Data (DD/MM/AAAA)'], '%d/%m/%Y').date()
                    logger.info(f"Parsed date: {data_date}")
                else:
                    error_msg = "Campo de data não encontrado ou vazio"
                    logger.error(error_msg)
                    return False, error_msg
            except Exception as e:
                error_msg = f"Erro ao converter data: {str(e)}"
                logger.error(f"{error_msg} - Dados recebidos: {data}")
                logger.error(traceback.format_exc())
                return False, error_msg

            # Create Surgery object with proper type conversion
            # Tratar valores NaN ou None antes de criar o objeto Surgery
            # Mapear os campos do formulário para os campos do banco de dados
            surgery = Surgery(
                data=data_date,
                nome=str(data.get('Paciente', data.get('nome', '')) or ''),
                unidade=str(data.get('Unidade', data.get('unidade', '')) or ''),
                medico=str(data.get('Médico', data.get('medico', '')) or ''),
                equipe=str(data.get('Equipe', data.get('equipe', '')) or ''),
                hora_cirurgia=str(data.get('Hora da Cirurgia (HH:MM)', data.get('hora_cirurgia', '')) or ''),
                tempo_cirurgia=float(data.get('Tempo de Cirurgia (horas)', data.get('tempo_cirurgia', 0)) or 0),
                total_foliculos=int(data.get('Total de Folículos', data.get('total_foliculos', 0)) or 0),
                frente=int(data.get('Frente', data.get('frente', 0)) or 0),
                densidade_scketh=float(data.get('Densidade Scketh', data.get('densidade_scketh', 0)) or 0),
                coroa=int(data.get('Coroa', data.get('coroa', 0)) or 0),
                scalpe=int(data.get('Scalpe', data.get('scalpe', 0)) or 0),
                peninsula_direita=int(data.get('Península Direita', data.get('peninsula_direita', 0)) or 0),
                peninsula_esquerda=int(data.get('Península Esquerda', data.get('peninsula_esquerda', 0)) or 0),
                # Campos da segunda página do formulário
                infiltracao=str(data.get('Infiltração', data.get('infiltracao', '')) or ''),
                sedacao=str(data.get('Sedação', data.get('sedacao', '')) or ''),
                sangramento=str(data.get('Sangramento', data.get('sangramento', '')) or ''),
                tadalafila=str(data.get('Tadalafila', data.get('tadalafila', '')) or ''),
                bloqueio_seringas=str(data.get('Bloqueio de Seringas', data.get('bloqueio_seringas', '')) or ''),
                fonte_1=str(data.get('Fonte 1', data.get('fonte_1', '')) or ''),
                fonte_2=str(data.get('Fonte 2', data.get('fonte_2', '')) or ''),
                fonte_3=str(data.get('Fonte 3', data.get('fonte_3', '')) or ''),
                fonte_4=str(data.get('Fonte 4', data.get('fonte_4', '')) or ''),
                fonte_5=str(data.get('Fonte 5', data.get('fonte_5', '')) or ''),
                pelos_corporais=str(data.get('Pelos Corporais', data.get('pelos_corporais', '')) or ''),
                # Body hair detailed fields
                barba_furos=int(data.get('barba_furos', 0) or 0),
                barba_fios=int(data.get('barba_fios', 0) or 0),
                barba_comentarios=str(data.get('barba_comentarios', '') or ''),
                peitoral_furos=int(data.get('peitoral_furos', 0) or 0),
                peitoral_fios=int(data.get('peitoral_fios', 0) or 0),
                peitoral_comentarios=str(data.get('peitoral_comentarios', '') or ''),
                abdome_furos=int(data.get('abdome_furos', 0) or 0),
                abdome_fios=int(data.get('abdome_fios', 0) or 0),
                abdome_comentarios=str(data.get('abdome_comentarios', '') or ''),
                pernas_furos=int(data.get('pernas_furos', 0) or 0),
                pernas_fios=int(data.get('pernas_fios', 0) or 0),
                pernas_comentarios=str(data.get('pernas_comentarios', '') or ''),
                tecnica=str(data.get('Técnica', data.get('tecnica', '')) or ''),
                solucao_frente=int(data.get('Solução Frente (ml)', data.get('solucao_frente', 0)) or 0),
                # Dados dos quadrantes - suporte a múltiplos formatos de nome
                q1_area=float(data.get('Q1 Área', data.get('q1_area', 0)) or 0),
                q1_furos=int(data.get('Q1 Furos', data.get('q1_furos', 0)) or 0),
                q1_fios=int(data.get('Q1 Fios', data.get('q1_fios', 0)) or 0),
                q1_densidade=float(data.get('Q1 Densidade', data.get('q1_densidade', 0)) or 0),
                q1_taxa_quebra=float(data.get('Q1 Taxa Quebra', data.get('q1_taxa_quebra', 0)) or 0),
                q2_area=float(data.get('Q2 Área', data.get('q2_area', 0)) or 0),
                q2_furos=int(data.get('Q2 Furos', data.get('q2_furos', 0)) or 0),
                q2_fios=int(data.get('Q2 Fios', data.get('q2_fios', 0)) or 0),
                q2_densidade=float(data.get('Q2 Densidade', data.get('q2_densidade', 0)) or 0),
                q2_taxa_quebra=float(data.get('Q2 Taxa Quebra', data.get('q2_taxa_quebra', 0)) or 0),
                q3_area=float(data.get('Q3 Área', data.get('q3_area', 0)) or 0),
                q3_furos=int(data.get('Q3 Furos', data.get('q3_furos', 0)) or 0),
                q3_fios=int(data.get('Q3 Fios', data.get('q3_fios', 0)) or 0),
                q3_densidade=float(data.get('Q3 Densidade', data.get('q3_densidade', 0)) or 0),
                q3_taxa_quebra=float(data.get('Q3 Taxa Quebra', data.get('q3_taxa_quebra', 0)) or 0),
                q4_area=float(data.get('Q4 Área', data.get('q4_area', 0)) or 0),
                q4_furos=int(data.get('Q4 Furos', data.get('q4_furos', 0)) or 0),
                q4_fios=int(data.get('Q4 Fios', data.get('q4_fios', 0)) or 0),
                q4_densidade=float(data.get('Q4 Densidade', data.get('q4_densidade', 0)) or 0),
                q4_taxa_quebra=float(data.get('Q4 Taxa Quebra', data.get('q4_taxa_quebra', 0)) or 0),
                densidade_extracao=float(data.get('Densidade Extração', data.get('densidade_extracao', 0)) or 0)
            )

            logger.info("Surgery object created, committing to database...")
            db.session.add(surgery)
            db.session.commit()
            logger.info("✅ Data saved to database successfully")

            # Verify the save by querying the database
            saved_surgery = Surgery.query.get(surgery.id)
            logger.info(f"Verified saved surgery: {saved_surgery.nome} (ID: {saved_surgery.id})")

        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
            logger.error(traceback.format_exc())
            db.session.rollback()
            raise e

        # Then save to Excel
        logger.info("Saving to Excel...")
        if os.path.exists(filename):
            try:
                df_existing = pd.read_excel(filename, engine='openpyxl')
                df_new = pd.DataFrame([data])
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            except Exception as e:
                logging.error(f"Error reading existing Excel file: {str(e)}")
                df_combined = pd.DataFrame([data])
        else:
            df_combined = pd.DataFrame([data])

        # Save with backup usando uma extensão válida para Excel
        temp_file = f"{filename}.backup.xlsx"
        df_combined.to_excel(temp_file, index=False, engine='openpyxl')

        # If save was successful, replace original file
        if os.path.exists(temp_file):
            if os.path.exists(filename):
                os.remove(filename)
            os.rename(temp_file, filename)

        logger.info("✅ Data saved to Excel successfully!")
        
        # Executar backup automático para Dropbox após salvar os dados
        try:
            logger.info("Iniciando backup automático para Dropbox...")
            backup_success, backup_message = export_and_backup()
            if backup_success:
                logger.info(f"✅ Backup automático realizado: {backup_message}")
            else:
                logger.warning(f"⚠️ Backup automático falhou: {backup_message}")
        except Exception as backup_e:
            logger.error(f"Erro no backup automático: {str(backup_e)}")
            # Não falhar o salvamento por causa de erro no backup
        
        return True, "Dados salvos com sucesso!"
    except Exception as e:
        logging.error(f"Error saving data: {str(e)}")
        logging.error(traceback.format_exc())
        return False, f"Erro ao salvar dados: {str(e)}"

# Initialize empty Excel files if they don't exist
def initialize_empty_files():
    # Initialize cirurgias.xlsx
    if not os.path.exists("cirurgias.xlsx"):
        columns = [
            'data', 'nome', 'unidade', 'medico', 'equipe', 'hora_cirurgia', 
            'tempo_cirurgia', 'total_foliculos', 'frente', 'densidade_scketh',
            'coroa', 'scalpe', 'peninsula_direita', 'peninsula_esquerda'
        ]
        pd.DataFrame(columns=columns).to_excel("cirurgias.xlsx", index=False, engine='openpyxl')
        logger.info("Created empty cirurgias.xlsx file")

    # Initialize necroses.xlsx
    if not os.path.exists("necroses.xlsx"):
        columns = [
            'patient_id', 'patient_unit', 'data_registro', 'lesion_count', 
            'largest_lesion', 'affected_band', 'photo_paths'
        ]
        pd.DataFrame(columns=columns).to_excel("necroses.xlsx", index=False, engine='openpyxl')
        logger.info("Created empty necroses.xlsx file")

# Initialize empty files at startup
initialize_empty_files()

@app.route('/')
def index():
    logger.info("Accessing index route")
    return render_template('base.html')

@app.route('/ping')
def ping():
    logger.info("Ping route accessed")
    return "Application is running!"

@app.route('/success')
def success():
    logger.info("Accessing success page")
    saved_data = session.get('last_saved_data', {})
    return render_template('success.html', saved_data=saved_data)

@app.route('/clear_data', methods=['POST'])
def clear_data():
    """Clear all data from Excel files before deployment"""
    try:
        # Clear cirurgias.xlsx
        if os.path.exists("cirurgias.xlsx"):
            # Create empty dataframe with columns
            columns = [
                'data', 'nome', 'unidade', 'medico', 'equipe', 'hora_cirurgia', 
                'tempo_cirurgia', 'total_foliculos', 'frente', 'densidade_scketh',
                'coroa', 'scalpe', 'peninsula_direita', 'peninsula_esquerda'
            ]
            pd.DataFrame(columns=columns).to_excel("cirurgias.xlsx", index=False, engine='openpyxl')

        # Clear necroses.xlsx
        if os.path.exists("necroses.xlsx"):
            columns = [
                'patient_id', 'patient_unit', 'data_registro', 'lesion_count', 
                'largest_lesion', 'affected_band', 'photo_paths'
            ]
            pd.DataFrame(columns=columns).to_excel("necroses.xlsx", index=False, engine='openpyxl')

        # Clear database
        with app.app_context():
            db.session.execute(Surgery.__table__.delete())
            db.session.commit()

        logger.info("✅ All data cleared successfully for deployment")
        flash("✅ Todos os dados foram limpos com sucesso! O sistema está pronto para deployment.", "success")
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}\n{traceback.format_exc()}")
        flash(f"❌ Erro ao limpar dados: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/clear_data_protected', methods=['POST'])
def clear_data_protected():
    """Clear all data from Excel files with password protection"""
    try:
        # Get password from request
        data = request.get_json()
        password = data.get('password', '')

        # Check if password is correct (12345)
        if password != '12345':
            logger.warning("Incorrect password attempt to clear data")
            return jsonify({'success': False, 'message': 'Senha incorreta'})

        # Clear cirurgias.xlsx
        if os.path.exists("cirurgias.xlsx"):
            columns = [
                'data', 'nome', 'unidade', 'medico', 'equipe', 'hora_cirurgia', 
                'tempo_cirurgia', 'total_foliculos', 'frente', 'densidade_scketh',
                'coroa', 'scalpe', 'peninsula_direita', 'peninsula_esquerda'
            ]
            pd.DataFrame(columns=columns).to_excel("cirurgias.xlsx", index=False, engine='openpyxl')

        # Clear necroses.xlsx
        if os.path.exists("necroses.xlsx"):
            columns = [
                'patient_id', 'patient_unit', 'data_registro', 'lesion_count', 
                'largest_lesion', 'affected_band', 'photo_paths'
            ]
            pd.DataFrame(columns=columns).to_excel("necroses.xlsx", index=False, engine='openpyxl')

        # Clear database
        with app.app_context():
            db.session.execute(Surgery.__table__.delete())
            db.session.commit()

        logger.info("✅ All data cleared successfully through dashboard")
        return jsonify({'success': True, 'message': 'Dados limpos com sucesso'})
    except Exception as e:
        logger.error(f"Error clearing data via dashboard: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Erro ao limpar dados: {str(e)}'})

@app.route('/get_patients_list')
def get_patients_list():
    """Endpoint to get list of registered patients sorted by unit and date"""
    try:
        with app.app_context():
            surgeries = Surgery.query.order_by(Surgery.unidade.asc(), Surgery.data.desc()).all()
            patients = [{
                'nome': s.nome,
                'data': s.data.strftime('%d/%m/%Y'),
                'unidade': s.unidade
            } for s in surgeries]
            return jsonify({'patients': patients})
    except Exception as e:
        logger.error(f"Error getting patients list: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e), 'patients': []})

@app.route('/get_last_record')
def get_last_record():
    """Get the last surgery record information"""
    try:
        with app.app_context():
            last_record = Surgery.query.order_by(Surgery.created_at.desc()).first()
            if last_record:
                patient_name = last_record.nome
                return jsonify({
                    'success': True, 
                    'patient_name': patient_name
                })
            else:
                return jsonify({'success': False, 'message': 'Nenhum registro encontrado'})
    except Exception as e:
        logger.error(f"Error getting last record: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Erro ao buscar último registro: {str(e)}'})

@app.route('/delete_patient', methods=['POST'])
def delete_patient():
    """Delete a specific patient"""
    try:
        data = request.get_json()
        patient_name = data.get('patient_name')
        
        if not patient_name:
            return jsonify({'success': False, 'message': 'Nome do paciente não fornecido'})
            
        with app.app_context():
            patient = Surgery.query.filter_by(nome=patient_name).first()
            if patient:
                db.session.delete(patient)
                db.session.commit()
                logger.info(f"✅ Patient deleted successfully: {patient_name}")
                return jsonify({
                    'success': True, 
                    'message': f'Paciente {patient_name} excluído com sucesso'
                })
            else:
                return jsonify({'success': False, 'message': 'Paciente não encontrado'})
    except Exception as e:
        logger.error(f"Error deleting patient: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Erro ao excluir paciente: {str(e)}'})

@app.route('/delete_last_record', methods=['POST'])
def delete_last_record():
    """Delete the last surgery record"""
    try:
        with app.app_context():
            last_record = Surgery.query.order_by(Surgery.created_at.desc()).first()
            if last_record:
                patient_name = last_record.nome
                db.session.delete(last_record)
                db.session.commit()
                logger.info(f"✅ Last record deleted successfully (Patient: {patient_name})")
                return jsonify({
                    'success': True, 
                    'message': f'Registro do paciente {patient_name} excluído com sucesso'
                })
            else:
                return jsonify({'success': False, 'message': 'Nenhum registro encontrado para excluir'})
    except Exception as e:
        logger.error(f"Error deleting last record: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Erro ao excluir último registro: {str(e)}'})


@app.route('/novo_cadastro', methods=['GET', 'POST'])
def novo_cadastro():
    logger.info("Accessing novo_cadastro route")
    if request.method == 'POST':
        try:
            # Process form data
            form_data = request.form.to_dict()
            logger.info(f"Received form data keys: {list(form_data.keys())}")
            logger.info(f"Request headers: {dict(request.headers)}")
            
            # Log de detalhes específicos importantes
            if 'Paciente' in form_data:
                logger.info(f"Paciente: {form_data['Paciente']}")
            if 'Data (DD/MM/AAAA)' in form_data:
                logger.info(f"Data: {form_data['Data (DD/MM/AAAA)']}")
            if 'Unidade' in form_data:
                logger.info(f"Unidade: {form_data['Unidade']}")
            
            # Log específico dos campos calculados para debugging
            quadrant_fields = ['q1_densidade', 'q1_taxa_quebra', 'q2_densidade', 'q2_taxa_quebra', 
                             'q3_densidade', 'q3_taxa_quebra', 'q4_densidade', 'q4_taxa_quebra']
            for field in quadrant_fields:
                if field in form_data:
                    logger.info(f"📊 Campo calculado encontrado - {field}: {form_data[field]}")
                else:
                    logger.warning(f"⚠️ Campo calculado AUSENTE - {field}")
            
            # Log completo dos dados para auditoria
            logger.info(f"💾 Dados completos recebidos: {form_data}")

            # Process multiple checkboxes for team members
            team_members = []
            
            # Collect all team-related fields
            for key, value in form_data.items():
                if key.startswith('equipe_') and value:
                    team_members.append(value)
                elif key == 'extra_person_1' and value:
                    team_members.append(f"Técnica Extra 1: {value}")
                elif key == 'extra_person_2' and value:
                    team_members.append(f"Técnica Extra 2: {value}")
            
            # Handle legacy equipe_values field
            if 'equipe_values' in form_data:
                if form_data['equipe_values']:
                    team_members.append(form_data['equipe_values'])
                del form_data['equipe_values']
            
            # Combine all team members
            if team_members:
                form_data['equipe'] = ', '.join(team_members)
            
            logger.info(f"📋 Equipe processada: {form_data.get('equipe', 'Nenhuma')}")
            logger.info(f"🔧 Membros coletados: {team_members}")

            # Process body hair checkbox and data
            body_hair_checked = form_data.get('body_hair_check') == 'on'
            form_data['pelos_corporais'] = 'Sim' if body_hair_checked else 'Não'
            
            logger.info(f"🧔 Body hair checkbox: {body_hair_checked} -> {form_data['pelos_corporais']}")
            
            # Process individual body hair parts
            body_hair_parts = ['barba', 'peitoral', 'abdome', 'pernas']
            for part in body_hair_parts:
                # Handle checkbox for each part
                part_checked = form_data.get(f'{part}_check') == 'on'
                
                # Set furos, fios, comentários based on checkbox state
                if part_checked:
                    form_data[f'{part}_furos'] = int(form_data.get(f'{part}_furos', 0) or 0)
                    form_data[f'{part}_fios'] = int(form_data.get(f'{part}_fios', 0) or 0)
                    form_data[f'{part}_comentarios'] = str(form_data.get(f'{part}_comentarios', '') or '')
                else:
                    # If not checked, set to default values
                    form_data[f'{part}_furos'] = 0
                    form_data[f'{part}_fios'] = 0
                    form_data[f'{part}_comentarios'] = ''
                
                logger.info(f"🎯 {part.title()}: checked={part_checked}, furos={form_data[f'{part}_furos']}, fios={form_data[f'{part}_fios']}")
            
            # Clean up checkbox fields that don't need to be saved
            for key in list(form_data.keys()):
                if key.endswith('_check'):
                    del form_data[key]

            # Save to Excel and database
            logger.info("Calling save_to_excel function")
            success, message = save_to_excel(form_data)
            logger.info(f"Save result: success={success}, message={message}")

            if success:
                flash("✅ Dados salvos com sucesso! 🎉", "success")
                logger.info("Flashed success message")
                
                # Salvar dados na sessão para mostrar na página de sucesso
                session['last_saved_data'] = form_data
                
            else:
                flash(message, "error")
                logger.error(f"Flashed error message: {message}")

            # Se for uma chamada da API (não do formulário web)
            if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                logger.info("API call detected, returning JSON response")
                return jsonify({"status": "success", "message": "Dados salvos com sucesso"})
            else:
                logger.info("Redirecting to success page")
                return redirect(url_for('success'))
        except Exception as e:
            error_msg = f"Error saving data: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            flash(f"Erro ao salvar dados: {str(e)}", "error")
            
            # Se for uma chamada da API (não do formulário web)
            if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                logger.info("API call detected, returning JSON error response")
                return jsonify({"status": "error", "message": error_msg}), 500

    # Recarregar configurações para garantir que estão atualizadas
    reload_admin_config()
    
    # Complete form structure
    form_data = {
        'title': 'Cadastro de Cirurgia Capilar',
        'fields': [
            # Dados Gerais da Cirurgia
            {'name': 'data', 'label': 'Data da Cirurgia', 'type': 'date', 'required': True},
            {'name': 'nome', 'label': 'Nome do Paciente', 'type': 'text', 'required': True},
            {'name': 'unidade', 'label': 'Unidade', 'type': 'select', 'required': True, 
             'options': UNIDADES},
            {'name': 'medico', 'label': 'Médico Responsável', 'type': 'select_dynamic', 'required': True},
            {'name': 'equipe', 'label': 'Equipe', 'type': 'select_dynamic', 'required': True},
            {'name': 'hora_cirurgia', 'label': 'Hora da Cirurgia (HH:MM)', 'type': 'time', 'required': True, 'default': '08:00'},
            {'name': 'tempo_cirurgia', 'label': 'Tempo de Cirurgia (horas)', 'type': 'number', 'required': True},

            # Informações do Implante
            {'name': 'total_foliculos', 'label': 'Total de Folículos', 'type': 'number', 'required': True},
            {'name': 'frente', 'label': 'Frente', 'type': 'number', 'required': False},
            {'name': 'densidade_scketh', 'label': 'Densidade Scketh', 'type': 'number', 'required': False},
            {'name': 'coroa', 'label': 'Coroa', 'type': 'number', 'required': False},
            {'name': 'scalpe', 'label': 'Scalpe', 'type': 'number', 'required': False},
            {'name': 'peninsula_direita', 'label': 'Península Direita', 'type': 'number', 'required': False},
            {'name': 'peninsula_esquerda', 'label': 'Península Esquerda', 'type': 'number', 'required': False},

            # Procedimentos e Ferramentas
            {'name': 'safira', 'label': 'Safira?', 'type': 'select', 'required': True,
             'options': ['Sim', 'Não']},
            {'name': 'punch', 'label': 'Punch (mm)', 'type': 'select', 'required': True,
             'options': ['0,85x3,5mm', '0,85x4mm', '0,85x5mm', '0,90x4mm', '0,90x5mm', '1,0x4mm']},
            {'name': 'solucao_frente', 'label': 'Solução Frente (ml)', 'type': 'number', 'required': True},
            {'name': 'solucao_coroa', 'label': 'Solução Coroa (ml)', 'type': 'number', 'required': False},
            {'name': 'solucao_xilo_frente', 'label': 'Solução Xilo Frente (ml)', 'type': 'number', 'required': False},

            # Extração
            {'name': 'q1_area', 'label': 'Quadrante 1 - Área', 'type': 'number', 'required': True},
            {'name': 'q1_furos', 'label': 'Quadrante 1 - Número de Furos', 'type': 'number', 'required': True},
            {'name': 'q1_fios', 'label': 'Quadrante 1 - Número de Fios Retirados', 'type': 'number', 'required': True},

            {'name': 'q2_area', 'label': 'Quadrante 2 - Área', 'type': 'number', 'required': True},
            {'name': 'q2_furos', 'label': 'Quadrante 2 - Número de Furos', 'type': 'number', 'required': True},
            {'name': 'q2_fios', 'label': 'Quadrante 2 - Número de Fios Retirados', 'type': 'number', 'required': True},

            {'name': 'q3_area', 'label': 'Quadrante 3 - Área', 'type': 'number', 'required': True},
            {'name': 'q3_furos', 'label': 'Quadrante 3 - Número de Furos', 'type': 'number', 'required': True},
            {'name': 'q3_fios', 'label': 'Quadrante 3 - Número de Fios Retirados', 'type': 'number', 'required': True},

            {'name': 'q4_area', 'label': 'Quadrante 4 - Área', 'type': 'number', 'required': True},
            {'name': 'q4_furos', 'label': 'Quadrante 4 - Número de Furos', 'type': 'number', 'required': True},
            {'name': 'q4_fios', 'label': 'Quadrante 4 - Número de Fios Retirados', 'type': 'number', 'required': True},

            # Avaliação Intraoperatória
            {'name': 'infiltracao', 'label': 'Infiltração (1-3)', 'type': 'select', 'required': True,
             'options': ['1', '2', '3']},
            {'name': 'sedacao', 'label': 'Sedação (1-3)', 'type': 'select', 'required': True,
             'options': ['1', '2', '3']},
            {'name': 'sangramento', 'label': 'Sangramento (1-3)', 'type': 'select', 'required': True,
             'options': ['1', '2', '3']},

            # Histórico do Paciente
            {'name': 'implante_secundario', 'label': 'Implante Secundário?', 'type': 'select', 'required': True,
             'options': ['Sim', 'Não']},
            {'name': 'transamin', 'label': 'Transamin?', 'type': 'select', 'required': True,
             'options': ['Sim', 'Não']},
            {'name': 'tadalafila', 'label': 'Tadalafila?', 'type': 'select', 'required': True,
             'options': ['Sim', 'Não']},
            {'name': 'diprospam', 'label': 'Diprospam/Beta 30?', 'type': 'select', 'required': True,
             'options': ['Sim', 'Não']},
            {'name': 'fumante', 'label': 'Fumante?', 'type': 'select', 'required': True,
             'options': ['Sim', 'Não']},
            {'name': 'antecedentes', 'label': 'Antecedentes Pessoais', 'type': 'textarea', 'required': False},

            # Comentários e Finalização
            {'name': 'comentarios', 'label': 'Comentários', 'type': 'textarea', 'required': False}
        ]
    }
    return render_template('form.html', form=form_data, data={})

@app.route('/get_medicos/<unidade>')
def get_medicos(unidade):
    logger.info(f"Retrieving doctors for unit: {unidade}")
    # Recarregar configurações para garantir que estão atualizadas
    reload_admin_config()
    return {'medicos': MEDICOS_POR_UNIDADE.get(unidade, [])}


@app.route('/import_data', methods=['GET', 'POST'])
def import_data():
    """Importa dados de um arquivo Excel para o banco de dados"""
    if request.method == 'POST':
        try:
            # Verificar se um arquivo foi enviado
            if 'excel_file' not in request.files:
                flash("❌ Nenhum arquivo selecionado", "error")
                return redirect(request.url)

            file = request.files['excel_file']
            if file.filename == '':
                flash("❌ Nenhum arquivo selecionado", "error")
                return redirect(request.url)

            # Salvar o arquivo temporariamente
            temp_path = "temp_import.xlsx"
            file.save(temp_path)

            # Ler o arquivo Excel
            df_import = pd.read_excel(temp_path)

            # Verificar se o arquivo está vazio
            if df_import.empty:
                flash("❌ O arquivo está vazio", "error")
                os.remove(temp_path)
                return redirect(request.url)

            # Verificar se já existe arquivo de dados
            target_file = "cirurgias.xlsx"
            if os.path.exists(target_file):
                # Ler arquivo existente e concatenar com novos dados
                df_existing = pd.read_excel(target_file)
                df_combined = pd.concat([df_existing, df_import], ignore_index=True)
                # Remover possíveis duplicatas
                df_combined = df_combined.drop_duplicates()
                df_combined.to_excel(target_file, index=False)
                num_added = len(df_import)
                flash(f"✅ Dados importados com sucesso! {num_added} registros adicionados.", "success")
            else:
                # Criar novo arquivo
                df_import.to_excel(target_file, index=False)
                flash(f"✅ Dados importados com sucesso! {len(df_import)} registros adicionados.", "success")

            # Remover arquivo temporário
            os.remove(temp_path)
            return redirect(url_for('index'))

        except Exception as e:
            logger.error(f"Erro ao importar dados: {str(e)}\n{traceback.format_exc()}")
            flash(f"❌ Erro ao importar dados: {str(e)}", "error")
            return redirect(request.url)

    # Se for GET, mostrar formulário de upload
    return render_template('import_data.html')

@app.route('/verify_data', methods=['GET'])
def verify_data():
    """Verifica se os dados foram mantidos após o deployment e tenta restaurá-los se necessário"""
    try:
        cirurgias_file = "cirurgias.xlsx"
        necroses_file = "necroses.xlsx"

        # Verificar arquivo de cirurgias
        if os.path.exists(cirurgias_file):
            df_cirurgias = pd.read_excel(cirurgias_file)
            count_cirurgias = len(df_cirurgias)
            logger.info(f"Arquivo {cirurgias_file} contém {count_cirurgias} registros")
        else:
            count_cirurgias = 0
            logger.warning(f"Arquivo {cirurgias_file} não encontrado")

        # Verificar arquivo de necroses
        if os.path.exists(necroses_file):
            df_necroses = pd.read_excel(necroses_file)
            count_necroses = len(df_necroses)
            logger.info(f"Arquivo {necroses_file} contém {count_necroses} registros")
        else:
            count_necroses = 0
            logger.warning(f"Arquivo {necroses_file} não encontrado")

        # Se não houver dados, tentar restaurar
        if count_cirurgias == 0:
            try:
                from restore_deployment_data import restore_deployment_data
                success, restored_files = restore_deployment_data()

                if success:
                    restored_info = "<br>".join([f"- {f[0]}: {f[2]} registros (fonte: {f[1]})" for f in restored_files])
                    flash(f"✅ Dados restaurados com sucesso!<br>{restored_info}", "success")
                else:
                    flash("⚠️ Não foi possível restaurar os dados automaticamente. Execute`python restore_deployment_data.py'", "warning")
            except Exception as e:
                logger.error(f"Erro ao restaurar dados: {str(e)}")
                flash(f"❌ Erro ao restaurar dados: {str(e)}", "error")
        else:
            flash(f"✅ Dados verificados: {count_cirurgias} cirurgias e {count_necroses} relatórios de necrose.", "info")

        return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Erro ao verificar dados: {str(e)}\n{traceback.format_exc()}")
        flash(f"❌ Erro ao verificar dados: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/get_equipe/<unidade>')
def get_equipe(unidade):
    logger.info(f"Retrieving team for unit: {unidade}")
    # Recarregar configurações para garantir que estão atualizadas
    reload_admin_config()
    return {'equipe': EQUIPE_POR_UNIDADE.get(unidade, [])}

def process_dashboard_data(df):
    """Process dataframe into dashboard-ready data"""
    # Initialize dashboard data structure
    dashboard_data = {
        'total_surgeries': 0,
        'avg_follicles': 0,
        'avg_density': 0,
        'labels': [],
        'datasets': [],
        'has_follicle_data': False,
        'follicles_data': {'labels': [], 'averages': [], 'le_density': []},
        'update_time': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'version': '2.4'  # Updated version number
    }

    # Return empty structure if DataFrame is empty
    if df.empty:
        logger.warning("Empty DataFrame received in process_dashboard_data")
        return dashboard_data

    try:
        logger.info("Processing dashboard data...")
        logger.info(f"DataFrame shape: {df.shape}")
        logger.info(f"DataFrame columns: {df.columns.tolist()}")

        # Calculate basic statistics
        dashboard_data['total_surgeries'] = len(df)
        logger.info(f"Total surgeries: {dashboard_data['total_surgeries']}")

        # Calculate follicle averages if the data exists
        if 'total_foliculos' in df.columns:
            # Convert to numeric, forcing invalid values to NaN
            total_foliculos = pd.to_numeric(df['total_foliculos'], errors='coerce')
            # Calculate mean ignoring NaN values
            media_foliculos = total_foliculos.mean()
            if pd.notna(media_foliculos):  # Check if mean is not NaN
                dashboard_data['avg_follicles'] = int(round(media_foliculos))
                dashboard_data['has_follicle_data'] = True
                logger.info(f"Average follicles: {dashboard_data['avg_follicles']}")

        # Calculate density averages if the data exists
        if 'densidade_scketh' in df.columns:
            # Convert to numeric, forcing invalid values to NaN
            densidade = pd.to_numeric(df['densidade_scketh'], errors='coerce')
            # Calculate mean ignoring NaN values
            media_densidade = densidade.mean()
            if pd.notna(media_densidade):  # Check if mean is not NaN
                dashboard_data['avg_density'] = int(round(media_densidade))
                logger.info(f"Average density: {dashboard_data['avg_density']}")

        # Process dates
        if 'data' in df.columns:
            logger.info("Processing date-based data...")
            # Convert dates properly
            df['mes_ano'] = pd.to_datetime(df['data']).dt.strftime('%m/%Y')

            # Group by month
            cirurgias_por_mes = df.groupby('mes_ano').size().reset_index(name='count')
            dashboard_data['labels'] = cirurgias_por_mes['mes_ano'].tolist()
            dashboard_data['datasets'].append({
                'label': 'Total de Cirurgias',
                'data': cirurgias_por_mes['count'].tolist()
            })

            # Group by unit if unit data exists
            if 'unidade' in df.columns:
                for unidade in df['unidade'].unique():
                    df_unidade = df[df['unidade'] == unidade]
                    cirurgias_unidade = df_unidade.groupby('mes_ano').size().reset_index(name='count')

                    # Create complete dataset with all months
                    dados_completos = pd.DataFrame({'mes_ano': dashboard_data['labels']})
                    merged = dados_completos.merge(cirurgias_unidade, on='mes_ano', how='left')
                    merged['count'] = merged['count'].fillna(0).astype(int)

                    dashboard_data['datasets'].append({
                        'label': f'Cirurgias - {unidade}',
                        'data': merged['count'].tolist()
                    })

            # Process follicle data by month
            if dashboard_data['has_follicle_data']:
                logger.info("Processingfollicle data by month...")
                # Calculate monthly averages for follicles
                follicles_by_month = df.groupby('mes_ano').agg({
                    'total_foliculos': lambda x: round(pd.to_numeric(x, errors='coerce').mean())
                }).reset_index()

                dashboard_data['follicles_data']['labels'] = follicles_by_month['mes_ano'].tolist()
                dashboard_data['follicles_data']['averages'] = follicles_by_month['total_foliculos'].tolist()

                # Calculate monthly averages for density if available
                if 'densidade_scketh' in df.columns:
                    density_by_month = df.groupby('mes_ano').agg({
                        'densidade_scketh': lambda x: int(round(pd.to_numeric(x, errors='coerce').mean()))
                    }).reset_index()
                    dashboard_data['follicles_data']['le_density'] = density_by_month['densidade_scketh'].tolist()

        logger.info(f"Dashboard data processed successfully: {dashboard_data}")
        return dashboard_data

    except Exception as e:
        logger.error(f"Error processing dashboard data: {str(e)}")
        logger.error(traceback.format_exc())
        return dashboard_data

@app.route('/get_unit_progress')
def get_unit_progress():
    """Endpoint para obter o progresso atual em relação à meta de unidade"""
    logger.info("Obtendo progresso da unidade")
    try:
        unit = request.args.get('unit', 'Ribeirão Preto')

        # Metas definidas por unidade -  Obtidas do banco de dados
        with app.app_context():
            unit_progress = db.session.execute(text("SELECT unidade, meta FROM unit_progress")).fetchall()
            metas = {unit_data.unidade: unit_data.meta for unit_data in unit_progress}

        # Meta para a unidade selecionada
        meta = metas.get(unit, 30)

        # Valor atual (número de cirurgias para esta unidade)
        with app.app_context():
            atual = Surgery.query.filter(Surgery.unidade == unit).count()

        logger.info(f"Progresso: Unidade={unit}, Meta={meta}, Atual={atual}")

        # Calcular o percentual alcançado da meta
        percentual = round((atual / meta) * 100) if meta > 0 else 0

        return jsonify({
            'unit': unit, 
            'meta': meta, 
            'atual': atual,
            'percentual': percentual
        })

    except Exception as e:
        logger.error(f"Erro ao obter progresso: {str(e)}")
        return jsonify({
            'unit': unit, 
            'meta': metas.get(unit, 30) if 'metas' in locals() else 30, 
            'atual': 0,
            'percentual': 0
        })

@app.route('/get_available_units')
def get_available_units():
    """Endpoint para obter todas asunidades disponíveis no banco de dados"""
    logger.info("Obtendo unidades disponíveis")
    try:
        with app.app_context():
            units = [unit.unidade for unit in Surgery.query.distinct(Surgery.unidade).all()]
            # Garantir que todas as unidades padrão estejam sempre disponíveis
            default_units = ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro']
            for unit in default_units:
                if unit not in units:
                    units.append(unit)
            return jsonify({'units': units})
    except Exception as e:
        logger.error(f"Erro ao obter unidades: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'units': ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro']})

@app.route('/get_tecnicas_data')
def get_tecnicas_data():
    """Endpoint para obter dados sobre técnicas utilizadas"""
    logger.info("Obtendo dados de técnicas")
    try:
        with app.app_context():
            # Exemplo: contagem por técnica (adaptar conforme os dados reais da planilha)
            tecnicas_count = []

            # Se houver coluna de técnica, contar por valores únicos
            if 'safira' in [col.name for col in Surgery.__table__.columns]:
                safira_counts = db.session.query(Surgery.safira, db.func.count(Surgery.safira)).group_by(Surgery.safira).all()
                for safira, count in safira_counts:
                    tecnicas_count.append({
                        'tecnica': f"Safira: {safira}", 
                        'quantidade': int(count)
                    })

            # Verificar se há dados de body hair (adicionar se necessário no modelo)

            # Se não houver dados suficientes, adicionar valores de exemplo
            if len(tecnicas_count) < 2:
                tecnicas_count = [
                    {'tecnica': 'FUE', 'quantidade': 45},
                    {'tecnica': 'FUT', 'quantidade': 23},
                    {'tecnica': 'Body Hair', 'quantidade': 12},
                    {'tecnica': 'Refinamento', 'quantidade': 8}
                ]

            return jsonify({'tecnicas': tecnicas_count})

    except Exception as e:
        logger.error(f"Erro ao obter dados de técnicas: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'tecnicas': []})

@app.route('/get_equipe_data')
def get_equipe_data():
    """Endpoint para obter dados sobre participantes da equipe"""
    logger.info("Obtendo dados de equipe")
    try:
        with app.app_context():
            # Obter parâmetros de filtro
            unit_filter = request.args.get('unit', 'all')
            year_filter = request.args.get('year', 'all')
            month_filter = request.args.get('month', 'all')
            
            logger.info(f"Filtros aplicados: unidade={unit_filter}, ano={year_filter}, mês={month_filter}")
            
            # Inicializar lista para armazenar os dados da equipe
            equipe_data = []

            # Verificar se existem as colunas necessárias
            if 'equipe' in [col.name for col in Surgery.__table__.columns] and 'unidade' in [col.name for col in Surgery.__table__.columns]:
                # Para contar cirurgias totais por pessoa (independente da unidade)
                cirurgias_por_pessoa = {}
                # Para rastrear em quais unidades cada pessoa trabalhou
                unidades_por_pessoa = {}

                # Identificar todas as colunas que podem conter membros da equipe
                equipe_columns = ['equipe']

                # Verificar colunas de técnicas extras
                for col in Surgery.__table__.columns:
                    if col.name.startswith('extra_person_') or col.name.startswith('tecnica_extra'):
                        equipe_columns.append(col.name)

                logger.info(f"Colunas de equipe encontradas: {equipe_columns}")

                # Dicionário para rastrear participações únicas por cirurgia para cada pessoa
                # Estrutura: {membro: {id_cirurgia1, id_cirurgia2, ...}}
                participacoes_por_pessoa = {}
                
                # Construir a query com filtros
                query = Surgery.query
                
                # Aplicar filtro de unidade se não for 'all'
                if unit_filter != 'all':
                    query = query.filter(Surgery.unidade == unit_filter)
                
                # Aplicar filtro de ano se não for 'all'
                if year_filter != 'all':
                    # Extrair o ano da data
                    query = query.filter(extract('year', Surgery.data) == int(year_filter))
                
                # Aplicar filtro de mês se não for 'all'
                if month_filter != 'all':
                    # Extrair o mês da data
                    query = query.filter(extract('month', Surgery.data) == int(month_filter))
                
                # Iterar sobre cada linha para contar participações
                for surgery in query.all():
                    unidade = surgery.unidade if surgery.unidade else "Não especificada"
                    cirurgia_id = surgery.id  # Usar o ID da cirurgia

                    # Conjunto para guardar todos os membros desta cirurgia
                    membros_desta_cirurgia = set()

                    # Processar todas as colunas relevantes
                    for col in equipe_columns:
                        if hasattr(surgery, col) and getattr(surgery, col):
                            # Limpar e dividir valores
                            value_str = str(getattr(surgery, col))

                            # Verificar se há menção de "(extra)" e remover
                            value_str = value_str.replace('(extra)', '').strip()

                            # Dividir a string em nomes individuais
                            members = [name.strip() for name in value_str.replace(',', ';').replace('|', ';').split(';')]

                            for member in members:
                                # Remover parênteses e seu conteúdo
                                member = re.sub(r'\s*\([^)]*\)', '', member).strip()

                                if member and len(member) > 1:  # Ignorar entradas vazias ou muito curtas
                                    membros_desta_cirurgia.add(member)

                    # Adicionar todos os membros desta cirurgia ao rastreamento
                    for member in membros_desta_cirurgia:
                        # Rastrear em quais cirurgias a pessoa trabalhou
                        if member not in participacoes_por_pessoa:
                            participacoes_por_pessoa[member] = set()
                        participacoes_por_pessoa[member].add(cirurgia_id)

                        # Rastrear em quais unidades a pessoa trabalhou
                        if member not in unidades_por_pessoa:
                            unidades_por_pessoa[member] = set()
                        unidades_por_pessoa[member].add(unidade)

                # Converter para contagem final (total de cirurgias por pessoa)
                for member, cirurgias_ids in participacoes_por_pessoa.items():
                    cirurgias_por_pessoa[member] = len(cirurgias_ids)

                # Converter os dados para o formato esperado
                for member, count in cirurgias_por_pessoa.items():
                    # Obter a lista de unidades onde esta pessoa trabalhou
                    unidades = sorted(list(unidades_por_pessoa.get(member, ["Não especificada"])))

                    equipe_data.append({
                        'nome': member,
                        'quantidade': count,
                        'unidades': ", ".join(unidades)
                    })

                # Ordenar por quantidade (decrescente) e depois por nome
                equipe_data.sort(key=lambda x: (-x['quantidade'], x['nome']))

                logger.info(f"Dados de equipe processados: {len(equipe_data)} membros encontrados")

            # Se não houver dados suficientes, usar dados de exemplo
            if len(equipe_data) < 2:
                equipe_data = [
                    {'nome': 'Aline', 'quantidade': 15, 'unidades': 'Ribeirão Preto, Rio de Janeiro'},
                    {'nome': 'Natália', 'quantidade': 12, 'unidades': 'Ribeirão Preto, Campinas'},
                    {'nome': 'Ana', 'quantidade': 18, 'unidades': 'Ribeirão Preto'},
                    {'nome': 'Juliana', 'quantidade': 10, 'unidades': 'Campinas'},
                    {'nome': 'Gabriela', 'quantidade': 9, 'unidades': 'Campinas, Rio de Janeiro'},
                    {'nome': 'Mariana Moro', 'quantidade': 14, 'unidades': 'Rio de Janeiro'},
                    {'nome': 'Mariana Silva', 'quantidade': 11, 'unidades': 'Rio de Janeiro, Campinas'},
                    {'nome': 'Dayane', 'quantidade': 7, 'unidades': 'Rio de Janeiro'}
                ]

            return jsonify({'equipe': equipe_data})

    except Exception as e:
        logger.error(f"Erro ao obter dados de equipe: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'equipe': []})

@app.route('/filter_dashboard')
def filter_dashboard():
    """Endpoint to get filtered dashboard data"""
    logger.info("Filtering dashboard data")
    logger.info(f"Filter parameters: {request.args}")
    try:
        # Get filter parameters
        year = request.args.get('year', 'all')
        month = request.args.get('month', 'all')
        unit = request.args.get('unit', 'all')
        doctor = request.args.get('doctor', 'all')
        equipe = request.args.get('equipe', 'all')

        # Médicos por unidade para filtros
        medicos_por_unidade = {
        'Ribeirão Preto': ['Dr. Arthur', 'Dr. Daniel'],
        'Campinas': ['Dra. Adriana', 'Dra. Isadora'],
        'Rio de Janeiro': ['Dra. Ana Clara', 'Dra. Paula'],
        'São Paulo': ['Dr. Daniel', 'Dr. Renan', 'Dra. Ariane', 'Dra. Isabella', 'Dra. Talita', 'Dra. Thaiza'],
        'Brasília': ['Dra. Leticia', 'Dra. Natalia'],
        'Goiania': [],
    }

        # Equipe por unidade para filtros
        equipe_por_unidade = {
        'Ribeirão Preto': ['Aline', 'Ana', 'Lavinia', 'Natália'],
        'Campinas': [
                  'Bruna Galhardo',                   'Dayane Andrade',                   'Eduarda de Sousa', 
                  'Isabelle de Campos',                   'Juliana Nunes',                   'Kesley Sabrina', 
                  'Larissa Hellen',                   'Thalita Corrêa',                   'Vitória Delino'
                 ],
        'Rio de Janeiro': ['Assistente Extra', 'Dayane', 'Mariana Moro', 'Mariana Silva'],
        'São Paulo': [
                  'Adriana Almeida',                   'Ana Paula dos Santos',                   'Dani Curti', 
                  'Eliene Rodrigues',                   'Gabriela Cruz',                   'Greice Barbosa', 
                  'Jaiza Valentim',                   'Joyce Eugênia Da Silva',                   'Josefa Wilma Vieira', 
                  'Merielen Venâncio Oliveira',                   'Rosana Pereira',                   'Sabrina Crott', 
                  'Thaís Paiva',                   'Thamiris Santos'
                 ],
        'Brasília': ['Angélica Sousa', 'Betânia Almeida', 'Dayse Fernandes', 'Layla Cardoso', 'Thamara Maciel'],
        'Goiania': [],
    }

        # Load data
        with app.app_context():
            df = pd.read_sql(Surgery.query.statement, db.session.get_bind())

        # Preencher valores nulos com zero para evitar erros de cálculo
        df = df.fillna(0)

        # Apply filters
        if year != 'all':
            try:
                df = df[df['ano'] == int(year)]
            except:
                # Process dates if not already done
                if 'ano' not in df.columns:
                    df['ano'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce').dt.year
                df = df[df['ano'] == int(year)]

        if month != 'all':
            try:
                df = df[df['mes'] == int(month)]
            except:
                # Process dates if not already done
                if 'mes' not in df.columns:
                    df['mes'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce').dt.month
                df = df[df['mes'] == int(month)]

        # Apply unit filter with restrictions on doctors and team members
        if unit != 'all' and 'unidade' in df.columns:
            # Filter by unit
            df = df[df['unidade'] == unit]

            # Restrict doctors to only those from this unit 
            if 'medico' in df.columns:
                valid_doctors = medicos_por_unidade.get(unit, [])
                df = df[df['medico'].isin(valid_doctors)]

            # Restrict team members to only those from this unit
            if 'equipe' in df.columns:
                valid_team = equipe_por_unidade.get(unit, [])
                # Handle case where equipe might be a single value or a list
                if df['equipe'].dtype == 'object':
                    # For columns that might contain lists (e.g., stored as strings)
                    mask = df['equipe'].apply(lambda x: 
                        any(member in str(x) for member in valid_team) if isinstance(x, str) else False
                    )
                    df = df[mask]
                else:
                    # For columns with single values
                    df = df[df['equipe'].isin(valid_team)]

        # Additional filters (only apply if not restricted by unit)
        if doctor != 'all' and 'medico' in df.columns:
            df = df[df['medico'] == doctor]

        if equipe != 'all' and 'equipe' in df.columns:
            df = df[df['equipe'] == equipe]

        # Process filtered data
        dashboard_data = process_dashboard_data(df)

        # Log data being returned for debugging
        logger.info(f"Returning dashboard data with {len(df)} records")
        logger.info(f"Total surgeries: {dashboard_data['total_surgeries']}")

        return jsonify(dashboard_data)

    except Exception as e:
        logger.error(f"Error filtering dashboard data: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'labels': [],
            'datasets': [{'label': 'Cirurgias', 'data': []}],
            'has_follicle_data': False,
            'follicles_data': {'labels': [], 'averages': [], 'le_density': []},
            'total_surgeries': 0,
            'avg_follicles': 0,
            'avg_density': 0
        })

@app.route('/download_excel')
def download_excel():
    """Endpoint to download the Excel data file"""
    logger.info("Downloading Excel file")
    try:
        # Get data from database with explicit session
        with app.app_context():
            db.session.expire_all()  # Clear any stale data
            surgeries = db.session.query(Surgery).order_by(Surgery.data.desc()).all()
            logger.info(f"Found {len(surgeries)} records")

            # Convert to DataFrame with all fields
            data = []
            for surgery in surgeries:
                data.append({
                    'data': surgery.data,
                    'nome': surgery.nome,
                    'unidade': surgery.unidade,
                    'medico': surgery.medico,
                    'equipe': surgery.equipe,
                    'hora_cirurgia': surgery.hora_cirurgia,
                    'tempo_cirurgia': surgery.tempo_cirurgia,
                    'total_foliculos': surgery.total_foliculos,
                    'frente': surgery.frente,
                    'densidade_scketh': surgery.densidade_scketh,
                    'coroa': surgery.coroa,
                    'scalpe': surgery.scalpe,
                    'peninsula_direita': surgery.peninsula_direita,
                    'peninsula_esquerda': surgery.peninsula_esquerda,
                    # Campos da segunda página - Informações adicionais
                    'infiltracao': getattr(surgery, 'infiltracao', ''),
                    'tadalafila': getattr(surgery, 'tadalafila', ''),
                    'bloqueio_seringas': getattr(surgery, 'bloqueio_seringas', ''),
                    'fonte_1': getattr(surgery, 'fonte_1', ''),
                    'fonte_2': getattr(surgery, 'fonte_2', ''),
                    'fonte_3': getattr(surgery, 'fonte_3', ''),
                    'fonte_4': getattr(surgery, 'fonte_4', ''),
                    'fonte_5': getattr(surgery, 'fonte_5', ''),
                    'pelos_corporais': getattr(surgery, 'pelos_corporais', ''),
                    'tecnica': getattr(surgery, 'tecnica', ''),
                    'solucao_frente': getattr(surgery, 'solucao_frente', ''),
                    # Dados dos quadrantes
                    'q1_area': getattr(surgery, 'q1_area', 0),
                    'q1_furos': getattr(surgery, 'q1_furos', 0),
                    'q1_fios': getattr(surgery, 'q1_fios', 0),
                    'q1_densidade': getattr(surgery, 'q1_densidade', 0),
                    'q1_taxa_quebra': getattr(surgery, 'q1_taxa_quebra', 0),
                    'q2_area': getattr(surgery, 'q2_area', 0),
                    'q2_furos': getattr(surgery, 'q2_furos', 0),
                    'q2_fios': getattr(surgery, 'q2_fios', 0),
                    'q2_densidade': getattr(surgery, 'q2_densidade', 0),
                    'q2_taxa_quebra': getattr(surgery, 'q2_taxa_quebra', 0),
                    'q3_area': getattr(surgery, 'q3_area', 0),
                    'q3_furos': getattr(surgery, 'q3_furos', 0),
                    'q3_fios': getattr(surgery, 'q3_fios', 0),
                    'q3_densidade': getattr(surgery, 'q3_densidade', 0),
                    'q3_taxa_quebra': getattr(surgery, 'q3_taxa_quebra', 0),
                    'q4_area': getattr(surgery, 'q4_area', 0),
                    'q4_furos': getattr(surgery, 'q4_furos', 0),
                    'q4_fios': getattr(surgery, 'q4_fios', 0),
                    'q4_densidade': getattr(surgery, 'q4_densidade', 0),
                    'q4_taxa_quebra': getattr(surgery, 'q4_taxa_quebra', 0),
                    'densidade_extracao': getattr(surgery, 'densidade_extracao', 0),
                    'created_at': getattr(surgery, 'created_at', '')
                })

            df = pd.DataFrame(data)
            logger.info(f"DataFrame created with {len(df)} rows")

            # Save to temporary file
            temp_file = "temp_download.xlsx"
            df.to_excel(temp_file, index=False)

            # Return file and then delete it
            from flask import send_file
            return_data = send_file(
                temp_file,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='relatorio_cirurgias.xlsx'
            )

            # Delete temp file after sending
            try:
                os.remove(temp_file)
            except:
                pass
            return return_data
    except Exception as e:
        logger.error(f"Error downloading Excel file: {str(e)}\n{traceback.format_exc()}")
        flash(f"Erro ao baixar arquivo: {str(e)}", "error")
        return redirect(url_for('dashboard'))

@app.route('/download_complete_data')
def download_complete_data():
    """Endpoint para baixar dados completos do banco com todos os campos"""
    logger.info("Gerando exportação completa do banco de dados...")
    try:
        with app.app_context():
            # Buscar todas as cirurgias
            surgeries = Surgery.query.order_by(Surgery.data.desc()).all()
            logger.info(f"Encontrados {len(surgeries)} registros no banco")
            
            if not surgeries:
                flash("Nenhum dado encontrado no banco de dados", "error")
                return redirect(url_for('dashboard'))
            
            # Converter para lista de dicionários com TODOS os campos
            data_list = []
            for surgery in surgeries:
                surgery_dict = {
                    'ID': surgery.id,
                    'Data': surgery.data.strftime('%d/%m/%Y') if surgery.data else '',
                    'Paciente': surgery.nome or '',
                    'Unidade': surgery.unidade or '',
                    'Médico': surgery.medico or '',
                    'Equipe': surgery.equipe or '',
                    'Hora da Cirurgia': surgery.hora_cirurgia or '',
                    'Tempo de Cirurgia (horas)': surgery.tempo_cirurgia or 0,
                    'Total de Folículos': surgery.total_foliculos or 0,
                    'Frente': surgery.frente or 0,
                    'Densidade Scketh': surgery.densidade_scketh or 0,
                    'Coroa': surgery.coroa or 0,
                    'Scalpe': surgery.scalpe or 0,
                    'Península Direita': surgery.peninsula_direita or 0,
                    'Península Esquerda': surgery.peninsula_esquerda or 0,
                    'Infiltração': surgery.infiltracao or '',
                    'Sedação': getattr(surgery, 'sedacao', '') or '',
                    'Sangramento': getattr(surgery, 'sangramento', '') or '',
                    'Tadalafila': surgery.tadalafila or '',
                    'Bloqueio de Seringas': surgery.bloqueio_seringas or '',
                    'Fonte 1': surgery.fonte_1 or '',
                    'Fonte 2': surgery.fonte_2 or '',
                    'Fonte 3': surgery.fonte_3 or '',
                    'Fonte 4': surgery.fonte_4 or '',
                    'Fonte 5': surgery.fonte_5 or '',
                    'Pelos Corporais': surgery.pelos_corporais or '',
                    # Body hair detailed fields
                    'Barba Furos': getattr(surgery, 'barba_furos', 0) or 0,
                    'Barba Fios': getattr(surgery, 'barba_fios', 0) or 0,
                    'Barba Comentários': getattr(surgery, 'barba_comentarios', '') or '',
                    'Peitoral Furos': getattr(surgery, 'peitoral_furos', 0) or 0,
                    'Peitoral Fios': getattr(surgery, 'peitoral_fios', 0) or 0,
                    'Peitoral Comentários': getattr(surgery, 'peitoral_comentarios', '') or '',
                    'Abdome Furos': getattr(surgery, 'abdome_furos', 0) or 0,
                    'Abdome Fios': getattr(surgery, 'abdome_fios', 0) or 0,
                    'Abdome Comentários': getattr(surgery, 'abdome_comentarios', '') or '',
                    'Pernas Furos': getattr(surgery, 'pernas_furos', 0) or 0,
                    'Pernas Fios': getattr(surgery, 'pernas_fios', 0) or 0,
                    'Pernas Comentários': getattr(surgery, 'pernas_comentarios', '') or '',
                    'Técnica': surgery.tecnica or '',
                    'Solução Frente (ml)': surgery.solucao_frente or 0,
                    'Q1 Área': surgery.q1_area or 0,
                    'Q1 Furos': surgery.q1_furos or 0,
                    'Q1 Fios': surgery.q1_fios or 0,
                    'Q1 Densidade': surgery.q1_densidade or 0,
                    'Q1 Taxa Quebra': surgery.q1_taxa_quebra or 0,
                    'Q2 Área': surgery.q2_area or 0,
                    'Q2 Furos': surgery.q2_furos or 0,
                    'Q2 Fios': surgery.q2_fios or 0,
                    'Q2 Densidade': surgery.q2_densidade or 0,
                    'Q2 Taxa Quebra': surgery.q2_taxa_quebra or 0,
                    'Q3 Área': surgery.q3_area or 0,
                    'Q3 Furos': surgery.q3_furos or 0,
                    'Q3 Fios': surgery.q3_fios or 0,
                    'Q3 Densidade': surgery.q3_densidade or 0,
                    'Q3 Taxa Quebra': surgery.q3_taxa_quebra or 0,
                    'Q4 Área': surgery.q4_area or 0,
                    'Q4 Furos': surgery.q4_furos or 0,
                    'Q4 Fios': surgery.q4_fios or 0,
                    'Q4 Densidade': surgery.q4_densidade or 0,
                    'Q4 Taxa Quebra': surgery.q4_taxa_quebra or 0,
                    'Densidade Extração': surgery.densidade_extracao or 0,
                    'Data de Criação': surgery.created_at.strftime('%d/%m/%Y %H:%M:%S') if surgery.created_at else ''
                }
                data_list.append(surgery_dict)
            
            # Criar DataFrame e salvar em Excel
            df = pd.DataFrame(data_list)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"dados_completos_banco_{timestamp}.xlsx"
            temp_file = f"temp_{filename}"
            
            # Salvar no arquivo temporário
            df.to_excel(temp_file, index=False, engine='openpyxl')
            
            logger.info(f"Exportação criada com {len(data_list)} registros: {filename}")
            
            # Enviar arquivo e depois deletar
            return_data = send_file(
                temp_file,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
            
            # Limpar arquivo temporário
            try:
                os.remove(temp_file)
            except:
                pass
                
            return return_data
            
    except Exception as e:
        logger.error(f"Erro ao exportar dados completos: {str(e)}")
        logger.error(traceback.format_exc())
        flash(f"Erro ao exportar dados: {str(e)}", "error")
        return redirect(url_for('dashboard'))

@app.route('/reload_config')
def reload_config():
    """Endpoint para recarregar as configurações administrativas"""
    try:
        reload_admin_config()
        return jsonify({
            'success': True,
            'message': 'Configurações recarregadas com sucesso',
            'unidades': UNIDADES,
            'total_medicos': sum(len(m) for m in MEDICOS_POR_UNIDADE.values()),
            'total_equipe': sum(len(e) for e in EQUIPE_POR_UNIDADE.values())
        })
    except Exception as e:
        logger.error(f"Erro ao recarregar configurações: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/necrose')
def necrose():
    """Página de avaliação de necrose"""
    logger.info("Accessing necrose page")
    return render_template('necrose.html')

@app.route('/check_duplicate')
def check_duplicate():
    """Endpoint para verificar se um paciente já existe na mesma data"""
    try:
        nome = request.args.get('nome', '')
        data_str = request.args.get('data', '')
        
        if not nome or not data_str:
            return jsonify({"exists": False, "error": "Nome e data são obrigatórios"})
            
        # Converter data de string para objeto data
        try:
            # Espera o formato DD/MM/AAAA
            data = datetime.strptime(data_str, '%d/%m/%Y').date()
        except ValueError:
            return jsonify({"exists": False, "error": "Formato de data inválido. Use DD/MM/AAAA"})
            
        # Verificar se o paciente existe na mesma data
        with app.app_context():
            exists = Surgery.query.filter(
                Surgery.nome == nome,
                Surgery.data == data
            ).first() is not None
            
        return jsonify({"exists": exists})
    except Exception as e:
        logger.error(f"Erro ao verificar duplicata: {str(e)}")
        return jsonify({"exists": False, "error": str(e)})

@app.route('/search_patients')
def search_patients():
    """Endpoint para busca de pacientes com sugestões automáticas"""
    logger.info("Searching for patients")
    try:
        term = request.args.get('term', '').lower()
        unit = request.args.get('unit', '')

        if not term or len(term) < 2:
            return jsonify([])

        # Buscar dados dos pacientes diretamente do banco
        with app.app_context():
            # Construir query base
            query = Surgery.query
            
            # Filtrar por unidade se especificado
            if unit and unit.strip():
                query = query.filter(Surgery.unidade == unit)
            
            # Buscar pacientes que contenham o termo no nome
            query = query.filter(Surgery.nome.ilike(f'%{term}%'))
            
            # Executar query e ordenar por data mais recente
            surgeries = query.order_by(Surgery.data.desc()).limit(15).all()

        # Processar resultados
        patients = []
        for surgery in surgeries:
            patient_data = {
                'id': surgery.id,
                'nome': surgery.nome or '',
                'unidade': surgery.unidade or '',
                'data': surgery.data.strftime('%d/%m/%Y') if surgery.data else '',
                'total_foliculos': surgery.total_foliculos or 0,
                'densidade_scketh': surgery.densidade_scketh or 0,
                'infiltracao': surgery.infiltracao or '',
                'tadalafila': surgery.tadalafila or 'Não informado',
                'medico': surgery.medico or '',
                'equipe': surgery.equipe or ''
            }
            patients.append(patient_data)

        logger.info(f"Found {len(patients)} patients for term '{term}' in unit '{unit}'")
        return jsonify(patients)
        
    except Exception as e:
        logger.error(f"Error searching patients: {str(e)}\n{traceback.format_exc()}")
        return jsonify([])

@app.route('/necrose_summary')
def necrose_summary():
    """Endpoint para retornar o resumo de necroses do banco de dados"""
    logger.info("Getting necrose summary from database")
    try:
        with app.app_context():
            total_surgeries = Surgery.query.count()
            total_necroses = Necrose.query.filter_by(tem_necrose=True).count()
            
            necrose_rate = "0%"
            if total_surgeries > 0:
                taxa = (total_necroses / total_surgeries) * 100
                necrose_rate = f"{taxa:.1f}%"

            # Dados por unidade
            unit_data = {}
            units = db.session.query(Surgery.unidade.distinct()).all()
            
            for unit_tuple in units:
                unit = unit_tuple[0]
                if unit:
                    unit_surgeries = Surgery.query.filter_by(unidade=unit).count()
                    unit_necroses = Necrose.query.join(Surgery).filter(
                        Surgery.unidade == unit,
                        Necrose.tem_necrose == True
                    ).count()
                    
                    unit_rate = (unit_necroses / unit_surgeries * 100) if unit_surgeries > 0 else 0
                    
                    unit_data[unit] = {
                        'surgeries': unit_surgeries,
                        'necroses': unit_necroses,
                        'rate': f"{unit_rate:.1f}%"
                    }

            logger.info(f"Necrose summary: {total_surgeries} surgeries, {total_necroses} necroses, rate: {necrose_rate}")
            
            return jsonify({
                'total_surgeries': total_surgeries,
                'total_necroses': total_necroses,
                'necrose_rate': necrose_rate,
                'by_unit': unit_data
            })
    except Exception as e:
        logger.error(f"Error getting necrose summary: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'total_surgeries': 0,
            'total_necroses': 0,
            'necrose_rate': '0%',
            'by_unit': {},
            'error': str(e)
        })

@app.route('/save_necrose', methods=['POST'])
def save_necrose():
    """Endpoint para salvar dados de necrose com upload de fotos"""
    logger.info("Saving necrose data to database")
    logger.info(f"Form data received: {dict(request.form)}")
    logger.info(f"Files received: {list(request.files.keys())}")
    
    try:
        # Obter dados do formulário
        patient_id = request.form.get('patient_id')
        logger.info(f"Patient ID: {patient_id}")
        
        if not patient_id:
            logger.error("Patient ID is missing")
            return jsonify({
                'success': False,
                'message': 'ID do paciente é obrigatório'
            }), 400
        
        # Buscar dados da cirurgia
        surgery = Surgery.query.get(patient_id)
        if not surgery:
            return jsonify({
                'success': False,
                'message': 'Paciente não encontrado'
            }), 404
        
        # Verificar se já existe registro de necrose para este paciente
        existing_necrose = Necrose.query.filter_by(surgery_id=patient_id).first()
        
        # Validar campos obrigatórios
        data_avaliacao = request.form.get('data_avaliacao')
        numero_necroses = request.form.get('numero_necroses')
        
        logger.info(f"Data avaliacao: {data_avaliacao}")
        logger.info(f"Numero necroses: {numero_necroses}")
        
        if not data_avaliacao:
            logger.error("Data avaliacao is missing")
            return jsonify({'success': False, 'message': 'Data da avaliação é obrigatória'})
        
        if not numero_necroses:
            logger.error("Numero necroses is missing")
            return jsonify({'success': False, 'message': 'Número de necroses é obrigatório'})
            
        # Validar tamanhos baseado no número de necroses
        numero_necroses_int = int(numero_necroses)
        tamanhos = []
        for i in range(1, numero_necroses_int + 1):
            tamanho = request.form.get(f'tamanho_{i}_cm')
            if not tamanho:
                return jsonify({'success': False, 'message': f'Tamanho da {i}ª necrose é obrigatório'})
            tamanhos.append(float(tamanho))
        
        # Verificar se pelo menos uma faixa foi selecionada
        faixas_selecionadas = [
            request.form.get('primeira_faixa') == 'true',
            request.form.get('segunda_faixa') == 'true', 
            request.form.get('terceira_faixa') == 'true',
            request.form.get('coroa') == 'true'
        ]
        
        if not any(faixas_selecionadas):
            return jsonify({'success': False, 'message': 'Selecione pelo menos uma faixa acometida'})
        
        # Regiões acometidas
        primeira_faixa = request.form.get('primeira_faixa') == 'true'
        segunda_faixa = request.form.get('segunda_faixa') == 'true'
        terceira_faixa = request.form.get('terceira_faixa') == 'true'
        coroa_acometida = request.form.get('coroa') == 'true'
        data_avaliacao_date = datetime.strptime(data_avaliacao, '%Y-%m-%d').date()
        medico_responsavel = surgery.medico  # Pega o médico da cirurgia
        
        # Processar fotos
        photos = request.files.getlist('fotos_necrose')
        # Filtrar fotos vazias (quando nenhum arquivo é selecionado, Flask pode retornar um arquivo vazio)
        photos = [photo for photo in photos if photo and photo.filename and photo.filename.strip()]
        logger.info(f"Number of valid photos received: {len(photos)}")
        
        # Validar número de fotos - permitir 0 ou mais fotos (até 3)
        if len(photos) > 3:
            return jsonify({'success': False, 'message': 'Máximo de 3 fotos permitidas'})
        
        if existing_necrose:
            # Atualizar registro existente
            existing_necrose.tem_necrose = True
            existing_necrose.numero_necroses = numero_necroses_int
            existing_necrose.primeira_faixa = primeira_faixa
            existing_necrose.segunda_faixa = segunda_faixa
            existing_necrose.terceira_faixa = terceira_faixa
            existing_necrose.coroa = coroa_acometida
            existing_necrose.data_avaliacao = data_avaliacao_date
            existing_necrose.medico_responsavel = medico_responsavel
            existing_necrose.status = 'Em acompanhamento'
            
            # Atualizar tamanhos
            existing_necrose.tamanho_1_cm = tamanhos[0] if len(tamanhos) > 0 else None
            existing_necrose.tamanho_2_cm = tamanhos[1] if len(tamanhos) > 1 else None
            existing_necrose.tamanho_3_cm = tamanhos[2] if len(tamanhos) > 2 else None
            existing_necrose.tamanho_4_cm = tamanhos[3] if len(tamanhos) > 3 else None
            
            existing_necrose.updated_at = datetime.utcnow()
            necrose_record = existing_necrose
        else:
            # Criar novo registro
            necrose_record = Necrose(
                surgery_id=patient_id,
                unidade=surgery.unidade,
                paciente_nome=surgery.nome,
                data_cirurgia=surgery.data,
                data_avaliacao=data_avaliacao_date,
                medico_responsavel=medico_responsavel,
                tem_necrose=True,
                numero_necroses=numero_necroses_int,
                primeira_faixa=primeira_faixa,
                segunda_faixa=segunda_faixa,
                terceira_faixa=terceira_faixa,
                coroa=coroa_acometida,
                status='Em acompanhamento',
                tamanho_1_cm=tamanhos[0] if len(tamanhos) > 0 else None,
                tamanho_2_cm=tamanhos[1] if len(tamanhos) > 1 else None,
                tamanho_3_cm=tamanhos[2] if len(tamanhos) > 2 else None,
                tamanho_4_cm=tamanhos[3] if len(tamanhos) > 3 else None
            )
            db.session.add(necrose_record)
        
        # Salvar no banco antes de processar fotos
        db.session.commit()
        
        # Processar upload de fotos
        uploaded_files = []
        # Usar as fotos já filtradas anteriormente
        
        for photo in photos:
            if photo and photo.filename:
                if allowed_file(photo.filename):
                    # Gerar nome único para o arquivo
                    filename = secure_filename(photo.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    
                    # Criar diretório se não existir
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                    # Salvar arquivo
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    photo.save(file_path)
                    
                    # Salvar informações da foto no banco
                    photo_record = NecrosePhoto(
                        necrose_id=necrose_record.id,
                        filename=unique_filename,
                        original_filename=filename,
                        file_path=file_path,
                        file_size=os.path.getsize(file_path),
                        mime_type=mimetypes.guess_type(filename)[0] or 'image/jpeg',
                        description=request.form.get(f'photo_description_{photos.index(photo)}', '')
                    )
                    db.session.add(photo_record)
                    uploaded_files.append(unique_filename)
        
        # Commit final
        db.session.commit()
        
        logger.info(f"Dados de necrose salvos para paciente: {surgery.nome} (ID: {patient_id})")
        if uploaded_files:
            logger.info(f"Fotos carregadas: {uploaded_files}")
        
        # Disparar backup automático após salvar necrose
        try:
            logger.info("Iniciando backup automático após registro de necrose...")
            backup_success, backup_message = trigger_automatic_backup()
            if backup_success:
                logger.info(f"✅ Backup automático realizado: {backup_message}")
            else:
                logger.warning(f"⚠️ Backup automático falhou: {backup_message}")
        except Exception as backup_error:
            logger.error(f"Erro no backup automático: {backup_error}")
        
        return jsonify({
            'success': True,
            'message': f'Necrose registrada com sucesso! {len(uploaded_files)} foto(s) carregada(s).',
            'necrose_id': necrose_record.id,
            'photos_uploaded': len(uploaded_files)
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao salvar dados de necrose: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao salvar dados: {str(e)}'
        }), 500

def allowed_file(filename):
    """Verificar se o arquivo é uma imagem permitida"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/necrose_analise')
def necrose_analise():
    """Página de análise de dados de necrose"""
    return render_template('necrose_analise.html')

@app.route('/api/necrose_analise_data')
def api_necrose_analise_data():
    """API para dados de análise de necrose"""
    try:
        # Buscar dados de necroses com dados das cirurgias e fotos
        necroses_data = db.session.query(Necrose, Surgery).join(
            Surgery, Necrose.surgery_id == Surgery.id
        ).all()
        
        # Organizar dados para cards
        analysis_cards = []
        for necrose, surgery in necroses_data:
            # Calcular tamanho total das necroses
            tamanhos = [necrose.tamanho_1_cm, necrose.tamanho_2_cm, necrose.tamanho_3_cm, necrose.tamanho_4_cm]
            tamanho_total = sum(t for t in tamanhos if t is not None)
            
            # Identificar faixas acometidas
            faixas_acometidas = []
            if necrose.primeira_faixa:
                faixas_acometidas.append("1ª Faixa")
            if necrose.segunda_faixa:
                faixas_acometidas.append("2ª Faixa")
            if necrose.terceira_faixa:
                faixas_acometidas.append("3ª Faixa")
            if necrose.coroa:
                faixas_acometidas.append("Coroa")
            
            # Buscar fotos associadas a esta necrose
            photos = NecrosePhoto.query.filter_by(necrose_id=necrose.id).all()
            photo_thumbnails = []
            for photo in photos:
                photo_thumbnails.append({
                    'id': photo.id,
                    'filename': photo.filename,
                    'path': photo.file_path or f'/static/uploads/necrose_photos/{photo.filename}',
                    'description': photo.description or 'Foto da necrose'
                })
            
            card_data = {
                'id': necrose.id,
                'paciente_nome': necrose.paciente_nome,
                'unidade': necrose.unidade,
                'data_cirurgia': necrose.data_cirurgia.strftime('%d/%m/%Y') if necrose.data_cirurgia else '',
                'data_avaliacao': necrose.data_avaliacao.strftime('%d/%m/%Y') if necrose.data_avaliacao else '',
                'medico_responsavel': necrose.medico_responsavel,
                'grau_necrose': necrose.grau_necrose,
                'numero_necroses': necrose.numero_necroses,
                'tamanho_total': round(tamanho_total, 2),
                'faixas_acometidas': ', '.join(faixas_acometidas),
                'infiltracao': surgery.infiltracao,
                'sangramento': surgery.sangramento,
                'tempo_cirurgia': surgery.tempo_cirurgia,
                'tadalafila': surgery.tadalafila,
                'solucao_frente': surgery.solucao_frente,
                'tecnica': surgery.tecnica,
                'photos': photo_thumbnails
            }
            analysis_cards.append(card_data)
        
        # Calcular estatísticas por unidade
        stats_by_unit = {}
        all_units = set()
        
        for necrose, surgery in necroses_data:
            unit = necrose.unidade
            all_units.add(unit)
            
            if unit not in stats_by_unit:
                stats_by_unit[unit] = {
                    'total_casos': 0,
                    'casos_leves': 0,
                    'casos_moderados': 0,
                    'casos_severos': 0,
                    'tamanho_medio': 0.0,
                    'total_tamanhos': []
                }
            
            stats_by_unit[unit]['total_casos'] += 1
            
            # Contar por grau
            grau = necrose.grau_necrose.lower() if necrose.grau_necrose else ''
            if 'leve' in grau:
                stats_by_unit[unit]['casos_leves'] += 1
            elif 'moderada' in grau or 'moderado' in grau:
                stats_by_unit[unit]['casos_moderados'] += 1
            elif 'severa' in grau or 'severo' in grau:
                stats_by_unit[unit]['casos_severos'] += 1
            
            # Calcular tamanho total da necrose
            tamanhos = [necrose.tamanho_1_cm, necrose.tamanho_2_cm, necrose.tamanho_3_cm, necrose.tamanho_4_cm]
            tamanho_total = sum(t for t in tamanhos if t is not None)
            if tamanho_total > 0:
                stats_by_unit[unit]['total_tamanhos'].append(tamanho_total)
        
        # Calcular tamanho médio para cada unidade
        for unit_stats in stats_by_unit.values():
            if unit_stats['total_tamanhos']:
                unit_stats['tamanho_medio'] = round(
                    sum(unit_stats['total_tamanhos']) / len(unit_stats['total_tamanhos']), 2
                )
            del unit_stats['total_tamanhos']  # Remover array temporário
        
        # Carregar todas as unidades disponíveis da configuração
        reload_admin_config()
        all_configured_units = UNIDADES

        return jsonify({
            'success': True,
            'data': analysis_cards,
            'total_casos': len(analysis_cards),
            'stats_by_unit': stats_by_unit,
            'all_units': list(all_configured_units)
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados de análise de necrose: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/necrose_statistics')
def api_necrose_statistics():
    """API para estatísticas específicas de necrose"""
    try:
        # Buscar todos os dados de cirurgias e necroses
        surgeries = Surgery.query.all()
        necroses = Necrose.query.all()
        necroses_with_surgery = db.session.query(Necrose, Surgery).join(
            Surgery, Necrose.surgery_id == Surgery.id
        ).all()
        
        # Inicializar contadores
        total_casos = len(necroses)
        densidade_primeira_faixa = []
        solucao_frente_values = []
        infiltracao_values = []
        sangramento_values = []
        transamin_count = 0
        tadalafil_count = 0
        
        # Processar dados das cirurgias associadas a necroses
        for necrose, surgery in necroses_with_surgery:
            # Densidade da primeira faixa (q1_densidade ou densidade_scketh)
            if hasattr(surgery, 'q1_densidade') and surgery.q1_densidade:
                try:
                    densidade_primeira_faixa.append(float(surgery.q1_densidade))
                except (ValueError, TypeError):
                    pass
            elif hasattr(surgery, 'densidade_scketh') and surgery.densidade_scketh:
                try:
                    densidade_primeira_faixa.append(float(surgery.densidade_scketh))
                except (ValueError, TypeError):
                    pass
            
            # Solução frente
            if surgery.solucao_frente:
                try:
                    solucao_frente_values.append(float(surgery.solucao_frente))
                except (ValueError, TypeError):
                    pass
            
            # Infiltração
            if surgery.infiltracao:
                try:
                    infiltracao_values.append(float(surgery.infiltracao))
                except (ValueError, TypeError):
                    pass
            
            # Sangramento
            if surgery.sangramento:
                try:
                    sangramento_values.append(float(surgery.sangramento))
                except (ValueError, TypeError):
                    pass
            
            # Transamin (buscar nos campos da cirurgia)
            surgery_dict = surgery.__dict__
            for key, value in surgery_dict.items():
                if 'transamin' in str(key).lower() and value and str(value).lower() in ['sim', 'yes', 'true', '1']:
                    transamin_count += 1
                    break
            
            # Tadalafil
            if surgery.tadalafila and str(surgery.tadalafila).lower() in ['sim', 'yes', 'true', '1']:
                tadalafil_count += 1
        
        # Calcular médias
        media_densidade = round(sum(densidade_primeira_faixa) / len(densidade_primeira_faixa), 2) if densidade_primeira_faixa else 0
        media_solucao_frente = round(sum(solucao_frente_values) / len(solucao_frente_values), 2) if solucao_frente_values else 0
        media_infiltracao = round(sum(infiltracao_values) / len(infiltracao_values), 2) if infiltracao_values else 0
        media_sangramento = round(sum(sangramento_values) / len(sangramento_values), 2) if sangramento_values else 0
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_casos': total_casos,
                'media_densidade_primeira_faixa': media_densidade,
                'media_solucao_frente': media_solucao_frente,
                'media_infiltracao': media_infiltracao,
                'media_sangramento': media_sangramento,
                'casos_com_transamin': transamin_count,
                'casos_com_tadalafil': tadalafil_count
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas de necrose: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/registered_necrose_patients')
def api_registered_necrose_patients():
    """API para listar pacientes com necrose cadastrada"""
    try:
        # Buscar todos os registros de necrose com dados das cirurgias e fotos
        necroses_data = db.session.query(Necrose, Surgery).join(
            Surgery, Necrose.surgery_id == Surgery.id
        ).order_by(Necrose.created_at.desc()).all()
        
        patients_data = []
        for necrose, surgery in necroses_data:
            # Calcular tamanho total das necroses
            tamanhos = [necrose.tamanho_1_cm, necrose.tamanho_2_cm, necrose.tamanho_3_cm, necrose.tamanho_4_cm]
            tamanho_total = sum(t for t in tamanhos if t is not None)
            
            # Identificar faixas acometidas
            faixas_acometidas = []
            if necrose.primeira_faixa:
                faixas_acometidas.append("1ª Faixa")
            if necrose.segunda_faixa:
                faixas_acometidas.append("2ª Faixa")
            if necrose.terceira_faixa:
                faixas_acometidas.append("3ª Faixa")
            if necrose.coroa:
                faixas_acometidas.append("Coroa")
            
            # Buscar fotos associadas a esta necrose
            photos = NecrosePhoto.query.filter_by(necrose_id=necrose.id).all()
            photo_data = []
            logger.info(f"Buscando fotos para necrose ID {necrose.id}: {len(photos)} fotos encontradas")
            
            for photo in photos:
                # Construir caminho da foto
                if photo.file_path:
                    if photo.file_path.startswith('http'):
                        # Link direto do Dropbox
                        web_path = photo.file_path
                        storage_type = 'dropbox'
                        exists = True  # Assumir que existe no Dropbox
                    elif photo.file_path.startswith('dropbox:'):
                        # Path do Dropbox sem link direto
                        web_path = photo.file_path
                        storage_type = 'dropbox'
                        exists = True
                    else:
                        # Arquivo local
                        web_path = photo.file_path if photo.file_path.startswith('/') else f'/{photo.file_path}'
                        file_path = photo.file_path.lstrip('/')
                        storage_type = 'local'
                        exists = os.path.exists(file_path)
                else:
                    # Fallback para caminho padrão
                    file_path = f'static/uploads/necrose_photos/{photo.filename}'
                    web_path = f'/{file_path}'
                    storage_type = 'local'
                    exists = os.path.exists(file_path)
                
                logger.info(f"Verificando foto: {photo.filename} -> {web_path} ({storage_type})")
                
                # Adicionar foto
                photo_data.append({
                    'id': photo.id,
                    'filename': photo.filename,
                    'path': web_path,
                    'description': photo.description or f'Foto {photo.id} da necrose',
                    'storage': storage_type,
                    'exists': exists
                })
            
            patient_info = {
                'id': necrose.id,
                'paciente_nome': necrose.paciente_nome,
                'unidade': necrose.unidade,
                'data_cirurgia': necrose.data_cirurgia.strftime('%d/%m/%Y') if necrose.data_cirurgia else '',
                'data_avaliacao': necrose.data_avaliacao.strftime('%d/%m/%Y') if necrose.data_avaliacao else '',
                'medico_responsavel': necrose.medico_responsavel,
                'numero_necroses': necrose.numero_necroses,
                'tamanho_total': f"{tamanho_total:.1f}" if tamanho_total > 0 else "0.0",
                'grau_necrose': necrose.grau_necrose or 'Não informado',
                'faixas_acometidas': ', '.join(faixas_acometidas) if faixas_acometidas else 'Nenhuma',
                'status': necrose.status or 'Em acompanhamento',
                'photos': photo_data
            }
            patients_data.append(patient_info)
        
        return jsonify({
            'success': True,
            'patients': patients_data
        })
        
    except Exception as e:
        logger.error(f"Error getting registered necrose patients: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/upload_necrose_photos', methods=['POST'])
def api_upload_necrose_photos():
    """API para fazer upload de fotos adicionais para necrose"""
    try:
        necrose_id = request.form.get('necrose_id')
        description = request.form.get('description', '')
        
        if not necrose_id:
            return jsonify({
                'success': False,
                'error': 'ID da necrose é obrigatório'
            }), 400
            
        # Verificar se a necrose existe
        necrose = Necrose.query.get(necrose_id)
        if not necrose:
            return jsonify({
                'success': False,
                'error': 'Registro de necrose não encontrado'
            }), 404
            
        # Verificar se há fotos para upload
        if 'photos' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nenhuma foto foi enviada'
            }), 400
            
        photos = request.files.getlist('photos')
        if not photos or len(photos) == 0:
            return jsonify({
                'success': False,
                'error': 'Nenhuma foto foi selecionada'
            }), 400
            
        if len(photos) > 3:
            return jsonify({
                'success': False,
                'error': 'Máximo de 3 fotos por vez'
            }), 400
            
        # Criar diretório local temporário
        temp_dir = 'static/uploads/necrose_photos'
        os.makedirs(temp_dir, exist_ok=True)
        
        uploaded_photos = []
        
        # Configurar Dropbox
        try:
            import dropbox
            dropbox_token = os.environ.get('DROPBOX_ACCESS_TOKEN')
            if dropbox_token:
                dbx = dropbox.Dropbox(dropbox_token)
                use_dropbox = True
                logger.info("Dropbox configurado para upload de fotos de necrose")
            else:
                use_dropbox = False
                logger.warning("DROPBOX_ACCESS_TOKEN não encontrado, usando armazenamento local")
        except ImportError:
            use_dropbox = False
            logger.warning("Módulo dropbox não disponível, usando armazenamento local")
        
        for photo in photos:
            if photo and photo.filename:
                # Gerar nome único para o arquivo
                file_extension = photo.filename.rsplit('.', 1)[1].lower() if '.' in photo.filename else 'jpg'
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"necrose_{necrose_id}_{timestamp}_{uuid.uuid4().hex[:8]}.{file_extension}"
                
                # Salvar temporariamente no local
                temp_file_path = os.path.join(temp_dir, unique_filename)
                photo.save(temp_file_path)
                
                if use_dropbox:
                    try:
                        # Upload para Dropbox na pasta específica de necrose
                        dropbox_path = f"/fotos_necrose/{unique_filename}"
                        
                        with open(temp_file_path, 'rb') as f:
                            dbx.files_upload(
                                f.read(),
                                dropbox_path,
                                mode=dropbox.files.WriteMode.overwrite
                            )
                        
                        # Obter link compartilhável
                        try:
                            shared_link = dbx.sharing_create_shared_link(dropbox_path)
                            # Converter para link direto
                            direct_link = shared_link.url.replace('dl=0', 'dl=1')
                            file_path = direct_link
                            logger.info(f"Foto uploaded para Dropbox: {dropbox_path}")
                        except:
                            # Fallback para path do Dropbox
                            file_path = f"dropbox:{dropbox_path}"
                        
                        # Remover arquivo temporário
                        os.remove(temp_file_path)
                        
                    except Exception as e:
                        logger.error(f"Erro ao fazer upload para Dropbox: {e}")
                        # Manter arquivo local como fallback
                        file_path = f"/{temp_file_path}"
                else:
                    # Usar armazenamento local
                    file_path = f"/{temp_file_path}"
                
                # Salvar no banco de dados
                new_photo = NecrosePhoto(
                    necrose_id=necrose_id,
                    filename=unique_filename,
                    file_path=file_path,
                    description=description
                )
                db.session.add(new_photo)
                
                uploaded_photos.append({
                    'filename': unique_filename,
                    'path': file_path,
                    'storage': 'dropbox' if use_dropbox and file_path.startswith('http') else 'local'
                })
                
        db.session.commit()
        logger.info(f"Uploaded {len(uploaded_photos)} photos for necrose ID {necrose_id}")
        
        storage_info = "no Dropbox" if use_dropbox else "localmente"
        return jsonify({
            'success': True,
            'message': f'{len(uploaded_photos)} fotos anexadas com sucesso {storage_info}',
            'photos': uploaded_photos,
            'storage_type': 'dropbox' if use_dropbox else 'local'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error uploading photos for necrose: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/delete_necrose/<int:necrose_id>', methods=['DELETE'])
def api_delete_necrose(necrose_id):
    """API para excluir registro de necrose"""
    try:
        # Buscar o registro de necrose
        necrose = Necrose.query.get(necrose_id)
        if not necrose:
            return jsonify({
                'success': False,
                'error': 'Registro de necrose não encontrado'
            }), 404
        
        # Buscar e excluir fotos associadas
        photos = NecrosePhoto.query.filter_by(necrose_id=necrose_id).all()
        
        for photo in photos:
            # Excluir arquivo físico se existir
            if photo.file_path and os.path.exists(photo.file_path):
                try:
                    os.remove(photo.file_path)
                    logger.info(f"Arquivo de foto excluído: {photo.file_path}")
                except Exception as e:
                    logger.warning(f"Erro ao excluir arquivo de foto {photo.file_path}: {str(e)}")
            
            # Excluir registro da foto do banco
            db.session.delete(photo)
        
        # Armazenar informações para log
        patient_name = necrose.paciente_nome
        patient_unit = necrose.unidade
        
        # Excluir registro de necrose
        db.session.delete(necrose)
        db.session.commit()
        
        logger.info(f"Registro de necrose excluído: Paciente {patient_name} da unidade {patient_unit}")
        
        return jsonify({
            'success': True,
            'message': f'Registro de necrose de {patient_name} excluído com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting necrose record {necrose_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao excluir registro: {str(e)}'
        }), 500

@app.route('/download_combined_data')
def download_combined_data():
    """Endpoint para baixar dados combinados de cirurgia e necrose em Excel"""
    logger.info("Gerando exportação combinada de cirurgia e necrose...")
    
    # Obter filtros da query string
    unit_filter = request.args.get('unit')
    month_filter = request.args.get('month')
    year_filter = request.args.get('year')
    try:
        with app.app_context():
            # Buscar todas as cirurgias com LEFT JOIN para incluir dados de necrose
            query = db.session.query(Surgery, Necrose).outerjoin(
                Necrose, Surgery.id == Necrose.surgery_id
            ).order_by(Surgery.data.desc())
            
            results = query.all()
            logger.info(f"Encontrados {len(results)} registros para exportação")
            
            if not results:
                flash("Nenhum dado encontrado no banco de dados", "error")
                return redirect(url_for('necrose'))
            
            # Converter para lista de dicionários combinando dados de cirurgia e necrose
            data_list = []
            for surgery, necrose in results:
                combined_dict = {
                    # Dados da Cirurgia
                    'ID Cirurgia': surgery.id,
                    'Data da Cirurgia': surgery.data.strftime('%d/%m/%Y') if surgery.data else '',
                    'Paciente': surgery.nome or '',
                    'Unidade': surgery.unidade or '',
                    'Médico': surgery.medico or '',
                    'Equipe': surgery.equipe or '',
                    'Hora da Cirurgia': surgery.hora_cirurgia or '',
                    'Tempo de Cirurgia (horas)': surgery.tempo_cirurgia or 0,
                    'Total de Folículos': surgery.total_foliculos or 0,
                    'Frente': surgery.frente or 0,
                    'Densidade Scketh': surgery.densidade_scketh or 0,
                    'Coroa': surgery.coroa or 0,
                    'Scalpe': surgery.scalpe or 0,
                    'Península Direita': surgery.peninsula_direita or 0,
                    'Península Esquerda': surgery.peninsula_esquerda or 0,
                    'Infiltração': surgery.infiltracao or '',
                    'Sedação': getattr(surgery, 'sedacao', '') or '',
                    'Sangramento': getattr(surgery, 'sangramento', '') or '',
                    'Tadalafila': surgery.tadalafila or '',
                    'Bloqueio de Seringas': surgery.bloqueio_seringas or '',
                    'Técnica': surgery.tecnica or '',
                    'Solução Frente (ml)': surgery.solucao_frente or 0,
                    'Q1 Área': surgery.q1_area or 0,
                    'Q1 Furos': surgery.q1_furos or 0,
                    'Q1 Fios': surgery.q1_fios or 0,
                    'Q1 Densidade': surgery.q1_densidade or 0,
                    'Q1 Taxa Quebra': surgery.q1_taxa_quebra or 0,
                    'Q2 Área': surgery.q2_area or 0,
                    'Q2 Furos': surgery.q2_furos or 0,
                    'Q2 Fios': surgery.q2_fios or 0,
                    'Q2 Densidade': surgery.q2_densidade or 0,
                    'Q2 Taxa Quebra': surgery.q2_taxa_quebra or 0,
                    'Q3 Área': surgery.q3_area or 0,
                    'Q3 Furos': surgery.q3_furos or 0,
                    'Q3 Fios': surgery.q3_fios or 0,
                    'Q3 Densidade': surgery.q3_densidade or 0,
                    'Q3 Taxa Quebra': surgery.q3_taxa_quebra or 0,
                    'Q4 Área': surgery.q4_area or 0,
                    'Q4 Furos': surgery.q4_furos or 0,
                    'Q4 Fios': surgery.q4_fios or 0,
                    'Q4 Densidade': surgery.q4_densidade or 0,
                    'Q4 Taxa Quebra': surgery.q4_taxa_quebra or 0,
                    'Densidade Extração': surgery.densidade_extracao or 0,
                    'Data de Criação': surgery.created_at.strftime('%d/%m/%Y %H:%M:%S') if surgery.created_at else '',
                    
                    # Dados da Necrose
                    'Tem Necrose': 'Sim' if necrose and necrose.tem_necrose else 'Não',
                    'Número de Necrose': necrose.numero_necroses if necrose else '',
                    'Data Avaliação Necrose': necrose.data_avaliacao.strftime('%d/%m/%Y') if necrose and necrose.data_avaliacao else '',
                    'Médico Responsável Necrose': necrose.medico_responsavel if necrose else '',
                    'Grau da Necrose': necrose.grau_necrose if necrose else '',
                    
                    # Regiões Acometidas
                    'Primeira Faixa Acometida': 'Sim' if necrose and necrose.primeira_faixa else 'Não',
                    'Segunda Faixa Acometida': 'Sim' if necrose and necrose.segunda_faixa else 'Não',
                    'Terceira Faixa Acometida': 'Sim' if necrose and necrose.terceira_faixa else 'Não',
                    'Coroa Acometida': 'Sim' if necrose and necrose.coroa else 'Não',
                    
                    'Localização Detalhada': necrose.localizacao if necrose else '',
                    'Tamanho da Necrose (mm)': necrose.tamanho_mm if necrose else '',
                    'Descrição da Necrose': necrose.descricao if necrose else '',
                    'Tratamento Aplicado': necrose.tratamento_aplicado if necrose else '',
                    'Observações Necrose': necrose.observacoes if necrose else '',
                    'Status da Necrose': necrose.status if necrose else '',
                    'Data Resolução': necrose.data_resolucao.strftime('%d/%m/%Y') if necrose and necrose.data_resolucao else '',
                    'Necrose Criada em': necrose.created_at.strftime('%d/%m/%Y %H:%M:%S') if necrose and necrose.created_at else '',
                    'Necrose Atualizada em': necrose.updated_at.strftime('%d/%m/%Y %H:%M:%S') if necrose and necrose.updated_at else '',
                    
                    # Informações sobre as 3 fotos obrigatórias para avaliação futura
                    'Fotos para Avaliação Futura': len(necrose.photos) if necrose and hasattr(necrose, 'photos') else 0,
                    'Arquivos das 3 Fotos': ', '.join([photo.filename for photo in necrose.photos]) if necrose and hasattr(necrose, 'photos') else ''
                }
                data_list.append(combined_dict)
            
            # Criar DataFrame e salvar em Excel
            df = pd.DataFrame(data_list)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"dados_cirurgia_necrose_{timestamp}.xlsx"
            temp_file = f"temp_{filename}"
            
            # Salvar no arquivo temporário
            df.to_excel(temp_file, index=False, engine='openpyxl')
            
            logger.info(f"Exportação combinada criada com {len(data_list)} registros: {filename}")
            
            # Enviar arquivo e depois deletar
            return_data = send_file(
                temp_file,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
            
            # Agendar remoção do arquivo temporário
            import threading
            def remove_temp_file():
                try:
                    import time
                    time.sleep(2)  # Aguardar download
                    os.remove(temp_file)
                except:
                    pass
            
            threading.Thread(target=remove_temp_file).start()
            
            return return_data
            
    except Exception as e:
        logger.error(f"Erro ao gerar exportação combinada: {str(e)}\n{traceback.format_exc()}")
        flash(f"Erro ao gerar arquivo: {str(e)}", "error")
        return redirect(url_for('necrose'))

# Rotas do Dashboard Médicos
@app.route('/medicos/login', methods=['GET', 'POST'])
def login_medicos():
    """Login para dashboard médicos"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '54321':
            session['medicos_logged_in'] = True
            return redirect(url_for('dashboard_medicos'))
        else:
            flash('Senha incorreta', 'error')
    
    return render_template('login_medicos.html')

@app.route('/medicos/dashboard')
def dashboard_medicos():
    """Dashboard médicos - requer autenticação"""
    if not session.get('medicos_logged_in'):
        return redirect(url_for('login_medicos'))
    
    return render_template('dashboard_medicos.html')

@app.route('/medicos/logout')
def logout_medicos():
    """Logout do dashboard médicos"""
    session.pop('medicos_logged_in', None)
    return redirect(url_for('login_medicos'))

@app.route('/medicos/dashboard_data')
def get_medicos_dashboard_data():
    """Endpoint para dados do dashboard médicos"""
    if not session.get('medicos_logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    try:
        unit_filter = request.args.get('unit', 'all')
        
        with app.app_context():
            # Construir query base
            query = Surgery.query
            
            # Aplicar filtro de unidade se especificado
            if unit_filter != 'all':
                query = query.filter(Surgery.unidade == unit_filter)
            
            surgeries = query.all()
            
            # Calcular estatísticas
            total_surgeries = len(surgeries)
            
            # Coletar dados de furos e taxa de quebra por quadrante
            q1_furos = []
            q2_furos = []
            q3_furos = []
            q4_furos = []
            q1_taxas = []
            q2_taxas = []
            q3_taxas = []
            q4_taxas = []
            
            # Extrair dados reais dos quadrantes (apenas valores > 0)
            for surgery in surgeries:
                if hasattr(surgery, 'q1_furos') and surgery.q1_furos is not None and surgery.q1_furos > 0:
                    q1_furos.append(surgery.q1_furos)
                if hasattr(surgery, 'q2_furos') and surgery.q2_furos is not None and surgery.q2_furos > 0:
                    q2_furos.append(surgery.q2_furos)
                if hasattr(surgery, 'q3_furos') and surgery.q3_furos is not None and surgery.q3_furos > 0:
                    q3_furos.append(surgery.q3_furos)
                if hasattr(surgery, 'q4_furos') and surgery.q4_furos is not None and surgery.q4_furos > 0:
                    q4_furos.append(surgery.q4_furos)
                    
                if hasattr(surgery, 'q1_taxa_quebra') and surgery.q1_taxa_quebra is not None and surgery.q1_taxa_quebra >= 0:
                    q1_taxas.append(surgery.q1_taxa_quebra)
                if hasattr(surgery, 'q2_taxa_quebra') and surgery.q2_taxa_quebra is not None and surgery.q2_taxa_quebra >= 0:
                    q2_taxas.append(surgery.q2_taxa_quebra)
                if hasattr(surgery, 'q3_taxa_quebra') and surgery.q3_taxa_quebra is not None and surgery.q3_taxa_quebra >= 0:
                    q3_taxas.append(surgery.q3_taxa_quebra)
                if hasattr(surgery, 'q4_taxa_quebra') and surgery.q4_taxa_quebra is not None and surgery.q4_taxa_quebra >= 0:
                    q4_taxas.append(surgery.q4_taxa_quebra)
            
            # Calcular máximos de furos por quadrante
            max_q1 = max(q1_furos) if q1_furos else 0
            max_q2 = max(q2_furos) if q2_furos else 0
            max_q3 = max(q3_furos) if q3_furos else 0
            max_q4 = max(q4_furos) if q4_furos else 0
            
            # Calcular taxa média de quebra por quadrante (converter decimal para porcentagem)
            avg_q1_taxa = round((sum(q1_taxas) / len(q1_taxas)) * 100, 2) if q1_taxas else 0
            avg_q2_taxa = round((sum(q2_taxas) / len(q2_taxas)) * 100, 2) if q2_taxas else 0
            avg_q3_taxa = round((sum(q3_taxas) / len(q3_taxas)) * 100, 2) if q3_taxas else 0
            avg_q4_taxa = round((sum(q4_taxas) / len(q4_taxas)) * 100, 2) if q4_taxas else 0
            
            breakage_rates = [avg_q1_taxa, avg_q2_taxa, avg_q3_taxa, avg_q4_taxa]
            
            # Taxa média geral de quebra (converter decimal para porcentagem)
            all_taxas = q1_taxas + q2_taxas + q3_taxas + q4_taxas
            avg_breakage_rate = round((sum(all_taxas) / len(all_taxas)) * 100, 2) if all_taxas else 0
            
            # Coletar dados de densidade de extração (apenas valores > 0)
            densidades_extracao = []
            for surgery in surgeries:
                if hasattr(surgery, 'densidade_extracao') and surgery.densidade_extracao is not None and surgery.densidade_extracao > 0:
                    densidades_extracao.append(surgery.densidade_extracao)
            
            avg_densidade_extracao = round(sum(densidades_extracao) / len(densidades_extracao), 2) if densidades_extracao else 0
            
            # Coletar dados de tempo de cirurgia (apenas valores > 0)
            tempos_cirurgia = []
            for surgery in surgeries:
                if hasattr(surgery, 'tempo_cirurgia') and surgery.tempo_cirurgia is not None and surgery.tempo_cirurgia > 0:
                    tempos_cirurgia.append(surgery.tempo_cirurgia)
            
            avg_tempo_cirurgia = round(sum(tempos_cirurgia) / len(tempos_cirurgia), 2) if tempos_cirurgia else 0
            
            # Coletar dados de solução frente (apenas valores > 0)
            solucoes_frente = []
            for surgery in surgeries:
                if hasattr(surgery, 'solucao_frente') and surgery.solucao_frente is not None and surgery.solucao_frente > 0:
                    solucoes_frente.append(surgery.solucao_frente)
            
            avg_solucao_frente = round(sum(solucoes_frente) / len(solucoes_frente), 2) if solucoes_frente else 0
            
            # Coletar dados de sangramento (apenas valores não nulos)
            sangramentos = []
            for surgery in surgeries:
                if hasattr(surgery, 'sangramento') and surgery.sangramento is not None and surgery.sangramento.strip():
                    sangramentos.append(surgery.sangramento.strip())
            
            # Calcular a média de sangramento (exemplo: porcentagem de casos com sangramento mínimo/moderado/intenso)
            sangramento_counts = {}
            for sang in sangramentos:
                sangramento_counts[sang] = sangramento_counts.get(sang, 0) + 1
            
            # Retornar o tipo de sangramento mais comum
            avg_sangramento = max(sangramento_counts, key=sangramento_counts.get) if sangramento_counts else "N/A"
            
            # Contar cirurgias com body hair (pelos corporais)
            body_hair_count = 0
            for surgery in surgeries:
                if hasattr(surgery, 'pelos_corporais') and surgery.pelos_corporais:
                    # Verifica se pelos_corporais é True ou string não vazia
                    if surgery.pelos_corporais is True or (isinstance(surgery.pelos_corporais, str) and surgery.pelos_corporais.strip().lower() in ['sim', 'yes', 'true', '1']):
                        body_hair_count += 1
            
            # Calcular métricas gerais para comparação (quando filtro específico está aplicado)
            general_avg_tempo_cirurgia = None
            general_avg_solucao_frente = None
            general_avg_sangramento = None
            general_body_hair_count = None
            
            if unit_filter != 'all':
                # Buscar dados de todas as unidades para comparação
                all_surgeries = Surgery.query.all()
                
                # Calcular métricas gerais
                all_tempos_cirurgia = [s.tempo_cirurgia for s in all_surgeries if hasattr(s, 'tempo_cirurgia') and s.tempo_cirurgia is not None and s.tempo_cirurgia > 0]
                general_avg_tempo_cirurgia = round(sum(all_tempos_cirurgia) / len(all_tempos_cirurgia), 2) if all_tempos_cirurgia else 0
                
                all_solucoes_frente = [s.solucao_frente for s in all_surgeries if hasattr(s, 'solucao_frente') and s.solucao_frente is not None and s.solucao_frente > 0]
                general_avg_solucao_frente = round(sum(all_solucoes_frente) / len(all_solucoes_frente), 2) if all_solucoes_frente else 0
                
                all_sangramentos = [s.sangramento.strip() for s in all_surgeries if hasattr(s, 'sangramento') and s.sangramento is not None and s.sangramento.strip()]
                if all_sangramentos:
                    all_sangramento_counts = {}
                    for sang in all_sangramentos:
                        all_sangramento_counts[sang] = all_sangramento_counts.get(sang, 0) + 1
                    general_avg_sangramento = max(all_sangramento_counts, key=all_sangramento_counts.get)
                    
                # Contar body hair de todas as unidades para comparação
                general_body_hair_count = 0
                for surgery in all_surgeries:
                    if hasattr(surgery, 'pelos_corporais') and surgery.pelos_corporais:
                        if surgery.pelos_corporais is True or (isinstance(surgery.pelos_corporais, str) and surgery.pelos_corporais.strip().lower() in ['sim', 'yes', 'true', '1']):
                            general_body_hair_count += 1
            
            # Calcular média de furos por quadrante global
            avg_q1_furos = round(sum(q1_furos) / len(q1_furos), 1) if q1_furos else 0
            avg_q2_furos = round(sum(q2_furos) / len(q2_furos), 1) if q2_furos else 0
            avg_q3_furos = round(sum(q3_furos) / len(q3_furos), 1) if q3_furos else 0
            avg_q4_furos = round(sum(q4_furos) / len(q4_furos), 1) if q4_furos else 0
            
            # Dados por unidade
            units_data = []
            if unit_filter == 'all':
                all_units = ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro', 'São Paulo', 'Brasília']
                for unit in all_units:
                    unit_surgeries = [s for s in surgeries if s.unidade == unit]
                    
                    if unit_surgeries:
                        # Calcular estatísticas para esta unidade (apenas dados > 0)
                        unit_q1_furos = [s.q1_furos for s in unit_surgeries if hasattr(s, 'q1_furos') and s.q1_furos is not None and s.q1_furos > 0]
                        unit_q2_furos = [s.q2_furos for s in unit_surgeries if hasattr(s, 'q2_furos') and s.q2_furos is not None and s.q2_furos > 0]
                        unit_q3_furos = [s.q3_furos for s in unit_surgeries if hasattr(s, 'q3_furos') and s.q3_furos is not None and s.q3_furos > 0]
                        unit_q4_furos = [s.q4_furos for s in unit_surgeries if hasattr(s, 'q4_furos') and s.q4_furos is not None and s.q4_furos > 0]
                        
                        # Calcular taxas de quebra médias por quadrante para esta unidade (dados >= 0)
                        unit_q1_taxas = [s.q1_taxa_quebra for s in unit_surgeries if hasattr(s, 'q1_taxa_quebra') and s.q1_taxa_quebra is not None and s.q1_taxa_quebra >= 0]
                        unit_q2_taxas = [s.q2_taxa_quebra for s in unit_surgeries if hasattr(s, 'q2_taxa_quebra') and s.q2_taxa_quebra is not None and s.q2_taxa_quebra >= 0]
                        unit_q3_taxas = [s.q3_taxa_quebra for s in unit_surgeries if hasattr(s, 'q3_taxa_quebra') and s.q3_taxa_quebra is not None and s.q3_taxa_quebra >= 0]
                        unit_q4_taxas = [s.q4_taxa_quebra for s in unit_surgeries if hasattr(s, 'q4_taxa_quebra') and s.q4_taxa_quebra is not None and s.q4_taxa_quebra >= 0]
                        
                        # Taxa média de quebra geral da unidade (converter decimal para porcentagem)
                        all_unit_taxas = unit_q1_taxas + unit_q2_taxas + unit_q3_taxas + unit_q4_taxas
                        unit_avg_breakage = round((sum(all_unit_taxas) / len(all_unit_taxas)) * 100, 2) if all_unit_taxas else 0
                        
                        # Densidade de extração da unidade (apenas dados > 0)
                        unit_densidades = [s.densidade_extracao for s in unit_surgeries if hasattr(s, 'densidade_extracao') and s.densidade_extracao is not None and s.densidade_extracao > 0]
                        unit_avg_densidade = round(sum(unit_densidades) / len(unit_densidades), 2) if unit_densidades else 0
                        
                        # Média de furos por quadrante da unidade
                        avg_q1_furos = round(sum(unit_q1_furos) / len(unit_q1_furos), 1) if unit_q1_furos else 0
                        avg_q2_furos = round(sum(unit_q2_furos) / len(unit_q2_furos), 1) if unit_q2_furos else 0
                        avg_q3_furos = round(sum(unit_q3_furos) / len(unit_q3_furos), 1) if unit_q3_furos else 0
                        avg_q4_furos = round(sum(unit_q4_furos) / len(unit_q4_furos), 1) if unit_q4_furos else 0
                        
                        # Taxa média de quebra por quadrante da unidade (converter decimal para porcentagem)
                        avg_q1_taxa_unit = round((sum(unit_q1_taxas) / len(unit_q1_taxas)) * 100, 2) if unit_q1_taxas else 0
                        avg_q2_taxa_unit = round((sum(unit_q2_taxas) / len(unit_q2_taxas)) * 100, 2) if unit_q2_taxas else 0
                        avg_q3_taxa_unit = round((sum(unit_q3_taxas) / len(unit_q3_taxas)) * 100, 2) if unit_q3_taxas else 0
                        avg_q4_taxa_unit = round((sum(unit_q4_taxas) / len(unit_q4_taxas)) * 100, 2) if unit_q4_taxas else 0
                        
                        units_data.append({
                            'name': unit,
                            'surgeries': len(unit_surgeries),
                            'breakage_rate': unit_avg_breakage,
                            'densidade_extracao': unit_avg_densidade,
                            'max_q1': max(unit_q1_furos) if unit_q1_furos else 0,
                            'max_q2': max(unit_q2_furos) if unit_q2_furos else 0,
                            'avg_q1_taxa': avg_q1_taxa_unit,
                            'avg_q2_taxa': avg_q2_taxa_unit,
                            'avg_q3_taxa': avg_q3_taxa_unit,
                            'avg_q4_taxa': avg_q4_taxa_unit,
                            'max_q3': max(unit_q3_furos) if unit_q3_furos else 0,
                            'max_q4': max(unit_q4_furos) if unit_q4_furos else 0,
                            'avg_q1': avg_q1_furos,
                            'avg_q2': avg_q2_furos,
                            'avg_q3': avg_q3_furos,
                            'avg_q4': avg_q4_furos,
                            'avg_q1_taxa': avg_q1_taxa_unit,
                            'avg_q2_taxa': avg_q2_taxa_unit,
                            'avg_q3_taxa': avg_q3_taxa_unit,
                            'avg_q4_taxa': avg_q4_taxa_unit
                        })
                    else:
                        units_data.append({
                            'name': unit,
                            'surgeries': 0,
                            'breakage_rate': 0,
                            'densidade_extracao': 0,
                            'max_q1': 0,
                            'max_q2': 0,
                            'max_q3': 0,
                            'max_q4': 0,
                            'avg_q1': 0,
                            'avg_q2': 0,
                            'avg_q3': 0,
                            'avg_q4': 0,
                            'avg_q1_taxa': 0,
                            'avg_q2_taxa': 0,
                            'avg_q3_taxa': 0,
                            'avg_q4_taxa': 0
                        })
            
            response_data = {
                'stats': {
                    'total_surgeries': total_surgeries,
                    'avg_breakage_rate': avg_breakage_rate,
                    'avg_densidade_extracao': avg_densidade_extracao,
                    'avg_tempo_cirurgia': avg_tempo_cirurgia,
                    'avg_solucao_frente': avg_solucao_frente,
                    'avg_sangramento': avg_sangramento,
                    'body_hair_count': body_hair_count,
                    'general_avg_tempo_cirurgia': general_avg_tempo_cirurgia,
                    'general_avg_solucao_frente': general_avg_solucao_frente,
                    'general_avg_sangramento': general_avg_sangramento,
                    'general_body_hair_count': general_body_hair_count,
                    'max_q1': max_q1,
                    'max_q2': max_q2,
                    'max_q3': max_q3,
                    'max_q4': max_q4,
                    'avg_q1_taxa': avg_q1_taxa,
                    'avg_q2_taxa': avg_q2_taxa,
                    'avg_q3_taxa': avg_q3_taxa,
                    'avg_q4_taxa': avg_q4_taxa
                },
                'charts': {
                    'breakage_rates': breakage_rates,
                    'max_holes': [max_q1, max_q2, max_q3, max_q4],
                    'avg_holes': [avg_q1_furos, avg_q2_furos, avg_q3_furos, avg_q4_furos],
                    'avg_breakage_by_quadrant': [avg_q1_taxa, avg_q2_taxa, avg_q3_taxa, avg_q4_taxa],
                    'unit_names': [unit['name'] for unit in units_data],
                    'unit_breakage_rates': [unit['breakage_rate']/100 for unit in units_data],
                    'quadrant_breakage_rates': [avg_q1_taxa, avg_q2_taxa, avg_q3_taxa, avg_q4_taxa]
                },
                'units': units_data
            }
            
            return jsonify(response_data)
            
    except Exception as e:
        logger.error(f"Erro ao obter dados do dashboard médicos: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

        # Adicionar novo registro
        #Necroses model needs to be defined and populated


        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error saving necrose data: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/test_backup')
def test_backup():
    """Rota para testar o backup manual para Dropbox"""
    try:
        logger.info("Iniciando teste de backup manual...")
        success, message = export_and_backup()
        
        if success:
            logger.info(f"✅ Teste de backup bem-sucedido: {message}")
            return jsonify({
                'success': True, 
                'message': message
            })
        else:
            logger.warning(f"⚠️ Falha no teste de backup: {message}")
            return jsonify({
                'success': False, 
                'message': f'Falha no backup: {message}'
            })
            
    except Exception as e:
        logger.error(f"Erro no teste de backup: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Erro no teste de backup: {str(e)}'
        })

# Controle de Cirurgias - Rotas com autenticação
@app.route('/controle_cirurgias')
def controle_cirurgias_login():
    """Página de login para controle de cirurgias"""
    return render_template('controle_login.html')

@app.route('/controle_cirurgias_auth', methods=['POST'])
def controle_cirurgias_auth():
    """Autenticação para controle de cirurgias"""
    password = request.form.get('password')
    if password == 'icb@':
        session['controle_authenticated'] = True
        return redirect(url_for('controle_dashboard'))
    else:
        flash('Senha incorreta!', 'danger')
        return redirect(url_for('controle_cirurgias_login'))

@app.route('/controle_dashboard')
def controle_dashboard():
    """Dashboard de controle de cirurgias"""
    if not session.get('controle_authenticated'):
        return redirect(url_for('controle_cirurgias_login'))
    
    try:
        # Buscar dados de cirurgias por unidade
        with app.app_context():
            # Cirurgias por unidade (mês atual)
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            sql_unidade = text("""
                SELECT unidade, COUNT(*) as total_cirurgias, 
                       EXTRACT(MONTH FROM data) as mes,
                       EXTRACT(YEAR FROM data) as ano
                FROM surgery
                WHERE EXTRACT(MONTH FROM data) = :month 
                AND EXTRACT(YEAR FROM data) = :year
                GROUP BY unidade, EXTRACT(MONTH FROM data), EXTRACT(YEAR FROM data)
                ORDER BY total_cirurgias DESC
            """)
            
            result_unidade = db.session.execute(sql_unidade, {
                'month': current_month, 
                'year': current_year
            })
            cirurgias_unidade = result_unidade.fetchall()
            
            # Cirurgias por membro da equipe (mês atual)
            sql_equipe = text("""
                SELECT equipe, unidade, COUNT(*) as total_cirurgias,
                       EXTRACT(MONTH FROM data) as mes,
                       EXTRACT(YEAR FROM data) as ano
                FROM surgery
                WHERE EXTRACT(MONTH FROM data) = :month 
                AND EXTRACT(YEAR FROM data) = :year
                AND equipe IS NOT NULL AND equipe != ''
                GROUP BY equipe, unidade, EXTRACT(MONTH FROM data), EXTRACT(YEAR FROM data)
                ORDER BY total_cirurgias DESC
            """)
            
            result_equipe = db.session.execute(sql_equipe, {
                'month': current_month, 
                'year': current_year
            })
            cirurgias_equipe = result_equipe.fetchall()
            
            # Dados históricos (últimos 6 meses)
            sql_historico = text("""
                SELECT unidade, equipe, COUNT(*) as total_cirurgias,
                       EXTRACT(MONTH FROM data) as mes,
                       EXTRACT(YEAR FROM data) as ano,
                       TO_CHAR(data, 'MM/YYYY') as mes_ano
                FROM surgery
                WHERE data >= CURRENT_DATE - INTERVAL '6 months'
                GROUP BY unidade, equipe, EXTRACT(MONTH FROM data), EXTRACT(YEAR FROM data), TO_CHAR(data, 'MM/YYYY')
                ORDER BY ano DESC, mes DESC, total_cirurgias DESC
            """)
            
            result_historico = db.session.execute(sql_historico)
            historico = result_historico.fetchall()
            
            # Organizar dados para o template
            dados_unidade = []
            for row in cirurgias_unidade:
                dados_unidade.append({
                    'unidade': row.unidade,
                    'total': row.total_cirurgias,
                    'mes': row.mes,
                    'ano': row.ano
                })
            
            dados_equipe = []
            for row in cirurgias_equipe:
                dados_equipe.append({
                    'equipe': row.equipe,
                    'unidade': row.unidade,
                    'total': row.total_cirurgias,
                    'mes': row.mes,
                    'ano': row.ano
                })
            
            dados_historico = []
            for row in historico:
                dados_historico.append({
                    'unidade': row.unidade,
                    'equipe': row.equipe,
                    'total': row.total_cirurgias,
                    'mes_ano': row.mes_ano
                })
            
            return render_template('controle_dashboard.html', 
                cirurgias_unidade=dados_unidade,
                cirurgias_equipe=dados_equipe,
                historico=dados_historico,
                mes_atual=current_month,
                ano_atual=current_year,
                mes_nome=['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                           'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][current_month]
            )
            
    except Exception as e:
        logger.error(f"Erro no controle dashboard: {str(e)}")
        return render_template('controle_dashboard.html', 
            cirurgias_unidade=[],
            cirurgias_equipe=[],
            historico=[],
            error=f'Erro ao carregar dados: {str(e)}'
        )

@app.route('/controle_logout')
def controle_logout():
    """Logout do controle de cirurgias"""
    session.pop('controle_authenticated', None)
    return redirect(url_for('controle_cirurgias_login'))

# Configure Flask app
app.config['ENV'] = 'production'
app.config['DEBUG'] = False

# Use environment variable for secret key
app.secret_key = os.environ.get('SESSION_SECRET', os.urandom(24))

if __name__ == '__main__':
    try:
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Starting Flask server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {str(e)}\n{traceback.format_exc()}")
        raise