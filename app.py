
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import pandas as pd
import os
import json
from datetime import datetime
import numpy as np

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Ensure xlsx file exists
def ensure_excel_file():
    if not os.path.exists('cirurgias.xlsx'):
        # Create empty DataFrame with columns
        columns = [
            'data', 'hora', 'unidade', 'medico', 'equipe', 'paciente', 'idade', 
            'genero', 'tecnica', 'area_total', 'area_recep', 'incisao',
            'infiltracao', 'anestesia', 'folioulos', 'fios', 'densidade', 
            'tempo_cirurgico', 'observacoes'
        ]
        pd.DataFrame(columns=columns).to_excel('cirurgias.xlsx', index=False)

@app.route('/')
def index():
    return redirect(url_for('form'))

@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        try:
            # Get form data
            data = {
                'data': request.form.get('data'),
                'hora': request.form.get('hora') or '08:00',
                'unidade': request.form.get('unidade'),
                'medico': request.form.get('medico'),
                'equipe': request.form.get('equipe'),
                'paciente': request.form.get('paciente'),
                'idade': request.form.get('idade'),
                'genero': request.form.get('genero'),
                'tecnica': request.form.get('tecnica'),
                'area_total': request.form.get('area_total'),
                'area_recep': request.form.get('area_recep'),
                'incisao': request.form.get('incisao'),
                'infiltracao': request.form.get('infiltracao'),
                'anestesia': request.form.get('anestesia'),
                'folioulos': request.form.get('folioulos'),
                'fios': request.form.get('fios'),
                'densidade': request.form.get('densidade'),
                'tempo_cirurgico': request.form.get('tempo_cirurgico'),
                'observacoes': request.form.get('observacoes')
            }
            
            # Ensure numeric fields have values
            numeric_fields = ['area_total', 'area_recep', 'folioulos', 'fios', 'densidade', 'tempo_cirurgico', 'idade']
            for field in numeric_fields:
                if not data[field] or (isinstance(data[field], str) and data[field].strip() == ''):
                    data[field] = '0'
            
            # Save to Excel
            ensure_excel_file()
            df = pd.read_excel('cirurgias.xlsx')
            df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
            df.to_excel('cirurgias.xlsx', index=False)
            
            flash('Cirurgia registrada com sucesso!', 'success')
            return redirect(url_for('form'))
        except Exception as e:
            flash(f'Erro ao salvar dados: {str(e)}', 'error')
            return redirect(url_for('form'))
    
    form_data = {
        'title': 'Cadastro de Cirurgia Capilar',
        'fields': [
            {'name': 'data', 'label': 'Data da Cirurgia', 'type': 'date', 'required': True},
            {'name': 'hora', 'label': 'Hora da Cirurgia (HH:MM)', 'type': 'time', 'required': True, 'value': '08:00'},
            {'name': 'unidade', 'label': 'Unidade', 'type': 'select', 'options': ['Ribeirão Preto', 'Campinas'], 'required': True},
            {'name': 'medico', 'label': 'Médico Responsável', 'type': 'select_dynamic', 'options': [], 'required': True},
            {'name': 'equipe', 'label': 'Equipe', 'type': 'select_dynamic', 'options': [], 'required': True},
            {'name': 'paciente', 'label': 'Nome do Paciente', 'type': 'text', 'required': True},
            {'name': 'idade', 'label': 'Idade', 'type': 'number', 'required': True},
            {'name': 'genero', 'label': 'Gênero', 'type': 'select', 'options': ['Masculino', 'Feminino', 'Outro'], 'required': True},
            {'name': 'tecnica', 'label': 'Técnica', 'type': 'select', 'options': ['FUE', 'FUT', 'Híbrida'], 'required': True},
            {'name': 'area_total', 'label': 'Área Total (cm²)', 'type': 'number', 'required': True},
            {'name': 'area_recep', 'label': 'Área Receptora (cm²)', 'type': 'number', 'required': True},
            {'name': 'incisao', 'label': 'Tipo de Incisão', 'type': 'select', 'options': ['Safira', 'Aço', 'Implanter'], 'required': True},
            {'name': 'infiltracao', 'label': 'Infiltração', 'type': 'select', 'options': ['Tumescente', 'Klein'], 'required': True},
            {'name': 'anestesia', 'label': 'Tipo de Anestesia', 'type': 'select', 'options': ['Local', 'Sedação'], 'required': True},
            {'name': 'q1_area', 'label': 'Quadrante 1 - Área (cm²)', 'type': 'number', 'required': False},
            {'name': 'q1_furos', 'label': 'Quadrante 1 - Furos', 'type': 'number', 'required': False},
            {'name': 'q1_fios', 'label': 'Quadrante 1 - Fios', 'type': 'number', 'required': False},
            {'name': 'q2_area', 'label': 'Quadrante 2 - Área (cm²)', 'type': 'number', 'required': False},
            {'name': 'q2_furos', 'label': 'Quadrante 2 - Furos', 'type': 'number', 'required': False},
            {'name': 'q2_fios', 'label': 'Quadrante 2 - Fios', 'type': 'number', 'required': False},
            {'name': 'q3_area', 'label': 'Quadrante 3 - Área (cm²)', 'type': 'number', 'required': False},
            {'name': 'q3_furos', 'label': 'Quadrante 3 - Furos', 'type': 'number', 'required': False},
            {'name': 'q3_fios', 'label': 'Quadrante 3 - Fios', 'type': 'number', 'required': False},
            {'name': 'q4_area', 'label': 'Quadrante 4 - Área (cm²)', 'type': 'number', 'required': False},
            {'name': 'q4_furos', 'label': 'Quadrante 4 - Furos', 'type': 'number', 'required': False},
            {'name': 'q4_fios', 'label': 'Quadrante 4 - Fios', 'type': 'number', 'required': False},
            {'name': 'area_marcada', 'label': 'Área Total Marcada', 'type': 'select', 'options': ['Sim', 'Não'], 'required': False},
            {'name': 'tensao_sutura', 'label': 'Tensão da Sutura', 'type': 'select', 'options': ['Baixa', 'Média', 'Alta'], 'required': False},
            {'name': 'tipo_fechamento', 'label': 'Tipo de Fechamento', 'type': 'select', 'options': ['Triplo', 'Simples'], 'required': False},
            {'name': 'microcoagulacao', 'label': 'Micro-coagulação', 'type': 'select', 'options': ['Sim', 'Não'], 'required': False},
            {'name': 'solucao_frente', 'label': 'Solução Frente (seringas)', 'type': 'number', 'required': False},
            {'name': 'solucao_coroa', 'label': 'Solução Coroa (seringas)', 'type': 'number', 'required': False},
            {'name': 'solucao_xilo_frente', 'label': 'Solução Xilo Frente (seringas)', 'type': 'number', 'required': False},
            {'name': 'calvicie_familiar', 'label': 'Calvície Familiar', 'type': 'select', 'options': ['Sim', 'Não'], 'required': False},
            {'name': 'uso_finasterida', 'label': 'Uso de Finasterida', 'type': 'select', 'options': ['Sim', 'Não'], 'required': False},
            {'name': 'uso_minoxidil', 'label': 'Uso de Minoxidil', 'type': 'select', 'options': ['Sim', 'Não'], 'required': False},
            {'name': 'frequencia_lavagem', 'label': 'Frequência de Lavagem', 'type': 'select', 'options': ['Diária', '2-3 vezes/semana', 'Semanal'], 'required': False},
            {'name': 'uso_capacete', 'label': 'Uso de Capacete', 'type': 'select', 'options': ['Sim', 'Não'], 'required': False},
            {'name': 'exposicao_sol', 'label': 'Exposição ao Sol', 'type': 'select', 'options': ['Alta', 'Média', 'Baixa', 'Nenhuma'], 'required': False},
            {'name': 'folioulos', 'label': 'Número Total de Folículos', 'type': 'number', 'required': True},
            {'name': 'fios', 'label': 'Número Total de Fios', 'type': 'number', 'required': True},
            {'name': 'densidade', 'label': 'Densidade (Fios/cm²)', 'type': 'number', 'required': False},
            {'name': 'tempo_cirurgico', 'label': 'Tempo Cirúrgico (min)', 'type': 'number', 'required': True},
            {'name': 'observacoes', 'label': 'Observações', 'type': 'textarea', 'required': False}
        ]
    }
    
    return render_template('form.html', form=form_data, data={})

