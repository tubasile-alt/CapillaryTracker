#!/usr/bin/env python
"""
Script para importar dados da planilha relatorio_cirurgias.xlsx 
para o banco de dados PostgreSQL.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_url():
    """Obter URL do banco de dados de variáveis de ambiente ou arquivo de configuração"""
    # Primeiro, tentar obter de variáveis de ambiente
    db_url = os.environ.get('DATABASE_URL')
    
    # Se não encontrado, tentar ler do arquivo config.cfg
    if not db_url and os.path.exists('config.cfg'):
        with open('config.cfg', 'r') as f:
            for line in f:
                if line.startswith('DATABASE_URL='):
                    db_url = line.strip().split('=', 1)[1]
                    # Remover aspas se existirem
                    if db_url.startswith('"') and db_url.endswith('"'):
                        db_url = db_url[1:-1]
                    break
    
    if not db_url:
        logger.error("❌ DATABASE_URL não encontrada!")
        sys.exit(1)
    
    logger.info(f"📌 URL do banco de dados: {db_url.replace('://', '://****:****@')}")
    return db_url

def create_app():
    """Criar aplicação Flask apenas para inicialização do SQLAlchemy"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = get_db_url()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    return app

def process_date(date_str):
    """Converter data no formato DD/MM/AAAA para objeto datetime"""
    if pd.isna(date_str):
        return None
    
    try:
        # Tentar converter diferentes formatos de data
        try:
            # Formato DD/MM/AAAA
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        except ValueError:
            try:
                # Formato AAAA-MM-DD
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                # Formato DD-MM-AAAA
                return datetime.strptime(date_str, '%d-%m-%Y').date()
    except Exception as e:
        logger.warning(f"⚠️ Erro ao converter data '{date_str}': {str(e)}")
        return None

def import_data(excel_path):
    """Importar dados da planilha para o banco de dados"""
    try:
        # Inicializar aplicação e banco de dados
        app = create_app()
        db = SQLAlchemy(app)
        
        # Modelo para a tabela Surgery
        class Surgery(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            data = db.Column(db.Date)
            nome = db.Column(db.String(255))
            unidade = db.Column(db.String(100))
            medico = db.Column(db.String(100))
            equipe = db.Column(db.String(255))
            hora_cirurgia = db.Column(db.String(5))
            tempo_cirurgia = db.Column(db.Float)
            total_foliculos = db.Column(db.Integer)
            frente = db.Column(db.Integer)
            densidade_scketh = db.Column(db.Float)
            coroa = db.Column(db.Integer)
            scalpe = db.Column(db.Integer)
            peninsula_direita = db.Column(db.Integer)
            peninsula_esquerda = db.Column(db.Integer)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
        # Modelo para a tabela UnitProgress
        class UnitProgress(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            unidade = db.Column(db.String(100), unique=True)
            meta = db.Column(db.Integer)
        
        # Ler a planilha
        logger.info(f"📊 Lendo planilha {excel_path}...")
        df = pd.read_excel(excel_path)
        
        # Verificar se a planilha tem dados
        if df.empty:
            logger.error("❌ A planilha está vazia!")
            return False
        
        # Criar contexto de aplicação
        with app.app_context():
            # Excluir registros existentes apenas para teste
            # Em produção, você pode querer verificar duplicatas em vez de excluir tudo
            Surgery.query.delete()
            db.session.commit()
            
            # Inicializar contador de registros importados
            count = 0
            
            # Para cada linha na planilha, inserir no banco de dados
            for _, row in df.iterrows():
                try:
                    # Mapear colunas da planilha para campos da tabela
                    surgery = Surgery(
                        data=process_date(row.get('data', None)),
                        nome=str(row.get('nome', '')),
                        unidade=str(row.get('unidade', '')),
                        medico=str(row.get('medico', '')),
                        equipe=str(row.get('equipe', '')),
                        hora_cirurgia=str(row.get('hora_cirurgia', '')),
                        tempo_cirurgia=float(row.get('tempo_cirurgia', 0)) if not pd.isna(row.get('tempo_cirurgia', 0)) else 0,
                        total_foliculos=int(row.get('total_foliculos', 0)) if not pd.isna(row.get('total_foliculos', 0)) else 0,
                        frente=int(row.get('frente', 0)) if not pd.isna(row.get('frente', 0)) else 0,
                        densidade_scketh=float(row.get('densidade_scketh', 0)) if not pd.isna(row.get('densidade_scketh', 0)) else 0,
                        coroa=int(row.get('coroa', 0)) if not pd.isna(row.get('coroa', 0)) else 0,
                        scalpe=int(row.get('scalpe', 0)) if not pd.isna(row.get('scalpe', 0)) else 0,
                        peninsula_direita=int(row.get('peninsula_direita', 0)) if not pd.isna(row.get('peninsula_direita', 0)) else 0,
                        peninsula_esquerda=int(row.get('peninsula_esquerda', 0)) if not pd.isna(row.get('peninsula_esquerda', 0)) else 0,
                        created_at=datetime.utcnow()
                    )
                    
                    # Adicionar ao banco de dados
                    db.session.add(surgery)
                    count += 1
                    
                    # Commit a cada 10 registros para não sobrecarregar o banco
                    if count % 10 == 0:
                        db.session.commit()
                        logger.info(f"✅ {count} registros importados...")
                
                except Exception as e:
                    logger.error(f"❌ Erro ao importar linha {_+1}: {str(e)}")
                    logger.error(f"Dados: {row.to_dict()}")
                    continue
            
            # Commit final para os registros restantes
            db.session.commit()
            
            # Configurar metas de unidade se não existirem
            unidades = {}
            for unidade in df['unidade'].unique():
                if pd.notna(unidade) and unidade.strip():
                    unidades[unidade] = 30  # Meta padrão
            
            # Inserir metas de unidade
            for unidade, meta in unidades.items():
                # Verificar se já existe
                existing = UnitProgress.query.filter_by(unidade=unidade).first()
                if not existing:
                    # Criar novo registro
                    unit_progress = UnitProgress(unidade=unidade, meta=meta)
                    db.session.add(unit_progress)
            
            # Commit das metas de unidade
            db.session.commit()
            
            logger.info(f"✅ Importação concluída! {count} registros importados com sucesso.")
            logger.info(f"✅ {len(unidades)} unidades configuradas: {', '.join(unidades.keys())}")
            
            return True
    
    except Exception as e:
        logger.error(f"❌ Erro durante a importação: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
    try:
        excel_path = 'attached_assets/relatorio_cirurgias.xlsx'
        
        # Verificar se o arquivo existe
        if not os.path.exists(excel_path):
            logger.error(f"❌ Arquivo não encontrado: {excel_path}")
            sys.exit(1)
        
        # Importar dados
        success = import_data(excel_path)
        
        if success:
            logger.info("✅ Importação concluída com sucesso!")
            sys.exit(0)
        else:
            logger.error("❌ Falha na importação dos dados.")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)