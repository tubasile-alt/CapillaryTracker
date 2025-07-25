#!/usr/bin/env python3
"""
Verificar status atual do token Dropbox
"""

import os

def check_current_token():
    """Verifica o status do token atual"""
    
    print("🔍 VERIFICANDO TOKEN ATUAL")
    print("=" * 40)
    
    token = os.environ.get('DROPBOX_ACCESS_TOKEN')
    
    if not token:
        print("❌ DROPBOX_ACCESS_TOKEN não encontrado")
        print("💡 Configure o token nas Secrets do Replit")
        return False
    
    # Limpar e analisar token
    token = token.strip()
    
    print(f"📊 Informações do token:")
    print(f"   Comprimento: {len(token)} caracteres")
    print(f"   Inicia com: {token[:15]}...")
    print(f"   Termina com: ...{token[-10:]}")
    
    # Verificar formato básico
    if token.startswith('sl.'):
        print("✅ Formato correto (inicia com 'sl.')")
    else:
        print("❌ Formato incorreto (deve iniciar com 'sl.')")
        return False
    
    if len(token) > 1000:
        print("✅ Comprimento adequado")
    else:
        print("⚠️ Token parece muito curto")
        return False
    
    # Testar conexão básica
    try:
        import dropbox
        print("\n🔄 Testando conexão...")
        dbx = dropbox.Dropbox(token)
        account = dbx.users_get_current_account()
        print(f"✅ SUCESSO! Conectado como: {account.email}")
        return True
    except Exception as e:
        print(f"❌ FALHA na conexão: {e}")
        print("\n🔧 Possíveis soluções:")
        print("1. Verifique se copiou o token completo")
        print("2. Gere um novo token no Dropbox Developer Console")
        print("3. Verifique as permissões da aplicação")
        return False

if __name__ == "__main__":
    check_current_token()