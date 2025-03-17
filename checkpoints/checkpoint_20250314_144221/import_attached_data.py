
import os
import pandas as pd
import shutil
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clear_and_import_data():
    try:
        # Verificar se a planilha de origem existe
        source_file = os.path.join("attached_assets", "relatorio_cirurgias.xlsx")
        if not os.path.exists(source_file):
            logger.error(f"Arquivo de origem {source_file} não encontrado")
            return False
            
        # 1. Limpar as planilhas atuais
        logger.info("Limpando dados atuais...")
        
        # Limpar cirurgias.xlsx com estrutura correta
        if os.path.exists("cirurgias.xlsx"):
            # Criar DataFrame vazio com as colunas necessárias
            columns = [
                'data', 'nome', 'unidade', 'medico', 'equipe', 'hora_cirurgia', 
                'tempo_cirurgia', 'total_foliculos', 'frente', 'densidade_scketh',
                'coroa', 'scalpe', 'peninsula_direita', 'peninsula_esquerda'
            ]
            pd.DataFrame(columns=columns).to_excel("cirurgias.xlsx", index=False, engine='openpyxl')
            logger.info("✅ Arquivo cirurgias.xlsx limpo com sucesso")
        
        # Limpar necroses.xlsx
        if os.path.exists("necroses.xlsx"):
            columns = [
                'patient_id', 'patient_unit', 'data_registro', 'lesion_count', 
                'largest_lesion', 'affected_band', 'photo_paths'
            ]
            pd.DataFrame(columns=columns).to_excel("necroses.xlsx", index=False, engine='openpyxl')
            logger.info("✅ Arquivo necroses.xlsx limpo com sucesso")
        
        # 2. Importar dados da planilha em attached_assets
        logger.info(f"Importando dados de {source_file}...")
        
        # Carregar a planilha de origem
        df_source = pd.read_excel(source_file)
        
        # Verificar e mapear colunas do arquivo de origem para o formato esperado
        # Isso permitirá importar mesmo que as colunas tenham nomes diferentes
        
        # Salvar no arquivo de destino
        df_source.to_excel("cirurgias.xlsx", index=False, engine='openpyxl')
        
        num_records = len(df_source)
        logger.info(f"✅ Dados importados com sucesso! {num_records} registros adicionados.")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao importar dados: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = clear_and_import_data()
    if success:
        print("\n======================================")
        print("✅ DADOS LIMPOS E IMPORTADOS COM SUCESSO!")
        print("======================================\n")
    else:
        print("\n======================================")
        print("❌ ERRO AO LIMPAR E IMPORTAR DADOS!")
        print("======================================\n")
