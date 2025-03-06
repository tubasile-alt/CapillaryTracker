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

@app.route('/health')
def health():
    """Rota simples para verificação de saúde do servidor"""
    return "OK"

@app.route('/test')
def test():
    """Rota de teste para verificar conectividade"""
    logger.info("Test route accessed")
    return "Servidor Flask está funcionando!"

@app.route('/')
def index():
    """Rota principal - serve a página de dashboard"""
    logger.info("Accessing index route")
    try:
        # Temporariamente retornando uma resposta simples para teste
        return "Sistema de Cirurgia Capilar - OK"
    except Exception as e:
        logger.exception(f"Erro crítico na rota index: {str(e)}")
        return "Error accessing the application", 500

@app.route('/form')
def form():
    """Página de formulário de cirurgia"""
    logger.info("Accessing form route")
    try:
        form_data = {
            'title': 'Cadastro de Cirurgia Capilar',
            'fields': [
                # Dados Gerais
                {'name': 'unidade', 'label': 'Unidade', 'type': 'select', 'required': True,
                 'options': ['Ribeirão Preto', 'Campinas']},
                {'name': 'medico', 'label': 'Médico', 'type': 'select_dynamic', 'required': True},
                {'name': 'equipe', 'label': 'Equipe', 'type': 'select_dynamic', 'required': True},
                {'name': 'data', 'label': 'Data da Cirurgia', 'type': 'date', 'required': True},
                {'name': 'hora_inicio', 'label': 'Hora de Início', 'type': 'time', 'required': True},
                {'name': 'hora_fim', 'label': 'Hora de Término', 'type': 'time', 'required': True},
                {'name': 'observacoes', 'label': 'Observações', 'type': 'textarea'},

                # Informações do Implante
                {'name': 'tipo_cirurgia', 'label': 'Tipo de Cirurgia', 'type': 'select', 'required': True,
                 'options': ['FUE', 'FUT', 'Híbrida']},
                {'name': 'area_receptora', 'label': 'Área Receptora', 'type': 'text', 'required': True},
                {'name': 'lamina_fio', 'label': 'Lâmina/Fio', 'type': 'text', 'required': True},
                {'name': 'punch', 'label': 'Punch', 'type': 'text', 'required': True},
                {'name': 'tadalafila', 'label': 'Tadalafila', 'type': 'select', 'required': True,
                 'options': ['Sim', 'Não']},
                {'name': 'anestesia', 'label': 'Anestesia', 'type': 'text', 'required': True},
                {'name': 'infiltracao', 'label': 'Infiltração', 'type': 'text', 'required': True},

                # Procedimentos e Ferramentas
                {'name': 'solucao_frente', 'label': 'Solução Frente (seringas)', 'type': 'number', 'required': True},
                {'name': 'solucao_coroa', 'label': 'Solução Coroa (seringas)', 'type': 'number', 'required': True},
                {'name': 'solucao_xilo_frente', 'label': 'Solução Xilo Frente (seringas)', 'type': 'number', 'required': True},
                {'name': 'solucao_xilo_coroa', 'label': 'Solução Xilo Coroa', 'type': 'number', 'required': True},
                {'name': 'punch_usado', 'label': 'Punch Utilizado', 'type': 'text', 'required': True},

                # Extração - Quadrante 1
                {'name': 'q1_area', 'label': 'Quadrante 1 - Área', 'type': 'number', 'required': True},
                {'name': 'q1_furos', 'label': 'Quadrante 1 - Furos', 'type': 'number', 'required': True},
                {'name': 'q1_fios', 'label': 'Quadrante 1 - Fios', 'type': 'number', 'required': True},

                # Extração - Quadrante 2
                {'name': 'q2_area', 'label': 'Quadrante 2 - Área', 'type': 'number', 'required': True},
                {'name': 'q2_furos', 'label': 'Quadrante 2 - Furos', 'type': 'number', 'required': True},
                {'name': 'q2_fios', 'label': 'Quadrante 2 - Fios', 'type': 'number', 'required': True},

                # Extração - Quadrante 3
                {'name': 'q3_area', 'label': 'Quadrante 3 - Área', 'type': 'number', 'required': True},
                {'name': 'q3_furos', 'label': 'Quadrante 3 - Furos', 'type': 'number', 'required': True},
                {'name': 'q3_fios', 'label': 'Quadrante 3 - Fios', 'type': 'number', 'required': True},

                # Extração - Quadrante 4
                {'name': 'q4_area', 'label': 'Quadrante 4 - Área', 'type': 'number', 'required': True},
                {'name': 'q4_furos', 'label': 'Quadrante 4 - Furos', 'type': 'number', 'required': True},
                {'name': 'q4_fios', 'label': 'Quadrante 4 - Fios', 'type': 'number', 'required': True},

                # Avaliação Intraoperatória
                {'name': 'dificuldade_extracao', 'label': 'Dificuldade na Extração', 'type': 'select',
                 'options': ['Baixa', 'Média', 'Alta'], 'required': True},
                {'name': 'sangramento', 'label': 'Sangramento', 'type': 'select',
                 'options': ['Mínimo', 'Moderado', 'Intenso'], 'required': True},
                {'name': 'observacoes_intra', 'label': 'Observações Intraoperatórias', 'type': 'textarea'},

                # Histórico do Paciente
                {'name': 'cirurgia_anterior', 'label': 'Cirurgia Anterior', 'type': 'select',
                 'options': ['Sim', 'Não'], 'required': True},
                {'name': 'data_anterior', 'label': 'Data da Cirurgia Anterior', 'type': 'date'},
                {'name': 'medicamentos', 'label': 'Medicamentos em Uso', 'type': 'textarea'},
                {'name': 'alergias', 'label': 'Alergias', 'type': 'textarea'},
                {'name': 'comorbidades', 'label': 'Comorbidades', 'type': 'textarea'},
                {'name': 'tratamentos', 'label': 'Tratamentos Anteriores', 'type': 'textarea'},

                # Comentários e Finalização
                {'name': 'observacoes_finais', 'label': 'Observações Finais', 'type': 'textarea'},
            ]
        }
        logger.debug(f"Form data generated: {form_data}") #Added debug log
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
        # ALWAYS serve the app on port 5000
        logger.info(f"Starting Flask server on port 5000")
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise