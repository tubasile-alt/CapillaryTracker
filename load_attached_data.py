
import os
import logging
import pandas as pd
import traceback
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_attached_data():
    """Carrega dados do arquivo anexado diretamente para o banco de dados"""
    try:
        # Caminho do arquivo anexado
        source_file = "attached_assets/relatorio_cirurgias.xlsx"
        
        # Verificar se o arquivo existe
        if not os.path.exists(source_file):
            logger.error(f"Arquivo {source_file} não encontrado!")
            return False
        
        # Carregar a planilha de origem
        logger.info(f"Carregando dados de {source_file}...")
        df_source = pd.read_excel(source_file)
        
        if df_source.empty:
            logger.error("O arquivo Excel está vazio!")
            return False
            
        # Fazer backup do arquivo atual se existir
        if os.path.exists("cirurgias.xlsx"):
            backup_dir = "data_backup"
            os.makedirs(backup_dir, exist_ok=True)
            backup_file = f"{backup_dir}/cirurgias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            logger.info(f"Fazendo backup dos dados atuais para {backup_file}...")
            
            # Copiar arquivo atual para backup
            import shutil
            shutil.copy2("cirurgias.xlsx", backup_file)
        
        # Salvar os dados no arquivo de destino, substituindo o atual
        logger.info("Substituindo dados atuais com os novos dados...")
        df_source.to_excel("cirurgias.xlsx", index=False, engine='openpyxl')
        
        num_records = len(df_source)
        logger.info(f"✅ Substituição concluída com sucesso! {num_records} registros importados.")
        
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
        print(f"Total de registros: {len(pd.read_excel('cirurgias.xlsx'))}")
        print("======================================\n")
    else:
        print("\n======================================")
        print("❌ ERRO AO CARREGAR DADOS!")
        print("======================================\n")
