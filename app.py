import os
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting Flask application...")

try:
    from flask import Flask, render_template, request, redirect, url_for, flash, session
    import pandas as pd
    from utils import validate_date, validate_time, validate_numeric, validate_range
    logger.info("Successfully imported all required packages")
except Exception as e:
    logger.error(f"Failed to import required packages: {str(e)}\n{traceback.format_exc()}")
    raise

app = Flask(__name__)
app.secret_key = os.urandom(24)

UNIDADES_MEDICOS = {
    "Ribeirão": ["Dr. Arthur", "Dr. Daniel"],
    "Campinas": ["Dra. Isadora", "Dra. Adriana"],
    "Sorocaba": ["Dra. Adriana"]
}

UNIDADES_EQUIPES = {
    "Ribeirão": ["Natália", "Aline", "Ana", "Lavine"],
    "Campinas": ["Juliana", "Larissa", "Gabriela"],
    "Sorocaba": ["Juliana", "Larissa", "Gabriela"]
}

FORMS = {
    "dados_gerais": {
        "title": "Dados Gerais",
        "fields": [
            {"name": "data", "label": "Data (DD/MM/AAAA)", "type": "text", "required": True},
            {"name": "unidade", "label": "Unidade", "type": "select", 
             "options": ["Ribeirão", "Campinas", "Sorocaba"], "required": True},
            {"name": "medico", "label": "Médico", "type": "select_dynamic", "required": True},
            {"name": "paciente", "label": "Paciente", "type": "text", "required": True},
            {"name": "equipe", "label": "Equipe", "type": "select_dynamic", "required": True},
            {"name": "hora_cirurgia", "label": "Hora da Cirurgia (HH:MM)", "type": "text", "required": True},
            {"name": "tempo_cirurgia", "label": "Tempo de Cirurgia (horas)", "type": "number", "required": True}
        ],
        "next": "implante"
    },
    "implante": {
        "title": "Informações do Implante",
        "fields": [
            {"name": "total_foliculos", "label": "Total de Folículos", "type": "number", "required": True},
            {"name": "frente", "label": "Frente", "type": "number", "required": False},
            {"name": "densidade_scketh", "label": "Densidade Scketh", "type": "number", "required": False},
            {"name": "coroa", "label": "Coroa", "type": "number", "required": False},
            {"name": "scalpe", "label": "Scalpe", "type": "number", "required": False},
            {"name": "peninsula_direita", "label": "Península Direita", "type": "number", "required": False},
            {"name": "peninsula_esquerda", "label": "Península Esquerda", "type": "number", "required": False}
        ],
        "next": "procedimentos",
        "prev": "dados_gerais"
    },
    "procedimentos": {
        "title": "Procedimentos e Ferramentas",
        "fields": [
            {"name": "safira", "label": "Safira?", "type": "select", "options": ["Sim", "Não"], "required": False},
            {"name": "punch", "label": "Punch (mm)", "type": "select", "options": ["0.75", "0.85", "0.95"], "required": True},
            {"name": "solucao_frente", "label": "Solução Frente (seringas)", "type": "number", "required": False},
            {"name": "solucao_coroa", "label": "Solução Coroa (seringas)", "type": "number", "required": False},
            {"name": "solucao_xilo_frente", "label": "Solução Xilo Frente (seringas)", "type": "number", "required": False}
        ],
        "next": "distribuicao",
        "prev": "implante"
    },
    "distribuicao": {
        "title": "Densidades de Extração",
        "fields": [
            {"name": "le", "label": "LE", "type": "number", "required": True},
            {"name": "me", "label": "ME", "type": "number", "required": True},
            {"name": "md", "label": "MD", "type": "number", "required": True},
            {"name": "ld", "label": "LD", "type": "number", "required": True}
        ],
        "next": "avaliacao",
        "prev": "procedimentos"
    },
    "avaliacao": {
        "title": "Avaliação Intraoperatória",
        "fields": [
            {"name": "infiltracao", "label": "Infiltração (1-3)", "type": "select", "options": ["1", "2", "3"], "required": True},
            {"name": "sedacao", "label": "Sedação (1-3)", "type": "select", "options": ["1", "2", "3"], "required": True},
            {"name": "sangramento", "label": "Sangramento (1-3)", "type": "select", "options": ["1", "2", "3"], "required": True}
        ],
        "next": "historico",
        "prev": "distribuicao"
    },
    "historico": {
        "title": "Histórico do Paciente",
        "fields": [
            {"name": "implante_secundario", "label": "Implante Secundário?", "type": "select", "options": ["Sim", "Não"], "required": True},
            {"name": "transamin", "label": "Transamin?", "type": "select", "options": ["Sim", "Não"], "required": False},
            {"name": "tadalafila", "label": "Tadalafila?", "type": "select", "options": ["Sim", "Não"], "required": False},
            {"name": "diprospam", "label": "Diprospam/Beta 30?", "type": "select", "options": ["Sim", "Não"], "required": False},
            {"name": "fumante", "label": "Fumante?", "type": "select", "options": ["Sim", "Não"], "required": True},
            {"name": "antecedentes", "label": "Antecedentes Pessoais", "type": "textarea", "required": False}
        ],
        "next": "finalizacao",
        "prev": "avaliacao"
    },
    "finalizacao": {
        "title": "Comentários e Finalização",
        "fields": [
            {"name": "comentarios", "label": "Comentários", "type": "textarea", "required": False}
        ],
        "prev": "historico"
    }
}

