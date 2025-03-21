#!/usr/bin/env python
"""
Script para aplicar migrações sem depender do comando flask db upgrade,
evitando o problema de importação circular com o Flask-MonitoringDashboard.
"""

import os
import sys
import logging
import importlib
import subprocess
from datetime import datetime
from sqlalchemy import create_engine, text
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_url():
    """
    Obtém a URL de conexão com o banco de dados
    """
    # Prioridade 1: Variável de ambiente
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return db_url
    
    # Prioridade 2: Arquivo de configuração
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read('config.cfg')
        return config.get('database', 'url')
    except Exception as e:
        logger.error(f"Erro ao ler arquivo de configuração: {str(e)}")
        return None

def create_isolated_app():
    """
    Cria uma aplicação Flask isolada apenas para migrações
    """
    app = Flask(__name__)
    db_url = get_db_url()
    
    if not db_url:
        logger.error("URL do banco de dados não encontrada")
        return None, None
        
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db = SQLAlchemy(app)
    
    # Definir os mesmos modelos que existem no app principal
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
    
    class UnitProgress(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        unidade = db.Column(db.String(100), unique=True)
        meta = db.Column(db.Integer)
        
    class TestModel(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100))
        description = db.Column(db.Text)
        created_at = db.Column(db.DateTime)
    
    return app, db

def apply_migrations():
    """
    Aplica migrações pendentes sem usar o comando 'flask db upgrade'
    """
    app, db = create_isolated_app()
    if not app:
        return False, "Falha ao criar aplicação isolada"
    
    migrate_obj = Migrate(app, db)
    
    with app.app_context():
        try:
            logger.info("Aplicando migrações pendentes...")
            
            # Aplicar as migrações
            upgrade()
            
            # Verificar tabelas atuais
            engine = db.engine
            inspector = db.inspect(engine)
            tables = inspector.get_table_names()
            logger.info(f"Tabelas após migração: {tables}")
            
            # Verificar versão atual
            with engine.connect() as connection:
                try:
                    result = connection.execute(text("SELECT version_num FROM alembic_version")).fetchone()
                    if result:
                        logger.info(f"Versão atual da migração: {result[0]}")
                    else:
                        logger.warning("Tabela alembic_version existe, mas não contém dados")
                except Exception as e:
                    logger.error(f"Erro ao consultar tabela alembic_version: {str(e)}")
                    
            return True, "Migrações aplicadas com sucesso"
        except Exception as e:
            logger.error(f"Erro ao aplicar migrações: {str(e)}")
            return False, f"Erro ao aplicar migrações: {str(e)}"

if __name__ == "__main__":
    success, message = apply_migrations()
    print(message)
    sys.exit(0 if success else 1)