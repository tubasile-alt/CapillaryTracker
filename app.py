import os
import logging
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_cors import CORS
from models import db, Cirurgia
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Temporarily set to DEBUG for more verbose output
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("Starting application initialization...")

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configure the SQLAlchemy part of the app instance
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

logger.info(f"Using database URL: {database_url.split('@')[1] if database_url else 'None'}")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///cirurgias.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_timeout': 20,
    'pool_size': 30,
    'max_overflow': 20
}
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Initialize SQLAlchemy with the app
db.init_app(app)
logger.info("Database initialized")

# Function to test database connection
def test_db_connection(max_retries=5, delay=1):
    """Test database connection with retry mechanism"""
    for attempt in range(max_retries):
        try:
            # Try to make a simple query
            with app.app_context():
                Cirurgia.query.first()
            logger.info("Database connection successful")
            return True
        except OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection attempt {attempt + 1} failed, retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error testing database connection: {str(e)}")
            return False

# Test database connection on startup
if not test_db_connection():
    logger.error("Unable to establish database connection")


@app.route('/ping')
def ping():
    """Basic connectivity test endpoint"""
    logger.info("Ping endpoint accessed")
    return "OK", 200

@app.route('/')
def index():
    """Main route for the application"""
    logger.info("Access to main route")
    try:
        return render_template('base.html')
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/novo_cadastro', methods=['GET', 'POST'])
def novo_cadastro():
    logger.info("Accessing novo_cadastro route")
    if request.method == 'POST':
        try:
            # Get form data
            form_data = request.form.to_dict()

            # Convert date string to Python date object
            date_str = form_data.get('data')
            if date_str:
                try:
                    data = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    data = datetime.strptime(date_str, '%d/%m/%Y').date()
            else:
                data = datetime.now().date()

            # Create new Cirurgia instance
            cirurgia = Cirurgia(
                data=data,
                nome=form_data.get('nome'),
                unidade=form_data.get('unidade'),
                medico=form_data.get('medico'),
                equipe=form_data.get('equipe'),
                hora_cirurgia=form_data.get('hora_cirurgia'),
                tempo_cirurgia=float(form_data.get('tempo_cirurgia', 0)),
                total_foliculos=int(form_data.get('total_foliculos', 0)),
                frente=int(form_data.get('frente', 0)),
                densidade_scketh=float(form_data.get('densidade_scketh', 0)),
                coroa=int(form_data.get('coroa', 0)),
                scalpe=int(form_data.get('scalpe', 0)),
                peninsula_direita=int(form_data.get('peninsula_direita', 0)),
                peninsula_esquerda=int(form_data.get('peninsula_esquerda', 0)),
                safira=form_data.get('safira'),
                punch=form_data.get('punch'),
                solucao_frente=float(form_data.get('solucao_frente', 0)),
                solucao_coroa=float(form_data.get('solucao_coroa', 0)),
                solucao_xilo_frente=float(form_data.get('solucao_xilo_frente', 0)),
                q1_area=float(form_data.get('q1_area', 0)),
                q1_furos=int(form_data.get('q1_furos', 0)),
                q1_fios=int(form_data.get('q1_fios', 0)),
                q2_area=float(form_data.get('q2_area', 0)),
                q2_furos=int(form_data.get('q2_furos', 0)),
                q2_fios=int(form_data.get('q2_fios', 0)),
                q3_area=float(form_data.get('q3_area', 0)),
                q3_furos=int(form_data.get('q3_furos', 0)),
                q3_fios=int(form_data.get('q3_fios', 0)),
                q4_area=float(form_data.get('q4_area', 0)),
                q4_furos=int(form_data.get('q4_furos', 0)),
                q4_fios=int(form_data.get('q4_fios', 0)),
                infiltracao=int(form_data.get('infiltracao', 0)),
                sedacao=int(form_data.get('sedacao', 0)),
                sangramento=int(form_data.get('sangramento', 0)),
                implante_secundario=form_data.get('implante_secundario'),
                transamin=form_data.get('transamin'),
                tadalafila=form_data.get('tadalafila'),
                diprospam=form_data.get('diprospam'),
                fumante=form_data.get('fumante'),
                antecedentes=form_data.get('antecedentes'),
                comentarios=form_data.get('comentarios')
            )

            # Calculate derived fields
            if cirurgia.q1_area > 0:
                cirurgia.q1_densidade = cirurgia.q1_furos / cirurgia.q1_area
                cirurgia.q1_taxa_quebra = (1 - cirurgia.q1_fios / cirurgia.q1_furos) * 100 if cirurgia.q1_furos > 0 else 0

            if cirurgia.q2_area > 0:
                cirurgia.q2_densidade = cirurgia.q2_furos / cirurgia.q2_area
                cirurgia.q2_taxa_quebra = (1 - cirurgia.q2_fios / cirurgia.q2_furos) * 100 if cirurgia.q2_furos > 0 else 0

            if cirurgia.q3_area > 0:
                cirurgia.q3_densidade = cirurgia.q3_furos / cirurgia.q3_area
                cirurgia.q3_taxa_quebra = (1 - cirurgia.q3_fios / cirurgia.q3_furos) * 100 if cirurgia.q3_furos > 0 else 0

            if cirurgia.q4_area > 0:
                cirurgia.q4_densidade = cirurgia.q4_furos / cirurgia.q4_area
                cirurgia.q4_taxa_quebra = (1 - cirurgia.q4_fios / cirurgia.q4_furos) * 100 if cirurgia.q4_furos > 0 else 0

            # Save to database
            db.session.add(cirurgia)
            db.session.commit()

            flash("✅ Dados salvos com sucesso!", "success")
            return redirect(url_for('index'))

        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            db.session.rollback()
            flash(f"❌ Erro ao salvar dados: {str(e)}", "error")
            return redirect(url_for('novo_cadastro'))

    # If GET request, show the form
    form_data = {
        'title': 'Cadastro de Cirurgia Capilar',
        'fields': [
            {'name': 'data', 'label': 'Data da Cirurgia', 'type': 'date', 'required': True},
            {'name': 'nome', 'label': 'Nome do Paciente', 'type': 'text', 'required': True},
            {'name': 'unidade', 'label': 'Unidade', 'type': 'select', 'required': True,
             'options': ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro']},
            {'name': 'medico', 'label': 'Médico Responsável', 'type': 'select_dynamic', 'required': True},
            {'name': 'equipe', 'label': 'Equipe', 'type': 'select_dynamic', 'required': True},
            {'name': 'hora_cirurgia', 'label': 'Hora da Cirurgia (HH:MM)', 'type': 'time', 'required': True, 'default': '08:00'},
            {'name': 'tempo_cirurgia', 'label': 'Tempo de Cirurgia (horas)', 'type': 'number', 'required': True},
            {'name': 'total_foliculos', 'label': 'Total de Folículos', 'type': 'number', 'required': True},
            {'name': 'frente', 'label': 'Frente', 'type': 'number', 'required': False},
            {'name': 'densidade_scketh', 'label': 'Densidade Scketh', 'type': 'number', 'required': False},
            {'name': 'coroa', 'label': 'Coroa', 'type': 'number', 'required': False},
            {'name': 'scalpe', 'label': 'Scalpe', 'type': 'number', 'required': False},
            {'name': 'peninsula_direita', 'label': 'Península Direita', 'type': 'number', 'required': False},
            {'name': 'peninsula_esquerda', 'label': 'Península Esquerda', 'type': 'number', 'required': False},
            {'name': 'safira', 'label': 'Safira?', 'type': 'select', 'required': True,
             'options': ['Sim', 'Não']},
            {'name': 'punch', 'label': 'Punch (mm)', 'type': 'select', 'required': True,
             'options': ['0.75', '0.85', '0.95']},
            {'name': 'solucao_frente', 'label': 'Solução Frente (ml)', 'type': 'number', 'required': True},
            {'name': 'solucao_coroa', 'label': 'Solução Coroa (ml)', 'type': 'number', 'required': False},
            {'name': 'solucao_xilo_frente', 'label': 'Solução Xilo Frente (ml)', 'type': 'number', 'required': False},
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
            {'name': 'infiltracao', 'label': 'Infiltração (1-3)', 'type': 'select', 'required': True,
             'options': ['1', '2', '3']},
            {'name': 'sedacao', 'label': 'Sedação (1-3)', 'type': 'select', 'required': True,
             'options': ['1', '2', '3']},
            {'name': 'sangramento', 'label': 'Sangramento (1-3)', 'type': 'select', 'required': True,
             'options': ['1', '2', '3']},
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
            {'name': 'comentarios', 'label': 'Comentários', 'type': 'textarea', 'required': False}
        ]
    }
    return render_template('form.html', form=form_data, data={})

@app.route('/get_medicos/<unidade>')
def get_medicos(unidade):
    """Get doctors for a specific unit"""
    medicos_por_unidade = {
        'Ribeirão Preto': ['Dr. Arthur', 'Dr. Daniel'],
        'Campinas': ['Dra. Isadora', 'Dra. Adriana'],
        'Rio de Janeiro': ['Dra. Paula', 'Dra. Ana Clara']
    }
    return jsonify({'medicos': medicos_por_unidade.get(unidade, [])})

@app.route('/get_equipe/<unidade>')
def get_equipe(unidade):
    """Get team members for a specific unit"""
    equipe_por_unidade = {
        'Ribeirão Preto': ['Aline', 'Natália', 'Ana'],
        'Campinas': ['Juliana', 'Gabriela'],
        'Rio de Janeiro': ['Mariana Moro', 'Mariana Silva', 'Dayane', 'Assistente Extra']
    }
    return jsonify({'equipe': equipe_por_unidade.get(unidade, [])})


@app.route('/health')
def health_check():
    """Health check endpoint to verify database connectivity"""
    try:
        # Try to count records
        count = db.session.query(Cirurgia).count()
        logger.info(f"Health check successful. Found {count} records.")
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "records_count": count
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/dashboard')
def dashboard():
    """Dashboard route to display surgery data"""
    logger.info("Accessing dashboard route")
    try:
        # Use raw SQL for better performance and debugging
        sql = """
        SELECT COUNT(*) as total_cirurgias,
               COALESCE(AVG(total_foliculos), 0) as media_foliculos,
               COALESCE(AVG(densidade_scketh), 0) as media_densidade,
               unidade,
               to_char(data, 'MM/YYYY') as mes_ano
        FROM cirurgias
        GROUP BY unidade, to_char(data, 'MM/YYYY')
        ORDER BY mes_ano;
        """
        result = db.session.execute(sql)
        rows = result.fetchall()
        logger.info(f"SQL query returned {len(rows)} rows")

        total_cirurgias = 0
        total_foliculos = 0
        total_densidade = 0
        cirurgias_por_mes = {}

        for row in rows:
            total_cirurgias += row.total_cirurgias
            total_foliculos += (row.media_foliculos * row.total_cirurgias)
            total_densidade += (row.media_densidade * row.total_cirurgias)

            mes_ano = row.mes_ano
            if mes_ano not in cirurgias_por_mes:
                cirurgias_por_mes[mes_ano] = {
                    'count': 0,
                    'foliculos': 0,
                    'densidade': 0
                }
            cirurgias_por_mes[mes_ano]['count'] += row.total_cirurgias
            cirurgias_por_mes[mes_ano]['foliculos'] += (row.media_foliculos * row.total_cirurgias)
            cirurgias_por_mes[mes_ano]['densidade'] += (row.media_densidade * row.total_cirurgias)

        logger.info(f"Total cirurgias: {total_cirurgias}")
        logger.info(f"Dados por mês: {cirurgias_por_mes}")

        # Prepare dashboard data
        dashboard_data = {
            'labels': [],
            'datasets': [],
            'has_follicle_data': True,
            'follicles_data': {'labels': [], 'averages': [], 'le_density': []},
            'total_surgeries': total_cirurgias,
            'avg_follicles': int(total_foliculos / total_cirurgias) if total_cirurgias > 0 else 0,
            'avg_density': int(total_densidade / total_cirurgias) if total_cirurgias > 0 else 0,
            'update_time': datetime.now().strftime('%d/%m/%Y %H:%M')
        }

        # Sort months
        meses_ordenados = sorted(cirurgias_por_mes.keys())
        dashboard_data['labels'] = meses_ordenados

        # Add surgery counts
        dashboard_data['datasets'].append({
            'label': 'Total de Cirurgias',
            'data': [cirurgias_por_mes[mes]['count'] for mes in meses_ordenados]
        })

        # Add follicle data
        dashboard_data['follicles_data']['labels'] = meses_ordenados
        dashboard_data['follicles_data']['averages'] = [
            int(cirurgias_por_mes[mes]['foliculos'] / cirurgias_por_mes[mes]['count'])
            if cirurgias_por_mes[mes]['count'] > 0 else 0
            for mes in meses_ordenados
        ]
        dashboard_data['follicles_data']['le_density'] = [
            int(cirurgias_por_mes[mes]['densidade'] / cirurgias_por_mes[mes]['count'])
            if cirurgias_por_mes[mes]['count'] > 0 else 0
            for mes in meses_ordenados
        ]

        logger.info(f"Dashboard data prepared: {dashboard_data}")
        return render_template('dashboard.html', data=dashboard_data)

    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}")
        return render_template('dashboard.html', data={
            'labels': [],
            'datasets': [{'label': 'Cirurgias', 'data': []}],
            'has_follicle_data': False,
            'follicles_data': {'labels': [], 'averages': [], 'le_density': []},
            'total_surgeries': 0,
            'avg_follicles': 0,
            'avg_density': 0
        })

