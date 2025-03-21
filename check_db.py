
import os
import logging
import pandas as pd
from sqlalchemy import inspect, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar a variável de ambiente DATABASE_URL antes de importar a aplicação
default_db_url = 'postgresql://neondb_owner:npg_BoiquUY6v8CN@ep-flat-salad-a4j7rvot.us-east-1.aws.neon.tech/neondb?sslmode=require'
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = default_db_url
    logger.info(f"⚠️ DATABASE_URL não encontrada. Usando configuração padrão para deploy: {default_db_url}")

# Importar app após configurar a variável de ambiente
from app import app, db, Surgery

def check_database():
    try:
        with app.app_context():
            # Test database connection
            result = db.session.execute(text('SELECT 1'))
            print("✅ Database connection successful")
            
            # Get surgery count
            result = db.session.execute(text('SELECT COUNT(*) FROM surgery'))
            count = result.scalar()
            print(f"Total records in database: {count}")
            
            return True
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False

if __name__ == "__main__":
    check_database()
