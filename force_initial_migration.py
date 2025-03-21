#!/usr/bin/env python
"""
Script para forçar a criação de uma migração inicial, mesmo sem alterações no esquema.
Isso é útil para inicializar o controle de versão do Alembic com o esquema atual.
"""

import os
import sys
import logging
import shutil
import subprocess
from sqlalchemy import create_engine, text
from datetime import datetime

# Configurando logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_url():
    """Obtém a URL do banco de dados"""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        import configparser
        config = configparser.ConfigParser()
        config.read('config.cfg')
        db_url = config.get('database', 'url', fallback=None)
    return db_url

def force_initial_migration():
    """Força a criação de uma migração inicial mesmo sem alterações no esquema"""
    try:
        # 1. Verificar se diretório migrations/versions existe
        versions_dir = "migrations/versions"
        if not os.path.exists(versions_dir):
            os.makedirs(versions_dir, exist_ok=True)
            logger.info(f"Criado diretório {versions_dir}")
        
        # 2. Criar um arquivo de migração manualmente
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        revision_id = timestamp + "_" + os.urandom(4).hex()
        migration_file = os.path.join(versions_dir, f"{revision_id}_initial_migration.py")
        
        with open(migration_file, "w") as f:
            f.write(f"""\"\"\"Initial migration

Revision ID: {revision_id}
Revises: 
Create Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}

\"\"\"
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '{revision_id}'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Este é um arquivo de migração inicial gerado manualmente.
    # As tabelas já foram criadas diretamente com db.create_all()
    pass


def downgrade():
    # Não implementado para migração inicial
    pass
""")
        logger.info(f"✅ Arquivo de migração criado: {migration_file}")
        
        # 3. Atualizar a tabela alembic_version com o ID da migração
        db_url = get_db_url()
        if not db_url:
            logger.error("URL do banco de dados não encontrada")
            return False, "URL do banco de dados não encontrada"
            
        engine = create_engine(db_url)
        with engine.connect() as connection:
            connection.execute(text(f"DELETE FROM alembic_version"))
            connection.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{revision_id}')"))
            connection.commit()
            logger.info(f"✅ Tabela alembic_version atualizada com revisão: {revision_id}")
        
        logger.info("✅ Migração inicial forçada com sucesso!")
        return True, "Migração inicial forçada com sucesso!"
    
    except Exception as e:
        logger.error(f"Erro ao forçar migração inicial: {str(e)}")
        return False, f"Erro ao forçar migração inicial: {str(e)}"

if __name__ == "__main__":
    success, message = force_initial_migration()
    print(message)
    sys.exit(0 if success else 1)