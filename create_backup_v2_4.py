#!/usr/bin/env python3
"""
Script para criar um backup completo do sistema na versão 2.4
"""
import os
import shutil
import datetime
import zipfile
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_backup_v2_4():
    """
    Cria um backup completo do sistema na versão 2.4
    Inclui:
    - Código-fonte
    - Arquivos de dados (Excel)
    - Backup do banco de dados (se possível)
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_v2_4_{timestamp}"
    backup_zip = f"{backup_dir}.zip"
    
    logger.info(f"Criando backup v2.4 com timestamp {timestamp}")
    
    try:
        # Criar diretório temporário para backup
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            logger.info(f"Diretório de backup criado: {backup_dir}")
        
        # Lista de arquivos importantes para backup
        files_to_backup = [
            # Arquivos Python principais
            "app.py", "main.py", "utils.py",
            # Arquivos de dados
            "cirurgias.xlsx", "necroses.xlsx",
            # Arquivos de configuração
            "config.cfg", "pyproject.toml",
            # Arquivos de migração
            "create_migration.py", "apply_migration.py",
            # Scripts de utilidade
            "import_data.py", "backup_and_prepare_data.py"
        ]
        
        # Lista de diretórios para backup
        dirs_to_backup = [
            "templates", "static", "migrations"
        ]
        
        # Copiar arquivos importantes
        for file in files_to_backup:
            if os.path.exists(file):
                shutil.copy2(file, os.path.join(backup_dir, file))
                logger.info(f"Arquivo copiado: {file}")
            else:
                logger.warning(f"Arquivo não encontrado: {file}")
        
        # Copiar diretórios importantes
        for directory in dirs_to_backup:
            if os.path.exists(directory):
                dest_dir = os.path.join(backup_dir, directory)
                shutil.copytree(directory, dest_dir)
                logger.info(f"Diretório copiado: {directory}")
            else:
                logger.warning(f"Diretório não encontrado: {directory}")
        
        # Criar arquivo de versão
        with open(os.path.join(backup_dir, "VERSION.txt"), "w") as f:
            f.write("Versão: 2.4\n")
            f.write(f"Data do backup: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("Alterações:\n")
            f.write("- Corrigido problema na atualização dinâmica dos campos de médico e equipe\n")
            f.write("- Corrigido problema de extensão de arquivo ao salvar dados no Excel\n")
            f.write("- Melhorias gerais de estabilidade\n")
        
        # Comprimir para arquivo ZIP
        with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_dir)
                    zipf.write(file_path, arcname)
        
        logger.info(f"Backup compactado criado: {backup_zip}")
        
        # Limpar diretório temporário
        shutil.rmtree(backup_dir)
        logger.info(f"Diretório temporário removido: {backup_dir}")
        
        logger.info(f"✅ Backup v2.4 concluído com sucesso: {backup_zip}")
        return True, backup_zip
    
    except Exception as e:
        logger.error(f"Erro ao criar backup v2.4: {str(e)}")
        return False, str(e)

if __name__ == "__main__":
    success, result = create_backup_v2_4()
    if success:
        print(f"Backup criado com sucesso: {result}")
    else:
        print(f"Erro ao criar backup: {result}")