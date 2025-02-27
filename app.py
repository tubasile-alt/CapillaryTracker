
import os
import logging
import traceback
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
from datetime import datetime

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

@app.route('/novo_cadastro', methods=['GET', 'POST'])
def novo_cadastro():
    logger.info("Accessing novo_cadastro route")
    if request.method == 'POST':
        try:
            # Processar os dados do formulário
            form_data = request.form.to_dict()
            
            # Processar checkboxes múltiplos
            if 'equipe_values' in form_data:
                form_data['equipe'] = form_data['equipe_values']
                del form_data['equipe_values']
            
            # Salvar no Excel
            save_to_excel(form_data)
            
            flash("Dados salvos com sucesso!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}\n{traceback.format_exc()}")
            flash(f"Erro ao salvar dados: {str(e)}", "error")
    
    # Estrutura do formulário completo
    form_data = {
        'title': 'Cadastro de Cirurgia Capilar',
        'fields': [
            # Dados Gerais da Cirurgia
            {'name': 'data', 'label': 'Data da Cirurgia', 'type': 'date', 'required': True},
            {'name': 'nome', 'label': 'Nome do Paciente', 'type': 'text', 'required': True},
            {'name': 'unidade', 'label': 'Unidade', 'type': 'select', 'required': True, 
             'options': ['Ribeirão Preto', 'Campinas']},
            {'name': 'medico', 'label': 'Médico Responsável', 'type': 'select_dynamic', 'required': True},
            {'name': 'equipe', 'label': 'Equipe', 'type': 'select_dynamic', 'required': True},
            {'name': 'hora_cirurgia', 'label': 'Hora da Cirurgia (HH:MM)', 'type': 'time', 'required': True},
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
            {'name': 'safira', 'label': 'Safira?', 'type': 'select', 'required': False,
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
            {'name': 'transamin', 'label': 'Transamin?', 'type': 'select', 'required': False,
             'options': ['Sim', 'Não']},
            {'name': 'tadalafila', 'label': 'Tadalafila?', 'type': 'select', 'required': False,
             'options': ['Sim', 'Não']},
            {'name': 'diprospam', 'label': 'Diprospam/Beta 30?', 'type': 'select', 'required': False,
             'options': ['Sim', 'Não']},
            {'name': 'fumante', 'label': 'Fumante?', 'type': 'select', 'required': True,
             'options': ['Sim', 'Não']},
            {'name': 'antecedentes', 'label': 'Antecedentes Pessoais', 'type': 'textarea', 'required': False},
            
            # Comentários e Finalização
            {'name': 'comentarios', 'label': 'Comentários', 'type': 'textarea', 'required': False}
        ]
    }
    return render_template('form.html', form=form_data, data={})

def save_to_excel(data):
    """Salva os dados em um arquivo Excel."""
    # Calcular dados adicionais
    if all(key in data for key in ['q1_area', 'q1_furos', 'q1_fios']):
        try:
            # Calcular densidade de extração por quadrante (furos/área)
            data['q1_densidade'] = float(data['q1_furos']) / float(data['q1_area']) if float(data['q1_area']) > 0 else 0
            data['q2_densidade'] = float(data['q2_furos']) / float(data['q2_area']) if float(data['q2_area']) > 0 else 0
            data['q3_densidade'] = float(data['q3_furos']) / float(data['q3_area']) if float(data['q3_area']) > 0 else 0
            data['q4_densidade'] = float(data['q4_furos']) / float(data['q4_area']) if float(data['q4_area']) > 0 else 0
            
            # Calcular taxa de quebra (fios/furos em porcentagem)
            data['q1_taxa_quebra'] = (1 - float(data['q1_fios']) / float(data['q1_furos'])) * 100 if float(data['q1_furos']) > 0 else 0
            data['q2_taxa_quebra'] = (1 - float(data['q2_fios']) / float(data['q2_furos'])) * 100 if float(data['q2_furos']) > 0 else 0
            data['q3_taxa_quebra'] = (1 - float(data['q3_fios']) / float(data['q3_furos'])) * 100 if float(data['q3_furos']) > 0 else 0
            data['q4_taxa_quebra'] = (1 - float(data['q4_fios']) / float(data['q4_furos'])) * 100 if float(data['q4_furos']) > 0 else 0
        except (ValueError, ZeroDivisionError) as e:
            logger.error(f"Error calculating derived values: {str(e)}")
    
    # Criar um DataFrame com os dados
    df_new = pd.DataFrame([data])
    
    # Nome do arquivo Excel
    filename = "cirurgias.xlsx"
    
    # Verificar se o arquivo existe
    if os.path.exists(filename):
        # Append to existing file
        df_existing = pd.read_excel(filename)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_excel(filename, index=False)
    else:
        # Create new file
        df_new.to_excel(filename, index=False)
    
    logger.info(f"Data saved to {filename}")
    return True

@app.route('/get_medicos/<unidade>')
def get_medicos(unidade):
    logger.info(f"Retrieving doctors for unit: {unidade}")
    # Médicos por unidade conforme especificação
    medicos_por_unidade = {
        'Ribeirão Preto': ['Dr. Arthur', 'Dr. Daniel'],
        'Campinas': ['Dra. Isadora', 'Dra. Adriana']
    }
    return {'medicos': medicos_por_unidade.get(unidade, [])}

@app.route('/get_equipe/<unidade>')
def get_equipe(unidade):
    logger.info(f"Retrieving team for unit: {unidade}")
    # Equipe por unidade conforme especificação
    equipe_por_unidade = {
        'Ribeirão Preto': ['Aline', 'Natália', 'Ana'],
        'Campinas': ['Juliana', 'Gabriela']
    }
    return {'equipe': equipe_por_unidade.get(unidade, [])}

@app.route('/dashboard')
def dashboard():
    logger.info("Accessing dashboard route")
    try:
        # Se o arquivo Excel existir, carregar os dados para o dashboard
        filename = "cirurgias.xlsx"
        if os.path.exists(filename):
            df = pd.read_excel(filename)
            # Processar dados para o dashboard
            # Exemplo simples - contar cirurgias por mês
            if not df.empty and 'data' in df.columns:
                df['mes_ano'] = pd.to_datetime(df['data']).dt.strftime('%m/%Y')
                cirurgias_por_mes = df.groupby('mes_ano').size().reset_index(name='count')
                
                dashboard_data = {
                    'labels': cirurgias_por_mes['mes_ano'].tolist(),
                    'datasets': [
                        {
                            'label': 'Cirurgias',
                            'data': cirurgias_por_mes['count'].tolist()
                        }
                    ],
                    'has_follicle_data': 'total_foliculos' in df.columns
                }
                
                # Se temos dados de folículos, adicionar ao dashboard
                if dashboard_data['has_follicle_data']:
                    folliculo_medio = df.groupby('mes_ano')['total_foliculos'].mean().reset_index()
                    dashboard_data['datasets'].append({
                        'label': 'Média de Folículos',
                        'data': folliculo_medio['total_foliculos'].tolist()
                    })
            else:
                dashboard_data = {
                    'labels': [],
                    'datasets': [{'label': 'Cirurgias', 'data': []}],
                    'has_follicle_data': False
                }
        else:
            dashboard_data = {
                'labels': [],
                'datasets': [{'label': 'Cirurgias', 'data': []}],
                'has_follicle_data': False
            }

        return render_template('dashboard.html', data=dashboard_data)

    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}\n{traceback.format_exc()}")
        return render_template('dashboard.html', data={}, 
                            error="Erro ao carregar dashboard")

if __name__ == '__main__':
    try:
        port = 3000
        logger.info(f"Starting Flask server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {str(e)}\n{traceback.format_exc()}")
        raise
