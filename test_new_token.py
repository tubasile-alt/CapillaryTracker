#!/usr/bin/env python3
"""
Script para testar o novo token do Dropbox diretamente
"""

import dropbox
import pandas as pd
import tempfile
import os
from datetime import datetime

# Token fornecido pelo usuário
NEW_TOKEN = "sl.u.AFzLVojrAeZc6aTkIs7vq4_Tpc35hrxsfV8tJNLv5ptz9n3eNh6MaTK0bcWBDDW5PZ-70KpoL7N55_fAeLR80Hs3ezUzh6Jo9DVtJopsGtr5NvgAtpL_00U567pZcvVNC04-0kofiz8Gh-Otzu7XcmIUOORXfs9G3IxBfqRDupuaL4sa91Uhn5SNAmwIfw_7xbqYLOA7SK3V2LRDAwI9f7v-GeWQicEIFPtDEkoaPrVe4eK2cZg2OsxXnLl9rWX5FiJJuTSoXfauixIHWbTHtdIHSa7O4RyDG8Ba6ImB2EHuFBRnLL27_ha_4yQTPG_vji3RpYYpuJqroX62KXKmUUihhbwrCiJrrhGXQBo_3EHe47Nq0rO_aN1kTtj0PPcFAXqMt3_T4QgMvd8sfrkovauoAnOU2bBkJahQViYIpFB5jLBEATijJGlhtHocLCgXVWSDHAHkhxH97NaL-v7zDJzyQKnSyzIialPSmX6XInXhuLfEmD4LyTI-naEKb7toi7XudfjNaYHVTdBgmUYPOnifSs8D5fip7AV6NjQRvgJznR0k8hSwOws_s2KoCKpupwfchpzsHTQ8PNLLz3pto-_Tvv7FpqOBeMc-5a7fVgnANxbYvSu2pyaYR37LEnD64HrXtfgN6N5cpW7toFhol_D6bZYrE4FBZU55q_YBn8h7tQUB_U9ruwNCFHgj222qO0xRxZ6vCogl0g4VPwKdwkfXDfpYP5rZ6s048l8cjKN4oo516z8RFPq2fFxzyPmd3vgxH6yGQriZePOt1HnO2ePeisjCHBT4CFVLUOTUxh7clEdgBc0aPT14Xt7uwKCddfbOQEbGAZp6Eye9T_C7eGG9gEEQ-hcYxqjYizTFkOOrygkeLI80CnztFJDFa13AfImYUBcElfWiA5ReIZQFUNsPSsmUtbzERXjMNlwU_eRjuP071oCmPuYkPIRJBy1_fJSAzTIf77ZqxcPCxDtZ2_rjZDrxt3hRKg0hDL6HeRfV0iR2GHBFADdhKoSGIQWx97hb_DAb_76I7nq88yuB3tdWOHIgYBcu5l_w8Qyx4MPa51DmUYdbK0BeR4DG5HKZWNliLiee8R_wSZDNgidWonkjvIe9Jq66EVeCmq4kiiSgtQPtdKlDNsdvbV0UvgB71N1Cacv8kq9scs1aNFUtuUXz1H62WUQ1kFGFHvX7FP4O6diqtfdKwojstZrLstT5Z4rkEu0_j_rRO1SCNZo4XKGCu4Vh9LH_iXxmTBEpI3BiaJBSkAPEc9aslrSPktcu66iDJJ_zBVCT4CzKEbM5uT64"

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