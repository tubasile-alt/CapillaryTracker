#!/usr/bin/env python3
"""
Script para importar dados específicos de Ribeirão Preto do arquivo Excel anexado
"""
import os
import pandas as pd
from datetime import datetime
import logging
from app import app, db, Surgery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_ribeirao_data():
    """Importa dados específicos de Ribeirão Preto"""
    try:
        excel_file = "attached_assets/relatorio_cirurgias (20)_1749492174430.xlsx"
        
        if not os.path.exists(excel_file):
            logger.error(f"Arquivo não encontrado: {excel_file}")
            return
        
        # Ler o arquivo Excel
        logger.info(f"Lendo arquivo: {excel_file}")
        df = pd.read_excel(excel_file, engine='openpyxl')
        
        logger.info(f"Arquivo carregado com {len(df)} registros")
        logger.info(f"Colunas disponíveis: {list(df.columns)}")
        
        # Mostrar primeiras linhas para verificar estrutura
        logger.info("Primeiras 3 linhas:")
        for i, row in df.head(3).iterrows():
            logger.info(f"Linha {i}: {dict(row)}")
        
        with app.app_context():
            # Verificar registros existentes antes da importação
            existing_count = Surgery.query.count()
            logger.info(f"Registros existentes no banco: {existing_count}")
            
            # Filtrar apenas dados de Ribeirão Preto se coluna existe
            if 'unidade' in df.columns:
                df_ribeirao = df[df['unidade'] == 'Ribeirão Preto']
                logger.info(f"Encontrados {len(df_ribeirao)} registros de Ribeirão Preto")
            elif 'Unidade' in df.columns:
                df_ribeirao = df[df['Unidade'] == 'Ribeirão Preto']
                logger.info(f"Encontrados {len(df_ribeirao)} registros de Ribeirão Preto")
            else:
                # Se não tem coluna de unidade, assumir que todos são de Ribeirão Preto
                df_ribeirao = df.copy()
                logger.info(f"Assumindo que todos os {len(df_ribeirao)} registros são de Ribeirão Preto")
            
            if df_ribeirao.empty:
                logger.warning("Nenhum registro de Ribeirão Preto encontrado no arquivo")
                return
            
            # Processar cada linha
            imported_count = 0
            for index, row in df_ribeirao.iterrows():
                try:
                    # Processar data
                    if 'data' in row:
                        date_field = row['data']
                    elif 'Data' in row:
                        date_field = row['Data']
                    elif 'Data (DD/MM/AAAA)' in row:
                        date_field = row['Data (DD/MM/AAAA)']
                    else:
                        logger.error(f"Campo de data não encontrado na linha {index}")
                        continue
                    
                    # Converter data
                    if pd.isna(date_field):
                        logger.error(f"Data vazia na linha {index}")
                        continue
                    
                    if isinstance(date_field, str):
                        if '/' in date_field:
                            data_obj = datetime.strptime(date_field, '%d/%m/%Y').date()
                        else:
                            data_obj = datetime.strptime(date_field, '%Y-%m-%d').date()
                    else:
                        data_obj = pd.to_datetime(date_field).date()
                    
                    # Verificar se já existe (evitar duplicatas)
                    nome_paciente = row.get('nome', row.get('Nome', row.get('Paciente', '')))
                    if pd.isna(nome_paciente):
                        logger.error(f"Nome do paciente vazio na linha {index}")
                        continue
                    
                    existing = Surgery.query.filter_by(
                        nome=str(nome_paciente).strip(),
                        data=data_obj
                    ).first()
                    
                    if existing:
                        logger.info(f"Registro já existe: {nome_paciente} - {data_obj}")
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
                    
                    # Criar novo registro
                    surgery = Surgery(
                        data=data_obj,
                        nome=str(nome_paciente).strip(),
                        unidade='Ribeirão Preto',
                        medico=safe_str(row.get('medico', row.get('Médico', ''))),
                        equipe=safe_str(row.get('equipe', row.get('Equipe', ''))),
                        hora_cirurgia=safe_str(row.get('hora_cirurgia', row.get('Hora da Cirurgia (HH:MM)', ''))),
                        tempo_cirurgia=safe_float(row.get('tempo_cirurgia', row.get('Tempo de Cirurgia (horas)', 0))),
                        total_foliculos=safe_int(row.get('total_foliculos', row.get('Total de Folículos', 0))),
                        frente=safe_int(row.get('frente', row.get('Frente', 0))),
                        densidade_scketh=safe_float(row.get('densidade_scketh', row.get('Densidade Scketh', 0))),
                        coroa=safe_int(row.get('coroa', row.get('Coroa', 0))),
                        scalpe=safe_int(row.get('scalpe', row.get('Scalpe', 0))),
                        peninsula_direita=safe_int(row.get('peninsula_direita', row.get('Península Direita', 0))),
                        peninsula_esquerda=safe_int(row.get('peninsula_esquerda', row.get('Península Esquerda', 0))),
                        # Campos da segunda página (se existirem)
                        infiltracao=safe_str(row.get('infiltracao', row.get('Infiltração', ''))),
                        tadalafila=safe_str(row.get('tadalafila', row.get('Tadalafila', ''))),
                        bloqueio_seringas=safe_str(row.get('bloqueio_seringas', row.get('Bloqueio de Seringas', ''))),
                        fonte_1=safe_str(row.get('fonte_1', row.get('Fonte 1', ''))),
                        fonte_2=safe_str(row.get('fonte_2', row.get('Fonte 2', ''))),
                        fonte_3=safe_str(row.get('fonte_3', row.get('Fonte 3', ''))),
                        fonte_4=safe_str(row.get('fonte_4', row.get('Fonte 4', ''))),
                        fonte_5=safe_str(row.get('fonte_5', row.get('Fonte 5', ''))),
                        pelos_corporais=safe_str(row.get('pelos_corporais', row.get('Pelos Corporais', ''))),
                        tecnica=safe_str(row.get('tecnica', row.get('Técnica', ''))),
                        solucao_frente=safe_int(row.get('solucao_frente', row.get('Solução Frente (ml)', 0))),
                        # Dados dos quadrantes (se existirem)
                        q1_area=safe_float(row.get('q1_area', row.get('Q1 Área', 0))),
                        q1_furos=safe_int(row.get('q1_furos', row.get('Q1 Furos', 0))),
                        q1_fios=safe_int(row.get('q1_fios', row.get('Q1 Fios', 0))),
                        q1_densidade=safe_float(row.get('q1_densidade', row.get('Q1 Densidade', 0))),
                        q1_taxa_quebra=safe_float(row.get('q1_taxa_quebra', row.get('Q1 Taxa Quebra', 0))),
                        q2_area=safe_float(row.get('q2_area', row.get('Q2 Área', 0))),
                        q2_furos=safe_int(row.get('q2_furos', row.get('Q2 Furos', 0))),
                        q2_fios=safe_int(row.get('q2_fios', row.get('Q2 Fios', 0))),
                        q2_densidade=safe_float(row.get('q2_densidade', row.get('Q2 Densidade', 0))),
                        q2_taxa_quebra=safe_float(row.get('q2_taxa_quebra', row.get('Q2 Taxa Quebra', 0))),
                        q3_area=safe_float(row.get('q3_area', row.get('Q3 Área', 0))),
                        q3_furos=safe_int(row.get('q3_furos', row.get('Q3 Furos', 0))),
                        q3_fios=safe_int(row.get('q3_fios', row.get('Q3 Fios', 0))),
                        q3_densidade=safe_float(row.get('q3_densidade', row.get('Q3 Densidade', 0))),
                        q3_taxa_quebra=safe_float(row.get('q3_taxa_quebra', row.get('Q3 Taxa Quebra', 0))),
                        q4_area=safe_float(row.get('q4_area', row.get('Q4 Área', 0))),
                        q4_furos=safe_int(row.get('q4_furos', row.get('Q4 Furos', 0))),
                        q4_fios=safe_int(row.get('q4_fios', row.get('Q4 Fios', 0))),
                        q4_densidade=safe_float(row.get('q4_densidade', row.get('Q4 Densidade', 0))),
                        q4_taxa_quebra=safe_float(row.get('q4_taxa_quebra', row.get('Q4 Taxa Quebra', 0))),
                        densidade_extracao=safe_float(row.get('densidade_extracao', row.get('Densidade Extração', 0)))
                    )
                    
                    db.session.add(surgery)
                    imported_count += 1
                    logger.info(f"Registro adicionado: {nome_paciente} - {data_obj}")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar linha {index}: {str(e)}")
                    continue
            
            # Salvar todas as alterações
            if imported_count > 0:
                db.session.commit()
                logger.info(f"✅ {imported_count} registros importados com sucesso!")
                
                # Verificar total após importação
                final_count = Surgery.query.count()
                logger.info(f"Total de registros no banco após importação: {final_count}")
            else:
                logger.warning("Nenhum registro novo foi importado")
    
    except Exception as e:
        logger.error(f"Erro durante importação: {str(e)}")
        if 'db' in locals():
            db.session.rollback()

if __name__ == "__main__":
    import_ribeirao_data()