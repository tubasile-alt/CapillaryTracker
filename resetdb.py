#!/usr/bin/env python
"""
Script para resetar completamente o banco de dados e as migrações.
Este script irá:
1. Remover todas as tabelas existentes
2. Remover todos os arquivos de migração
3. Reinicializar as migrações do Flask-Migrate
4. Criar a migração inicial
5. Aplicar a migração ao banco de dados

ATENÇÃO: Este script irá remover TODOS os dados do banco de dados.
         Use apenas quando for absolutamente necessário.
"""

import os
import sys
import time
import shutil
import logging
import subprocess
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def confirm_reset():
    """Solicita confirmação do usuário antes de prosseguir com o reset"""
    print("\n" + "!"*60)
    print("!!! ATENÇÃO: ESTA OPERAÇÃO IRÁ REMOVER TODOS OS DADOS !!!")
    print("!"*60)
    print("\nEste script irá:")
    print("  1. Fazer backup dos arquivos Excel atuais")
    print("  2. Remover TODAS as tabelas do banco de dados")
    print("  3. Remover todos os arquivos de migração")
    print("  4. Reinicializar o sistema de migrações")
    print("  5. Criar e aplicar uma nova migração inicial\n")
    
    answer = input('Digite "RESET" para confirmar: ')
    
    return answer.strip().upper() == "RESET"

def backup_data():
    """Cria um backup dos arquivos Excel antes do reset"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Lista de arquivos para backup
    files_to_backup = [
        'cirurgias.xlsx',
        'necroses.xlsx'
    ]
    
    # Criar diretório de backup se não existir
    backup_dir = 'data_backup'
    os.makedirs(backup_dir, exist_ok=True)
    
    for file in files_to_backup:
        if os.path.exists(file):
            backup_file = f"{backup_dir}/{os.path.splitext(file)[0]}_{timestamp}{os.path.splitext(file)[1]}"
            shutil.copy2(file, backup_file)
            logger.info(f"Backup criado: {backup_file}")

def main():
    """Função principal para resetar o banco de dados"""
    if not confirm_reset():
        logger.info("Reset cancelado pelo usuário.")
        sys.exit(0)
    
    try:
        # Passo 1: Backup dos dados
        logger.info("Iniciando backup dos dados...")
        backup_data()
        logger.info("Backup concluído.")
        
        # Passo 2: Remover todas as tabelas
        logger.info("Removendo todas as tabelas...")
        subprocess.run([sys.executable, 'drop_tables.py'], check=True)
        logger.info("Tabelas removidas.")
        
        # Passo 3: Resetar migrações
        logger.info("Resetando sistema de migrações...")
        subprocess.run([sys.executable, 'reset_migrations.py'], check=True)
        logger.info("Sistema de migrações resetado.")
        
        # Passo 4: Criar migração inicial
        logger.info("Criando migração inicial...")
        subprocess.run([sys.executable, 'force_initial_migration.py'], check=True)
        logger.info("Migração inicial criada.")
        
        # Passo 5: Aplicar migração
        logger.info("Aplicando migração...")
        subprocess.run([sys.executable, 'apply_migration.py'], check=True)
        logger.info("Migração aplicada.")
        
        # Passo 6: Verificar estado final
        logger.info("Verificando estado final...")
        subprocess.run([sys.executable, 'check_migrations.py'], check=True)
        
        logger.info("\n" + "="*50)
        logger.info("✅ RESET COMPLETO REALIZADO COM SUCESSO")
        logger.info("="*50)
        logger.info("O banco de dados foi completamente resetado.")
        logger.info("Backups dos dados foram salvos em 'data_backup/'")
        logger.info("="*50)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro durante o reset: {str(e)}")
        logger.error(f"Código de saída: {e.returncode}")
        if e.output:
            logger.error(f"Detalhes: {e.output}")
        
        logger.error("\n" + "="*50)
        logger.error("❌ RESET FALHOU")
        logger.error("="*50)
        logger.error("O banco de dados pode estar em um estado inconsistente.")
        logger.error("Verifique os logs para mais detalhes.")
        logger.error("="*50)
        
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()