def validate_form_data(form_id, data):
    form = FORMS[form_id]
    errors = []

    for field in form["fields"]:
        value = data.get(field["name"], "").strip()

        if field["required"] and not value:
            errors.append(f"O campo {field['label']} é obrigatório")
            continue

        if value:
            if field["name"] == "data" and not validate_date(value):
                errors.append("Data inválida. Use o formato DD/MM/AAAA")
            elif field["name"] == "hora_cirurgia" and not validate_time(value):
                errors.append("Hora inválida. Use o formato HH:MM")
            elif field["type"] == "number" and not validate_numeric(value):
                errors.append(f"O campo {field['label']} deve ser numérico")
            elif "1-3" in field["label"] and not validate_range(value, 1, 3):
                errors.append(f"O campo {field['label']} deve estar entre 1 e 3")

    return errors

@app.route('/')
def index():
    session.clear()
    return redirect(url_for('form', form_id='dados_gerais'))

@app.route('/form/<form_id>', methods=['GET', 'POST'])
def form(form_id):
    logger.info(f"Accessing form: {form_id}")
    if form_id not in FORMS:
        return redirect(url_for('index'))

    if request.method == 'POST':
        form_data = request.form.to_dict()
        logger.debug(f"Form data received: {form_data}")

        # Use formatted date if available
        if 'data_formatted' in form_data and form_data['data_formatted']:
            form_data['data'] = form_data['data_formatted']

        errors = validate_form_data(form_id, form_data)

        if errors:
            for error in errors:
                flash(error, 'error')
                logger.warning(f"Form validation error: {error}")
            return render_template('form.html', form=FORMS[form_id], data=form_data)

        # Store form data in session
        if 'form_data' not in session:
            session['form_data'] = {}
        session['form_data'].update(form_data)
        logger.debug("Form data stored in session")

        # If there's a next form, go to it
        if 'next' in FORMS[form_id]:
            return redirect(url_for('form', form_id=FORMS[form_id]['next']))
        else:
            return redirect(url_for('save'))

    # GET request
    form_data = session.get('form_data', {})
    return render_template('form.html', form=FORMS[form_id], data=form_data)

@app.route('/save')
def save():
    if 'form_data' not in session:
        return redirect(url_for('index'))

    data = session['form_data']
    df_new = pd.DataFrame([data])

    filename = 'cirurgias.xlsx'
    if os.path.exists(filename):
        df_existing = pd.read_excel(filename)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_excel(filename, index=False)
    else:
        df_new.to_excel(filename, index=False)

    session.clear()
    flash('Dados salvos com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/get_medicos/<unidade>')
def get_medicos(unidade):
    logger.debug(f"Getting doctors for unit: {unidade}")
    return {"medicos": UNIDADES_MEDICOS.get(unidade, [])}

