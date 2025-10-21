#!/usr/bin/env python3
"""
Script de teste para o sistema de Estudo Científico
Valida filtros, métricas e cruzamento de dados
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_estudo_cientifico():
    """Testa o sistema de estudo científico"""
    
    print("=" * 60)
    print("TESTE DO SISTEMA DE ESTUDO CIENTÍFICO")
    print("=" * 60)
    print()
    
    # Criar sessão para manter autenticação
    session = requests.Session()
    
    # 1. Testar login
    print("1. Testando autenticação...")
    login_response = session.post(
        f"{BASE_URL}/estudo_cientifico/login",
        data={"password": "54321"},
        allow_redirects=False
    )
    
    if login_response.status_code in [302, 200]:
        print("   ✅ Login bem-sucedido!")
    else:
        print(f"   ❌ Falha no login: {login_response.status_code}")
        return
    
    print()
    
    # 2. Teste 1: Contar cirurgias em Ribeirão Preto com Tadalafila
    print("2. Teste 1: Cirurgias em Ribeirão Preto com Tadalafila")
    test_data_1 = {
        "surgeryFilters": [
            {"field": "unidade", "operator": "equals", "value": "Ribeirão Preto"},
            {"field": "tadalafila", "operator": "contains", "value": "Sim"}
        ],
        "necroseFilters": [],
        "cards": [
            {
                "title": "Cirurgias em Ribeirão Preto com Tadalafila",
                "metric": "count"
            },
            {
                "title": "Média de Folículos",
                "metric": "avg_foliculos"
            }
        ]
    }
    
    response_1 = session.post(
        f"{BASE_URL}/api/estudo_cientifico_data",
        json=test_data_1,
        headers={"Content-Type": "application/json"}
    )
    
    if response_1.status_code == 200:
        result_1 = response_1.json()
        print("   ✅ API respondeu com sucesso!")
        print(f"   📊 Resultados: {len(result_1.get('cards', []))} cards retornados")
        for card in result_1.get('cards', []):
            print(f"      - {card['title']}: {card['value']}")
            print(f"        {card['description']}")
    else:
        print(f"   ❌ Erro na API: {response_1.status_code}")
        print(f"      {response_1.text}")
    
    print()
    
    # 3. Teste 2: Taxa de necrose em Campinas
    print("3. Teste 2: Taxa de necrose em Campinas")
    test_data_2 = {
        "surgeryFilters": [
            {"field": "unidade", "operator": "equals", "value": "Campinas"}
        ],
        "necroseFilters": [
            {"field": "unidade", "operator": "equals", "value": "Campinas"}
        ],
        "cards": [
            {
                "title": "Total de Cirurgias em Campinas",
                "metric": "count"
            },
            {
                "title": "Casos de Necrose em Campinas",
                "metric": "necrose_count"
            },
            {
                "title": "Taxa de Necrose em Campinas",
                "metric": "necrose_rate"
            }
        ]
    }
    
    response_2 = session.post(
        f"{BASE_URL}/api/estudo_cientifico_data",
        json=test_data_2,
        headers={"Content-Type": "application/json"}
    )
    
    if response_2.status_code == 200:
        result_2 = response_2.json()
        print("   ✅ API respondeu com sucesso!")
        print(f"   📊 Resultados: {len(result_2.get('cards', []))} cards retornados")
        for card in result_2.get('cards', []):
            print(f"      - {card['title']}: {card['value']}")
            print(f"        {card['description']}")
            if card.get('details'):
                for key, val in card['details'].items():
                    print(f"          • {key}: {val}")
    else:
        print(f"   ❌ Erro na API: {response_2.status_code}")
        print(f"      {response_2.text}")
    
    print()
    
    # 4. Teste 3: Comparação de tempo e densidade
    print("4. Teste 3: Métricas agregadas de todas as cirurgias")
    test_data_3 = {
        "surgeryFilters": [],
        "necroseFilters": [],
        "cards": [
            {
                "title": "Total de Cirurgias Cadastradas",
                "metric": "count"
            },
            {
                "title": "Média Geral de Folículos",
                "metric": "avg_foliculos"
            },
            {
                "title": "Média de Tempo de Cirurgia",
                "metric": "avg_tempo"
            },
            {
                "title": "Média de Densidade",
                "metric": "avg_densidade"
            }
        ]
    }
    
    response_3 = session.post(
        f"{BASE_URL}/api/estudo_cientifico_data",
        json=test_data_3,
        headers={"Content-Type": "application/json"}
    )
    
    if response_3.status_code == 200:
        result_3 = response_3.json()
        print("   ✅ API respondeu com sucesso!")
        print(f"   📊 Resultados: {len(result_3.get('cards', []))} cards retornados")
        for card in result_3.get('cards', []):
            print(f"      - {card['title']}: {card['value']}")
            print(f"        {card['description']}")
    else:
        print(f"   ❌ Erro na API: {response_3.status_code}")
        print(f"      {response_3.text}")
    
    print()
    print("=" * 60)
    print("TESTES CONCLUÍDOS")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_estudo_cientifico()
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao servidor Flask.")
        print("   Certifique-se de que o servidor está rodando em http://localhost:5000")
    except Exception as e:
        print(f"❌ Erro durante os testes: {str(e)}")
        import traceback
        traceback.print_exc()
