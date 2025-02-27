from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import os
from utils import validate_date, validate_time, validate_numeric, validate_range

app = Flask(__name__)
app.secret_key = os.urandom(24)

FORMS = {
    "dados_gerais": {
        "title": "Dados Gerais",
        "fields": [
            {"name": "data", "label": "Data (DD/MM/AAAA)", "type": "text", "required": True},
            {"name": "paciente", "label": "Paciente", "type": "text", "required": True},
            {"name": "medico", "label": "Médico", "type": "text", "required": True},
            {"name": "equipe", "label": "Equipe", "type": "text", "required": True},
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
            {"name": "punch", "label": "Punch", "type": "number", "required": True},
            {"name": "solucao_frente", "label": "Solução Frente (ml)", "type": "number", "required": False},
            {"name": "solucao_coroa", "label": "Solução Coroa (ml)", "type": "number", "required": False},
            {"name": "solucao_xilo_frente", "label": "Solução Xilo Frente (ml)", "type": "number", "required": False}
        ],
        "next": "distribuicao",
        "prev": "implante"
    },
    "distribuicao": {
        "title": "Distribuição dos Implantes",
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
    if form_id not in FORMS:
        return redirect(url_for('index'))

    if request.method == 'POST':
        form_data = request.form.to_dict()

        # Use formatted date if available
        if 'data_formatted' in form_data and form_data['data_formatted']:
            form_data['data'] = form_data['data_formatted']

        errors = validate_form_data(form_id, form_data)

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('form.html', form=FORMS[form_id], data=form_data)

        # Store form data in session
        if 'form_data' not in session:
            session['form_data'] = {}
        session['form_data'].update(form_data)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)