@app.route('/filter_dashboard')
def filter_dashboard():
    return jsonify({"message": "Filter dashboard endpoint not yet implemented"})

@app.route('/download_excel')
def download_excel():
    return jsonify({"message": "Download endpoint not yet implemented"})

@app.route('/necrose')
def necrose():
    return jsonify({"message": "Necrose endpoint not yet implemented"})

@app.route('/search_patients')
def search_patients():
    return jsonify({"message": "Search patients endpoint not yet implemented"})

@app.route('/necrose_summary')
def necrose_summary():
    return jsonify({"message": "Necrose summary endpoint not yet implemented"})

@app.route('/save_necrose', methods=['POST'])
def save_necrose():
    return jsonify({"message": "Save necrose endpoint not yet implemented"})

@app.route('/get_available_units')
def get_available_units():
    return jsonify({"message": "Get available units endpoint not yet implemented"})

# Adicionar logs detalhados na função get_unit_progress
@app.route('/get_unit_progress')
def get_unit_progress():
    """Get progress data for a specific unit"""
    try:
        unit = request.args.get('unit')
        logger.debug(f"Unit requested: {unit}") #Added log
        if not unit:
            logger.error("Unidade não especificada") #Added log
            return jsonify({"error": "Unidade não especificada"}), 400

        # Get current month and year
        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        logger.debug(f"Start of month: {start_of_month}") #Added log

        # Get surgeries for this unit in the current month
        cirurgias = Cirurgia.query.filter(
            Cirurgia.unidade == unit,
            Cirurgia.data >= start_of_month
        ).all()
        logger.debug(f"Number of surgeries found: {len(cirurgias)}") #Added log

        total_cirurgias = len(cirurgias)
        logger.info(f"Unidade {unit}: {total_cirurgias} cirurgias em {start_of_month.strftime('%B/%Y')}")

        # Meta mensal por unidade
        metas = {
            'Ribeirão Preto': 35,
            'Campinas': 25,
            'Rio de Janeiro': 20
        }
        meta_mensal = metas.get(unit, 20)
        logger.debug(f"Meta mensal for {unit}: {meta_mensal}") #Added log

        # Calcular percentual
        percentual = round((total_cirurgias / meta_mensal * 100), 1) if meta_mensal > 0 else 0

        response_data = {
            "meta": meta_mensal,
            "atual": total_cirurgias,
            "percentual": percentual
        }
        logger.info(f"Progress data for {unit}: {response_data}")
        return jsonify(response_data)

    except Exception as e:
        logger.exception(f"Error getting unit progress: {str(e)}") #Added exception log
        return jsonify({"error": str(e)}), 500

