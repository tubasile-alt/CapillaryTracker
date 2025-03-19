
import os
from app import app, db, Surgery
import pandas as pd
from sqlalchemy import inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

with app.app_context():
    # 1. Check record count
    count = Surgery.query.count()
    logger.info(f"Total records in database: {count}")

    # 2. Test manual query
    results = db.session.execute(db.text("SELECT * FROM surgery")).fetchall()
    logger.info(f"First few records from manual query:")
    for row in results[:3]:
        logger.info(row)

    # 3. Check database structure
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    logger.info(f"Tables in database: {tables}")
    
    for table in tables:
        columns = inspector.get_columns(table)
        logger.info(f"\nColumns in {table}:")
        for col in columns:
            logger.info(f"- {col['name']}: {col['type']}")

    # 4. Load and display data
    df = pd.read_sql(Surgery.query.statement, db.session.get_bind())
    logger.info("\nFirst 10 rows of data:")
    logger.info(df.head(10))

    # 5. Add test record if empty
    if count == 0:
        from datetime import datetime
        test_surgery = Surgery(
            data=datetime.now().date(),
            nome="Test Patient",
            unidade="Ribeirão Preto",
            medico="Dr. Arthur",
            equipe="Test Team",
            hora_cirurgia="09:00",
            tempo_cirurgia=2.5,
            total_foliculos=3000,
            frente=1000,
            densidade_scketh=80.0,
            coroa=800,
            scalpe=400,
            peninsula_direita=400,
            peninsula_esquerda=400
        )
        db.session.add(test_surgery)
        db.session.commit()
        logger.info("Added test record")
