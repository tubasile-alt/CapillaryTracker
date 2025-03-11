
import os
import pandas as pd
import logging
from datetime import datetime
import shutil

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def importar_dados_rapidos():
    """Importa dados para o sistema a partir de arquivos anexados ou de backup"""
    try:
        print("\n==================================================")
        print("🔄 INICIANDO IMPORTAÇÃO RÁPIDA 🔄")
        print("==================================================\n")
        
        # Verificar fontes de dados possíveis
        sources = []
        
        # 1. Verificar dados anexados (relatorio_cirurgias.xlsx)
        if os.path.exists("attached_assets/relatorio_cirurgias.xlsx"):
            sources.append(("attached_assets/relatorio_cirurgias.xlsx", "arquivo anexado"))
        
        # 2. Verificar dados de deployment
        if os.path.exists("deploy_data/cirurgias.xlsx"):
            sources.append(("deploy_data/cirurgias.xlsx", "dados de deployment"))
        
        # 3. Verificar backups mais recentes
        backup_dir = "data_backup"
        if os.path.exists(backup_dir):
            backup_files = [f for f in os.listdir(backup_dir) if f.startswith("cirurgias_") and f.endswith(".xlsx")]
            if backup_files:
                # Ordenar por data (mais recente primeiro)
                backup_files.sort(reverse=True)
                sources.append((os.path.join(backup_dir, backup_files[0]), "backup mais recente"))
        
        if not sources:
            print("❌ Nenhuma fonte de dados encontrada para importação!")
            return False
        
        # Fazer backup dos dados atuais antes de substituir
        if os.path.exists("cirurgias.xlsx"):
            os.makedirs("data_backup", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"data_backup/cirurgias_{timestamp}.xlsx"
            shutil.copy2("cirurgias.xlsx", backup_filename)
            print(f"✅ Backup dos dados atuais criado: {backup_filename}")
        
        # Importar da primeira fonte disponível
        source_path, source_type = sources[0]
        
        # Ler e salvar os dados
        df = pd.read_excel(source_path)
        df.to_excel("cirurgias.xlsx", index=False)
        
        print(f"✅ Dados importados com sucesso de {source_type}!")
        print(f"   Fonte: {source_path}")
        print(f"   Registros importados: {len(df)}")
        
        # Listar pacientes importados (até 10)
        if len(df) > 0:
            print("\nPacientes importados:")
            for i, (idx, row) in enumerate(df.iterrows(), 1):
                if i <= 10:  # Mostrar apenas os 10 primeiros
                    data = row.get('data', '')
                    if isinstance(data, pd.Timestamp):
                        data = data.strftime('%Y-%m-%d')
                    print(f"  {i}. {row.get('nome', 'N/A')} ({row.get('unidade', 'N/A')}) - {data}")
                else:
                    print(f"  ... e mais {len(df) - 10} pacientes")
                    break
        
        print("\n==================================================")
        print("✅ IMPORTAÇÃO RÁPIDA CONCLUÍDA COM SUCESSO!")
        print("==================================================")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE A IMPORTAÇÃO: {str(e)}")
        logger.error(f"Erro na importação rápida: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    importar_dados_rapidos()
