
import os
import pandas as pd
import shutil
from datetime import datetime
import logging
import traceback

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_from_attachment():
    """Carrega dados do arquivo anexado para o sistema"""
    try:
        # Caminho do arquivo anexado
        source_file = "attached_assets/relatorio_cirurgias.xlsx"
        
        # Verificar se o arquivo existe
        if not os.path.exists(source_file):
            logger.error(f"Arquivo {source_file} não encontrado!")
            return False
        
        # Fazer backup do arquivo atual se existir
        if os.path.exists("cirurgias.xlsx"):
            backup_dir = "data_backup"
            os.makedirs(backup_dir, exist_ok=True)
            backup_file = f"{backup_dir}/cirurgias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            logger.info(f"Fazendo backup dos dados atuais para {backup_file}...")
            
            # Copiar arquivo atual para backup
            shutil.copy2("cirurgias.xlsx", backup_file)
        
        # Copiar o arquivo anexado para substituir o atual
        logger.info(f"Substituindo dados atuais com os de {source_file}...")
        shutil.copy2(source_file, "cirurgias.xlsx")
        
        # Verificar se a operação foi bem-sucedida
        if os.path.exists("cirurgias.xlsx"):
            try:
                df = pd.read_excel("cirurgias.xlsx")
                num_records = len(df)
                logger.info(f"✅ Substituição concluída com sucesso! {num_records} registros carregados.")
                return True
            except Exception as e:
                logger.error(f"Erro ao ler o arquivo após a substituição: {str(e)}")
                return False
        else:
            logger.error("Falha ao copiar o arquivo!")
            return False
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = load_from_attachment()
    if success:
        print("\n======================================")
        print("✅ DADOS CARREGADOS COM SUCESSO!")
        try:
            print(f"Total de registros: {len(pd.read_excel('cirurgias.xlsx'))}")
        except:
            print("Não foi possível contar os registros, mas o arquivo foi copiado.")
        print("======================================\n")
    else:
        print("\n======================================")
        print("❌ ERRO AO CARREGAR DADOS!")
        print("======================================\n")
