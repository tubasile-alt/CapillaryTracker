
import os
import shutil
import logging
import json
import pandas as pd

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def restore_deployment_data():
    """
    Restaura os dados do sistema após o deployment
    Prioriza dados em deploy_data, mas também verifica backups se necessário
    """
    try:
        restored_files = []
        expected_patient_count = 0
        
        # 1. Verificar se o diretório de dados de deploy existe
        deploy_data_dir = "deploy_data"
        if not os.path.exists(deploy_data_dir):
            logger.warning(f"⚠️ Diretório {deploy_data_dir} não encontrado. Verificando backups...")
        
        # 2. Verificar manifesto de deployment
        manifest_file = "deploy_manifest.json"
        if os.path.exists(manifest_file):
            with open(manifest_file, "r") as f:
                manifest = json.load(f)
            logger.info(f"Manifesto de deployment carregado: {manifest}")
            # Obter a contagem esperada de pacientes do manifesto
            expected_patient_count = manifest.get("patient_count", 0)
            if expected_patient_count > 0:
                logger.info(f"✓ De acordo com o manifesto, devemos restaurar {expected_patient_count} pacientes")
                print(f"\n==================================================")
                print(f"Verificando restauração de {expected_patient_count} pacientes")
                print(f"==================================================\n")
        else:
            logger.warning("⚠️ Manifesto de deployment não encontrado.")
            manifest = {"data_files": ["cirurgias.xlsx", "necroses.xlsx"], "include_data": True}
        
        # 3. Se include_data for False, não restaurar dados
        if not manifest.get("include_data", True):
            logger.info("Restauração de dados desativada no manifesto.")
            return True, []
        
        # 4. Restaurar cada arquivo de dados do deploy_data
        for file in manifest.get("data_files", []):
            deploy_file = os.path.join(deploy_data_dir, file)
            
            if os.path.exists(deploy_file):
                try:
                    df_deploy = pd.read_excel(deploy_file)
                    if len(df_deploy) > 0:
                        # Verificar se o arquivo atual existe e tem dados
                        current_has_data = False
                        if os.path.exists(file):
                            try:
                                df_current = pd.read_excel(file)
                                current_has_data = len(df_current) > 0
                                
                                # Se ambos têm dados, verificar qual tem mais registros
                                if current_has_data and len(df_current) > len(df_deploy):
                                    logger.warning(f"⚠️ Arquivo atual {file} tem mais registros ({len(df_current)}) que o backup de deploy ({len(df_deploy)}). Mantendo arquivo atual.")
                                    restored_files.append((file, "mantido", len(df_current)))
                                    continue
                            except:
                                pass
                        
                        # Restaurar arquivo
                        shutil.copy2(deploy_file, file)
                        logger.info(f"✅ Dados restaurados: {deploy_file} → {file} ({len(df_deploy)} registros)")
                        restored_files.append((file, "deploy_data", len(df_deploy)))
                    else:
                        logger.info(f"🔄 Arquivo {deploy_file} está vazio, verificando backups...")
                except Exception as e:
                    logger.error(f"⚠️ Erro ao ler {deploy_file}: {str(e)}")
            else:
                logger.warning(f"⚠️ Arquivo {deploy_file} não encontrado, verificando backups...")
            
            # 5. Se não restaurou do deploy_data, tentar restaurar do backup mais recente
            if not any(f[0] == file for f in restored_files):
                backup_dir = "data_backup"
                if os.path.exists(backup_dir):
                    # Encontrar o backup mais recente para este arquivo
                    base_name = os.path.splitext(file)[0]
                    backup_files = [f for f in os.listdir(backup_dir) if f.startswith(base_name)]
                    
                    if backup_files:
                        # Ordenar por data/hora no nome (mais recente primeiro)
                        backup_files.sort(reverse=True)
                        latest_backup = os.path.join(backup_dir, backup_files[0])
                        
                        try:
                            df_backup = pd.read_excel(latest_backup)
                            if len(df_backup) > 0:
                                # Restaurar do backup
                                shutil.copy2(latest_backup, file)
                                logger.info(f"✅ Dados restaurados do backup: {latest_backup} → {file} ({len(df_backup)} registros)")
                                restored_files.append((file, "backup", len(df_backup)))
                            else:
                                logger.warning(f"⚠️ Backup {latest_backup} está vazio")
                        except Exception as e:
                            logger.error(f"⚠️ Erro ao ler backup {latest_backup}: {str(e)}")
                
                if not any(f[0] == file for f in restored_files):
                    logger.warning(f"⚠️ Não foi possível restaurar dados para {file}")
        
        # 6. Verificar backup do checkpoint se nenhum dado foi restaurado
        if not restored_files:
            logger.warning("⚠️ Nenhum dado restaurado. Tentando restaurar do último checkpoint...")
            checkpoint_dir = "checkpoints"
            if os.path.exists(checkpoint_dir):
                checkpoints = sorted(os.listdir(checkpoint_dir), reverse=True)
                if checkpoints:
                    latest_checkpoint = os.path.join(checkpoint_dir, checkpoints[0])
                    for file in manifest.get("data_files", []):
                        checkpoint_file = os.path.join(latest_checkpoint, file)
                        if os.path.exists(checkpoint_file):
                            try:
                                df_cp = pd.read_excel(checkpoint_file)
                                if len(df_cp) > 0:
                                    shutil.copy2(checkpoint_file, file)
                                    logger.info(f"✅ Dados restaurados do checkpoint: {checkpoint_file} → {file} ({len(df_cp)} registros)")
                                    restored_files.append((file, "checkpoint", len(df_cp)))
                            except Exception as e:
                                logger.error(f"⚠️ Erro ao ler checkpoint {checkpoint_file}: {str(e)}")
        
        # Verificar se a restauração foi bem-sucedida
        success = len(restored_files) > 0
        
        # Verificar se a contagem de pacientes foi restaurada corretamente
        if success and expected_patient_count > 0:
            # Verificar quantos pacientes foram restaurados
            import pandas as pd
            actual_count = 0
            if os.path.exists("cirurgias.xlsx"):
                try:
                    df = pd.read_excel("cirurgias.xlsx")
                    actual_count = len(df)
                    
                    # Exibir resultado da verificação
                    if actual_count >= expected_patient_count:
                        logger.info(f"✅ Verificação concluída: {actual_count} pacientes restaurados (esperados: {expected_patient_count})")
                        print(f"\n==================================================")
                        print(f"✅ VERIFICAÇÃO CONCLUÍDA COM SUCESSO!")
                        print(f"✅ {actual_count} pacientes restaurados (esperados: {expected_patient_count})")
                        
                        # Mostrar os pacientes restaurados
                        print("\nPacientes restaurados:")
                        for i, row in df.iterrows():
                            nome = row.get('nome', 'Nome não disponível')
                            data = row.get('data', 'Data não disponível')
                            unidade = row.get('unidade', 'Unidade não disponível')
                            print(f"  {i+1}. {nome} ({unidade}) - {data}")
                        
                        print(f"==================================================\n")
                    else:
                        logger.warning(f"⚠️ Verificação concluída: {actual_count} pacientes restaurados, mas esperávamos {expected_patient_count}")
                        print(f"\n==================================================")
                        print(f"⚠️ VERIFICAÇÃO CONCLUÍDA COM AVISO!")
                        print(f"⚠️ {actual_count} pacientes restaurados, mas esperávamos {expected_patient_count}")
                        print(f"==================================================\n")
                except Exception as e:
                    logger.error(f"❌ Erro ao verificar contagem de pacientes: {str(e)}")
        
        return success, restored_files
        
    except Exception as e:
        logger.error(f"❌ Erro durante restauração dos dados: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False, []

if __name__ == "__main__":
    print("\n==================================================")
    print("🔄 INICIANDO RESTAURAÇÃO DE DADOS PÓS-DEPLOYMENT 🔄")
    print("==================================================\n")
    
    success = restore_deployment_data()
    
    if success:
        print("\n==================================================")
        print("✅ DADOS RESTAURADOS COM SUCESSO!")
        print("==================================================")
        print("O sistema está pronto para uso com os dados anteriores.")
    else:
        print("\n==================================================")
        print("❌ ERRO DURANTE RESTAURAÇÃO DOS DADOS!")
        print("==================================================")
        print("Verifique os logs para mais detalhes.")
