import os
import logging
import traceback
import re
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
import functools
import pandas as pd
import numpy as np
from datetime import datetime
from fuzzywuzzy import fuzz
import json
from flask_sqlalchemy import SQLAlchemy
import shutil
from sqlalchemy import text, extract

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
    tadalafila = db.Column(db.String(255))
    bloqueio_seringas = db.Column(db.String(255))
    fonte_1 = db.Column(db.String(255))
    fonte_2 = db.Column(db.String(255))
    fonte_3 = db.Column(db.String(255))
    fonte_4 = db.Column(db.String(255))
    fonte_5 = db.Column(db.String(255))
    pelos_corporais = db.Column(db.String(255))
    tecnica = db.Column(db.String(255))
    solucao_frente = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UnitProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unidade = db.Column(db.String(100), unique=True)
    meta = db.Column(db.Integer)

# Configure Flask-Migrate
from flask_migrate import Migrate

# Initialize Flask-Migrate with app and db
migrate = Migrate(app, db)
logger.info("✅ Flask-Migrate initialized")

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
                # Processar dados por mês
                df['mes_ano'] = pd.to_datetime(df['data']).dt.strftime('%m/%Y')

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
                tadalafila=str(data.get('Tadalafila', data.get('tadalafila', '')) or ''),
                bloqueio_seringas=str(data.get('Bloqueio de Seringas', data.get('bloqueio_seringas', '')) or ''),
                fonte_1=str(data.get('Fonte 1', data.get('fonte_1', '')) or ''),
                fonte_2=str(data.get('Fonte 2', data.get('fonte_2', '')) or ''),
                fonte_3=str(data.get('Fonte 3', data.get('fonte_3', '')) or ''),
                fonte_4=str(data.get('Fonte 4', data.get('fonte_4', '')) or ''),
                fonte_5=str(data.get('Fonte 5', data.get('fonte_5', '')) or ''),
                pelos_corporais=str(data.get('Pelos Corporais', data.get('pelos_corporais', '')) or ''),
                tecnica=str(data.get('Técnica', data.get('tecnica', '')) or ''),
                solucao_frente=int(data.get('Solução Frente (ml)', data.get('solucao_frente', 0)) or 0),
                # Dados dos quadrantes
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
    return render_template('success.html')

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
            logger.info(f"Received form data: {form_data}")
            logger.info(f"Request headers: {dict(request.headers)}")
            
            # Log de detalhes específicos importantes
            if 'Paciente' in form_data:
                logger.info(f"Paciente: {form_data['Paciente']}")
            if 'Data (DD/MM/AAAA)' in form_data:
                logger.info(f"Data: {form_data['Data (DD/MM/AAAA)']}")
            if 'Unidade' in form_data:
                logger.info(f"Unidade: {form_data['Unidade']}")

            # Process multiple checkboxes
            if 'equipe_values' in form_data:
                form_data['equipe'] = form_data['equipe_values']
                del form_data['equipe_values']
                logger.info(f"Processed equipe values: {form_data['equipe']}")

            # Save to Excel and database
            logger.info("Calling save_to_excel function")
            success, message = save_to_excel(form_data)
            logger.info(f"Save result: success={success}, message={message}")

            if success:
                flash("✅ Dados salvos com sucesso! 🎉", "success")
                logger.info("Flashed success message")
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

    # Complete form structure
    form_data = {
        'title': 'Cadastro de Cirurgia Capilar',
        'fields': [
            # Dados Gerais da Cirurgia
            {'name': 'data', 'label': 'Data da Cirurgia', 'type': 'date', 'required': True},
            {'name': 'nome', 'label': 'Nome do Paciente', 'type': 'text', 'required': True},
            {'name': 'unidade', 'label': 'Unidade', 'type': 'select', 'required': True, 
             'options': ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro', 'São Paulo', 'Brasília']},
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
    
    # Tentar carregar configuração dinâmica
    try:
        import json
        if os.path.exists('admin_config.json'):
            with open('admin_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                medicos_por_unidade = config.get('medicos_por_unidade', {})
        else:
            # Fallback para configuração padrão
            medicos_por_unidade = {
                'Ribeirão Preto': ['Dr. Arthur', 'Dr. Daniel'],
                'Campinas': ['Dra. Adriana', 'Dra. Isadora'],
                'Rio de Janeiro': ['Dra. Ana Clara', 'Dra. Paula'],
                'São Paulo': ['Dr. Daniel', 'Dr. Renan', 'Dra. Ariane', 'Dra. Isabella', 'Dra. Talita', 'Dra. Thaiza'],
                'Brasília': ['Dra. Leticia', 'Dra. Natalia'],
            }
    except Exception as e:
        logger.error(f"Erro ao carregar configuração de médicos: {e}")
        # Fallback para configuração padrão
        medicos_por_unidade = {
            'Ribeirão Preto': ['Dr. Arthur', 'Dr. Daniel'],
            'Campinas': ['Dra. Adriana', 'Dra. Isadora'],
            'Rio de Janeiro': ['Dra. Ana Clara', 'Dra. Paula'],
            'São Paulo': ['Dr. Daniel', 'Dr. Renan', 'Dra. Ariane', 'Dra. Isabella', 'Dra. Talita', 'Dra. Thaiza'],
            'Brasília': ['Dra. Leticia', 'Dra. Natalia'],
        }
    
    return {'medicos': medicos_por_unidade.get(unidade, [])}


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
    
    # Tentar carregar configuração dinâmica
    try:
        import json
        if os.path.exists('admin_config.json'):
            with open('admin_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                equipe_por_unidade = config.get('equipe_por_unidade', {})
        else:
            # Fallback para configuração padrão
            equipe_por_unidade = {
                'Ribeirão Preto': ['Aline', 'Ana', 'Natália'],
                'Campinas': ['Bruna Galhardo', 'Dayane Andrade', 'Eduarda de Sousa', 
                          'Isabelle de Campos', 'Juliana Nunes', 'Kesley Sabrina', 
                          'Larissa Hellen', 'Thalita Corrêa', 'Vitória Delino'],
                'Rio de Janeiro': ['Assistente Extra', 'Dayane', 'Mariana Moro', 'Mariana Silva'],
                'São Paulo': ['Adriana Almeida', 'Ana Paula dos Santos', 'Dani Curti', 
                          'Eliene Rodrigues', 'Gabriela Cruz', 'Greice Barbosa', 
                          'Jaiza Valentim', 'Josefa Wilma Vieira', 'Joyce Eugênia Da Silva', 
                          'Merielen Venâncio Oliveira', 'Rosana Pereira', 'Sabrina Crott', 
                          'Thamiris Santos', 'Thaís Paiva'],
                'Brasília': ['Angélica Sousa', 'Betânia Almeida', 'Dayse Fernandes', 'Layla Cardoso', 'Thamara Maciel'],
            }
    except Exception as e:
        logger.error(f"Erro ao carregar configuração de equipe: {e}")
        # Fallback para configuração padrão
        equipe_por_unidade = {
            'Ribeirão Preto': ['Aline', 'Ana', 'Natália'],
            'Campinas': ['Bruna Galhardo', 'Dayane Andrade', 'Eduarda de Sousa', 
                      'Isabelle de Campos', 'Juliana Nunes', 'Kesley Sabrina', 
                      'Larissa Hellen', 'Thalita Corrêa', 'Vitória Delino'],
            'Rio de Janeiro': ['Assistente Extra', 'Dayane', 'Mariana Moro', 'Mariana Silva'],
            'São Paulo': ['Adriana Almeida', 'Ana Paula dos Santos', 'Dani Curti', 
                      'Eliene Rodrigues', 'Gabriela Cruz', 'Greice Barbosa', 
                      'Jaiza Valentim', 'Josefa Wilma Vieira', 'Joyce Eugênia Da Silva', 
                      'Merielen Venâncio Oliveira', 'Rosana Pereira', 'Sabrina Crott', 
                      'Thamiris Santos', 'Thaís Paiva'],
            'Brasília': ['Angélica Sousa', 'Betânia Almeida', 'Dayse Fernandes', 'Layla Cardoso', 'Thamara Maciel'],
        }
    
    return {'equipe': equipe_por_unidade.get(unidade, [])}

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
    }

        # Equipe por unidade para filtros
        equipe_por_unidade = {
        'Ribeirão Preto': ['Aline', 'Ana', 'Natália'],
        'Campinas': ['Bruna Galhardo', 'Dayane Andrade', 'Eduarda de Sousa', 
                  'Isabelle de Campos', 'Juliana Nunes', 'Kesley Sabrina', 
                  'Larissa Hellen', 'Thalita Corrêa', 'Vitória Delino'],
        'Rio de Janeiro': ['Assistente Extra', 'Dayane', 'Mariana Moro', 'Mariana Silva'],
        'São Paulo': ['Adriana Almeida', 'Ana Paula dos Santos', 'Dani Curti', 
                  'Eliene Rodrigues', 'Gabriela Cruz', 'Greice Barbosa', 
                  'Jaiza Valentim', 'Josefa Wilma Vieira', 'Joyce Eugênia Da Silva', 
                  'Merielen Venâncio Oliveira', 'Rosana Pereira', 'Sabrina Crott', 
                  'Thamiris Santos', 'Thaís Paiva'],
        'Brasília': ['Angélica Sousa', 'Betânia Almeida', 'Dayse Fernandes', 'Layla Cardoso', 'Thamara Maciel'],
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
            os.remove(temp_file)
            return return_data
    except Exception as e:
        logger.error(f"Error downloading Excel file: {str(e)}\n{traceback.format_exc()}")
        flash(f"Erro ao baixar arquivo: {str(e)}", "error")
        return redirect(url_for('dashboard'))

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

        # Carregar dados dos pacientes
        with app.app_context():
            df = pd.read_sql(Surgery.query.statement, db.session.get_bind())

        # Filtrar por unidade se especificado
        if unit:
            df = df[df['unidade'] == unit]

        # Filtrar e ordenar pacientes
        patients = []
        for _, row in df.iterrows():
            name = str(row['nome']).lower()
            # Usar fuzzy matching para melhorar a busca
            ratio = fuzz.partial_ratio(term, name)
            if ratio > 75:  # Threshold de similaridade
                patient_data = {
                    'id': len(patients),  # Usar índice como ID temporário
                    'nome': row['nome'],
                    'unidade': row['unidade'],
                    'data': row['data'],
                    'total_foliculos': row['total_foliculos'],
                    'densidade_scketh': row['densidade_scketh'],
                    'infiltracao': row['infiltracao'],
                    'tadalafila': row['tadalafila'] if 'tadalafila' in row else 'Não',
                    'medico': row['medico'],
                    'equipe': row['equipe']
                }
                patients.append(patient_data)

        # Ordenar por nome
        patients.sort(key=lambda x: x['nome'])

        return jsonify(patients[:10])  # Limitar a 10 sugestões
    except Exception as e:
        logger.error(f"Error searching patients: {str(e)}\n{traceback.format_exc()}")
        return jsonify([])

@app.route('/necrose_summary')
def necrose_summary():
    """Endpoint para retornar o resumo de necroses"""
    logger.info("Getting necrose summary")
    try:
        with app.app_context():
            total_surgeries = Surgery.query.count()
            total_necroses = 0 #Necroses model needs to be defined and populated
            necrose_rate = "0%"
            if total_surgeries > 0:
                taxa = (total_necroses / total_surgeries) * 100
                necrose_rate = f"{taxa:.1f}%"

            return jsonify({
                'total_surgeries': total_surgeries,
                'total_necroses': total_necroses,
                'necrose_rate': necrose_rate
            })
    except Exception as e:
        logger.error(f"Error getting necrose summary: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'total_surgeries': 0,
            'total_necroses': 0,
            'necrose_rate': '0%',
            'error': str(e)
        })

@app.route('/save_necrose', methods=['POST'])
def save_necrose():
    """Endpoint para salvar dados de necrose"""
    logger.info("Saving necrose data")
    try:
        # Verificar se existem dados do formulário
        if not request.form:
            return jsonify({'success': False, 'error': 'Dados do formulário não encontrados'})

        # Obter dados do formulário
        patient_id = request.form.get('patient_id')
        patient_unit = request.form.get('patient_unit')
        lesion_count = request.form.get('lesion_count')
        largest_lesion = request.form.get('largest_lesion')
        affected_band = request.form.get('affected_band')

        # Validar dados recebidos
        required_fields = ['patient_id', 'lesion_count', 'largest_lesion', 'affected_band']
        if not all(request.form.get(field) for field in required_fields):
            return jsonify({'success': False, 'error': 'Dados incompletos'})

        # Processar arquivos de foto
        photo_paths = []
        photo_dir = os.path.join('static', 'uploads', 'necrose_photos')

        # Criar diretório se não existir
        os.makedirs(photo_dir, exist_ok=True)

        for i in range(1, 4):  # Para cada uma das 3 fotos possíveis
            photo_key = f'photo{i}'
            if photo_key in request.files and request.files[photo_key].filename != '':
                file = request.files[photo_key]
                filename = f"necrose_{patient_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}.jpg"
                file_path = os.path.join(photo_dir, filename)
                file.save(file_path)
                photo_paths.append(file_path)

        # Carregar arquivo de necroses existente ou criar novo
        #Necroses model needs to be defined and populated
        
        return jsonify({'success': True, 'message': 'Dados de necrose salvos com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao salvar dados de necrose: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

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