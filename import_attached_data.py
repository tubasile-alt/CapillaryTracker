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

def clear_and_import_data():
    try:
        # Create backup of current data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"data_backup/cirurgias_{timestamp}.xlsx"
        os.makedirs("data_backup", exist_ok=True)
        if os.path.exists("cirurgias.xlsx"):
            shutil.copy2("cirurgias.xlsx", backup_path)
            logger.info(f"✅ Backup created at {backup_path}")

        # Verificar se a planilha de origem existe
        source_file = os.path.join("attached_assets", "relatorio_cirurgias.xlsx")
        if not os.path.exists(source_file):
            logger.error(f"Arquivo de origem {source_file} não encontrado")
            return False

        # 2. Importar dados da planilha em attached_assets
        logger.info(f"Importando dados de {source_file}...")

        # Carregar a planilha de origem
        df_source = pd.read_excel(source_file, engine='openpyxl')

        # Salvar no arquivo de destino
        df_source.to_excel("cirurgias.xlsx", index=False, engine='openpyxl')

        num_records = len(df_source)
        logger.info(f"✅ Dados importados com sucesso! {num_records} registros adicionados.")

        return True

    except Exception as e:
        logger.error(f"Erro ao importar dados: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = clear_and_import_data()
    if success:
        print("\n======================================")
        print("✅ DADOS LIMPOS E IMPORTADOS COM SUCESSO!")
        print("======================================\n")
    else:
        print("\n======================================")
        print("❌ ERRO AO LIMPAR E IMPORTAR DADOS!")
        print("======================================\n")