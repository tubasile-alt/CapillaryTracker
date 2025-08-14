#!/usr/bin/env python3
"""
Script para limpar duplicatas no campo 'equipe' da tabela surgery
Especificamente para Ribeirão Preto
"""

import os
import sys
from sqlalchemy import create_engine, text
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_equipe_duplicates():
    """Remove duplicatas do campo equipe"""
    
    # Conectar ao banco de dados
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL não encontrada!")
        return False
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Primeiro, vamos ver todos os registros problemáticos
            logger.info("🔍 Analisando registros com equipe duplicada...")
            
            select_query = text("""
                SELECT id, data, equipe 
                FROM surgery 
                WHERE unidade = 'Ribeirão Preto' 
                AND (equipe LIKE '%,%,%,%,%' OR LENGTH(equipe) > 50)
                ORDER BY data DESC
            """)
            
            result = conn.execute(select_query)
            records = result.fetchall()
            
            logger.info(f"📊 Encontrados {len(records)} registros com duplicação")
            
            # Função para limpar string de equipe
            def clean_equipe_string(equipe_str):
                if not equipe_str:
                    return equipe_str
                
                # Dividir por vírgula e limpar
                nomes = [nome.strip() for nome in equipe_str.split(',')]
                
                # Remover duplicatas mantendo ordem
                nomes_limpos = []
                for nome in nomes:
                    # Limpar nomes extras
                    nome_clean = nome.strip()
                    # Remover texto extra como "(extra)", "Técnica Extra", etc
                    if '(' in nome_clean:
                        nome_clean = nome_clean.split('(')[0].strip()
                    if 'Técnica Extra' in nome_clean:
                        continue  # Pular técnicas extras
                    if nome_clean and nome_clean not in nomes_limpos:
                        # Normalizar nomes conhecidos
                        if nome_clean.lower() in ['natalia', 'natália']:
                            nome_clean = 'Natália'
                        elif nome_clean.lower() in ['lavinia', 'lavínia']:
                            nome_clean = 'Lavínia'
                        elif nome_clean.lower() == 'aline':
                            nome_clean = 'Aline'
                        elif nome_clean.lower() == 'ana':
                            nome_clean = 'Ana'
                        
                        nomes_limpos.append(nome_clean)
                
                return ', '.join(nomes_limpos)
            
            # Atualizar cada registro
            updates_count = 0
            for record in records:
                old_equipe = record.equipe
                new_equipe = clean_equipe_string(old_equipe)
                
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
                    logger.info(f"✅ ID {record.id}: '{old_equipe[:50]}...' -> '{new_equipe}'")
            
            # Commit das mudanças
            conn.commit()
            
            logger.info(f"🎉 Limpeza concluída! {updates_count} registros atualizados")
            
            # Verificar resultado
            verification_query = text("""
                SELECT equipe, COUNT(*) as total 
                FROM surgery 
                WHERE unidade = 'Ribeirão Preto' 
                AND equipe IN ('Ana', 'Aline', 'Natália', 'Lavínia')
                GROUP BY equipe 
                ORDER BY equipe
            """)
            
            result = conn.execute(verification_query)
            final_counts = result.fetchall()
            
            logger.info("📋 Contagem final por membro da equipe:")
            for row in final_counts:
                logger.info(f"   {row.equipe}: {row.total} cirurgias")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erro na limpeza: {str(e)}")
        return False

if __name__ == '__main__':
    success = clean_equipe_duplicates()
    if success:
        print("✅ Limpeza de duplicatas concluída com sucesso!")
    else:
        print("❌ Falha na limpeza de duplicatas!")
        sys.exit(1)