import os
from app import app #Import flask app

# Configuração das opções por unidade
UNIDADES_MEDICOS = {
    "Ribeirão Preto": ["Dr. Arthur", "Dr. Daniel"],
    "Campinas": ["Dra. Isadora", "Dra. Adriana"],
    "Rio de Janeiro": ["Dra. Paula", "Dra. Ana Clara"]
}

UNIDADES_EQUIPES = {
    "Ribeirão Preto": ["Aline", "Natália", "Ana"],
    "Campinas": ["Juliana", "Gabriela"],
    "Rio de Janeiro": ["Mariana Moro", "Mariana Silva", "Dayane", "Assistente Extra"]
}

#The rest of the code (classes and functions) related to Tkinter is removed here.


if __name__ == "__main__":
    # Check if we're running in Replit environment
    if not os.environ.get('REPL_ID'):
        print("Running in Replit environment - Tkinter interface disabled") #message indicating Tkinter is disabled
    else:
        app.run(host='0.0.0.0', port=5000) #Run flask app