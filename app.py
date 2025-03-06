import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_cors import CORS
import pandas as pd
from datetime import datetime

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    """Rota principal - serve a página de dashboard"""
    logger.info("Accessing index route")
    try:
        # Inicializar dados vazios para o dashboard
        dashboard_data = {
            'total_surgeries': 0,
            'avg_follicles': 0,
            'avg_density': 0,
            'labels': [],
            'datasets': [],
            'update_time': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        return render_template('dashboard.html', data=dashboard_data)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return "Error accessing the application", 500

@app.route('/form')
def form():
    """Página de formulário de cirurgia"""
    logger.info("Accessing form route")
    try:
        form_data = {
            'title': 'Cadastro de Cirurgia Capilar',
            'fields': []  # Campos serão adicionados conforme necessário
        }
        return render_template('form.html', form=form_data, data={})
    except Exception as e:
        logger.error(f"Error in form route: {str(e)}")
        return "Error accessing the form", 500

@app.route('/novo_cadastro')
def novo_cadastro():
    """Redireciona para o formulário de cadastro"""
    logger.info("Redirecting to form from novo_cadastro")
    return redirect(url_for('form'))

@app.route('/necrose')
def necrose():
    """Página de avaliação de necrose"""
    logger.info("Accessing necrose route")
    try:
        return render_template('necrose.html')
    except Exception as e:
        logger.error(f"Error in necrose route: {str(e)}")
        return "Error accessing necrose page", 500

@app.route('/get_medicos/<unidade>')
def get_medicos(unidade):
    """API para obter médicos por unidade"""
    logger.info(f"Retrieving doctors for unit: {unidade}")
    medicos_por_unidade = {
        'Ribeirão Preto': ['Dr. Arthur', 'Dr. Daniel'],
        'Campinas': ['Dra. Isadora', 'Dra. Adriana']
    }
    return {'medicos': medicos_por_unidade.get(unidade, [])}

@app.route('/get_equipe/<unidade>')
def get_equipe(unidade):
    """API para obter equipe por unidade"""
    logger.info(f"Retrieving team for unit: {unidade}")
    equipe_por_unidade = {
        'Ribeirão Preto': ['Aline', 'Natália', 'Ana'],
        'Campinas': ['Juliana', 'Gabriela']
    }
    return {'equipe': equipe_por_unidade.get(unidade, [])}

if __name__ == "__main__":
    try:
        import os
        # Use PORT environment variable with fallback to 8080
        port = int(os.environ.get("PORT", 8080))
        logger.info(f"Starting Flask server on port {port}")
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise
