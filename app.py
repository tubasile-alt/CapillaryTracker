
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
            {'name': 'medico', 'label': 'Médico Responsável', 'type': 'select', 'options': [], 'required': True},
            {'name': 'equipe', 'label': 'Equipe', 'type': 'select', 'options': [], 'required': True},
            {'name': 'paciente', 'label': 'Nome do Paciente', 'type': 'text', 'required': True},
            {'name': 'idade', 'label': 'Idade', 'type': 'number', 'required': True},
            {'name': 'genero', 'label': 'Gênero', 'type': 'select', 'options': ['Masculino', 'Feminino', 'Outro'], 'required': True},
            {'name': 'tecnica', 'label': 'Técnica', 'type': 'select', 'options': ['FUE', 'FUT', 'Híbrida'], 'required': True}
        ],
        'fields_page2': [
            {'name': 'area_total', 'label': 'Área Total (cm²)', 'type': 'number', 'required': True},
            {'name': 'area_recep', 'label': 'Área Receptora (cm²)', 'type': 'number', 'required': True},
            {'name': 'incisao', 'label': 'Tipo de Incisão', 'type': 'select', 'options': ['Safira', 'Aço', 'Implanter'], 'required': True},
            {'name': 'infiltracao', 'label': 'Infiltração', 'type': 'select', 'options': ['Tumescente', 'Klein'], 'required': True},
            {'name': 'anestesia', 'label': 'Tipo de Anestesia', 'type': 'select', 'options': ['Local', 'Sedação'], 'required': True},
            {'name': 'folioulos', 'label': 'Número de Folículos', 'type': 'number', 'required': True},
            {'name': 'fios', 'label': 'Número de Fios', 'type': 'number', 'required': True},
            {'name': 'densidade', 'label': 'Densidade (Fios/cm²)', 'type': 'number', 'required': False},
            {'name': 'tempo_cirurgico', 'label': 'Tempo Cirúrgico (min)', 'type': 'number', 'required': True},
            {'name': 'observacoes', 'label': 'Observações', 'type': 'textarea', 'required': False}
        ]
    }
    
    return render_template('form.html', form=form_data)

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

@app.route('/dashboard')
def dashboard():
    try:
        ensure_excel_file()
        df = pd.read_excel('cirurgias.xlsx')
        
        if df.empty:
            return render_template('dashboard.html', has_data=False)
        
        # Para campos numéricos vazios, substituir por 0
        numeric_columns = ['folioulos', 'fios', 'densidade', 'area_total', 'area_recep', 'tempo_cirurgico']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Converter data para datetime
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        
        # Dados para gráficos
        data = {
            'cirurgias_por_mes': {},
            'cirurgias_por_unidade': {},
            'media_foliculos': {},
            'densidade_extracao': {},
            'tempo_medio': {}
        }
        
        # Cirurgias por mês
        if not df['data'].isna().all():
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
        unidades = df['unidade'].value_counts().to_dict()
        data['cirurgias_por_unidade'] = unidades
        
        # Média de folículos por unidade
        media_foliculos = df.groupby('unidade')['folioulos'].mean().to_dict()
        data['media_foliculos'] = {k: round(v, 2) for k, v in media_foliculos.items()}
        
        # Densidade média de extração (Fios/cm²)
        densidade_media = df.groupby('unidade')['densidade'].mean().to_dict()
        data['densidade_extracao'] = {k: round(v, 2) for k, v in densidade_media.items()}
        
        # Tempo médio cirúrgico por unidade
        tempo_medio = df.groupby('unidade')['tempo_cirurgico'].mean().to_dict()
        data['tempo_medio'] = {k: round(v, 2) for k, v in tempo_medio.items()}
        
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
            patients = df[['paciente', 'unidade', 'data', 'tempo_cirurgico', 'densidade', 'infiltracao', 'medico', 'equipe']].to_dict('records')
    
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
