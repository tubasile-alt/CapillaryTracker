#!/usr/bin/env python3
"""
Script para testar o novo token do Dropbox diretamente
"""

import dropbox
import pandas as pd
import tempfile
import os
from datetime import datetime

# Usar token das variáveis de ambiente
import os
NEW_TOKEN = os.environ.get('DROPBOX_ACCESS_TOKEN')

def test_new_dropbox_token():
    """Testa o novo token do Dropbox"""
    
    print("🔧 TESTANDO NOVO TOKEN DO DROPBOX")
    print("=" * 50)
    
    try:
        # Limpar o token
        token = NEW_TOKEN.strip()
        print(f"📊 Token: comprimento = {len(token)}, inicia com = {token[:20]}...")
        
        # Testar conexão
        print("🔄 Testando conexão com Dropbox...")
        dbx = dropbox.Dropbox(token)
        
        # Verificar conta
        account = dbx.users_get_current_account()
        print(f"✅ Conectado como: {account.name.display_name}")
        print(f"✅ Email: {account.email}")
        
        # Criar dados de teste
        test_data = {
            'data': [datetime.now().strftime('%d/%m/%Y')],
            'nome': ['Teste Backup'],
            'unidade': ['Teste'],
            'medico': ['Dr. Teste'],
            'equipe': ['Equipe Teste'],
            'total_foliculos': [1000]
        }
        df = pd.DataFrame(test_data)
        
        # Criar arquivo Excel temporário
        print("📄 Criando arquivo Excel de teste...")
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_filename = temp_file.name
            df.to_excel(temp_filename, sheet_name='Teste', index=False, engine='openpyxl')
        
        # Ler o arquivo Excel como bytes
        with open(temp_filename, 'rb') as f:
            excel_content = f.read()
        
        # Remover arquivo temporário
        os.unlink(temp_filename)
        
        # Testar upload
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        test_path = f"/teste_backup_{timestamp}.xlsx"
        
        print(f"⬆️ Fazendo upload de teste: {test_path}")
        dbx.files_upload(
            excel_content,
            test_path,
            mode=dropbox.files.WriteMode.overwrite,
            autorename=False
        )
        
        print(f"✅ Upload realizado com sucesso!")
        
        # Listar arquivos
        print("📁 Listando arquivos na pasta:")
        try:
            entries = dbx.files_list_folder("").entries
            for entry in entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    print(f"  📄 {entry.name} ({entry.size} bytes)")
        except Exception as e:
            print(f"  (Erro ao listar: {e})")
        
        print("\n🎉 SUCESSO! O token está funcionando perfeitamente!")
        print("\nPróximos passos:")
        print("1. Vá nas Secrets do Replit")
        print("2. Edite a secret DROPBOX_ACCESS_TOKEN")
        print("3. Cole o novo token (que você já forneceu)")
        print("4. Reinicie o servidor Flask")
        
        return True
        
    except dropbox.exceptions.AuthError as e:
        print(f"❌ Erro de autenticação: {e}")
        print("Token inválido ou sem as permissões necessárias")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    test_new_dropbox_token()