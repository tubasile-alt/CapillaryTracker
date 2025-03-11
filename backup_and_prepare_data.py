
import os
import pandas as pd
import shutil
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def backup_and_prepare_data():
    """
    1. Faz backup dos arquivos de dados existentes
    2. Prepara os dados para o novo deploy
    """
    try:
        # Criar pasta de backup se não existir
        backup_folder = "data_backup"
        os.makedirs(backup_folder, exist_ok=True)
        
        # Timestamp para o nome dos arquivos de backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Lista de arquivos de dados para backup
        data_files = ["cirurgias.xlsx", "necroses.xlsx"]
        
        # 1. Fazer backup dos arquivos
        backed_up_files = []
        for file in data_files:
            if os.path.exists(file):
                # Verificar se o arquivo tem dados
                try:
                    df = pd.read_excel(file)
                    if len(df) > 0:
                        # Criar nome do arquivo de backup
                        backup_file = os.path.join(backup_folder, f"{os.path.splitext(file)[0]}_{timestamp}.xlsx")
                        # Copiar para o backup
                        shutil.copy2(file, backup_file)
                        backed_up_files.append((file, backup_file))
                        logger.info(f"✅ Backup de {file} criado em {backup_file}")
                    else:
                        logger.info(f"🔄 Arquivo {file} está vazio, backup não necessário")
                except Exception as e:
                    logger.error(f"⚠️ Erro ao ler {file}: {str(e)}")
            else:
                logger.info(f"🔄 Arquivo {file} não existe, ignorando")
        
        # 2. Copiar dados para arquivos de deploy
        deploy_data_dir = "deploy_data"
        os.makedirs(deploy_data_dir, exist_ok=True)
        
        for original_file, backup_file in backed_up_files:
            deploy_file = os.path.join(deploy_data_dir, original_file)
            shutil.copy2(backup_file, deploy_file)
            logger.info(f"✅ Dados de {original_file} copiados para {deploy_file}")
        
        return True, backed_up_files
    
    except Exception as e:
        logger.error(f"❌ Erro durante backup e preparação: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False, []

if __name__ == "__main__":
    print("\n==================================================")
    print("🔄 INICIANDO BACKUP E PREPARAÇÃO PARA DEPLOY 🔄")
    print("==================================================\n")
    
    success, backed_up_files = backup_and_prepare_data()
    
    if success:
        print("\n==================================================")
        print("✅ BACKUP E PREPARAÇÃO CONCLUÍDOS COM SUCESSO!")
        print("==================================================")
        print("Arquivos com backup:")
        for original, backup in backed_up_files:
            print(f"  - {original} → {backup}")
        print("\nEstes dados estão prontos para serem incluídos no deploy.")
    else:
        print("\n==================================================")
        print("❌ OCORREU UM ERRO DURANTE O PROCESSO!")
        print("==================================================")
        print("Verifique os logs para mais detalhes.")
