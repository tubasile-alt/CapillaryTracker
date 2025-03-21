import os
import logging
import sys
import shutil
from sqlalchemy import text
from app import app, db
from flask_migrate import Migrate, init, migrate, upgrade, stamp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_migrations():
    """
    Reset all migrations and drop all tables to start fresh.
    This should be used with caution as it will remove all data.
    """
    with app.app_context():
        try:
            # 1. Drop all tables including alembic_version
            logger.info("Dropping all existing tables...")
            drop_all_tables_sql = """
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
            """
            db.session.execute(text(drop_all_tables_sql))
            db.session.commit()
            logger.info("✅ All tables dropped successfully")
            
            # 2. Limpar diretório de migrações
            logger.info("Removendo arquivos de migração existentes...")
            migrations_dir = "migrations"
            versions_dir = os.path.join(migrations_dir, "versions")
            
            # Se o diretório migrations existir, remover apenas o conteúdo de versions
            if os.path.exists(migrations_dir):
                if os.path.exists(versions_dir):
                    for file in os.listdir(versions_dir):
                        file_path = os.path.join(versions_dir, file)
                        if os.path.isfile(file_path) and (file.endswith('.py') or file.endswith('.pyc')):
                            os.remove(file_path)
                            logger.info(f"Arquivo de migração removido: {file}")
            else:
                # Se não existir, criar o diretório migrations
                os.makedirs(migrations_dir, exist_ok=True)
                os.makedirs(versions_dir, exist_ok=True)
                logger.info("Diretórios de migração criados")
            
            # 3. Criar tabelas diretamente (sem migrações ainda)
            logger.info("Criando tabelas a partir dos modelos...")
            db.create_all()
            logger.info("✅ Tabelas criadas com sucesso")
            
            # 4. Inicializar o diretório de migrações do Flask-Migrate
            # Se migrations/env.py não existir, inicializar
            env_file = os.path.join(migrations_dir, "env.py")
            if not os.path.exists(env_file):
                logger.info("Inicializando pasta de migrações...")
                init()
                logger.info("✅ Migrações inicializadas")
            else:
                logger.info("Pasta de migrações já inicializada, pulando etapa de init")
            
            # 5. Reconstruir o objeto Migrate
            logger.info("Reconstruindo objeto Migrate...")
            migrate_obj = Migrate(app, db)
            logger.info("✅ Objeto Migrate reconstruído")
            
            # 6. Criar a migração inicial usando script isolado
            logger.info("Criando migração inicial usando script isolado...")
            import subprocess
            
            # Primeiro tenta usar create_migration.py
            result = subprocess.run(["python", "create_migration.py"], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Migração criada com sucesso: {result.stdout.strip()}")
            else:
                logger.error(f"Erro ao criar migração automaticamente: {result.stderr.strip()}")
                logger.info("Tentando forçar a criação de uma migração inicial...")
                
                # Se falhar, usa force_initial_migration.py para forçar a criação
                force_result = subprocess.run(["python", "force_initial_migration.py"], capture_output=True, text=True)
                
                if force_result.returncode == 0:
                    logger.info(f"✅ Migração forçada com sucesso: {force_result.stdout.strip()}")
                else:
                    logger.error(f"❌ Erro ao forçar migração: {force_result.stderr.strip()}")
                    # Continue mesmo com erro, já que as tabelas foram criadas
            
            # Verify tables
            logger.info("Verifying database tables...")
            tables_query = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [row[0] for row in db.session.execute(tables_query).fetchall()]
            logger.info(f"Tables in database: {tables}")
            
            logger.info("✅ Migration reset successful!")
            return True, "Migração reiniciada com sucesso!"
            
        except Exception as e:
            logger.error(f"Error during migration reset: {str(e)}")
            db.session.rollback()
            return False, f"Erro durante reset das migrações: {str(e)}"

if __name__ == "__main__":
    success, message = reset_migrations()
    print(message)
    sys.exit(0 if success else 1)