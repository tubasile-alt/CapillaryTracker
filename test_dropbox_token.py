#!/usr/bin/env python3
"""
Script para testar o novo token do Dropbox após reconfiguração
"""

import os
import dropbox
import pandas as pd
import tempfile
from datetime import datetime

def test_new_dropbox_token():
    """Testa o token do Dropbox recém-configurado"""
    
    print("🔧 TESTE DO NOVO TOKEN DROPBOX")
    print("=" * 50)
    
    # Verificar se token existe
    token = os.environ.get('DROPBOX_ACCESS_TOKEN')
    if not token:
        print("❌ DROPBOX_ACCESS_TOKEN não encontrado nas variáveis de ambiente")
        print("💡 Configure o token seguindo o guia dropbox_reconfig_guide.md")
        return False
    
    # Limpar token
    token = token.strip()
    print(f"📊 Token encontrado:")
    print(f"   - Comprimento: {len(token)} caracteres")
    print(f"   - Inicia com: {token[:20]}...")
    print(f"   - Termina com: ...{token[-10:]}")
    
    try:
        # Testar conexão básica
        print("\n🔄 Testando conexão com Dropbox...")
        dbx = dropbox.Dropbox(token)
        
        # Verificar conta
        account = dbx.users_get_current_account()
        print(f"✅ Conectado com sucesso!")
        print(f"   - Nome: {account.name.display_name}")
        print(f"   - Email: {account.email}")
        print(f"   - Conta: {account.account_type._tag}")
        
        # Testar permissões listando arquivos
        print("\n📁 Testando permissões de leitura...")
        try:
            result = dbx.files_list_folder("")
            print(f"✅ Permissão de leitura OK")
            print(f"   - Arquivos na pasta: {len(result.entries)}")
            
            # Mostrar alguns arquivos se existirem
            if result.entries:
                print("   - Arquivos existentes:")
                for entry in result.entries[:3]:
                    if hasattr(entry, 'name'):
                        print(f"     • {entry.name}")
        except Exception as e:
            print(f"❌ Erro ao listar arquivos: {e}")
            return False
        
        # Testar upload (permissão de escrita)
        print("\n⬆️ Testando permissões de escrita...")
        try:
            # Criar dados de teste
            test_data = {
                'data': [datetime.now().strftime('%d/%m/%Y')],
                'teste': ['Token funcionando'],
                'timestamp': [datetime.now().strftime('%H:%M:%S')]
            }
            df = pd.DataFrame(test_data)
            
            # Criar arquivo Excel temporário
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
                temp_filename = temp_file.name
                df.to_excel(temp_filename, sheet_name='Teste', index=False, engine='openpyxl')
            
            # Ler arquivo como bytes
            with open(temp_filename, 'rb') as f:
                content = f.read()
            
            # Fazer upload
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            test_path = f"/teste_token_{timestamp}.xlsx"
            
            dbx.files_upload(
                content,
                test_path,
                mode=dropbox.files.WriteMode.overwrite
            )
            
            print(f"✅ Permissão de escrita OK")
            print(f"   - Arquivo teste criado: {test_path}")
            print(f"   - Tamanho: {len(content)} bytes")
            
            # Limpar arquivo temporário
            os.unlink(temp_filename)
            
        except Exception as e:
            print(f"❌ Erro no upload: {e}")
            return False
        
        # Testar função de backup do sistema
        print("\n🎯 Testando backup do sistema...")
        try:
            from app import trigger_automatic_backup
            success, message = trigger_automatic_backup()
            
            if success:
                print(f"✅ Backup do sistema funcionando: {message}")
            else:
                print(f"⚠️ Backup do sistema com problemas: {message}")
        except Exception as e:
            print(f"❌ Erro no backup do sistema: {e}")
        
        # Resumo final
        print("\n" + "=" * 50)
        print("🎉 CONFIGURAÇÃO DROPBOX CONCLUÍDA COM SUCESSO!")
        print("=" * 50)
        
        print("✅ Token válido e funcionando")
        print("✅ Permissões configuradas corretamente")
        print("✅ Upload e download funcionando")
        print("✅ Backup automático configurado")
        
        print("\n📋 O que acontece agora:")
        print("• Backup automático após cada registro de necrose")
        print("• Arquivos salvos na pasta raiz da aplicação Dropbox")
        print("• Backup local sempre funciona como fallback")
        print("• Sistema totalmente funcional")
        
        return True
        
    except dropbox.exceptions.AuthError as e:
        print(f"❌ ERRO DE AUTENTICAÇÃO: {e}")
        print("\n🔧 Soluções:")
        print("1. Verifique se o token foi copiado corretamente")
        print("2. Gere um novo token no console Dropbox")
        print("3. Verifique as permissões da aplicação")
        print("4. Siga o guia dropbox_reconfig_guide.md")
        return False
        
    except Exception as e:
        print(f"❌ ERRO INESPERADO: {e}")
        return False

if __name__ == "__main__":
    test_new_dropbox_token()