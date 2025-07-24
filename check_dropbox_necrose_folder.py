#!/usr/bin/env python3
"""
Script para verificar a pasta de fotos de necrose no Dropbox
"""

import os
import dropbox
from datetime import datetime

def check_dropbox_necrose_folder():
    """Verifica e mostra o conteúdo da pasta de necrose no Dropbox"""
    
    print("🔍 VERIFICAÇÃO DA PASTA DE FOTOS DE NECROSE NO DROPBOX")
    print("=" * 60)
    
    # Verificar token
    token = os.environ.get('DROPBOX_ACCESS_TOKEN')
    if not token:
        print("❌ DROPBOX_ACCESS_TOKEN não encontrado")
        return
    
    try:
        dbx = dropbox.Dropbox(token)
        
        # Verificar conta
        account = dbx.users_get_current_account()
        print(f"📧 Conta Dropbox: {account.email}")
        print(f"👤 Nome: {account.name.display_name}")
        
        # Caminho da pasta de necrose
        necrose_folder = "/fotos_necrose"
        print(f"\n📁 PASTA DE NECROSE: {necrose_folder}")
        print("=" * 40)
        
        # Verificar se a pasta existe
        try:
            folder_content = dbx.files_list_folder(necrose_folder)
            print(f"✅ Pasta encontrada com {len(folder_content.entries)} itens")
            
            if folder_content.entries:
                print("\n📋 CONTEÚDO DA PASTA:")
                for i, entry in enumerate(folder_content.entries, 1):
                    if isinstance(entry, dropbox.files.FileMetadata):
                        size_mb = entry.size / (1024 * 1024)
                        modified = entry.server_modified.strftime('%d/%m/%Y %H:%M')
                        print(f"  {i:2d}. 📄 {entry.name}")
                        print(f"      💾 {size_mb:.2f} MB | 📅 {modified}")
                        
                        # Tentar obter link de compartilhamento
                        try:
                            shared_link = dbx.sharing_create_shared_link(f"{necrose_folder}/{entry.name}")
                            print(f"      🔗 Link: {shared_link.url}")
                        except dropbox.exceptions.ApiError as e:
                            if "shared_link_already_exists" in str(e):
                                # Link já existe, tentar obter
                                try:
                                    links = dbx.sharing_list_shared_links(f"{necrose_folder}/{entry.name}")
                                    if links.links:
                                        print(f"      🔗 Link: {links.links[0].url}")
                                except:
                                    print(f"      🔗 Link: (não disponível)")
                            else:
                                print(f"      🔗 Link: (erro ao gerar)")
                        print()
            else:
                print("📂 Pasta vazia")
                
        except dropbox.exceptions.ApiError as e:
            if "not_found" in str(e):
                print("📂 Pasta não existe ainda - será criada no primeiro upload")
                
                # Tentar criar a pasta
                try:
                    dbx.files_create_folder_v2(necrose_folder)
                    print("✅ Pasta criada com sucesso!")
                except dropbox.exceptions.ApiError as create_error:
                    print(f"❌ Erro ao criar pasta: {create_error}")
            else:
                print(f"❌ Erro ao acessar pasta: {e}")
        
        # Mostrar estrutura completa
        print("\n" + "=" * 60)
        print("📋 ESTRUTURA COMPLETA DO DROPBOX:")
        print("=" * 60)
        
        try:
            all_content = dbx.files_list_folder("")
            print("📁 Raiz do aplicativo:")
            for entry in all_content.entries:
                if isinstance(entry, dropbox.files.FolderMetadata):
                    print(f"  📁 {entry.name}/")
                    if entry.name == "fotos_necrose":
                        print(f"      👆 Esta é a pasta onde as fotos de necrose são salvas")
                elif isinstance(entry, dropbox.files.FileMetadata):
                    print(f"  📄 {entry.name}")
                    
        except Exception as e:
            print(f"❌ Erro ao listar conteúdo: {e}")
        
        # Informações finais
        print("\n" + "=" * 60)
        print("📝 INFORMAÇÕES IMPORTANTES:")
        print("=" * 60)
        print(f"🌐 Caminho completo: https://dropbox.com/home/Apps/[nome-do-app]{necrose_folder}")
        print(f"📂 Caminho da API: {necrose_folder}")
        print(f"💾 Arquivos salvos com formato: necrose_[ID]_[timestamp]_[hash].[extensão]")
        print(f"📸 Tipos aceitos: JPG, JPEG, PNG")
        print(f"📊 Limite por upload: 3 fotos")
        
    except dropbox.exceptions.AuthError:
        print("❌ Erro de autenticação - Token inválido")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    check_dropbox_necrose_folder()