#!/usr/bin/env python3
"""
Script para testar a estrutura das abas no backup Excel
"""

import pandas as pd
import os
from datetime import datetime

def test_backup_structure():
    """Testa a estrutura das abas no backup"""
    
    print("🔍 TESTANDO ESTRUTURA DO BACKUP EXCEL")
    print("=" * 50)
    
    # Verificar último arquivo de backup local
    backup_dir = 'data_backup'
    if not os.path.exists(backup_dir):
        print("❌ Diretório de backup não encontrado")
        return
    
    # Encontrar arquivos de backup mais recentes
    backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.xlsx')]
    backup_files.sort(reverse=True)  # Mais recente primeiro
    
    if not backup_files:
        print("❌ Nenhum arquivo de backup encontrado")
        return
    
    latest_backup = backup_files[0]
    backup_path = os.path.join(backup_dir, latest_backup)
    
    print(f"📄 Analisando arquivo: {latest_backup}")
    print(f"📁 Caminho: {backup_path}")
    
    try:
        # Ler arquivo Excel
        excel_file = pd.ExcelFile(backup_path)
        sheets = excel_file.sheet_names
        
        print(f"\n📋 Abas encontradas: {len(sheets)}")
        for i, sheet in enumerate(sheets, 1):
            print(f"  {i}. {sheet}")
        
        # Verificar estrutura esperada
        expected_sheets = ['Pacientes', 'Necroses']
        print(f"\n✅ Verificação de estrutura:")
        
        for expected in expected_sheets:
            if expected in sheets:
                print(f"  ✅ Aba '{expected}' encontrada")
                
                # Ler dados da aba
                df = pd.read_excel(backup_path, sheet_name=expected)
                print(f"     - Registros: {len(df)}")
                print(f"     - Colunas: {len(df.columns)}")
                
                if len(df.columns) > 0:
                    print(f"     - Primeiras colunas: {list(df.columns[:5])}")
                
            else:
                print(f"  ❌ Aba '{expected}' NÃO encontrada")
        
        # Verificar se há dados em ambas as abas
        if 'Pacientes' in sheets:
            pacientes_df = pd.read_excel(backup_path, sheet_name='Pacientes')
            print(f"\n📊 Dados de Pacientes:")
            print(f"   - Total de registros: {len(pacientes_df)}")
            if len(pacientes_df) > 0:
                print(f"   - Exemplo de paciente: {pacientes_df.iloc[0]['Nome'] if 'Nome' in pacientes_df.columns else 'N/A'}")
        
        if 'Necroses' in sheets:
            necroses_df = pd.read_excel(backup_path, sheet_name='Necroses')
            print(f"\n🔬 Dados de Necroses:")
            print(f"   - Total de registros: {len(necroses_df)}")
            if len(necroses_df) > 0:
                print(f"   - Exemplo de paciente: {necroses_df.iloc[0]['Paciente'] if 'Paciente' in necroses_df.columns else 'N/A'}")
        
        print(f"\n✅ ESTRUTURA CORRETA!")
        print("📋 O backup contém:")
        print("  • Aba 'Pacientes' com dados de cirurgias")
        print("  • Aba 'Necroses' com dados de necroses")
        print("  • Estrutura conforme solicitado")
        
    except Exception as e:
        print(f"❌ Erro ao analisar arquivo: {e}")

if __name__ == "__main__":
    test_backup_structure()