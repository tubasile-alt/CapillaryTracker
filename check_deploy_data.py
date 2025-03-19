import os
import pandas as pd
from app import app, db, Surgery
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_deployment_consistency():
    logger.info("Verificando consistência dos dados de deployment...")

    # Check local database
    with app.app_context():
        local_count = Surgery.query.count()
        logger.info(f"Registros no banco local: {local_count}")

        # Get local data
        local_surgeries = Surgery.query.all()
        local_names = [s.nome for s in local_surgeries]

    # Check deployment data
    deploy_file = os.path.join("deploy_data", "cirurgias.xlsx")
    if os.path.exists(deploy_file):
        df_deploy = pd.read_excel(deploy_file)
        deploy_count = len(df_deploy)
        logger.info(f"Registros nos dados de deployment: {deploy_count}")

        if deploy_count != local_count:
            logger.error(f"❌ INCONSISTÊNCIA DETECTADA!")
            logger.error(f"Local: {local_count} registros")
            logger.error(f"Deployment: {deploy_count} registros")

            # Show deployment data
            logger.info("\nDados no arquivo de deployment:")
            for _, row in df_deploy.iterrows():
                logger.info(f"- {row['nome']} ({row['unidade']}) - {row['data']}")

            # Show local data
            logger.info("\nDados locais:")
            for surgery in local_surgeries:
                logger.info(f"- {surgery.nome} ({surgery.unidade}) - {surgery.data}")
    else:
        logger.error("❌ Arquivo de deployment não encontrado!")

if __name__ == "__main__":
    check_deployment_consistency()