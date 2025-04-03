#!/usr/bin/env python3
"""
Script para extrair e exibir o arquivo VERSION.txt de um backup
"""
import zipfile
import sys
import os

def extract_version_info(zip_file):
    """Extrai e exibe o conteúdo do arquivo VERSION.txt"""
    try:
        with zipfile.ZipFile(zip_file, 'r') as zipf:
            if 'VERSION.txt' in zipf.namelist():
                with zipf.open('VERSION.txt') as version_file:
                    content = version_file.read().decode('utf-8')
                    print(content)
            else:
                print("Arquivo VERSION.txt não encontrado no backup!")
    except Exception as e:
        print(f"Erro ao abrir arquivo ZIP: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        zip_file = sys.argv[1]
    else:
        # Tentar encontrar o arquivo de backup mais recente
        backups = [f for f in os.listdir('.') if f.startswith('backup_v2_4_') and f.endswith('.zip')]
        if not backups:
            print("Nenhum arquivo de backup encontrado!")
            sys.exit(1)
        
        backups.sort(reverse=True)  # Ordenar por nome (que contém timestamp)
        zip_file = backups[0]
        print(f"Usando o backup mais recente: {zip_file}")
    
    extract_version_info(zip_file)