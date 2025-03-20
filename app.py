import os
import logging
import traceback
import re
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
import numpy as np
from datetime import datetime
from fuzzywuzzy import fuzz
import json
from flask_sqlalchemy import SQLAlchemy
import shutil
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting Flask application...")

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure SQLAlchemy with detailed logging and connection settings
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Handle Heroku-style PostgreSQL URLs
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True  # Enable SQL query logging
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UnitProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unidade = db.Column(db.String(100), unique=True)
    meta = db.Column(db.Integer)

# Create tables
with app.app_context():
    db.create_all()
    logger.info("✅ Database tables created successfully")
    # Insert test data if database is empty
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
                    'version': '2.3'
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
                'version': '2.3'
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
            'version': '2.3'
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
        filename = "cirurgias.xlsx"

        # Create backup before modifying
        backup_excel_file(filename)

        # Save to database first
        try:
            logger.info(f"Saving to database: {data}")

            # Convert to DataFrame and handle NaN values
            dados = pd.DataFrame([data])
            dados = dados.fillna(0)
            data = dados.iloc[0].to_dict()

            # Convert date string to date object
            data_date = datetime.strptime(data['data'], '%Y-%m-%d').date()

            # Create Surgery object with proper type conversion
            # Tratar valores NaN ou None antes de criar o objeto Surgery
            surgery = Surgery(
                data=data_date,
                nome=str(data.get('nome', '') or ''),
                unidade=str(data.get('unidade', '') or ''),
                medico=str(data.get('medico', '') or ''),
                equipe=str(data.get('equipe', '') or ''),
                hora_cirurgia=str(data.get('hora_cirurgia', '') or ''),
                tempo_cirurgia=float(data.get('tempo_cirurgia', 0) or 0),
                total_foliculos=int(data.get('total_foliculos', 0) or 0),
                frente=int(data.get('frente', 0) or 0),
                densidade_scketh=float(data.get('densidade_scketh', 0) or 0),
                coroa=int(data.get('coroa', 0) or 0),
                scalpe=int(data.get('scalpe', 0) or 0),
                peninsula_direita=int(data.get('peninsula_direita', 0) or 0),
                peninsula_esquerda=int(data.get('peninsula_esquerda', 0) or 0)
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

        # Save with backup
        temp_file = f"{filename}.temp"
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

            # Process multiple checkboxes
            if 'equipe_values' in form_data:
                form_data['equipe'] = form_data['equipe_values']
                del form_data['equipe_values']

            # Save to Excel and database
            success, message = save_to_excel(form_data)

            if success:
                flash("✅ Dados salvos com sucesso! 🎉", "success")
            else:
                flash(message, "error")

            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}\n{traceback.format_exc()}")
            flash(f"Erro ao salvar dados: {str(e)}", "error")

    # Complete form structure
    form_data = {
        'title': 'Cadastro de Cirurgia Capilar',
        'fields': [
            # Dados Gerais da Cirurgia
            {'name': 'data', 'label': 'Data da Cirurgia', 'type': 'date', 'required': True},
            {'name': 'nome', 'label': 'Nome do Paciente', 'type': 'text', 'required': True},
            {'name': 'unidade', 'label': 'Unidade', 'type': 'select', 'required': True, 
             'options': ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro']},
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
             'options': ['0.75', '0.85', '0.95']},
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
    # Médicos por unidade conforme especificação
    medicos_por_unidade = {
        'Ribeirão Preto': ['Dr. Arthur', 'Dr. Daniel'],
        'Campinas': ['Dra. Isadora', 'Dra. Adriana'],
        'Rio de Janeiro': ['Dra. Paula', 'Dra. Ana Clara']
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
    # Equipe por unidade conforme especificação
    equipe_por_unidade = {
        'Ribeirão Preto': ['Aline', 'Natália', 'Ana'],
        'Campinas': ['Juliana', 'Gabriela'],
        'Rio de Janeiro': ['Mariana Moro', 'Mariana Silva', 'Dayane', 'Assistente Extra']
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
        'version': '2.3'  # Updated version number
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

                # Iterar sobre cada linha para contar participações
                for surgery in Surgery.query.all():
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
            'Campinas': ['Dra. Isadora', 'Dra. Adriana']
        }

        # Equipe por unidade para filtros
        equipe_por_unidade = {
            'Ribeirão Preto': ['Aline', 'Natália', 'Ana'],
            'Campinas': ['Juliana', 'Gabriela']
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
        filename = "cirurgias.xlsx"
        if os.path.exists(filename):
            # Return the file for download
            from flask import send_file
            return send_file(filename, 
                             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             as_attachment=True,
                             download_name='relatorio_cirurgias.xlsx')
        else:
            flash("Arquivo de dados não encontrado.", "error")
            return redirect(url_for('dashboard'))
    except Exception as e:
        logger.error(f"Error downloading Excel file: {str(e)}\n{traceback.format_exc()}")
        flash(f"Erro ao baixar arquivo: {str(e)}", "error")
        return redirect(url_for('dashboard'))

@app.route('/necrose')
def necrose():
    """Página de avaliação de necrose"""
    logger.info("Accessing necrose page")
    return render_template('necrose.html')

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
        port = int(os.environ.get('PORT', 3000))
        logger.info(f"Starting Flask server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {str(e)}\n{traceback.format_exc()}")
        raise