@app.route('/get_equipe/<unidade>')
def get_equipe(unidade):
    logger.debug(f"Getting team for unit: {unidade}")
    return {"equipe": UNIDADES_EQUIPES.get(unidade, [])}

@app.route('/dashboard')
def dashboard():
    logger.info("Accessing dashboard")
    try:
        if not os.path.exists('cirurgias.xlsx'):
            logger.warning("No data file found for dashboard")
            return render_template('dashboard.html', data={})

        # Read Excel file
        df = pd.read_excel('cirurgias.xlsx')
        logger.debug(f"Loaded data from Excel: {len(df)} rows")
        logger.debug(f"Columns in DataFrame: {df.columns.tolist()}")

        # Skip processing if DataFrame is empty
        if df.empty:
            logger.warning("DataFrame is empty")
            return render_template('dashboard.html', data={})

        # Convert data to datetime
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')

        # Check required columns
        required_columns = ['data', 'unidade', 'total_foliculos', 'le']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return render_template('dashboard.html', data={}, 
                                error=f"Colunas ausentes no arquivo: {', '.join(missing_columns)}")

        try:
            # Log first few rows for debugging
            logger.debug("First few rows of the DataFrame:")
            logger.debug(df.head().to_string())

            # Check if required columns exist for follicle and density charts
            has_follicle_data = all(col in df.columns for col in ['total_foliculos', 'le'])

            # Prepare data for patients per month/unit
            monthly_data = df.groupby([pd.Grouper(key='data', freq='M'), 'unidade']).size().reset_index()
            monthly_data.columns = ['data', 'unidade', 'total']
            monthly_data['mes_ano'] = monthly_data['data'].dt.strftime('%m/%Y')

            # Calculate average follicles per month and LE density if data exists
            if has_follicle_data:
                monthly_follicles = df.groupby(pd.Grouper(key='data', freq='M')).agg({
                    'total_foliculos': 'mean',
                    'le': 'mean'  # LE density (primeira faixa)
                }).reset_index()
                monthly_follicles['mes_ano'] = monthly_follicles['data'].dt.strftime('%m/%Y')
            else:
                # Create empty structure when data isn't available
                monthly_follicles = pd.DataFrame({'data': [], 'mes_ano': [], 'total_foliculos': [], 'le': []})

            # Create dashboard data dictionary
            dashboard_data = {
                'labels': sorted(monthly_data['mes_ano'].unique().tolist()),
                'unidades': sorted(monthly_data['unidade'].unique().tolist()),
                'datasets': [],
                'follicles_data': {
                    'labels': sorted(monthly_follicles['mes_ano'].tolist()),
                    'averages': monthly_follicles['total_foliculos'].round(2).tolist(),
                    'le_density': monthly_follicles['le'].round(2).tolist()
                }
            }

            # Prepare data for each unidade
            for unidade in dashboard_data['unidades']:
                unidade_data = monthly_data[monthly_data['unidade'] == unidade]
                dataset = {
                    'label': unidade,
                    'data': [int(unidade_data[unidade_data['mes_ano'] == mes]['total'].iloc[0]) 
                            if not unidade_data[unidade_data['mes_ano'] == mes].empty else 0 
                            for mes in dashboard_data['labels']]
                }
                dashboard_data['datasets'].append(dataset)

            logger.info("Dashboard data prepared successfully")
            logger.debug(f"Dashboard data: {dashboard_data}")
            return render_template('dashboard.html', data=dashboard_data)
        except Exception as e:
            logger.error(f"Error processing dashboard data: {str(e)}\n{traceback.format_exc()}")
            return render_template('dashboard.html', data={}, 
                                error="Erro ao processar dados do dashboard")

    except Exception as e:
        logger.error(f"Error preparing dashboard data: {str(e)}\n{traceback.format_exc()}")
        return render_template('dashboard.html', data={}, 
                            error="Erro ao carregar dados do dashboard")

if __name__ == '__main__':
    try:
        logger.info("Starting Flask server on port 8080...")
        logger.debug("Debug mode is enabled")
        logger.debug("Current working directory: %s", os.getcwd())
        logger.debug("Environment variables: %s", str(dict(os.environ)))
        app.run(host='0.0.0.0', port=8080, debug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {str(e)}\n{traceback.format_exc()}")
        raise