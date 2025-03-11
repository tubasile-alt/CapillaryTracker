
import os
import shutil
import logging
import json
import pandas as pd

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def restore_deployment_data():
    """
    Restaura os dados do sistema após o deployment
    """
    try:
        # Verificar se o diretório de dados de deploy existe
        deploy_data_dir = "deploy_data"
        if not os.path.exists(deploy_data_dir):
            logger.error(f"❌ Diretório {deploy_data_dir} não encontrado!")
            return False
        
        # Verificar manifesto de deployment
        manifest_file = "deploy_manifest.json"
        if os.path.exists(manifest_file):
            with open(manifest_file, "r") as f:
                manifest = json.load(f)
            logger.info(f"Manifesto de deployment carregado: {manifest}")
        else:
            logger.warning("⚠️ Manifesto de deployment não encontrado.")
            manifest = {"data_files": ["cirurgias.xlsx", "necroses.xlsx"], "include_data": True}
        
        # Se include_data for False, não restaurar dados
        if not manifest.get("include_data", True):
            logger.info("Restauração de dados desativada no manifesto.")
            return True
        
        # Restaurar cada arquivo de dados
        for file in manifest.get("data_files", []):
            deploy_file = os.path.join(deploy_data_dir, file)
            
            if os.path.exists(deploy_file):
                # Verificar se o arquivo tem dados
                try:
                    df = pd.read_excel(deploy_file)
                    if len(df) > 0:
                        # Restaurar arquivo
                        shutil.copy2(deploy_file, file)
                        logger.info(f"✅ Dados restaurados: {deploy_file} → {file} ({len(df)} registros)")
                    else:
                        logger.info(f"🔄 Arquivo {deploy_file} está vazio, não restaurado")
                except Exception as e:
                    logger.error(f"⚠️ Erro ao ler {deploy_file}: {str(e)}")
            else:
                logger.warning(f"⚠️ Arquivo {deploy_file} não encontrado, não restaurado")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro durante restauração dos dados: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("\n==================================================")
    print("🔄 INICIANDO RESTAURAÇÃO DE DADOS PÓS-DEPLOYMENT 🔄")
    print("==================================================\n")
    
    success = restore_deployment_data()
    
    if success:
        print("\n==================================================")
        print("✅ DADOS RESTAURADOS COM SUCESSO!")
        print("==================================================")
        print("O sistema está pronto para uso com os dados anteriores.")
    else:
        print("\n==================================================")
        print("❌ ERRO DURANTE RESTAURAÇÃO DOS DADOS!")
        print("==================================================")
        print("Verifique os logs para mais detalhes.")
