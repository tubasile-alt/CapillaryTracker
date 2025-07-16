#!/usr/bin/env python3
"""
Script para testar o sistema de administração
"""

import json
import os
import requests
from datetime import datetime

def test_admin_system():
    """Testa o sistema de administração"""
    
    print("=== TESTE DO SISTEMA DE ADMINISTRAÇÃO ===")
    print(f"Timestamp: {datetime.now()}")
    
    # 1. Verificar se o arquivo de configuração existe
    print("\n1. Verificando arquivo de configuração...")
    if os.path.exists('admin_config.json'):
        with open('admin_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ Arquivo encontrado com {len(config.get('unidades', []))} unidades")
        print(f"  Unidades: {config.get('unidades', [])}")
    else:
        print("❌ Arquivo admin_config.json não encontrado!")
        return False
    
    # 2. Testar endpoint de recarga
    print("\n2. Testando endpoint de recarga...")
    try:
        response = requests.get('http://localhost:5000/reload_config')
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Recarga bem-sucedida: {data.get('message', 'OK')}")
            print(f"  Unidades carregadas: {len(data.get('unidades', []))}")
        else:
            print(f"❌ Erro na recarga: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False
    
    # 3. Testar endpoint de médicos
    print("\n3. Testando endpoint de médicos...")
    try:
        response = requests.get('http://localhost:5000/get_medicos/São Paulo')
        if response.status_code == 200:
            data = response.json()
            medicos = data.get('medicos', [])
            print(f"✓ Médicos de São Paulo: {len(medicos)} encontrados")
            print(f"  Lista: {medicos}")
        else:
            print(f"❌ Erro ao buscar médicos: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False
    
    # 4. Testar endpoint de equipe
    print("\n4. Testando endpoint de equipe...")
    try:
        response = requests.get('http://localhost:5000/get_equipe/São Paulo')
        if response.status_code == 200:
            data = response.json()
            equipe = data.get('equipe', [])
            print(f"✓ Equipe de São Paulo: {len(equipe)} membros encontrados")
            print(f"  Lista: {equipe[:3]}{'...' if len(equipe) > 3 else ''}")
        else:
            print(f"❌ Erro ao buscar equipe: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False
    
    print("\n=== TESTE CONCLUÍDO COM SUCESSO! ===")
    print("O sistema de administração está funcionando corretamente.")
    print("Se você não vê as alterações na interface web, tente:")
    print("1. Fazer logout e login novamente no painel administrativo")
    print("2. Limpar o cache do navegador (Ctrl+F5)")
    print("3. Aguardar alguns segundos após fazer alterações")
    
    return True

if __name__ == "__main__":
    test_admin_system()