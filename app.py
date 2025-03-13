import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_cors import CORS
from models import db, Cirurgia

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Initialize SQLAlchemy with the app
db.init_app(app)

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
    return render_template('form.html', form=form_data)

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


# Placeholder for dashboard route and other endpoints that need database interaction
@app.route('/dashboard')
def dashboard():
    return jsonify({"message": "Dashboard endpoint not yet implemented"})

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


@app.route('/get_unit_progress')
def get_unit_progress():
    return jsonify({"message": "Get unit progress endpoint not yet implemented"})


@app.route('/get_tecnicas_data')
def get_tecnicas_data():
    return jsonify({"message": "Get tecnicas data endpoint not yet implemented"})

@app.route('/get_equipe_data')
def get_equipe_data():
    return jsonify({"message": "Get equipe data endpoint not yet implemented"})



# Create database tables within app context
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    try:
        logger.info(f"Starting server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.exception("Failed to start server:")
        raise