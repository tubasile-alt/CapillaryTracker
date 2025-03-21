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
            import os
            # Configurar a variável de ambiente DATABASE_URL
            default_db_url = 'postgresql://neondb_owner:npg_BoiquUY6v8CN@ep-flat-salad-a4j7rvot.us-east-1.aws.neon.tech/neondb?sslmode=require'
            if 'DATABASE_URL' not in os.environ:
                os.environ['DATABASE_URL'] = default_db_url
                logger.info(f"⚠️ DATABASE_URL não encontrada. Usando configuração padrão para deploy: {default_db_url}")
            
            # Importar app após configurar a variável de ambiente
            from app import app, db, Surgery, UnitProgress
            
            logger.info(f"📌 URL do banco de dados: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            with app.app_context():
                # Limpar dados existentes
                logger.info("🗑️ Removendo registros existentes...")
                db.session.query(Surgery).delete()
                
                # Verificar se temos as unidades configuradas
                unit_count = db.session.query(UnitProgress).count()
                logger.info(f"Verificando unidades: {unit_count} unidades configuradas")
                
                if unit_count == 0:
                    # Configurar unidade Ribeirão Preto com meta de 30
                    logger.info("Configurando unidade Ribeirão Preto com meta de 30")
                    unit = UnitProgress(unidade="Ribeirão Preto", meta=30)
                    db.session.add(unit)
                    db.session.commit()

                # Recarregar dados do Excel
                df = pd.read_excel("cirurgias.xlsx")
                
                # Substituir NaN por 0 para colunas inteiras
                integer_columns = ['total_foliculos', 'frente', 'coroa', 'scalpe', 
                                 'peninsula_direita', 'peninsula_esquerda']
                df[integer_columns] = df[integer_columns].fillna(0).astype(int)
                
                # Substituir NaN por 0 para colunas float
                float_columns = ['tempo_cirurgia', 'densidade_scketh']
                df[float_columns] = df[float_columns].fillna(0.0).astype(float)
                
                # Substituir NaN por string vazia para colunas de texto
                text_columns = ['nome', 'unidade', 'medico', 'equipe', 'hora_cirurgia']
                df[text_columns] = df[text_columns].fillna('')
                
                for _, row in df.iterrows():
                    print(f"\nProcessando linha: {row}")
                    try:
                        surgery = Surgery(
                            data=pd.to_datetime(row['data']).date(),
                            nome=str(row['nome']),
                            unidade=str(row['unidade']),
                            medico=str(row['medico']),
                            equipe=str(row['equipe']),
                            hora_cirurgia=str(row['hora_cirurgia']),
                            tempo_cirurgia=float(row['tempo_cirurgia'] if pd.notna(row['tempo_cirurgia']) else 0),
                            total_foliculos=int(row['total_foliculos'] if pd.notna(row['total_foliculos']) else 0),
                            frente=int(row['frente'] if pd.notna(row['frente']) else 0),
                            densidade_scketh=float(row['densidade_scketh'] if pd.notna(row['densidade_scketh']) else 0),
                            coroa=int(row['coroa'] if pd.notna(row['coroa']) else 0),
                            scalpe=int(row['scalpe'] if pd.notna(row['scalpe']) else 0),
                            peninsula_direita=int(row['peninsula_direita'] if pd.notna(row['peninsula_direita']) else 0),
                            peninsula_esquerda=int(row['peninsula_esquerda'] if pd.notna(row['peninsula_esquerda']) else 0)
                        )
                        print("✅ Linha convertida com sucesso")
                    except Exception as e:
                        print(f"❌ Erro ao converter linha: {str(e)}")
                        raise
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