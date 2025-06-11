#!/usr/bin/env python3
"""
Script de configuração para o backup automático no Dropbox

Para usar este sistema de backup:

1. Crie uma aplicação no Dropbox:
   - Acesse https://www.dropbox.com/developers/apps
   - Clique em "Create app"
   - Escolha "Scoped access"
   - Escolha "App folder" para acesso limitado à pasta da aplicação
   - Dê um nome como "replit-relatorio-cirurgia"

2. Configure as permissões:
   - Na aba "Permissions", marque:
     - files.metadata.write
     - files.content.write
     - files.content.read

3. Gere um token de acesso:
   - Na aba "Settings", role até "OAuth 2"
   - Clique em "Generate access token"
   - Copie o token gerado

4. Configure a variável de ambiente:
   - No Replit, vá em "Secrets" (ícone de cadeado)
   - Adicione uma nova secret:
     - Key: DROPBOX_ACCESS_TOKEN
     - Value: cole o token que você copiou

5. Teste o backup:
   - Acesse /test_backup no seu app
   - Verifique se o arquivo foi criado na pasta do Dropbox
"""

import os
import sys
import dropbox
from datetime import datetime

def test_dropbox_connection():
    """Testa a conexão com o Dropbox"""
    
    # Verificar se o token está configurado
    token = os.environ.get('DROPBOX_ACCESS_TOKEN')
    if not token:
        print("❌ DROPBOX_ACCESS_TOKEN não encontrado nas variáveis de ambiente")
        print("Configure o token nas Secrets do Replit:")
        print("1. Clique no ícone de cadeado (Secrets)")
        print("2. Adicione: DROPBOX_ACCESS_TOKEN = seu_token_aqui")
        return False
    
    try:
        # Testar conexão
        print("🔄 Testando conexão com Dropbox...")
        dbx = dropbox.Dropbox(token)
        
        # Verificar conta
        account = dbx.users_get_current_account()
        print(f"✅ Conectado como: {account.name.display_name}")
        print(f"✅ Email: {account.email}")
        
        # Testar criação de arquivo
        test_content = f"Teste de conexão - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        test_path = "/teste_conexao.txt"
        
        print("🔄 Testando upload de arquivo...")
        dbx.files_upload(
            test_content.encode('utf-8'),
            test_path,
            mode=dropbox.files.WriteMode.overwrite
        )
        print(f"✅ Arquivo de teste criado: {test_path}")
        
        # Listar arquivos na raiz
        print("📁 Arquivos na pasta do app:")
        try:
            entries = dbx.files_list_folder("").entries
            for entry in entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    print(f"  📄 {entry.name} ({entry.size} bytes)")
                elif isinstance(entry, dropbox.files.FolderMetadata):
                    print(f"  📁 {entry.name}/")
        except dropbox.exceptions.ApiError as e:
            print(f"  (Pasta vazia ou erro: {e})")
        
        return True
        
    except dropbox.exceptions.AuthError:
        print("❌ Erro de autenticação: Token inválido ou expirado")
        print("Verifique se o token está correto e não expirou")
        return False
    except dropbox.exceptions.ApiError as e:
        print(f"❌ Erro da API do Dropbox: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def setup_dropbox():
    """Guia de configuração do Dropbox"""
    
    print("🚀 CONFIGURAÇÃO DO BACKUP AUTOMÁTICO PARA DROPBOX")
    print("=" * 50)
    
    print("\n📋 PASSO 1: Criar aplicação no Dropbox")
    print("1. Acesse: https://www.dropbox.com/developers/apps")
    print("2. Clique em 'Create app'")
    print("3. Escolha 'Scoped access'")
    print("4. Escolha 'App folder'")
    print("5. Nome sugerido: 'replit-relatorio-cirurgia'")
    
    print("\n🔐 PASSO 2: Configurar permissões")
    print("Na aba 'Permissions', marque:")
    print("- files.metadata.write")
    print("- files.content.write")
    print("- files.content.read")
    
    print("\n🎫 PASSO 3: Gerar token de acesso")
    print("1. Na aba 'Settings', role até 'OAuth 2'")
    print("2. Clique em 'Generate access token'")
    print("3. Copie o token gerado")
    
    print("\n⚙️ PASSO 4: Configurar no Replit")
    print("1. No Replit, clique no ícone de cadeado (Secrets)")
    print("2. Adicione uma nova secret:")
    print("   Key: DROPBOX_ACCESS_TOKEN")
    print("   Value: [cole o token aqui]")
    
    print("\n🧪 PASSO 5: Testar configuração")
    print("Execute este script novamente ou acesse /test_backup no seu app")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    print("🔧 CONFIGURAÇÃO DO BACKUP DROPBOX")
    print("=" * 40)
    
    # Verificar se já está configurado
    if os.environ.get('DROPBOX_ACCESS_TOKEN'):
        print("✅ Token encontrado, testando conexão...")
        success = test_dropbox_connection()
        if success:
            print("\n🎉 Configuração completa e funcionando!")
            print("O backup automático está pronto para uso.")
        else:
            print("\n❌ Há problemas com a configuração.")
            print("Verifique o token e tente novamente.")
    else:
        print("⚠️ Token não configurado.")
        setup_dropbox()