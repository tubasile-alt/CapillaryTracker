import os
import logging
import pandas as pd
import traceback
from datetime import datetime
import shutil

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_attached_data():
    """Carrega dados do arquivo anexado diretamente"""
    try:
        # Caminho do arquivo anexado
        source_file = "attached_assets/relatorio_cirurgias.xlsx"
        target_file = "cirurgias.xlsx"

        # Verificar se o arquivo existe
        if not os.path.exists(source_file):
            logger.error(f"Arquivo {source_file} não encontrado!")
            return False

        # Fazer backup do arquivo atual se existir
        if os.path.exists(target_file):
            backup_dir = "data_backup"
            os.makedirs(backup_dir, exist_ok=True)
            backup_file = f"{backup_dir}/cirurgias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            logger.info(f"Fazendo backup dos dados atuais para {backup_file}...")
            shutil.copy2(target_file, backup_file)

        # Copiar arquivo novo diretamente
        logger.info(f"Copiando dados de {source_file} para {target_file}...")
        shutil.copy2(source_file, target_file)

        logger.info("✅ Dados substituídos com sucesso!")
        return True

    except Exception as e:
        logger.error(f"Erro ao carregar dados: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = load_attached_data()
    if success:
        print("\n======================================")
        print("✅ DADOS CARREGADOS COM SUCESSO!")
        print("======================================\n")
    else:
        print("\n======================================")
        print("❌ ERRO AO CARREGAR DADOS!")
        print("======================================\n")