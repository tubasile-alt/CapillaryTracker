"""
Script para testar a funcionalidade de verificação de duplicatas
"""
import requests
import json
import sys
import time

def test_duplicate_check():
    """Testa o endpoint de verificação de duplicatas"""
    print("Iniciando teste de verificação de duplicatas...")
    
    # URL do endpoint
    base_url = "http://localhost:5000/check_duplicate"
    
    # Caso 1: Verificar paciente existente (Joao Silva na data 27/03/2025)
    params = {
        "nome": "Joao Silva",
        "data": "27/03/2025"
    }
    
    try:
        # Tentar conexão com o servidor
        print(f"Testando conexão com o servidor: {base_url}")
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("exists") == True:
                print("✅ Teste 1 passou: Duplicata corretamente identificada para Joao Silva em 27/03/2025")
            else:
                print("❌ Teste 1 falhou: Não identificou corretamente a duplicata")
                print(f"Resposta recebida: {result}")
        else:
            print(f"❌ Erro na requisição: {response.status_code}")
            print(f"Resposta: {response.text}")
    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
    
    # Caso 2: Verificar paciente não existente (Maria Oliveira na data 27/03/2025)
    params = {
        "nome": "Maria Oliveira",
        "data": "27/03/2025"
    }
    
    try:
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("exists") == False:
                print("✅ Teste 2 passou: Corretamente identificou que Maria Oliveira não existe em 27/03/2025")
            else:
                print("❌ Teste 2 falhou: Identificou incorretamente como duplicata")
                print(f"Resposta recebida: {result}")
        else:
            print(f"❌ Erro na requisição: {response.status_code}")
            print(f"Resposta: {response.text}")
    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
    
    # Caso 3: Formato de data inválido
    params = {
        "nome": "Joao Silva",
        "data": "2025-03-27"  # Formato incorreto (deveria ser DD/MM/AAAA)
    }
    
    try:
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            result = response.json()
            if "error" in result and "formato de data" in result.get("error", "").lower():
                print("✅ Teste 3 passou: Corretamente identificou formato de data inválido")
            else:
                print("❌ Teste 3 falhou: Não identificou formato de data inválido")
                print(f"Resposta recebida: {result}")
        else:
            print(f"❌ Erro na requisição: {response.status_code}")
            print(f"Resposta: {response.text}")
    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
    
    print("Testes de verificação de duplicatas concluídos.")

if __name__ == "__main__":
    # Dar um tempo para o servidor iniciar
    print("Aguardando servidor iniciar...")
    time.sleep(2)
    
    # Executar os testes
    test_duplicate_check()