#!/usr/bin/env python3
"""
Script para atualizar registros existentes com dados dos quadrantes faltantes
"""
import os
import pandas as pd
from datetime import datetime
import logging
from app import app, db, Surgery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_quadrant_data():
    """Atualiza registros existentes com dados dos quadrantes"""
    try:
        excel_file = "attached_assets/relatorio_cirurgias (20)_1749492174430.xlsx"
        
        if not os.path.exists(excel_file):
            logger.error(f"Arquivo não encontrado: {excel_file}")
            return
        
        # Ler o arquivo Excel
        logger.info(f"Lendo arquivo: {excel_file}")
        df = pd.read_excel(excel_file, engine='openpyxl')
        
        logger.info(f"Arquivo carregado com {len(df)} registros")
        
        # Filtrar apenas dados de Ribeirão Preto
        df_ribeirao = df[df['unidade'] == 'Ribeirão Preto']
        logger.info(f"Encontrados {len(df_ribeirao)} registros de Ribeirão Preto")
        
        with app.app_context():
            updated_count = 0
            
            # Processar cada linha
            for index, row in df_ribeirao.iterrows():
                try:
                    # Processar data
                    date_field = row['data']
                    if pd.isna(date_field):
                        continue
                    
                    if isinstance(date_field, str):
                        if '/' in date_field:
                            data_obj = datetime.strptime(date_field, '%d/%m/%Y').date()
                        else:
                            data_obj = datetime.strptime(date_field, '%Y-%m-%d').date()
                    else:
                        data_obj = pd.to_datetime(date_field).date()
                    
                    # Nome do paciente
                    nome_paciente = str(row['nome']).strip()
                    
                    # Encontrar registro existente
                    existing = Surgery.query.filter_by(
                        nome=nome_paciente,
                        data=data_obj
                    ).first()
                    
                    if not existing:
                        logger.info(f"Registro não encontrado: {nome_paciente} - {data_obj}")
                        continue
                    
                    # Função auxiliar para converter valores seguros
                    def safe_int(value, default=0):
                        if pd.isna(value) or value == '' or value is None:
                            return default
                        try:
                            return int(float(value))
                        except (ValueError, TypeError):
                            return default
                    
                    def safe_float(value, default=0.0):
                        if pd.isna(value) or value == '' or value is None:
                            return default
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            return default
                    
                    def safe_str(value, default=''):
                        if pd.isna(value) or value is None:
                            return default
                        return str(value).strip()
                    
                    # Verificar se precisa atualizar (tem dados de quadrantes no arquivo)
                    has_quadrant_data = not pd.isna(row.get('q1_area', None))
                    
                    if has_quadrant_data:
                        # Atualizar dados dos quadrantes
                        existing.q1_area = safe_float(row.get('q1_area'))
                        existing.q1_furos = safe_int(row.get('q1_furos'))
                        existing.q1_fios = safe_int(row.get('q1_fios'))
                        existing.q1_densidade = safe_float(row.get('q1_densidade'))
                        existing.q1_taxa_quebra = safe_float(row.get('q1_taxa_quebra'))
                        
                        existing.q2_area = safe_float(row.get('q2_area'))
                        existing.q2_furos = safe_int(row.get('q2_furos'))
                        existing.q2_fios = safe_int(row.get('q2_fios'))
                        existing.q2_densidade = safe_float(row.get('q2_densidade'))
                        existing.q2_taxa_quebra = safe_float(row.get('q2_taxa_quebra'))
                        
                        existing.q3_area = safe_float(row.get('q3_area'))
                        existing.q3_furos = safe_int(row.get('q3_furos'))
                        existing.q3_fios = safe_int(row.get('q3_fios'))
                        existing.q3_densidade = safe_float(row.get('q3_densidade'))
                        existing.q3_taxa_quebra = safe_float(row.get('q3_taxa_quebra'))
                        
                        existing.q4_area = safe_float(row.get('q4_area'))
                        existing.q4_furos = safe_int(row.get('q4_furos'))
                        existing.q4_fios = safe_int(row.get('q4_fios'))
                        existing.q4_densidade = safe_float(row.get('q4_densidade'))
                        existing.q4_taxa_quebra = safe_float(row.get('q4_taxa_quebra'))
                        
                        existing.densidade_extracao = safe_float(row.get('densidade_extracao'))
                        
                        # Atualizar campos da segunda página se existirem
                        if not pd.isna(row.get('infiltracao')):
                            existing.infiltracao = safe_str(row.get('infiltracao'))
                        if not pd.isna(row.get('tadalafila')):
                            existing.tadalafila = safe_str(row.get('tadalafila'))
                        if not pd.isna(row.get('bloqueio_seringas')):
                            existing.bloqueio_seringas = safe_str(row.get('bloqueio_seringas'))
                        if not pd.isna(row.get('fonte_1')):
                            existing.fonte_1 = safe_str(row.get('fonte_1'))
                        if not pd.isna(row.get('fonte_2')):
                            existing.fonte_2 = safe_str(row.get('fonte_2'))
                        if not pd.isna(row.get('fonte_3')):
                            existing.fonte_3 = safe_str(row.get('fonte_3'))
                        if not pd.isna(row.get('fonte_4')):
                            existing.fonte_4 = safe_str(row.get('fonte_4'))
                        if not pd.isna(row.get('fonte_5')):
                            existing.fonte_5 = safe_str(row.get('fonte_5'))
                        if not pd.isna(row.get('pelos_corporais')):
                            existing.pelos_corporais = safe_str(row.get('pelos_corporais'))
                        if not pd.isna(row.get('tecnica')):
                            existing.tecnica = safe_str(row.get('tecnica'))
                        if not pd.isna(row.get('solucao_frente')):
                            existing.solucao_frente = safe_int(row.get('solucao_frente'))
                        
                        updated_count += 1
                        logger.info(f"Atualizado: {nome_paciente} - {data_obj}")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar linha {index}: {str(e)}")
                    continue
            
            # Salvar todas as alterações
            if updated_count > 0:
                db.session.commit()
                logger.info(f"✅ {updated_count} registros atualizados com sucesso!")
                
                # Verificar total após atualização
                final_count = Surgery.query.count()
                logger.info(f"Total de registros no banco: {final_count}")
            else:
                logger.warning("Nenhum registro foi atualizado")
    
    except Exception as e:
        logger.error(f"Erro durante atualização: {str(e)}")
        if 'db' in locals():
            db.session.rollback()

if __name__ == "__main__":
    update_quadrant_data()