import os
import logging
import traceback
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
from datetime import datetime
from fuzzywuzzy import fuzz
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting Flask application...")

app = Flask(__name__)
app.secret_key = os.urandom(24)

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

        logger.info("✅ All data cleared successfully through dashboard")
        return jsonify({'success': True, 'message': 'Dados limpos com sucesso'})
    except Exception as e:
        logger.error(f"Error clearing data via dashboard: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Erro ao limpar dados: {str(e)}'})

@app.route('/get_last_record')
def get_last_record():
    """Get the last surgery record information"""
    try:
        filename = "cirurgias.xlsx"
        if not os.path.exists(filename):
            return jsonify({'success': False, 'message': 'Nenhum registro encontrado'})
        
        df = pd.read_excel(filename)
        if df.empty:
            return jsonify({'success': False, 'message': 'Nenhum registro encontrado'})
        
        # Get last row
        last_record = df.iloc[-1]
        
        # Get patient name
        patient_name = last_record.get('nome', 'Nome não disponível')
        
        return jsonify({
            'success': True, 
            'patient_name': patient_name
        })
    except Exception as e:
        logger.error(f"Error getting last record: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Erro ao buscar último registro: {str(e)}'})

@app.route('/delete_last_record', methods=['POST'])
def delete_last_record():
    """Delete the last surgery record"""
    try:
        filename = "cirurgias.xlsx"
        if not os.path.exists(filename):
            return jsonify({'success': False, 'message': 'Nenhum registro encontrado para excluir'})
        
        df = pd.read_excel(filename)
        if df.empty:
            return jsonify({'success': False, 'message': 'Nenhum registro encontrado para excluir'})
        
        # Store the patient name before deletion
        patient_name = df.iloc[-1].get('nome', 'Nome não disponível')
        
        # Remove the last row
        df = df.iloc[:-1]
        
        # Save back to file
        df.to_excel(filename, index=False, engine='openpyxl')
        
        logger.info(f"✅ Last record deleted successfully (Patient: {patient_name})")
        return jsonify({
            'success': True, 
            'message': f'Registro do paciente {patient_name} excluído com sucesso'
        })
    except Exception as e:
        logger.error(f"Error deleting last record: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Erro ao excluir último registro: {str(e)}'})


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

            flash("✅ Dados salvos com sucesso! 🎉", "success")
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

def save_to_excel(data):
    try:
        logging.info("Salvando dados na planilha Excel...")
        filename = "cirurgias.xlsx"

        # Verificar se o arquivo existe
        if os.path.exists(filename):
            try:
                # Tente ler com openpyxl
                df_existing = pd.read_excel(filename, engine='openpyxl')
                # Adicionar nova linha
                df_new = pd.DataFrame([data])
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            except Exception as e:
                logging.error(f"Erro ao ler o arquivo Excel existente: {str(e)}")
                logging.error(traceback.format_exc())
                # Se falhar, criar um novo DataFrame
                df_combined = pd.DataFrame([data])
        else:
            # Criar novo arquivo
            df_combined = pd.DataFrame([data])

        # Salvar o DataFrame no arquivo Excel com engine específico
        df_combined.to_excel(filename, index=False, engine='openpyxl')
        logging.info("Dados salvos com sucesso!")
        return True, "Dados salvos com sucesso!"
    except Exception as e:
        logging.error(f"Erro ao salvar dados no Excel: {str(e)}")
        logging.error(traceback.format_exc())
        return False, f"Erro ao salvar dados: {str(e)}"

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
    # Lidar com valores vazios
    df = df.fillna(0)

    # Garantir que colunas numéricas tenham valores zerados quando vazios
    numeric_columns = df.select_dtypes(include=['number']).columns
    for col in numeric_columns:
        df[col] = df[col].fillna(0).replace('', 0)

    # Estrutura para armazenar os dados do dashboard
    dashboard_data = {
        'labels': [],
        'datasets': [],
        'has_follicle_data': False,
        'follicles_data': {'labels': [], 'averages': [], 'le_density': []},
        'total_surgeries': 0,
        'avg_follicles': 0,
        'avg_density': 0,
        'update_time': datetime.now().strftime('%d/%m/%Y %H:%M')
    }

    if df.empty:
        return dashboard_data

    # Processar datas e criar coluna mes_ano
    try:
        if 'data' in df.columns:
            df['mes_ano'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce').dt.strftime('%m/%Y')
            # Extrair ano e mês para filtragem
            df['ano'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce').dt.year
            df['mes'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce').dt.month
        else:
            # Se não houver coluna 'data', usar uma data padrão
            df['mes_ano'] = datetime.now().strftime('%m/%Y')
            df['ano'] = datetime.now().year
            df['mes'] = datetime.now().month
    except Exception as e:
        logger.error(f"Error processing dates: {str(e)}")
        df['mes_ano'] = datetime.now().strftime('%m/%Y')
        df['ano'] = datetime.now().year
        df['mes'] = datetime.now().month

    # Calcular estatísticas gerais
    dashboard_data['total_surgeries'] = len(df)

    # 1. Cirurgias por mês (total)
    cirurgias_por_mes = df.groupby('mes_ano').size().reset_index(name='count')
    cirurgias_por_mes['count'] = cirurgias_por_mes['count'].fillna(0).astype(int)

    dashboard_data['labels'] = cirurgias_por_mes['mes_ano'].tolist()

    # Adicionar dataset principal
    dashboard_data['datasets'].append({
        'label': 'Total de Cirurgias',
        'data': cirurgias_por_mes['count'].tolist()
    })

    # 2. Cirurgias por mês por unidade
    if 'unidade' in df.columns:
        # Substituir valores vazios na coluna unidade
        df['unidade'] = df['unidade'].fillna('Não especificada')

        cirurgias_por_mes_unidade = df.groupby(['mes_ano', 'unidade']).size().reset_index(name='count')
        cirurgias_por_mes_unidade['count'] = cirurgias_por_mes_unidade['count'].fillna(0).astype(int)

        # Preparar datasets por unidade
        unidades = df['unidade'].unique()

        for unidade in unidades:
            dados_unidade = cirurgias_por_mes_unidade[cirurgias_por_mes_unidade['unidade'] == unidade]
            # Mapa para todas as datas possíveis
            dados_completos = pd.DataFrame({
                'mes_ano': cirurgias_por_mes['mes_ano'].unique()
            })
            # Juntar com dados existentes
            merged = dados_completos.merge(dados_unidade, on='mes_ano', how='left')
            # Tratar valores nulos corretamente
            merged['count'] = merged['count'].fillna(0).astype(int)

            dashboard_data['datasets'].append({
                'label': f'Cirurgias - {unidade}',
                'data': merged['count'].tolist()
            })

    # 3. Verificar se existem dados de folículos
    has_follicle_data = 'total_foliculos' in df.columns

    # Se temos dados de folículos, processar
    if has_follicle_data:
        # Converter coluna para numérico, tratando erros
        df['total_foliculos'] = pd.to_numeric(df['total_foliculos'], errors='coerce').fillna(0)

        # Média geral de folículos
        dashboard_data['avg_follicles'] = int(df['total_foliculos'].mean())

        # Média de folículos por mês
        folliculo_medio = df.groupby('mes_ano')['total_foliculos'].mean().reset_index()

        # Preparar dados para gráficos
        dashboard_data['follicles_data']['labels'] = folliculo_medio['mes_ano'].tolist()
        dashboard_data['follicles_data']['averages'] = folliculo_medio['total_foliculos'].round(0).astype(int).tolist()

        # Se tiver dado de densidade, calcular média
        if 'densidade_scketh' in df.columns:
            # Converter coluna para numérico, tratando erros
            df['densidade_scketh'] = pd.to_numeric(df['densidade_scketh'], errors='coerce').fillna(0)

            # Média geral de densidade
            dashboard_data['avg_density'] = int(df['densidade_scketh'].mean())

            densidade_media = df.groupby('mes_ano')['densidade_scketh'].mean().reset_index()
            dashboard_data['follicles_data']['le_density'] = densidade_media['densidade_scketh'].round(0).astype(int).tolist()

        dashboard_data['has_follicle_data'] = True

    # Adicionar timestamp de atualização
    dashboard_data['update_time'] = datetime.now().strftime('%d/%m/%Y %H:%M')

    return dashboard_data

@app.route('/dashboard')
def dashboard():
    logger.info("Accessing dashboard route")
    try:
        # Se o arquivo Excel existir, carregar os dados para o dashboard
        filename = "cirurgias.xlsx"
        if os.path.exists(filename):
            # Carregar o dataframe
            df = pd.read_excel(filename)
            dashboard_data = process_dashboard_data(df)
        else:
            dashboard_data = {
                'labels': [],
                'datasets': [{'label': 'Cirurgias', 'data': []}],
                'has_follicle_data': False,
                'follicles_data': {'labels': [], 'averages': [], 'le_density': []},
                'total_surgeries': 0,
                'avg_follicles': 0,
                'avg_density': 0
            }

        return render_template('dashboard.html', data=dashboard_data)

    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}\n{traceback.format_exc()}")
        return render_template('dashboard.html', data={
            'labels': [],
            'datasets': [{'label': 'Cirurgias', 'data': []}],
            'has_follicle_data': False,
            'follicles_data': {'labels': [], 'averages': [], 'le_density': []},
            'total_surgeries': 0,
            'avg_follicles': 0,
            'avg_density': 0
        }, error=f"Erro ao carregar dashboard: {str(e)}")

@app.route('/get_available_units')
def get_available_units():
    """Endpoint para obter todas as unidades disponíveis no banco de dados"""
    logger.info("Obtendo unidades disponíveis")
    try:
        filename = "cirurgias.xlsx"
        if not os.path.exists(filename):
            return jsonify({'units': ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro']})
        
        df = pd.read_excel(filename)
        if 'unidade' not in df.columns:
            return jsonify({'units': ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro']})
        
        units = df['unidade'].unique().tolist()
        # Garantir que todas as unidades padrão estejam sempre disponíveis
        default_units = ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro']
        for unit in default_units:
            if unit not in units:
                units.append(unit)
        
        return jsonify({'units': units})
    except Exception as e:
        logger.error(f"Erro ao obter unidades: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'units': ['Ribeirão Preto', 'Campinas', 'Rio de Janeiro']})

@app.route('/get_unit_progress')
def get_unit_progress():
    """Endpoint para obter o progresso atual em relação à meta de unidade"""
    logger.info("Obtendo progresso da unidade")
    try:
        unit = request.args.get('unit', 'Ribeirão Preto')
        
        # Metas definidas por unidade
        metas = {
            'Ribeirão Preto': 35,
            'Campinas': 25,
            'Rio de Janeiro': 20
        }
        
        # Meta para a unidade selecionada
        meta = metas.get(unit, 30)
        
        filename = "cirurgias.xlsx"
        if not os.path.exists(filename):
            logger.info(f"Arquivo {filename} não encontrado. Retornando atual=0.")
            return jsonify({'unit': unit, 'meta': meta, 'atual': 0})
        
        # Carregar o dataframe com tratamento explícito de erros
        try:
            df = pd.read_excel(filename, engine='openpyxl')
            logger.info(f"DataFrame carregado com sucesso: {len(df)} registros no total")
        except Exception as e:
            logger.error(f"Erro ao ler o arquivo Excel: {str(e)}")
            return jsonify({'unit': unit, 'meta': meta, 'atual': 0, 'error': f'Erro ao ler arquivo: {str(e)}'})
        
        # Verificar se a coluna unidade existe
        if 'unidade' not in df.columns:
            logger.warning("Coluna 'unidade' não encontrada no DataFrame")
            return jsonify({'unit': unit, 'meta': meta, 'atual': 0, 'error': 'Coluna unidade não encontrada'})
        
        # Garantir que valores nulos na coluna 'unidade' não causem problemas
        df['unidade'] = df['unidade'].fillna('').astype(str)
        
        # Contar todos os registros da unidade
        # Garantir que valores nulos na coluna 'unidade' não causem problemas
        df['unidade'] = df['unidade'].fillna('').astype(str)
        
        # Usar método exato de comparação de strings
        filtered_df = df[df['unidade'].str.strip() == unit.strip()]
        atual = len(filtered_df)  # Conta as linhas filtradas
        
        # Mostrar mais informações para debug
        logger.info(f"Unidade: {unit}, Total de registros para esta unidade: {atual}")
        logger.info(f"Valores únicos na coluna 'unidade': {df['unidade'].unique().tolist()}")
        logger.info(f"Dados da unidade selecionada: {filtered_df.to_dict(orient='records')}")
        
        # Garantir que o valor atual seja um inteiro válido
        if pd.isna(atual) or not isinstance(atual, (int, float)):
            atual = 0
        else:
            atual = int(atual)
        
        # Verificar se o número real de registros foi capturado
        registro_real = len(filtered_df) if 'filtered_df' in locals() else 0
        if registro_real != atual:
            logger.warning(f"Discrepância na contagem: atual={atual}, registros reais={registro_real}")
            atual = registro_real
        
        logger.info(f"Progresso final: Unidade={unit}, Meta={meta}, Atual={atual}")
        return jsonify({
            'unit': unit, 
            'meta': meta, 
            'atual': atual
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter progresso: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'unit': unit, 'meta': meta if 'meta' in locals() else 30, 'atual': 0, 'error': str(e)})

@app.route('/get_tecnicas_data')
def get_tecnicas_data():
    """Endpoint para obter dados sobre técnicas utilizadas"""
    logger.info("Obtendo dados de técnicas")
    try:
        filename = "cirurgias.xlsx"
        if not os.path.exists(filename):
            # Dados de exemplo
            return jsonify({
                'tecnicas': [
                    {'tecnica': 'FUE', 'quantidade': 45},
                    {'tecnica': 'FUT', 'quantidade': 23},
                    {'tecnica': 'Body Hair', 'quantidade': 12},
                    {'tecnica': 'Refinamento', 'quantidade': 8}
                ]
            })
        
        df = pd.read_excel(filename)
        
        # Exemplo: contagem por técnica (adaptar conforme os dados reais da planilha)
        tecnicas_count = []
        
        # Se houver coluna de técnica, contar por valores únicos
        if 'safira' in df.columns:
            safira_counts = df['safira'].value_counts().reset_index()
            safira_counts.columns = ['safira', 'quantidade']
            for _, row in safira_counts.iterrows():
                tecnicas_count.append({
                    'tecnica': f"Safira: {row['safira']}", 
                    'quantidade': int(row['quantidade'])
                })
        
        # Verificar se há dados de body hair
        body_hair_count = 0
        if 'body_hair' in df.columns:
            body_hair_count = df[df['body_hair'] == 'Sim'].shape[0]
            tecnicas_count.append({
                'tecnica': 'Body Hair', 
                'quantidade': body_hair_count
            })
        
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
        filename = "cirurgias.xlsx"
        if not os.path.exists(filename):
            # Dados de exemplo
            return jsonify({
                'equipe': [
                    {'nome': 'Aline', 'quantidade': 15, 'unidade': 'Ribeirão Preto'},
                    {'nome': 'Natália', 'quantidade': 12, 'unidade': 'Ribeirão Preto'},
                    {'nome': 'Ana', 'quantidade': 18, 'unidade': 'Ribeirão Preto'},
                    {'nome': 'Juliana', 'quantidade': 10, 'unidade': 'Campinas'},
                    {'nome': 'Gabriela', 'quantidade': 9, 'unidade': 'Campinas'},
                    {'nome': 'Mariana Moro', 'quantidade': 14, 'unidade': 'Rio de Janeiro'},
                    {'nome': 'Mariana Silva', 'quantidade': 11, 'unidade': 'Rio de Janeiro'},
                    {'nome': 'Dayane', 'quantidade': 7, 'unidade': 'Rio de Janeiro'}
                ]
            })
        
        df = pd.read_excel(filename)
        
        # Inicializar lista para armazenar os dados da equipe
        equipe_data = []
        
        # Verificar se existem as colunas necessárias
        if 'equipe' in df.columns and 'unidade' in df.columns:
            # Processar membros da equipe regular
            equipe_counts = {}
            
            # Iterar sobre cada linha para contar participações
            for _, row in df.iterrows():
                unidade = row['unidade']
                
                # Processar equipe regular (pode ser uma string ou lista)
                equipe_str = str(row['equipe'])
                
                # Dividir a string em nomes individuais (assumindo que estão separados por vírgula ou outros caracteres)
                equipe_members = [name.strip() for name in equipe_str.replace(',', ';').replace('|', ';').split(';')]
                
                for member in equipe_members:
                    if member and len(member) > 1:  # Ignorar entradas vazias ou muito curtas
                        key = f"{member}|{unidade}"
                        if key in equipe_counts:
                            equipe_counts[key] += 1
                        else:
                            equipe_counts[key] = 1
                
                # Processar técnica extra 1 se existir e tiver valor
                if 'tecnica_extra1' in df.columns and pd.notna(row['tecnica_extra1']) and str(row['tecnica_extra1']).strip():
                    tecnica_extra = str(row['tecnica_extra1']).strip()
                    key = f"{tecnica_extra}|{unidade}"
                    if key in equipe_counts:
                        equipe_counts[key] += 1
                    else:
                        equipe_counts[key] = 1
                
                # Processar técnica extra 2 se existir e tiver valor
                if 'tecnica_extra2' in df.columns and pd.notna(row['tecnica_extra2']) and str(row['tecnica_extra2']).strip():
                    tecnica_extra = str(row['tecnica_extra2']).strip()
                    key = f"{tecnica_extra}|{unidade}"
                    if key in equipe_counts:
                        equipe_counts[key] += 1
                    else:
                        equipe_counts[key] = 1
            
            # Converter o dicionário para o formato esperado
            for key, count in equipe_counts.items():
                member, unidade = key.split('|')
                equipe_data.append({
                    'nome': member,
                    'quantidade': count,
                    'unidade': unidade
                })
            
            # Ordenar por quantidade (decrescente) e depois por nome
            equipe_data.sort(key=lambda x: (-x['quantidade'], x['nome']))
            
        # Se não houver dados suficientes, usar dados de exemplo
        if len(equipe_data) < 2:
            equipe_data = [
                {'nome': 'Aline', 'quantidade': 15, 'unidade': 'Ribeirão Preto'},
                {'nome': 'Natália', 'quantidade': 12, 'unidade': 'Ribeirão Preto'},
                {'nome': 'Ana', 'quantidade': 18, 'unidade': 'Ribeirão Preto'},
                {'nome': 'Juliana', 'quantidade': 10, 'unidade': 'Campinas'},
                {'nome': 'Gabriela', 'quantidade': 9, 'unidade': 'Campinas'},
                {'nome': 'Mariana Moro', 'quantidade': 14, 'unidade': 'Rio de Janeiro'},
                {'nome': 'Mariana Silva', 'quantidade': 11, 'unidade': 'Rio de Janeiro'},
                {'nome': 'Dayane', 'quantidade': 7, 'unidade': 'Rio de Janeiro'}
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
        filename = "cirurgias.xlsx"
        if not os.path.exists(filename):
            return jsonify({
                'labels': [],
                'datasets': [{'label': 'Cirurgias', 'data': []}],
                'has_follicle_data': False,
                'follicles_data': {'labels': [], 'averages': [], 'le_density': []},
                'total_surgeries': 0,
                'avg_follicles': 0,
                'avg_density': 0
            })

        df = pd.read_excel(filename)

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
        df = pd.read_excel("cirurgias.xlsx")

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
        # Carregar dados de cirurgias
        cirurgias_file = "cirurgias.xlsx"
        total_surgeries = 0
        if os.path.exists(cirurgias_file):
            df_cirurgias = pd.read_excel(cirurgias_file)
            total_surgeries = len(df_cirurgias)

        # Carregar dados de necroses
        necroses_file = "necroses.xlsx"
        total_necroses = 0
        if os.path.exists(necroses_file):
            df_necroses = pd.read_excel(necroses_file)
            total_necroses = len(df_necroses)

        # Calcular taxa de necrose
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
        filename = "necroses.xlsx"
        if os.path.exists(filename):
            df = pd.read_excel(filename)
        else:
            df = pd.DataFrame(columns=[
                'patient_id', 'patient_unit', 'data_registro', 'lesion_count', 
                'largest_lesion', 'affected_band', 'photo_paths'
            ])

        # Adicionar novo registro
        new_data = {
            'patient_id': patient_id,
            'patient_unit': patient_unit,
            'data_registro': datetime.now().strftime('%d/%m/%Y'),
            'lesion_count': lesion_count,
            'largest_lesion': largest_lesion,
            'affected_band': affected_band,
            'photo_paths': ','.join(photo_paths) if photo_paths else ''
        }

        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df.to_excel(filename, index=False)

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error saving necrose data: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)})



if __name__ == '__main__':
    try:
        # ALWAYS serve the app on port 5000
        port = 5000
        logger.info(f"Starting Flask server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {str(e)}\n{traceback.format_exc()}")
        raise