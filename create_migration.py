#!/usr/bin/env python
"""
Script para criar uma migração inicial sem conflitos com o Flask-MonitoringDashboard.
Este script contorna problemas de importação circular criando um ambiente isolado
para gerar migrações do Alembic.
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
from flask_migrate import Migrate, init, migrate, upgrade, stamp

# Configurando logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_url():
    """
    Obtém a URL de conexão com o banco de dados das variáveis de ambiente
    ou do arquivo config.cfg
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
    Cria uma aplicação Flask isolada apenas para gerenciar migrações,
    sem importar todas as dependências do app principal
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
    
    return app, db

def create_migration():
    """
    Cria uma migração inicial para o banco de dados
    """
    app, db = create_isolated_app()
    if not app:
        return False, "Falha ao criar aplicação isolada"
    
    migrate_obj = Migrate(app, db)
    
    with app.app_context():
        try:
            logger.info("Criando migração inicial...")
            
            # Verificar se o diretório versions existe
            versions_dir = "migrations/versions"
            if not os.path.exists(versions_dir):
                os.makedirs(versions_dir, exist_ok=True)
                logger.info(f"Criado diretório {versions_dir}")
            
            # Criar a migração
            migrate(message="Initial migration")
            logger.info("✅ Migração criada com sucesso!")
            
            # Aplicar a migração
            upgrade()
            logger.info("✅ Migração aplicada com sucesso!")
            
            # Executar o comando SQL para inserir a versão na tabela alembic_version
            try:
                from alembic.script import ScriptDirectory
                from alembic.config import Config
                
                # Obter a versão mais recente
                alembic_cfg = Config("migrations/alembic.ini")
                script = ScriptDirectory.from_config(alembic_cfg)
                head_revision = script.get_current_head()
                
                if head_revision:
                    # Inserir a versão diretamente na tabela alembic_version
                    db.session.execute(text(f"DELETE FROM alembic_version"))
                    db.session.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{head_revision}')"))
                    db.session.commit()
                    logger.info(f"✅ Versão atualizada para HEAD: {head_revision}")
                else:
                    logger.warning("⚠️ Não foi possível obter a versão atual. A tabela alembic_version não será atualizada.")
            except Exception as e:
                logger.error(f"Erro ao atualizar versão: {str(e)}")
                # Continuar mesmo com o erro
            
            # Verificar os arquivos de migração
            if os.path.exists(versions_dir):
                migrations = [f for f in os.listdir(versions_dir) if f.endswith('.py')]
                logger.info(f"Arquivos de migração ({len(migrations)}):")
                for migration in migrations:
                    logger.info(f"  - {migration}")
            
            return True, "Migração criada e aplicada com sucesso"
        except Exception as e:
            logger.error(f"Erro ao criar migração: {str(e)}")
            return False, f"Erro ao criar migração: {str(e)}"

if __name__ == "__main__":
    success, message = create_migration()
    print(message)
    sys.exit(0 if success else 1)