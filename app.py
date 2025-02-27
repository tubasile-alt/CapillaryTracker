import os
import logging
import traceback
from flask import Flask, render_template

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting Flask application...")

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    logger.info("Accessing index route")
    return render_template('base.html')

@app.route('/novo_cadastro')
def novo_cadastro():
    logger.info("Accessing novo_cadastro route")
    # Estrutura básica do formulário
    form_data = {
        'title': 'Cadastro de Cirurgia Capilar',
        'fields': [
            {'name': 'nome', 'label': 'Nome do Paciente', 'type': 'text', 'required': True},
            {'name': 'data', 'label': 'Data da Cirurgia', 'type': 'date', 'required': True},
            {'name': 'unidade', 'label': 'Unidade', 'type': 'select', 'required': True, 
             'options': ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte']},
            {'name': 'medico', 'label': 'Médico Responsável', 'type': 'select_dynamic', 'required': True},
            {'name': 'equipe', 'label': 'Equipe', 'type': 'select_dynamic', 'required': True},
            {'name': 'observacoes', 'label': 'Observações', 'type': 'textarea', 'required': False}
        ]
    }
    return render_template('form.html', form=form_data, data={})

@app.route('/dashboard')
def dashboard():
    logger.info("Accessing dashboard route")
    try:
        # Create a simple dashboard data structure
        dashboard_data = {
            'labels': ['01/2025', '02/2025'],
            'datasets': [
                {
                    'label': 'Exemplo',
                    'data': [0, 0]
                }
            ],
            'has_follicle_data': False
        }

        return render_template('dashboard.html', data=dashboard_data)

    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}\n{traceback.format_exc()}")
        return render_template('dashboard.html', data={}, 
                            error="Erro ao carregar dashboard")

@app.route('/get_medicos/<unidade>')
def get_medicos(unidade):
    logger.info(f"Retrieving doctors for unit: {unidade}")
    # Simulando médicos por unidade
    medicos_por_unidade = {
        'São Paulo': ['Dr. Silva', 'Dra. Oliveira', 'Dr. Santos'],
        'Rio de Janeiro': ['Dr. Costa', 'Dra. Lima', 'Dr. Almeida'],
        'Belo Horizonte': ['Dr. Pereira', 'Dra. Ferreira', 'Dr. Ribeiro']
    }
    return {'medicos': medicos_por_unidade.get(unidade, [])}

@app.route('/get_equipe/<unidade>')
def get_equipe(unidade):
    logger.info(f"Retrieving team for unit: {unidade}")
    # Simulando equipe por unidade
    equipe_por_unidade = {
        'São Paulo': ['Enfermeiro João', 'Técnico Pedro', 'Auxiliar Maria'],
        'Rio de Janeiro': ['Enfermeira Ana', 'Técnico Carlos', 'Auxiliar Teresa'],
        'Belo Horizonte': ['Enfermeiro Lucas', 'Técnica Amanda', 'Auxiliar Roberto']
    }
    return {'equipe': equipe_por_unidade.get(unidade, [])}

if __name__ == '__main__':
    try:
        port = 3000
        logger.info(f"Starting Flask server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {str(e)}\n{traceback.format_exc()}")
        raise