@app.route('/get_tecnicas_data')
def get_tecnicas_data():
    return jsonify({"message": "Get tecnicas data endpoint not yet implemented"})

@app.route('/get_equipe_data')
def get_equipe_data():
    """Get surgery data grouped by team members"""
    try:
        # Get all surgeries and group by team members
        cirurgias = Cirurgia.query.all()
        logger.debug(f"Number of surgeries retrieved: {len(cirurgias)}")
        equipe_data = {}

        for cirurgia in cirurgias:
            # Split team members (assuming they're comma-separated)
            membros = [membro.strip() for membro in cirurgia.equipe.split(',')]
            logger.debug(f"Team members for surgery {cirurgia.id}: {membros}")

            # Count surgeries for each team member
            for membro in membros:
                if membro not in equipe_data:
                    equipe_data[membro] = {
                        'quantidade': 0,
                        'unidades': set()
                    }
                equipe_data[membro]['quantidade'] += 1
                equipe_data[membro]['unidades'].add(cirurgia.unidade)

        # Format data for response
        formatted_data = {
            'equipe': [
                {
                    'nome': membro,
                    'quantidade': data['quantidade'],
                    'unidades': len(data['unidades'])
                }
                for membro, data in equipe_data.items()
            ]
        }
        logger.debug(f"Formatted equipe data: {formatted_data}")

        return jsonify(formatted_data)

    except Exception as e:
        logger.exception(f"Error getting team data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/import_excel', methods=['POST'])
def import_excel():
    """Import data from Excel file to PostgreSQL database"""
    try:
        logger.info("Starting Excel data import")

        # Read Excel file
        df = pd.read_excel('attached_assets/relatorio_cirurgias.xlsx')
        logger.info(f"Successfully read Excel file with {len(df)} rows")
        logger.info(f"DataFrame columns: {df.columns.tolist()}")
        logger.info(f"DataFrame shape: {df.shape}")
        logger.info("First few rows of data:")
        logger.info(df.head().to_string())

        # Clear existing records before import
        Cirurgia.query.delete()
        db.session.commit()
        logger.info("Cleared existing records from database")

        # Import each row to database
        successful_imports = 0
        for index, row in df.iterrows():
            try:
                # Convert date string to date object
                data = pd.to_datetime(row['data']).date() if pd.notna(row['data']) else datetime.now().date()

                # Function to safely convert values
                def safe_convert(value, type_func, default=0):
                    try:
                        if pd.isna(value):
                            return default
                        return type_func(value)
                    except (ValueError, TypeError):
                        logger.warning(f"Error converting value '{value}' to {type_func.__name__}")
                        return default

                # Create new Cirurgia instance with proper type conversions
                cirurgia = Cirurgia(
                    data=data,
                    nome=str(row.get('nome', '')).strip(),
                    unidade=str(row.get('unidade', '')).strip(),
                    medico=str(row.get('medico', '')).strip(),
                    equipe=str(row.get('equipe', '')).strip(),
                    hora_cirurgia=str(row.get('hora_cirurgia', '')).strip(),
                    tempo_cirurgia=safe_convert(row.get('tempo_cirurgia'), float),
                    total_foliculos=safe_convert(row.get('total_foliculos'), int),
                    frente=safe_convert(row.get('frente'), int),
                    densidade_scketh=safe_convert(row.get('densidade_scketh'), float),
                    coroa=safe_convert(row.get('coroa'), int),
                    scalpe=safe_convert(row.get('scalpe'), int),
                    peninsula_direita=safe_convert(row.get('peninsula_direita'), int),
                    peninsula_esquerda=safe_convert(row.get('peninsula_esquerda'), int),
                    safira=str(row.get('safira', '')).strip(),
                    punch=str(row.get('punch', '')).strip(),
                    solucao_frente=safe_convert(row.get('solucao_frente'), float),
                    solucao_coroa=safe_convert(row.get('solucao_coroa'), float),
                    solucao_xilo_frente=safe_convert(row.get('solucao_xilo_frente'), float),
                    q1_area=safe_convert(row.get('q1_area'), float),
                    q1_furos=safe_convert(row.get('q1_furos'), int),
                    q1_fios=safe_convert(row.get('q1_fios'), int),
                    q2_area=safe_convert(row.get('q2_area'), float),
                    q2_furos=safe_convert(row.get('q2_furos'), int),
                    q2_fios=safe_convert(row.get('q2_fios'), int),
                    q3_area=safe_convert(row.get('q3_area'), float),
                    q3_furos=safe_convert(row.get('q3_furos'), int),
                    q3_fios=safe_convert(row.get('q3_fios'), int),
                    q4_area=safe_convert(row.get('q4_area'), float),
                    q4_furos=safe_convert(row.get('q4_furos'), int),
                    q4_fios=safe_convert(row.get('q4_fios'), int),
                    infiltracao=safe_convert(row.get('infiltracao'), int),
                    sedacao=safe_convert(row.get('sedacao'), int),
                    sangramento=safe_convert(row.get('sangramento'), int),
                    implante_secundario=str(row.get('implante_secundario', '')).strip(),
                    transamin=str(row.get('transamin', '')).strip(),
                    tadalafila=str(row.get('tadalafila', '')).strip(),
                    diprospam=str(row.get('diprospam', '')).strip(),
                    fumante=str(row.get('fumante', '')).strip(),
                    antecedentes=str(row.get('antecedentes', '')).strip(),
                    comentarios=str(row.get('comentarios', '')).strip()
                )

                # Calculate derived fields
                if cirurgia.q1_area > 0:
                    cirurgia.q1_densidade = cirurgia.q1_furos / cirurgia.q1_area
                    cirurgia.q1_taxa_quebra = (1 - cirurgia.q1_fios / cirurgia.q1_furos) * 100 if cirurgia.q1_furos > 0 else 0

                if cirurgia.q2_area > 0:
                    cirurgia.q2_densidade = cirurgia.q2_furos / cirurgia.q2_area
                    cirurgia.q2_taxa_quebra = (1 - cirurgia.q2_fios / cirurgia.q2_furos) * 100 if cirurgia.q2_furos > 0 else 0

                if cirurgia.q3_area > 0:
                    cirurgia.q3_densidade = cirurgia.q3_furos / cirurgia.q3_area
                    cirurgia.q3_taxa_quebra = (1 - cirurgia.q3_fios / cirurgia.q3_furos) * 100 if cirurgia.q3_furos > 0 else 0

                if cirurgia.q4_area > 0:
                    cirurgia.q4_densidade = cirurgia.q4_furos / cirurgia.q4_area
                    cirurgia.q4_taxa_quebra = (1 - cirurgia.q4_fios / cirurgia.q4_furos) * 100 if cirurgia.q4_furos > 0 else 0

                db.session.add(cirurgia)
                successful_imports += 1
                logger.info(f"Successfully processed row {index + 1}")

            except Exception as row_error:
                logger.error(f"Error processing row {index + 1}:")
                logger.error(f"Row data: {row.to_dict()}")
                logger.error(f"Error details: {str(row_error)}")
                continue

        # Commit all changes
        db.session.commit()
        logger.info(f"Excel data imported successfully to database. Imported {successful_imports} out of {len(df)} rows.")
        return jsonify({"success": True, "message": f"Dados importados com sucesso! ({successful_imports} registros)"})

    except Exception as e:
        logger.error(f"Error importing Excel data: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao importar dados: {str(e)}"})

# Create database tables within app context
with app.app_context():
    db.create_all()

    # Verify and restore data after deployment
    try:
        from restore_deployment_data import restore_deployment_data
        success, restored_files = restore_deployment_data()
        if success:
            logger.info("✅ Dados restaurados com sucesso após deployment")
        else:
            logger.warning("⚠️ Não foi possível restaurar os dados automaticamente")
    except Exception as e:
        logger.error(f"❌ Erro ao restaurar dados: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    try:
        logger.info(f"Starting server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.exception("Failed to start server:")
        raise