@app.route('/get_options', methods=['GET'])
def get_options():
    option_type = request.args.get('type')
    unidade = request.args.get('unidade')
    
    if option_type == 'medicos':
        if unidade == 'Ribeirão Preto':
            return jsonify(['Dr. Silva', 'Dr. Costa', 'Dra. Oliveira'])
        elif unidade == 'Campinas':
            return jsonify(['Dr. Santos', 'Dra. Lima', 'Dr. Pereira'])
    elif option_type == 'equipe':
        if unidade == 'Ribeirão Preto':
            return jsonify(['Equipe A', 'Equipe B', 'Equipe C'])
        elif unidade == 'Campinas':
            return jsonify(['Equipe X', 'Equipe Y', 'Equipe Z'])
    
    return jsonify([])

@app.route('/get_medicos/<unidade>', methods=['GET'])
def get_medicos(unidade):
    medicos = []
    if unidade == 'Ribeirão Preto':
        medicos = ['Dr. Silva', 'Dr. Costa', 'Dra. Oliveira']
    elif unidade == 'Campinas':
        medicos = ['Dr. Santos', 'Dra. Lima', 'Dr. Pereira']
    return jsonify({'medicos': medicos})

@app.route('/get_equipe/<unidade>', methods=['GET'])
def get_equipe(unidade):
    equipe = []
    if unidade == 'Ribeirão Preto':
        equipe = ['Ana', 'Carlos', 'Mariana', 'Pedro']
    elif unidade == 'Campinas':
        equipe = ['Juliana', 'Roberto', 'Teresa', 'Vitor']
    return jsonify({'equipe': equipe})

