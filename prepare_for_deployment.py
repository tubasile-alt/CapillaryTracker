
import os
import shutil
import logging
from datetime import datetime
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def prepare_deployment():
    """
    Preparar os arquivos para deployment, assegurando que os dados existentes sejam mantidos
    """
    try:
        # 0. Verificar quantos registros existem atualmente
        import pandas as pd
        patient_count = 0
        if os.path.exists("cirurgias.xlsx"):
            df = pd.read_excel("cirurgias.xlsx")
            patient_count = len(df)
            logger.info(f"✅ Verificado: Existem {patient_count} pacientes registrados no sistema atual")
            print(f"\n==================================================")
            print(f"Atualmente existem {patient_count} pacientes registrados no sistema")
            print(f"==================================================\n")
            # Exibir informações dos pacientes
            if patient_count > 0:
                print("Resumo dos pacientes:")
                for i, row in df.iterrows():
                    nome = row.get('nome', 'Nome não disponível')
                    data = row.get('data', 'Data não disponível')
                    unidade = row.get('unidade', 'Unidade não disponível')
                    print(f"  {i+1}. {nome} ({unidade}) - {data}")
                print()
        
        # 1. Executar o backup e preparação de dados
        logger.info("Executando backup e preparação de dados...")
        from backup_and_prepare_data import backup_and_prepare_data
        success, backup_files = backup_and_prepare_data()
        
        if not success:
            logger.error("Falha ao fazer backup dos dados!")
            return False
        
        # 2. Criar manifesto de deployment
        logger.info("Criando manifesto de deployment...")
        deploy_manifest = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_files": [file[0] for file in backup_files],
            "version": datetime.now().strftime("%Y%m%d%H%M%S"),
            "include_data": True,
            "patient_count": patient_count
        }
        
        # Salvar manifesto em JSON
        with open("deploy_manifest.json", "w") as f:
            json.dump(deploy_manifest, f, indent=2)
        
        logger.info(f"✅ Manifesto de deployment criado: {deploy_manifest}")
        
        # 3. Configurar script post-deployment para restaurar dados
        logger.info("Configurando script post-deployment...")
        
        # Criar instrução para restaurar dados após deployment
        post_deploy_instructions = f"""
============================================================
✅ DEPLOYMENT CONCLUÍDO! AGORA RESTAURE OS DADOS:

Execute o seguinte comando para restaurar os dados existentes:
    python restore_deployment_data.py
============================================================
"""
        with open("post_deploy_instructions.txt", "w") as f:
            f.write(post_deploy_instructions)
        
        logger.info("✅ Instruções post-deployment criadas")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro durante preparação para deployment: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("\n==================================================")
    print("🚀 INICIANDO PREPARAÇÃO PARA DEPLOYMENT 🚀")
    print("==================================================\n")
    
    success = prepare_deployment()
    
    if success:
        print("\n==================================================")
        print("✅ PREPARAÇÃO PARA DEPLOYMENT CONCLUÍDA!")
        print("==================================================")
        print("Seu sistema está pronto para deployment com os dados atuais.")
        print("Após o deployment, execute 'python restore_deployment_data.py'")
    else:
        print("\n==================================================")
        print("❌ ERRO DURANTE PREPARAÇÃO PARA DEPLOYMENT!")
        print("==================================================")
