#!/usr/bin/env python3
"""
Script para adicionar os 19 registros faltantes de Ribeirão Preto
"""
import os
import pandas as pd
from datetime import datetime
import logging
from app import app, db, Surgery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_missing_records():
    """Adiciona os registros faltantes de Ribeirão Preto"""
    try:
        excel_file = "attached_assets/relatorio_cirurgias (20)_1749492174430.xlsx"
        
        if not os.path.exists(excel_file):
            logger.error(f"Arquivo não encontrado: {excel_file}")
            return
        
        # Ler o arquivo Excel
        logger.info(f"Lendo arquivo: {excel_file}")
        df = pd.read_excel(excel_file, engine='openpyxl')
        
        # Filtrar apenas dados de Ribeirão Preto
        df_ribeirao = df[df['unidade'] == 'Ribeirão Preto']
        logger.info(f"Encontrados {len(df_ribeirao)} registros de Ribeirão Preto no arquivo")
        
        with app.app_context():
            # Obter registros existentes
            existing_records = Surgery.query.filter_by(unidade='Ribeirão Preto').all()
            existing_names = {r.nome.strip().lower() for r in existing_records}
            logger.info(f"Registros existentes no banco: {len(existing_records)}")
            
            added_count = 0
            
            # Lista dos 19 pacientes faltantes
            missing_patients = {
                'almir ferreira', 'antonio borges junior', 'cleber galhardi', 
                'daniel dias dos santos', 'darci vanderlei lopes', 'eduardo moura filho',
                'felipe gattaz kawano', 'fernando faria', 'gustavo henrique sigoline',
                'joao pedro zani coeti', 'julio vieira de araujo', 'leandro luiz lima zaparoli',
                'maicon ferreira martins', 'marcelo antonio nunes', 'matheus henrique da silva magalhaes',
                'pedro henrique siqueira de oliveira', 'santiago barbosa ambrosio', 
                'silvio david guidastre junior', 'wendel ferreira bento'
            }
            
            # Processar cada linha do arquivo
            for index, row in df_ribeirao.iterrows():
                try:
                    # Nome do paciente
                    nome_paciente = str(row['nome']).strip()
                    nome_lower = nome_paciente.lower()
                    
                    # Verificar se é um dos pacientes faltantes
                    if nome_lower not in missing_patients:
                        continue
                    
                    # Processar data
                    date_field = row['data']
                    if pd.isna(date_field):
                        logger.error(f"Data vazia para {nome_paciente}")
                        continue
                    
                    if isinstance(date_field, str):
                        if '/' in date_field:
                            data_obj = datetime.strptime(date_field, '%d/%m/%Y').date()
                        else:
                            data_obj = datetime.strptime(date_field, '%Y-%m-%d').date()
                    else:
                        data_obj = pd.to_datetime(date_field).date()
                    
                    # Verificar se já existe (dupla verificação)
                    existing = Surgery.query.filter_by(
                        nome=nome_paciente,
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
                        nome=nome_paciente,
                        unidade='Ribeirão Preto',
                        medico=safe_str(row.get('medico', '')),
                        equipe=safe_str(row.get('equipe', '')),
                        hora_cirurgia=safe_str(row.get('hora_cirurgia', '')),
                        tempo_cirurgia=safe_float(row.get('tempo_cirurgia', 0)),
                        total_foliculos=safe_int(row.get('total_foliculos', 0)),
                        frente=safe_int(row.get('frente', 0)),
                        densidade_scketh=safe_float(row.get('densidade_scketh', 0)),
                        coroa=safe_int(row.get('coroa', 0)),
                        scalpe=safe_int(row.get('scalpe', 0)),
                        peninsula_direita=safe_int(row.get('peninsula_direita', 0)),
                        peninsula_esquerda=safe_int(row.get('peninsula_esquerda', 0)),
                        # Campos da segunda página
                        infiltracao=safe_str(row.get('infiltracao', '')),
                        tadalafila=safe_str(row.get('tadalafila', '')),
                        bloqueio_seringas=safe_str(row.get('bloqueio_seringas', '')),
                        fonte_1=safe_str(row.get('fonte_1', '')),
                        fonte_2=safe_str(row.get('fonte_2', '')),
                        fonte_3=safe_str(row.get('fonte_3', '')),
                        fonte_4=safe_str(row.get('fonte_4', '')),
                        fonte_5=safe_str(row.get('fonte_5', '')),
                        pelos_corporais=safe_str(row.get('pelos_corporais', '')),
                        tecnica=safe_str(row.get('tecnica', '')),
                        solucao_frente=safe_int(row.get('solucao_frente', 0)),
                        # Dados dos quadrantes
                        q1_area=safe_float(row.get('q1_area', 0)),
                        q1_furos=safe_int(row.get('q1_furos', 0)),
                        q1_fios=safe_int(row.get('q1_fios', 0)),
                        q1_densidade=safe_float(row.get('q1_densidade', 0)),
                        q1_taxa_quebra=safe_float(row.get('q1_taxa_quebra', 0)),
                        q2_area=safe_float(row.get('q2_area', 0)),
                        q2_furos=safe_int(row.get('q2_furos', 0)),
                        q2_fios=safe_int(row.get('q2_fios', 0)),
                        q2_densidade=safe_float(row.get('q2_densidade', 0)),
                        q2_taxa_quebra=safe_float(row.get('q2_taxa_quebra', 0)),
                        q3_area=safe_float(row.get('q3_area', 0)),
                        q3_furos=safe_int(row.get('q3_furos', 0)),
                        q3_fios=safe_int(row.get('q3_fios', 0)),
                        q3_densidade=safe_float(row.get('q3_densidade', 0)),
                        q3_taxa_quebra=safe_float(row.get('q3_taxa_quebra', 0)),
                        q4_area=safe_float(row.get('q4_area', 0)),
                        q4_furos=safe_int(row.get('q4_furos', 0)),
                        q4_fios=safe_int(row.get('q4_fios', 0)),
                        q4_densidade=safe_float(row.get('q4_densidade', 0)),
                        q4_taxa_quebra=safe_float(row.get('q4_taxa_quebra', 0)),
                        densidade_extracao=safe_float(row.get('densidade_extracao', 0))
                    )
                    
                    db.session.add(surgery)
                    added_count += 1
                    logger.info(f"Adicionado: {nome_paciente} - {data_obj}")
                    
                except Exception as e:
                    logger.error(f"Erro ao processar {nome_paciente}: {str(e)}")
                    continue
            
            # Salvar todas as alterações
            if added_count > 0:
                db.session.commit()
                logger.info(f"✅ {added_count} registros faltantes adicionados com sucesso!")
                
                # Verificar total após adição
                final_count = Surgery.query.filter_by(unidade='Ribeirão Preto').count()
                total_count = Surgery.query.count()
                logger.info(f"Total de registros de Ribeirão Preto: {final_count}")
                logger.info(f"Total geral de registros no banco: {total_count}")
            else:
                logger.warning("Nenhum registro faltante foi adicionado")
    
    except Exception as e:
        logger.error(f"Erro durante adição: {str(e)}")
        if 'db' in locals():
            db.session.rollback()

if __name__ == "__main__":
    add_missing_records()