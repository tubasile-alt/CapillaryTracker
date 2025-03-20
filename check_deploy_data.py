import logging
from app import app, db, Surgery
import pandas as pd
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_data():
    try:
        with app.app_context():
            # Check database
            db_count = Surgery.query.count()
            logger.info(f"Database count: {db_count}")

            # Check Excel file
            if os.path.exists("cirurgias.xlsx"):
                df = pd.read_excel("cirurgias.xlsx")
                excel_count = len(df)
                logger.info(f"Excel count: {excel_count}")

                # Compare data
                if db_count != excel_count:
                    logger.warning(f"⚠️ Data mismatch: DB={db_count}, Excel={excel_count}")

                    # Clear database and restore from Excel
                    db.session.query(Surgery).delete()
                    db.session.commit()

                    # Restore data from Excel
                    for _, row in df.iterrows():
                        surgery = Surgery(
                            data=pd.to_datetime(row['data']).date(),
                            nome=str(row['nome']),
                            unidade=str(row['unidade']),
                            medico=str(row['medico']),
                            equipe=str(row['equipe']),
                            hora_cirurgia=str(row['hora_cirurgia']),
                            tempo_cirurgia=float(row.get('tempo_cirurgia', 0) or 0),
                            total_foliculos=int(row.get('total_foliculos', 0) or 0),
                            frente=int(row.get('frente', 0) or 0),
                            densidade_scketh=float(row.get('densidade_scketh', 0) or 0),
                            coroa=int(row.get('coroa', 0) or 0),
                            scalpe=int(row.get('scalpe', 0) or 0),
                            peninsula_direita=int(row.get('peninsula_direita', 0) or 0),
                            peninsula_esquerda=int(row.get('peninsula_esquerda', 0) or 0)
                        )
                        db.session.add(surgery)
                    db.session.commit()
                    logger.info("✅ Data restored successfully")

                    # Verify restoration
                    final_count = Surgery.query.count()
                    logger.info(f"Final database count: {final_count}")
                else:
                    logger.info("✅ Data is consistent")

if __name__ == "__main__":
    verify_data()