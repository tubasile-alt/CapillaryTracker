#!/usr/bin/env python3
# Verificador de integridade pós-deployment
import os
import json

def check_integrity():
    print("🔍 Verificando integridade dos dados...")
    
    # Verificar arquivos essenciais
    essential_files = ['admin_config.json', 'admin_config_backup.json', 'admin_config_safe_backup.json', 'surgery_data.xlsx', 'patient_data.xlsx']
    missing_files = []
    
    for file in essential_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Arquivos ausentes após deployment:")
        for file in missing_files:
            print(f"  - {file}")
        print(f"\n🔄 Execute: deployment_protection/backup_20250826_191204/restore.sh")
        return False
    else:
        print("✅ Todos os arquivos essenciais estão presentes")
        return True

if __name__ == '__main__':
    check_integrity()
