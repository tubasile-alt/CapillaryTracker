#!/usr/bin/env python3
"""
Sistema de proteção de dados para deployment
Cria backups seguros de todos os dados antes do deployment
"""

import os
import json
import shutil
from datetime import datetime
import subprocess

def create_data_protection():
    """Cria sistema completo de proteção de dados"""
    
    # Criar diretório de proteção
    protection_dir = "deployment_protection"
    if not os.path.exists(protection_dir):
        os.makedirs(protection_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"{protection_dir}/backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    print(f"🛡️ Criando proteção de dados em: {backup_dir}")
    
    # 1. Backup da configuração administrativa
    admin_files = [
        "admin_config.json",
        "admin_config_backup.json",
        "admin_config_safe_backup.json"
    ]
    
    for file in admin_files:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
            print(f"✅ Backup: {file}")
    
    # 2. Backup dos dados Excel
    excel_files = ["surgery_data.xlsx", "patient_data.xlsx"]
    for file in excel_files:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
            print(f"✅ Backup: {file}")
    
    # 3. Backup do banco de dados (dump SQL)
    try:
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            dump_file = f"{backup_dir}/database_backup.sql"
            # Usar pg_dump para criar backup do banco
            cmd = f"pg_dump '{db_url}' > {dump_file}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Backup do banco de dados criado: {dump_file}")
            else:
                print(f"⚠️ Erro no backup do banco: {result.stderr}")
    except Exception as e:
        print(f"⚠️ Erro no backup do banco: {e}")
    
    # 4. Criar script de restauração
    restore_script = f"""#!/bin/bash
# Script de restauração automática
# Criado em: {datetime.now().isoformat()}

echo "🔄 Restaurando dados após deployment..."

# Restaurar arquivos de configuração
""" + "\n".join([f'cp {backup_dir}/{file} .' for file in admin_files if os.path.exists(file)]) + f"""

# Restaurar arquivos Excel
""" + "\n".join([f'cp {backup_dir}/{file} .' for file in excel_files if os.path.exists(file)]) + f"""

# Restaurar banco de dados (se necessário)
if [ -f "{backup_dir}/database_backup.sql" ] && [ ! -z "$DATABASE_URL" ]; then
    echo "Restaurando banco de dados..."
    psql "$DATABASE_URL" < {backup_dir}/database_backup.sql
fi

echo "✅ Restauração concluída!"
"""
    
    with open(f"{backup_dir}/restore.sh", "w") as f:
        f.write(restore_script)
    
    os.chmod(f"{backup_dir}/restore.sh", 0o755)
    
    # 5. Criar verificador de integridade pós-deployment
    integrity_check = f"""#!/usr/bin/env python3
# Verificador de integridade pós-deployment
import os
import json

def check_integrity():
    print("🔍 Verificando integridade dos dados...")
    
    # Verificar arquivos essenciais
    essential_files = {admin_files + excel_files}
    missing_files = []
    
    for file in essential_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Arquivos ausentes após deployment:")
        for file in missing_files:
            print(f"  - {{file}}")
        print(f"\\n🔄 Execute: {backup_dir}/restore.sh")
        return False
    else:
        print("✅ Todos os arquivos essenciais estão presentes")
        return True

if __name__ == '__main__':
    check_integrity()
"""
    
    with open(f"{backup_dir}/check_integrity.py", "w") as f:
        f.write(integrity_check)
    
    # 6. Criar instruções de recuperação
    instructions = f"""
# INSTRUÇÕES DE PROTEÇÃO DE DADOS - DEPLOYMENT

## Backup criado em: {datetime.now().isoformat()}

### ANTES DO DEPLOYMENT:
✅ Backup completo criado em: {backup_dir}

### APÓS O DEPLOYMENT:
1. Execute a verificação de integridade:
   python3 {backup_dir}/check_integrity.py

2. Se houver dados ausentes, execute a restauração:
   bash {backup_dir}/restore.sh

### ARQUIVOS PROTEGIDOS:
{chr(10).join(['- ' + file for file in admin_files + excel_files if os.path.exists(file)])}

### CONTATOS EM CASO DE EMERGÊNCIA:
- Verifique logs em: /var/log/
- Execute testes de integridade regularmente
- Mantenha este backup seguro

IMPORTANTE: NÃO DELETE ESTE DIRETÓRIO APÓS O DEPLOYMENT!
"""
    
    with open(f"{backup_dir}/LEIA_ME_DEPLOYMENT.txt", "w") as f:
        f.write(instructions)
    
    print(f"📋 Instruções salvas em: {backup_dir}/LEIA_ME_DEPLOYMENT.txt")
    print(f"🛡️ Proteção completa ativada!")
    print(f"📂 Backup localizado em: {backup_dir}")
    
    return backup_dir

if __name__ == '__main__':
    backup_location = create_data_protection()
    print(f"\n✅ PROTEÇÃO ATIVADA: {backup_location}")