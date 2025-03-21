#!/usr/bin/env python
"""
Script para remover todas as tabelas do banco de dados.
ATENÇÃO: Este script irá remover TODOS os dados!
"""

import logging
from sqlalchemy import text
from app import app, db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def drop_all_tables():
    """Remover todas as tabelas do banco de dados"""
    with app.app_context():
        try:
            logger.info("Removendo todas as tabelas...")
            
            # SQL para listar todas as tabelas
            tables_query = text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            tables = [row[0] for row in db.session.execute(tables_query).fetchall()]
            
            logger.info(f"Tabelas encontradas: {tables}")
            
            # SQL para remover todas as tabelas em uma transação
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
            
            # Verificar se as tabelas foram removidas
            tables_after = [row[0] for row in db.session.execute(tables_query).fetchall()]
            
            if not tables_after:
                logger.info("✅ Todas as tabelas foram removidas com sucesso!")
                return True, "Tabelas removidas com sucesso"
            else:
                logger.warning(f"⚠️ Algumas tabelas permaneceram: {tables_after}")
                return False, f"Algumas tabelas não puderam ser removidas: {tables_after}"
                
        except Exception as e:
            logger.error(f"❌ Erro ao remover tabelas: {str(e)}")
            db.session.rollback()
            return False, f"Erro ao remover tabelas: {str(e)}"

if __name__ == "__main__":
    success, message = drop_all_tables()
    print(message)