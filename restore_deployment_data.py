
import os
import shutil
import logging
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def restore_deployment_data():
    """Restaura dados de deploy_data após deployment"""
    try:
        restored_files = []
        deploy_data_dir = "deploy_data"

        # Verificar se diretório deploy_data existe
        if not os.path.exists(deploy_data_dir):
            logger.warning(f"⚠️ Diretório {deploy_data_dir} não encontrado.")
            return False, []

        # Carregar manifesto
        manifest_file = "deploy_manifest.json"
        if os.path.exists(manifest_file):
            import json
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            logger.info(f"✅ Manifesto carregado: {manifest}")
        else:
            logger.warning("⚠️ Manifesto não encontrado.")
            manifest = {"data_files": ["cirurgias.xlsx"], "include_data": True}

        if not manifest.get("include_data", True):
            logger.info("Restauração de dados desativada no manifesto.")
            return True, []

        for file in manifest.get("data_files", []):
            deploy_file = os.path.join(deploy_data_dir, file)

            if os.path.exists(deploy_file):
                try:
                    df_deploy = pd.read_excel(deploy_file)
                    if len(df_deploy) > 0:
                        # Fazer backup do arquivo atual se existir
                        if os.path.exists(file):
                            backup_dir = "data_backup"
                            os.makedirs(backup_dir, exist_ok=True)
                            backup_file = f"{backup_dir}/{os.path.splitext(file)[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                            shutil.copy2(file, backup_file)
                            logger.info(f"✅ Backup criado: {backup_file}")

                            # Comparar dados antes de restaurar
                            df_local = pd.read_excel(file)
                            if len(df_local) > len(df_deploy):
                                logger.warning(f"⚠️ Arquivo local tem mais registros ({len(df_local)}) que deploy ({len(df_deploy)})")
                                continue

                        # Restaurar arquivo
                        shutil.copy2(deploy_file, file)
                        logger.info(f"✅ Dados restaurados: {deploy_file} → {file} ({len(df_deploy)} registros)")
                        restored_files.append((file, "deploy_data", len(df_deploy)))
                except Exception as e:
                    logger.error(f"⚠️ Erro ao processar {deploy_file}: {str(e)}")

        # Verificar se a restauração foi bem-sucedida
        if restored_files:
            from app import app, db, Surgery
            with app.app_context():
                # Limpar dados existentes
                db.session.query(Surgery).delete()
                
                # Recarregar dados do Excel
                df = pd.read_excel("cirurgias.xlsx")
                for _, row in df.iterrows():
                    surgery = Surgery(
                        data=pd.to_datetime(row['data']).date(),
                        nome=row['nome'],
                        unidade=row['unidade'],
                        medico=row['medico'],
                        equipe=row['equipe'],
                        hora_cirurgia=row['hora_cirurgia'],
                        tempo_cirurgia=float(row['tempo_cirurgia']),
                        total_foliculos=int(row['total_foliculos']),
                        frente=int(row['frente']),
                        densidade_scketh=float(row['densidade_scketh']),
                        coroa=int(row['coroa']),
                        scalpe=int(row['scalpe']),
                        peninsula_direita=int(row['peninsula_direita']),
                        peninsula_esquerda=int(row['peninsula_esquerda'])
                    )
                    db.session.add(surgery)
                db.session.commit()

        return True, restored_files

    except Exception as e:
        logger.error(f"❌ Erro na restauração dos dados: {str(e)}")
        return False, []

if __name__ == "__main__":
    success, files = restore_deployment_data()
    if success and files:
        print("\n✅ Dados restaurados com sucesso!")
        for f in files:
            print(f"- {f[0]}: {f[2]} registros")
    else:
        print("\n❌ Erro na restauração dos dados")