@app.route('/dashboard')
def dashboard():
    try:
        ensure_excel_file()
        df = pd.read_excel('cirurgias.xlsx')
        
        if df.empty:
            return render_template('dashboard.html', has_data=False)
        
        # Verificar quais colunas realmente existem no DataFrame
        available_numeric_columns = [col for col in ['folioulos', 'fios', 'densidade', 'area_total', 'area_recep', 'tempo_cirurgico'] 
                                   if col in df.columns]
        
        # Para campos numéricos vazios, substituir por 0
        for col in available_numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Converter data para datetime
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True)
        
        # Dados para gráficos
        data = {
            'cirurgias_por_mes': {},
            'cirurgias_por_unidade': {},
            'media_foliculos': {},
            'densidade_extracao': {},
            'tempo_medio': {}
        }
        
        # Cirurgias por mês
        if 'data' in df.columns and not df['data'].isna().all():
            df['mes'] = df['data'].dt.strftime('%m/%Y')
            cirurgias_mes = df.groupby(['mes', 'unidade']).size().reset_index(name='count')
            
            for _, row in cirurgias_mes.iterrows():
                mes = row['mes']
                unidade = row['unidade']
                count = row['count']
                
                if mes not in data['cirurgias_por_mes']:
                    data['cirurgias_por_mes'][mes] = {}
                
                data['cirurgias_por_mes'][mes][unidade] = count
                
                if 'Total' not in data['cirurgias_por_mes'][mes]:
                    data['cirurgias_por_mes'][mes]['Total'] = 0
                data['cirurgias_por_mes'][mes]['Total'] += count
        
        # Cirurgias por unidade
        if 'unidade' in df.columns:
            unidades = df['unidade'].value_counts().to_dict()
            data['cirurgias_por_unidade'] = unidades
        
        # Média de folículos por unidade
        if 'folioulos' in df.columns and 'unidade' in df.columns:
            media_foliculos = df.groupby('unidade')['folioulos'].mean().to_dict()
            data['media_foliculos'] = {k: round(v, 2) for k, v in media_foliculos.items()}
        else:
            data['media_foliculos'] = {'Sem dados': 0}
        
        # Densidade média de extração (Fios/cm²)
        if 'densidade' in df.columns and 'unidade' in df.columns:
            densidade_media = df.groupby('unidade')['densidade'].mean().to_dict()
            data['densidade_extracao'] = {k: round(v, 2) for k, v in densidade_media.items()}
        else:
            data['densidade_extracao'] = {'Sem dados': 0}
        
        # Tempo médio cirúrgico por unidade
        if 'tempo_cirurgico' in df.columns and 'unidade' in df.columns:
            tempo_medio = df.groupby('unidade')['tempo_cirurgico'].mean().to_dict()
            data['tempo_medio'] = {k: round(v, 2) for k, v in tempo_medio.items()}
        else:
            data['tempo_medio'] = {'Sem dados': 0}
        
        return render_template('dashboard.html', has_data=True, data=data)
    except Exception as e:
        print(f"Erro no dashboard: {str(e)}")
        return render_template('dashboard.html', has_data=False, error=str(e))

