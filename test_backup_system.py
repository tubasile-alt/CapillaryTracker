#!/usr/bin/env python3
"""
Script para testar o sistema de backup automático
"""

import requests
import json
from datetime import datetime

def test_automatic_backup():
    """Testa o sistema de backup automático"""
    
    print("🔧 TESTE DO SISTEMA DE BACKUP AUTOMÁTICO")
    print("=" * 50)
    
    # URL base do servidor
    base_url = "http://localhost:5000"
    
    # 1. Testar backup manual
    print("\n1️⃣ Testando backup manual...")
    try:
        response = requests.get(f"{base_url}/test_backup", timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Backup manual: {result.get('message')}")
            else:
                print(f"❌ Backup manual falhou: {result.get('message')}")
        else:
            print(f"❌ Erro na requisição: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    # 2. Verificar arquivos de backup local
    print("\n2️⃣ Verificando backups locais...")
    try:
        import os
        backup_dir = 'data_backup'
        if os.path.exists(backup_dir):
            files = [f for f in os.listdir(backup_dir) if f.endswith('.xlsx')]
            files.sort(reverse=True)  # Mais recentes primeiro
            
            print(f"📁 Diretório: {backup_dir}")
            print(f"📊 Total de arquivos: {len(files)}")
            
            if files:
                print("📋 Últimos 5 backups:")
                for i, file in enumerate(files[:5], 1):
                    file_path = os.path.join(backup_dir, file)
                    size = os.path.getsize(file_path) / 1024  # KB
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    print(f"  {i}. {file}")
                    print(f"     💾 {size:.1f} KB | 📅 {mtime.strftime('%d/%m/%Y %H:%M')}")
            else:
                print("⚠️ Nenhum arquivo de backup encontrado")
        else:
            print(f"⚠️ Diretório {backup_dir} não existe")
    except Exception as e:
        print(f"❌ Erro ao verificar backups locais: {e}")
    
    # 3. Verificar configuração do Dropbox
    print("\n3️⃣ Verificando configuração Dropbox...")
    try:
        import os
        token = os.environ.get('DROPBOX_ACCESS_TOKEN')
        if token:
            print(f"✅ Token configurado (comprimento: {len(token)})")
            print(f"🔑 Início do token: {token[:10]}...")
            
            # Testar conexão básica
            try:
                import dropbox
                dbx = dropbox.Dropbox(token)
                account = dbx.users_get_current_account()
                print(f"✅ Conexão Dropbox OK: {account.email}")
            except Exception as e:
                print(f"❌ Erro de conexão Dropbox: {e}")
        else:
            print("⚠️ Token Dropbox não configurado")
    except Exception as e:
        print(f"❌ Erro ao verificar Dropbox: {e}")
    
    # 4. Testar uma operação que deveria disparar backup
    print("\n4️⃣ Simulando registro que dispara backup...")
    print("(Este teste requer uma operação real de registro)")
    print("💡 Dica: Registre uma necrose para testar o backup automático")
    
    # 5. Resumo e recomendações
    print("\n" + "=" * 50)
    print("📋 RESUMO E RECOMENDAÇÕES:")
    print("=" * 50)
    
    print("🔄 Sistema de backup configurado com:")
    print("  • Backup local em data_backup/ (sempre ativo)")
    print("  • Backup Dropbox (se token válido)")
    print("  • Disparo automático após registro de necrose")
    
    print("\n💡 Para ativar backup Dropbox:")
    print("  1. Renove o token em https://dropbox.com/developers/apps")
    print("  2. Atualize DROPBOX_ACCESS_TOKEN nas Secrets")
    print("  3. Reinicie o servidor")
    
    print("\n🧪 Para testar:")
    print("  • Acesse /test_backup para teste manual")
    print("  • Registre uma necrose para testar automático")
    print("  • Verifique data_backup/ para arquivos locais")

if __name__ == "__main__":
    test_automatic_backup()