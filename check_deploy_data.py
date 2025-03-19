
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
            db_records = Surgery.query.all()
            db_count = len(db_records)
            logger.info(f"Registros no banco local: {db_count}")
            
            if db_count > 0:
                db_data = pd.DataFrame([{
                    'nome': r.nome,
                    'data': r.data,
                    'unidade': r.unidade,
                    'total_foliculos': r.total_foliculos
                } for r in db_records])
                logger.info("Primeiros registros do banco:")
                logger.info(db_data.head())

        # 2. Verificar Excel local
        excel_data = None
        if os.path.exists("cirurgias.xlsx"):
            excel_data = pd.read_excel("cirurgias.xlsx")
            excel_count = len(excel_data)
            logger.info(f"Registros no Excel local: {excel_count}")
            logger.info("Primeiros registros do Excel local:")
            logger.info(excel_data.head())
        else:
            excel_count = 0
            logger.warning("Arquivo cirurgias.xlsx não encontrado")

        # 3. Verificar dados de deployment
        deploy_data = None
        deploy_file = os.path.join("deploy_data", "cirurgias.xlsx")
        if os.path.exists(deploy_file):
            deploy_data = pd.read_excel(deploy_file)
            deploy_count = len(deploy_data)
            logger.info(f"Registros no deploy: {deploy_count}")
            logger.info("Primeiros registros do deploy:")
            logger.info(deploy_data.head())

            # Comparação detalhada
            if deploy_count > 0:
                # Verificar estrutura dos dados
                if db_count > 0 and deploy_count != db_count:
                    logger.error(f"❌ Diferença no número de registros: BD={db_count}, Deploy={deploy_count}")
                
                if excel_data is not None:
                    # Comparar dados do Excel com deploy
                    try:
                        deploy_data['data'] = pd.to_datetime(deploy_data['data'])
                        excel_data['data'] = pd.to_datetime(excel_data['data'])
                        
                        # Ordenar ambos os dataframes
                        deploy_data = deploy_data.sort_values(['data', 'nome'])
                        excel_data = excel_data.sort_values(['data', 'nome'])
                        
                        # Resetar índices para comparação
                        deploy_data = deploy_data.reset_index(drop=True)
                        excel_data = excel_data.reset_index(drop=True)
                        
                        # Comparar apenas colunas comuns
                        common_columns = list(set(deploy_data.columns) & set(excel_data.columns))
                        if not deploy_data[common_columns].equals(excel_data[common_columns]):
                            logger.error("❌ Dados diferentes entre Excel local e deploy")
                            
                            # Identificar diferenças
                            for col in common_columns:
                                if not deploy_data[col].equals(excel_data[col]):
                                    logger.error(f"Diferenças na coluna {col}")
                                    
                        else:
                            logger.info("✅ Dados iguais entre Excel local e deploy")
                            
                    except Exception as e:
                        logger.error(f"Erro na comparação: {str(e)}")

                # Tentar restaurar se necessário
                if db_count == 0 or deploy_count != db_count:
                    from restore_deployment_data import restore_deployment_data
                    logger.info("Tentando restaurar dados...")
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