@app.route('/necrose', methods=['GET', 'POST'])
def necrose():
    if request.method == 'POST':
        try:
            # Get form data
            data = {
                'paciente_id': request.form.get('paciente_id'),
                'num_necroses': request.form.get('num_necroses') or '0',
                'area_maior_necrose': request.form.get('area_maior_necrose') or '0',
                'faixa_acometida': request.form.get('faixa_acometida')
            }
            
            # Save to necrose.xlsx or append to existing file
            if os.path.exists('necroses.xlsx'):
                df = pd.read_excel('necroses.xlsx')
                df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
            else:
                df = pd.DataFrame([data])
            
            df.to_excel('necroses.xlsx', index=False)
            
            flash('Dados de necrose registrados com sucesso!', 'success')
            return redirect(url_for('necrose'))
        except Exception as e:
            flash(f'Erro ao salvar dados: {str(e)}', 'error')
            return redirect(url_for('necrose'))
    
    # Get patient list
    patients = []
    if os.path.exists('cirurgias.xlsx'):
        df = pd.read_excel('cirurgias.xlsx')
        if not df.empty and 'paciente' in df.columns:
            # Get only columns that exist in the DataFrame
            available_columns = ['paciente', 'unidade']
            
            for col in ['data', 'tempo_cirurgico', 'densidade', 'infiltracao', 'medico', 'equipe']:
                if col in df.columns:
                    available_columns.append(col)
            
            patients = df[available_columns].to_dict('records')
    
    return render_template('necrose.html', patients=patients)

@app.route('/search_patients', methods=['GET'])
def search_patients():
    query = request.args.get('query', '').lower()
    
    if not os.path.exists('cirurgias.xlsx'):
        return jsonify([])
    
    df = pd.read_excel('cirurgias.xlsx')
    if df.empty or 'paciente' not in df.columns:
        return jsonify([])
    
    filtered = df[df['paciente'].str.lower().str.contains(query, na=False)]
    results = filtered[['paciente', 'unidade']].drop_duplicates().to_dict('records')
    return jsonify(results)

@app.route('/get_patient_details', methods=['GET'])
def get_patient_details():
    patient = request.args.get('patient')
    
    if not os.path.exists('cirurgias.xlsx') or not patient:
        return jsonify({})
    
    df = pd.read_excel('cirurgias.xlsx')
    if df.empty or 'paciente' not in df.columns:
        return jsonify({})
    
    patient_data = df[df['paciente'] == patient].iloc[-1].to_dict()
    
    # Convert NaN to None
    for k, v in patient_data.items():
        if pd.isna(v):
            patient_data[k] = None
    
    return jsonify(patient_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
