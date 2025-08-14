#!/usr/bin/env python3
"""
Script para limpar duplicatas no campo 'equipe' de TODAS as unidades
Remove strings duplicadas e normaliza nomes
"""

import os
import sys
from sqlalchemy import create_engine, text
import logging
import re

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_equipe_string(equipe_str):
    """Limpa e normaliza string de equipe"""
    if not equipe_str:
        return equipe_str
    
    # Dividir por vírgula e limpar
    nomes = [nome.strip() for nome in equipe_str.split(',')]
    
    # Remover duplicatas mantendo ordem
    nomes_limpos = []
    for nome in nomes:
        nome_clean = nome.strip()
        
        # Remover texto extra como "(extra)", "Técnica Extra", etc
        if '(' in nome_clean and 'extra' in nome_clean.lower():
            continue
        if 'Técnica Extra' in nome_clean:
            continue
        if ':' in nome_clean and any(x in nome_clean.lower() for x in ['técnica', 'extra']):
            continue
            
        # Limpar acentos inconsistentes e normalizar
        nome_clean = re.sub(r'\s+', ' ', nome_clean)  # Múltiplos espaços
        
        if nome_clean and nome_clean not in nomes_limpos:
            nomes_limpos.append(nome_clean)
    
    return ', '.join(nomes_limpos)

def clean_all_equipe_duplicates():
    """Remove duplicatas do campo equipe de todas as unidades"""
    
    # Conectar ao banco de dados
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL não encontrada!")
        return False
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Buscar todos os registros com duplicação
            logger.info("🔍 Analisando registros com equipe duplicada em TODAS as unidades...")
            
            select_query = text("""
                SELECT id, unidade, data, equipe 
                FROM surgery 
                WHERE (equipe LIKE '%,%,%,%,%' OR LENGTH(equipe) > 50)
                ORDER BY unidade, data DESC
            """)
            
            result = conn.execute(select_query)
            records = result.fetchall()
            
            logger.info(f"📊 Encontrados {len(records)} registros com duplicação")
            
            # Contadores por unidade
            unidades_stats = {}
            
            # Atualizar cada registro
            updates_count = 0
            for record in records:
                old_equipe = record.equipe
                new_equipe = clean_equipe_string(old_equipe)
                
                # Estatísticas por unidade
                if record.unidade not in unidades_stats:
                    unidades_stats[record.unidade] = {'total': 0, 'updated': 0}
                unidades_stats[record.unidade]['total'] += 1
                
                if old_equipe != new_equipe:
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
                    unidades_stats[record.unidade]['updated'] += 1
                    
                    if updates_count <= 10:  # Mostrar apenas os primeiros 10 exemplos
                        logger.info(f"✅ {record.unidade} ID {record.id}: '{old_equipe[:50]}...' -> '{new_equipe[:50]}...'")
                    elif updates_count == 11:
                        logger.info("... (mostrando apenas os primeiros 10 exemplos)")
            
            # Commit das mudanças
            conn.commit()
            
            logger.info(f"🎉 Limpeza concluída! {updates_count} registros atualizados")
            
            # Estatísticas por unidade
            logger.info("📋 Estatísticas por unidade:")
            for unidade, stats in unidades_stats.items():
                logger.info(f"   {unidade}: {stats['updated']}/{stats['total']} registros atualizados")
            
            # Verificar resultado final
            verification_query = text("""
                SELECT unidade, 
                       COUNT(*) as total_registros_duplicados_restantes
                FROM surgery 
                WHERE (equipe LIKE '%,%,%,%,%' OR LENGTH(equipe) > 50)
                AND unidade IS NOT NULL
                GROUP BY unidade
                ORDER BY total_registros_duplicados_restantes DESC
            """)
            
            result = conn.execute(verification_query)
            remaining_duplicates = result.fetchall()
            
            if remaining_duplicates:
                logger.warning("⚠️ Ainda existem duplicações:")
                for row in remaining_duplicates:
                    logger.warning(f"   {row.unidade}: {row.total_registros_duplicados_restantes} registros")
            else:
                logger.info("✅ Todas as duplicações foram removidas!")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erro na limpeza: {str(e)}")
        return False

if __name__ == '__main__':
    success = clean_all_equipe_duplicates()
    if success:
        print("✅ Limpeza de duplicatas de todas as unidades concluída!")
    else:
        print("❌ Falha na limpeza de duplicatas!")
        sys.exit(1)