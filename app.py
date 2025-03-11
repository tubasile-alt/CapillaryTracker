
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

@app.route('/dashboard')
def dashboard():
    try:
        # Read data from Excel
        df = pd.read_excel("cirurgias.xlsx")
        
        # Format date for display
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
        df['data_formatada'] = df['data'].dt.strftime('%d/%m/%Y')
        
        # Count surgeries by month
        df['mes'] = df['data'].dt.strftime('%Y-%m')
        cirurgias_por_mes = df.groupby('mes').size().reset_index(name='count')
        cirurgias_por_mes['mes_formatado'] = pd.to_datetime(cirurgias_por_mes['mes']).dt.strftime('%b/%Y')
        
        # Surgeries by team
        df['equipe_lista'] = df['equipe'].apply(lambda x: [membro.strip() for membro in str(x).split(',')] if pd.notna(x) else [])
        
        # Get unique team members and count surgeries per member
        equipes = {}
        for idx, row in df.iterrows():
            for membro in row['equipe_lista']:
                if membro and isinstance(membro, str) and membro.strip():
                    equipes[membro.strip()] = equipes.get(membro.strip(), 0) + 1
        
        equipes_sorted = sorted(equipes.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate density
        df['densidade'] = df['total_foliculos'] / df['tempo_cirurgia']
        densidade_media = df['densidade'].mean()
        
        # Surgeries by unit
        cirurgias_por_unidade = df.groupby('unidade').size().reset_index(name='count')
        
        # Total follicles by month
        foliculos_por_mes = df.groupby('mes')['total_foliculos'].sum().reset_index()
        foliculos_por_mes['mes_formatado'] = pd.to_datetime(foliculos_por_mes['mes']).dt.strftime('%b/%Y')
        
        return render_template(
            'dashboard.html',
            cirurgias_por_mes=cirurgias_por_mes.to_dict('records'),
            equipes=equipes_sorted,
            densidade_media=densidade_media,
            cirurgias_por_unidade=cirurgias_por_unidade.to_dict('records'),
            foliculos_por_mes=foliculos_por_mes.to_dict('records')
        )
    except Exception as e:
        logger.error(f"Error in dashboard: {str(e)}\n{traceback.format_exc()}")
        return f"Erro ao carregar o dashboard: {str(e)}", 500

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/submit_form', methods=['POST'])
def submit_form():
    try:
        # Get form data
        data = request.form.to_dict()
        
        # Convert date string to datetime
        data['data'] = datetime.strptime(data['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
        
        # Create DataFrame
        df_new = pd.DataFrame([data])
        
        # Check if file exists and append or create new
        filename = "cirurgias.xlsx"
        if os.path.exists(filename):
            df_existing = pd.read_excel(filename)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_excel(filename, index=False)
        else:
            df_new.to_excel(filename, index=False)
        
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in form submission: {str(e)}\n{traceback.format_exc()}")
        return f"Erro ao enviar o formulário: {str(e)}", 500

@app.route('/clear_data', methods=['POST'])
def clear_data():
    try:
        # Create empty dataframes
        columns = [
            'data', 'nome', 'unidade', 'medico', 'equipe', 'hora_cirurgia', 
            'tempo_cirurgia', 'total_foliculos', 'frente', 'densidade_scketh',
            'coroa', 'scalpe', 'peninsula_direita', 'peninsula_esquerda'
        ]
        pd.DataFrame(columns=columns).to_excel("cirurgias.xlsx", index=False)
        
        columns = [
            'patient_id', 'patient_unit', 'data_registro', 'lesion_count', 
            'largest_lesion', 'affected_band', 'photo_paths'
        ]
        pd.DataFrame(columns=columns).to_excel("necroses.xlsx", index=False)
        
        flash("Dados limpos com sucesso!", "success")
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}\n{traceback.format_exc()}")
        flash(f"Erro ao limpar dados: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/importar_rapido', methods=['POST'])
def importar_rapido():
    try:
        # Importar usando o script de importação rápida
        from import_deployed_data import importar_dados_rapidos
        
        success = importar_dados_rapidos()
        
        if success:
            flash("Dados importados com sucesso!", "success")
        else:
            flash("Erro ao importar dados. Verifique os logs.", "error")
            
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error importing data: {str(e)}\n{traceback.format_exc()}")
        flash(f"Erro ao importar dados: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/search_patients', methods=['GET'])
def search_patients():
    try:
        search_term = request.args.get('term', '')
        if not search_term:
            return jsonify([])
            
        # Read data from Excel
        df = pd.read_excel("cirurgias.xlsx")
        
        # Filter patients by name using fuzzy matching
        results = []
        for idx, row in df.iterrows():
            name = str(row['nome'])
            score = fuzz.partial_ratio(search_term.lower(), name.lower())
            if score > 70:  # Threshold for matching
                results.append({
                    'id': idx,
                    'name': name,
                    'unit': row['unidade'],
                    'date': pd.to_datetime(row['data']).strftime('%d/%m/%Y') if pd.notna(row['data']) else '',
                    'score': score
                })
        
        # Sort by score descending
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        return jsonify(results[:10])  # Return top 10 results
    except Exception as e:
        logger.error(f"Error searching patients: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/necrose')
def necrose_form():
    return render_template('necrose.html')

@app.route('/save_necrose', methods=['POST'])
def save_necrose():
    try:
        # Get form data
        data = request.form.to_dict()
        patient_id = data.get('patient_id')
        patient_unit = data.get('patient_unit')
        
        # Process photo uploads
        uploaded_files = request.files.getlist('photos')
        photo_paths = []
        
        os.makedirs('static/uploads', exist_ok=True)
        
        for file in uploaded_files:
            if file and file.filename:
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"{timestamp}_{file.filename}"
                filepath = os.path.join('static/uploads', filename)
                file.save(filepath)
                photo_paths.append(filepath)
        
        # Create new data record
        new_data = {
            'patient_id': patient_id,
            'patient_unit': patient_unit,
            'data_registro': datetime.now().strftime('%d/%m/%Y'),
            'lesion_count': data.get('lesion_count'),
            'largest_lesion': data.get('largest_lesion'),
            'affected_band': data.get('affected_band'),
            'photo_paths': json.dumps(photo_paths)
        }
        
        # Save to Excel
        filename = "necroses.xlsx"
        if os.path.exists(filename):
            df = pd.read_excel(filename)
        else:
            df = pd.DataFrame(columns=[
                'patient_id', 'patient_unit', 'data_registro', 'lesion_count', 
                'largest_lesion', 'affected_band', 'photo_paths'
            ])

        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df.to_excel(filename, index=False)

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error saving necrose data: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/import_data')
def import_data_form():
    return render_template('import_data.html')

if __name__ == '__main__':
    try:
        # ALWAYS serve the app on port 5000
        port = 5000
        logger.info(f"Starting Flask server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {str(e)}\n{traceback.format_exc()}")
