
import os
import pandas as pd
import logging
import json
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_data():
    """Verifica os dados atuais e os dados preparados para deployment"""
    
    print("\n==================================================")
    print("🔍 VERIFICAÇÃO DE DADOS PARA DEPLOYMENT")
    print("==================================================\n")
    
    # 1. Verificar dados atuais
    current_patients = 0
    if os.path.exists("cirurgias.xlsx"):
        df = pd.read_excel("cirurgias.xlsx")
        current_patients = len(df)
        print(f"📊 Sistema atual: {current_patients} pacientes")
        
        if current_patients > 0:
            print("\nPacientes no sistema atual:")
            for i, row in df.iterrows():
                nome = row.get('nome', 'Nome não disponível')
                data = row.get('data', 'Data não disponível')
                unidade = row.get('unidade', 'Unidade não disponível')
                print(f"  {i+1}. {nome} ({unidade}) - {data}")
    else:
        print("⚠️ Arquivo cirurgias.xlsx não encontrado no sistema atual")
    
    print("\n--------------------------------------------------\n")
    
    # 2. Verificar dados de deployment
    deploy_patients = 0
    deploy_file = os.path.join("deploy_data", "cirurgias.xlsx")
    if os.path.exists(deploy_file):
        df_deploy = pd.read_excel(deploy_file)
        deploy_patients = len(df_deploy)
        print(f"📊 Dados de deployment: {deploy_patients} pacientes")
        
        if deploy_patients > 0:
            print("\nPacientes nos dados de deployment:")
            for i, row in df_deploy.iterrows():
                nome = row.get('nome', 'Nome não disponível')
                data = row.get('data', 'Data não disponível')
                unidade = row.get('unidade', 'Unidade não disponível')
                print(f"  {i+1}. {nome} ({unidade}) - {data}")
    else:
        print("⚠️ Dados de deployment não encontrados")
    
    print("\n--------------------------------------------------\n")
    
    # 3. Verificar backups recentes
    backup_dir = "data_backup"
    if os.path.exists(backup_dir):
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith("cirurgias_")]
        if backup_files:
            backup_files.sort(reverse=True)  # Ordenar por mais recente
            latest_backup = os.path.join(backup_dir, backup_files[0])
            
            df_backup = pd.read_excel(latest_backup)
            backup_patients = len(df_backup)
            print(f"📊 Backup mais recente ({os.path.basename(latest_backup)}): {backup_patients} pacientes")
            
            if backup_patients > 0:
                print("\nPacientes no backup mais recente:")
                for i, row in df_backup.iterrows():
                    nome = row.get('nome', 'Nome não disponível')
                    data = row.get('data', 'Data não disponível')
                    unidade = row.get('unidade', 'Unidade não disponível')
                    print(f"  {i+1}. {nome} ({unidade}) - {data}")
        else:
            print("⚠️ Nenhum arquivo de backup encontrado")
    else:
        print("⚠️ Diretório de backup não encontrado")
    
    # 4. Verificar manifesto de deployment
    print("\n--------------------------------------------------\n")
    manifest_file = "deploy_manifest.json"
    if os.path.exists(manifest_file):
        with open(manifest_file, "r") as f:
            manifest = json.load(f)
        
        print(f"📝 Manifesto de deployment:")
        print(f"  - Timestamp: {manifest.get('timestamp', 'Não definido')}")
        print(f"  - Versão: {manifest.get('version', 'Não definida')}")
        print(f"  - Incluir dados: {'Sim' if manifest.get('include_data', True) else 'Não'}")
        print(f"  - Contagem de pacientes: {manifest.get('patient_count', 'Não definida')}")
        print(f"  - Arquivos de dados: {', '.join(manifest.get('data_files', []))}")
    else:
        print("⚠️ Manifesto de deployment não encontrado")
    
    # 5. Resumo e conclusão
    print("\n==================================================")
    print("📋 RESUMO DA VERIFICAÇÃO")
    print("==================================================")
    
    print(f"Sistema atual: {current_patients} pacientes")
    print(f"Dados de deployment: {deploy_patients} pacientes")
    
    if current_patients > deploy_patients:
        print(f"\n⚠️ ALERTA: O sistema atual tem {current_patients} pacientes, mas os")
        print(f"   dados de deployment têm apenas {deploy_patients} pacientes.")
        print(f"   Execute 'python prepare_for_deployment.py' antes do deployment.")
    elif current_patients < deploy_patients:
        print(f"\n⚠️ ALERTA: Os dados de deployment têm {deploy_patients} pacientes,")
        print(f"   mas o sistema atual tem apenas {current_patients} pacientes.")
        print(f"   Execute 'python restore_deployment_data.py' para restaurar os dados.")
    else:
        print(f"\n✅ VERIFICAÇÃO OK: O sistema atual e os dados de deployment")
        print(f"   têm a mesma quantidade de pacientes ({current_patients}).")
    
    print("\n==================================================\n")
    
    return current_patients, deploy_patients

if __name__ == "__main__":
    check_data()
