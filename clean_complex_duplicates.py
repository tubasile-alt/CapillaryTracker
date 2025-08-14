#!/usr/bin/env python3
"""
Script para limpar duplicatas complexas restantes
Abordagem mais agressiva para remover padrões repetitivos
"""

import os
import sys
from sqlalchemy import create_engine, text
import logging
import re
from collections import OrderedDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def advanced_clean_equipe_string(equipe_str):
    """Limpeza avançada para remover padrões repetitivos complexos"""
    if not equipe_str:
        return equipe_str
    
    # Dividir por vírgula
    nomes = [nome.strip() for nome in equipe_str.split(',')]
    
    # Remover elementos extras e técnicos
    nomes_filtrados = []
    for nome in nomes:
        nome_clean = nome.strip()
        
        # Skip técnicos extras, parenteses com extra, etc
        if any(skip_word in nome_clean.lower() for skip_word in [
            'técnica extra', 'extra', '(extra)', 'técnico', 'auxiliar'
        ]):
            continue
            
        # Remover números e caracteres especiais do início
        nome_clean = re.sub(r'^[^a-zA-ZÀ-ÿ]*', '', nome_clean)
        nome_clean = re.sub(r'[^a-zA-ZÀ-ÿ\s]*$', '', nome_clean)
        
        if nome_clean and len(nome_clean) > 1:
            nomes_filtrados.append(nome_clean)
    
    # Usar OrderedDict para manter ordem e remover duplicatas
    nomes_unicos = list(OrderedDict.fromkeys(nomes_filtrados))
    
    # Se ainda há muitos nomes, pode ser uma repetição - detectar padrões
    if len(nomes_unicos) > 8:
        # Tentar detectar se há um padrão repetitivo
        metade = len(nomes_unicos) // 2
        primeira_metade = nomes_unicos[:metade]
        segunda_metade = nomes_unicos[metade:metade*2]
        
        if primeira_metade == segunda_metade:
            # Padrão detectado, usar apenas a primeira metade
            nomes_unicos = primeira_metade
    
    return ', '.join(nomes_unicos)

def clean_complex_duplicates():
    """Remove duplicatas complexas restantes"""
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL não encontrada!")
        return False
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            logger.info("🔍 Segunda rodada: limpando duplicatas complexas restantes...")
            
            # Buscar registros ainda problemáticos
            select_query = text("""
                SELECT id, unidade, equipe 
                FROM surgery 
                WHERE (equipe LIKE '%,%,%,%,%' OR LENGTH(equipe) > 50)
                ORDER BY unidade, LENGTH(equipe) DESC
            """)
            
            result = conn.execute(select_query)
            records = result.fetchall()
            
            logger.info(f"📊 Encontrados {len(records)} registros complexos restantes")
            
            updates_count = 0
            for record in records:
                old_equipe = record.equipe
                new_equipe = advanced_clean_equipe_string(old_equipe)
                
                if old_equipe != new_equipe and len(new_equipe) < len(old_equipe):
                    update_query = text("""
                        UPDATE surgery 
                        SET equipe = :new_equipe 
                        WHERE id = :record_id
                    """)
                    
                    conn.execute(update_query, {
                        'new_equipe': new_equipe,
                        'record_id': record.id
                    })
                    
                    updates_count += 1
                    
                    if updates_count <= 5:
                        logger.info(f"✅ {record.unidade} ID {record.id}:")
                        logger.info(f"   ANTES: {old_equipe[:100]}...")
                        logger.info(f"   DEPOIS: {new_equipe}")
            
            conn.commit()
            
            logger.info(f"🎉 Segunda rodada concluída! {updates_count} registros atualizados")
            
            # Verificação final
            final_check = text("""
                SELECT unidade, COUNT(*) as restantes
                FROM surgery 
                WHERE (equipe LIKE '%,%,%,%,%' OR LENGTH(equipe) > 50)
                GROUP BY unidade
                ORDER BY restantes DESC
            """)
            
            result = conn.execute(final_check)
            remaining = result.fetchall()
            
            if remaining:
                logger.warning("⚠️ Duplicações complexas restantes:")
                for row in remaining:
                    logger.warning(f"   {row.unidade}: {row.restantes}")
            else:
                logger.info("✅ Todas as duplicações complexas foram removidas!")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erro: {str(e)}")
        return False

if __name__ == '__main__':
    success = clean_complex_duplicates()
    if success:
        print("✅ Limpeza de duplicatas complexas concluída!")
    else:
        print("❌ Falha na limpeza!")
        sys.exit(1)