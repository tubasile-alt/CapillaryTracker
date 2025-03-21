#!/usr/bin/env python
"""
Script para testar a criação de uma migração
"""

import os
import sys
import logging
import subprocess
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_migration():
    """Tenta criar uma migração de teste"""
    try:
        # 1. Criar um script temporário que define um novo modelo
        temp_script = "temp_model.py"
        
        with open(temp_script, "w") as f:
            f.write("""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

app = Flask(__name__)

# Configurar DB
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    import configparser
    config = configparser.ConfigParser()
    config.read('config.cfg')
    db_url = config.get('database', 'url', fallback=None)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Modelo original
class Surgery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date)
    nome = db.Column(db.String(255))
    unidade = db.Column(db.String(100))
    medico = db.Column(db.String(100))
    equipe = db.Column(db.String(255))
    hora_cirurgia = db.Column(db.String(5))
    tempo_cirurgia = db.Column(db.Float)
    total_foliculos = db.Column(db.Integer)
    frente = db.Column(db.Integer)
    densidade_scketh = db.Column(db.Float)
    coroa = db.Column(db.Integer)
    scalpe = db.Column(db.Integer)
    peninsula_direita = db.Column(db.Integer)
    peninsula_esquerda = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)

# Modelo original
class UnitProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unidade = db.Column(db.String(100), unique=True)
    meta = db.Column(db.Integer)

# Novo modelo para teste
class TestModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime)

if __name__ == '__main__':
    with app.app_context():
        from flask_migrate import init, migrate, upgrade, current
        
        try:
            # Tenta criar uma migração
            migrate(message="Add test model")
            print("✅ Migração criada com sucesso!")
            
            # Mostrar versão atual
            version = current()
            print(f"Versão atual: {version}")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            sys.exit(1)
""")
            
        logger.info(f"Arquivo temporário criado: {temp_script}")
        
        # 2. Executar o script temporário
        logger.info("Executando script temporário para testar migração...")
        result = subprocess.run(["python", temp_script], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ Teste executado com sucesso: {result.stdout.strip()}")
        else:
            logger.error(f"❌ Erro durante teste: {result.stderr.strip()}")
        
        # 3. Limpar (remover arquivo temporário)
        if os.path.exists(temp_script):
            os.remove(temp_script)
            logger.info(f"Arquivo temporário removido: {temp_script}")
            
        # 4. Retornar resultado do teste
        return result.returncode == 0, result.stdout if result.returncode == 0 else result.stderr
    
    except Exception as e:
        logger.error(f"Erro durante teste de migração: {str(e)}")
        return False, str(e)

if __name__ == "__main__":
    success, output = test_migration()
    print("\n" + "="*40)
    print(f"Resultado do teste: {'✅ SUCESSO' if success else '❌ FALHA'}")
    print("="*40)
    print(output)
    sys.exit(0 if success else 1)