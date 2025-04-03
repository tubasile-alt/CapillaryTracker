#!/usr/bin/env python3
"""
Script para verificar o conteúdo de um arquivo de backup ZIP
"""
import zipfile
import sys
import os

def list_zip_contents(zip_file):
    """Lista o conteúdo de um arquivo ZIP"""
    print(f"Conteúdo do arquivo: {zip_file}")
    print("-" * 80)
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zipf:
            # Listar arquivos
            file_list = zipf.namelist()
            file_list.sort()
            
            # Imprimir estatísticas
            print(f"Total de arquivos: {len(file_list)}")
            total_size = sum(zipf.getinfo(name).file_size for name in file_list)
            print(f"Tamanho total descompactado: {total_size / 1024:.2f} KB")
            
            # Imprimir diretórios principais
            directories = set()
            for file in file_list:
                parts = file.split('/')
                if len(parts) > 1:
                    directories.add(parts[0])
            
            print(f"Diretórios principais: {', '.join(sorted(directories))}")
            print("-" * 80)
            
            # Listar arquivos (limitado aos primeiros 30)
            limit = 30
            for i, name in enumerate(file_list):
                if i >= limit:
                    print(f"... e mais {len(file_list) - limit} arquivos")
                    break
                    
                info = zipf.getinfo(name)
                size = info.file_size
                print(f"{name} - {size / 1024:.2f} KB")
            
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
    
    list_zip_contents(zip_file)