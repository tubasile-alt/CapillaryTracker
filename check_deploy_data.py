
import os
import logging
import pandas as pd
from app import app, db, Surgery
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_deployment_consistency():
    """Verifica consistência dos dados após deployment"""
    logger.info("Verificando consistência dos dados...")

    try:
        # 1. Verificar banco de dados local
        with app.app_context():
            local_count = Surgery.query.count()
            logger.info(f"Registros no banco local: {local_count}")
            
            # Get actual records for detailed comparison
            local_records = Surgery.query.all()
            local_names = [r.nome for r in local_records]
            logger.info(f"Nomes no banco local: {local_names}")

        # 2. Verificar arquivo Excel local
        local_excel_data = None
        if os.path.exists("cirurgias.xlsx"):
            df_local = pd.read_excel("cirurgias.xlsx")
            excel_count = len(df_local)
            logger.info(f"Registros no Excel local: {excel_count}")
            local_excel_data = df_local
            logger.info(f"Nomes no Excel local: {df_local['nome'].tolist()}")
        else:
            excel_count = 0
            logger.warning("Arquivo cirurgias.xlsx não encontrado")

        # 3. Verificar dados de deployment
        deploy_data = None
        deploy_file = os.path.join("deploy_data", "cirurgias.xlsx")
        if os.path.exists(deploy_file):
            df_deploy = pd.read_excel(deploy_file)
            deploy_count = len(df_deploy)
            logger.info(f"Registros no deploy: {deploy_count}")
            deploy_data = df_deploy
            logger.info(f"Nomes no deploy: {df_deploy['nome'].tolist()}")

            # Detailed comparison
            if local_excel_data is not None and deploy_data is not None:
                logger.info("Comparando dados detalhadamente...")
                # Compare records
                missing_in_deploy = set(local_excel_data['nome']) - set(df_deploy['nome'])
                missing_in_local = set(df_deploy['nome']) - set(local_excel_data['nome'])
                
                if missing_in_deploy:
                    logger.error(f"Registros faltando no deploy: {missing_in_deploy}")
                if missing_in_local:
                    logger.error(f"Registros faltando no local: {missing_in_local}")

            if deploy_count != local_count or deploy_count != excel_count:
                logger.error("❌ INCONSISTÊNCIA DETECTADA!")
                logger.error(f"- Banco local: {local_count} registros")
                logger.error(f"- Excel local: {excel_count} registros")
                logger.error(f"- Deploy: {deploy_count} registros")

                # Tentar restaurar dados se necessário
                from restore_deployment_data import restore_deployment_data
                success, restored = restore_deployment_data()
                if success:
                    logger.info("✅ Dados restaurados automaticamente")
                    return True
                else:
                    logger.error("❌ Falha na restauração automática")
                    return False
            else:
                logger.info("✅ Dados consistentes")
                return True
        else:
            logger.error("❌ Arquivo de deployment não encontrado")
            return False

    except Exception as e:
        logger.error(f"❌ Erro na verificação: {str(e)}")
        return False

if __name__ == "__main__":
    check_deployment_consistency()
