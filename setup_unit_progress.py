#!/usr/bin/env python
"""
Script para configurar a tabela UnitProgress com as metas de unidades.
Este script verifica se as unidades já existem e adiciona apenas as que não existirem.
"""

import os
import logging
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurar a variável de ambiente DATABASE_URL antes de importar a aplicação
default_db_url = 'postgresql://neondb_owner:npg_BoiquUY6v8CN@ep-flat-salad-a4j7rvot.us-east-1.aws.neon.tech/neondb?sslmode=require'
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = default_db_url
    logger.info(f"⚠️ DATABASE_URL não encontrada. Usando configuração padrão para deploy: {default_db_url}")

# Importar app após configurar a variável de ambiente
from app import app, db, UnitProgress

def setup_unit_progress():
    """Configurar a tabela UnitProgress com metas de unidades"""
    try:
        # Lista de unidades com suas metas
        unidades = {
            "Ribeirão Preto": 30,
            "São Paulo": 20,
            "Campinas": 25
        }
        
        with app.app_context():
            # Verificar quais unidades já existem
            existing_units = {unit.unidade: unit.meta for unit in UnitProgress.query.all()}
            logger.info(f"Unidades existentes: {existing_units}")
            
            # Adicionar apenas as unidades que não existem
            added_units = []
            for unidade, meta in unidades.items():
                if unidade not in existing_units:
                    unit = UnitProgress(unidade=unidade, meta=meta)
                    db.session.add(unit)
                    added_units.append(f"{unidade} (meta: {meta})")
            
            # Commit se houver unidades para adicionar
            if added_units:
                db.session.commit()
                logger.info(f"✅ Adicionadas {len(added_units)} unidades: {', '.join(added_units)}")
            else:
                logger.info("✅ Todas as unidades já estão configuradas.")
            
            # Mostrar configuração final
            final_units = {unit.unidade: unit.meta for unit in UnitProgress.query.all()}
            logger.info(f"Configuração final: {final_units}")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erro ao configurar unidades: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("\n==================================================")
    print("🔄 CONFIGURANDO METAS DE UNIDADES 🔄")
    print("==================================================\n")
    
    success = setup_unit_progress()
    
    if success:
        print("\n==================================================")
        print("✅ CONFIGURAÇÃO DE UNIDADES CONCLUÍDA!")
        print("==================================================")
    else:
        print("\n==================================================")
        print("❌ ERRO AO CONFIGURAR UNIDADES!")
        print("==================================================")