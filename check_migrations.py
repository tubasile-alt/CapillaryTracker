#!/usr/bin/env python
"""
Script para verificar o estado das migrações e do banco de dados
"""

import os
import sys
import logging
from sqlalchemy import text
from app import app, db
from flask_migrate import current
from datetime import datetime

# Configure logging to file and console
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = f"{log_dir}/migration_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Set up file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)

# Set up console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(console_format)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def check_migrations():
    """Verifica o estado das migrações do banco de dados"""
    
    with app.app_context():
        try:
            # 1. Verificar tabelas existentes
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in db.session.execute(tables_query).fetchall()]
            logger.info("📋 Tabelas no banco de dados:")
            for table in tables:
                logger.info(f"  - {table}")
            
            # 2. Verificar se a tabela alembic_version existe
            has_alembic = 'alembic_version' in tables
            logger.info(f"✓ Tabela alembic_version: {'Existe' if has_alembic else 'NÃO existe'}")
            
            # 3. Verificar versão do Alembic
            if has_alembic:
                version_query = text("SELECT version_num FROM alembic_version")
                versions = [row[0] for row in db.session.execute(version_query).fetchall()]
                if versions:
                    logger.info(f"✓ Versão atual do Alembic: {versions[0]}")
                else:
                    logger.warning("⚠️ Tabela alembic_version existe mas não contém nenhuma versão")
            
            # 4. Verificar arquivos de migração
            versions_dir = "migrations/versions"
            if os.path.exists(versions_dir):
                migrations = [f for f in os.listdir(versions_dir) if f.endswith('.py')]
                logger.info(f"📋 Arquivos de migração ({len(migrations)}):")
                for migration in migrations:
                    logger.info(f"  - {migration}")
            else:
                logger.warning("⚠️ Diretório migrations/versions não existe")
            
            # 5. Verificar versão atual
            try:
                curr = current()
                logger.info(f"✓ Versão atual da migração: {curr}")
            except Exception as e:
                logger.error(f"❌ Erro ao obter versão atual: {str(e)}")
            
            # 6. Verificar contagem de registros
            for model_name in ['Surgery', 'UnitProgress']:
                try:
                    count_query = text(f"SELECT COUNT(*) FROM {model_name.lower()}")
                    count = db.session.execute(count_query).scalar()
                    logger.info(f"📊 Registros em {model_name}: {count}")
                except Exception as e:
                    logger.error(f"❌ Erro ao contar registros de {model_name}: {str(e)}")
            
            return True, "Verificação de migrações concluída"
            
        except Exception as e:
            logger.error(f"Erro durante verificação: {str(e)}")
            return False, f"Erro durante verificação: {str(e)}"

if __name__ == "__main__":
    success, message = check_migrations()
    print(message)
    sys.exit(0 if success else 1)