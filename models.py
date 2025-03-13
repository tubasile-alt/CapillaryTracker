from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()

class Cirurgia(db.Model):
    __tablename__ = 'cirurgias'
    
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    unidade = db.Column(db.String(50), nullable=False)
    medico = db.Column(db.String(100), nullable=False)
    equipe = db.Column(db.String(200), nullable=False)
    hora_cirurgia = db.Column(db.String(5), nullable=False)
    tempo_cirurgia = db.Column(db.Float, nullable=False)
    
    # Informações do Implante
    total_foliculos = db.Column(db.Integer)
    frente = db.Column(db.Integer)
    densidade_scketh = db.Column(db.Float)
    coroa = db.Column(db.Integer)
    scalpe = db.Column(db.Integer)
    peninsula_direita = db.Column(db.Integer)
    peninsula_esquerda = db.Column(db.Integer)
    
    # Procedimentos
    safira = db.Column(db.String(3))  # Sim/Não
    punch = db.Column(db.String(4))
    solucao_frente = db.Column(db.Float)
    solucao_coroa = db.Column(db.Float)
    solucao_xilo_frente = db.Column(db.Float)
    
    # Distribuição
    q1_area = db.Column(db.Float)
    q1_furos = db.Column(db.Integer)
    q1_fios = db.Column(db.Integer)
    q2_area = db.Column(db.Float)
    q2_furos = db.Column(db.Integer)
    q2_fios = db.Column(db.Integer)
    q3_area = db.Column(db.Float)
    q3_furos = db.Column(db.Integer)
    q3_fios = db.Column(db.Integer)
    q4_area = db.Column(db.Float)
    q4_furos = db.Column(db.Integer)
    q4_fios = db.Column(db.Integer)
    
    # Avaliação
    infiltracao = db.Column(db.Integer)
    sedacao = db.Column(db.Integer)
    sangramento = db.Column(db.Integer)
    
    # Histórico
    implante_secundario = db.Column(db.String(3))  # Sim/Não
    transamin = db.Column(db.String(3))  # Sim/Não
    tadalafila = db.Column(db.String(3))  # Sim/Não
    diprospam = db.Column(db.String(3))  # Sim/Não
    fumante = db.Column(db.String(3))  # Sim/Não
    antecedentes = db.Column(db.Text)
    
    # Comentários
    comentarios = db.Column(db.Text)
    
    # Campos calculados (podem ser recalculados a qualquer momento)
    q1_densidade = db.Column(db.Float)
    q2_densidade = db.Column(db.Float)
    q3_densidade = db.Column(db.Float)
    q4_densidade = db.Column(db.Float)
    q1_taxa_quebra = db.Column(db.Float)
    q2_taxa_quebra = db.Column(db.Float)
    q3_taxa_quebra = db.Column(db.Float)
    q4_taxa_quebra = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'data': self.data.strftime('%d/%m/%Y') if self.data else None,
            'nome': self.nome,
            'unidade': self.unidade,
            'medico': self.medico,
            'equipe': self.equipe,
            'hora_cirurgia': self.hora_cirurgia,
            'tempo_cirurgia': self.tempo_cirurgia,
            'total_foliculos': self.total_foliculos,
            'frente': self.frente,
            'densidade_scketh': self.densidade_scketh,
            'coroa': self.coroa,
            'scalpe': self.scalpe,
            'peninsula_direita': self.peninsula_direita,
            'peninsula_esquerda': self.peninsula_esquerda,
            'safira': self.safira,
            'punch': self.punch,
            'solucao_frente': self.solucao_frente,
            'solucao_coroa': self.solucao_coroa,
            'solucao_xilo_frente': self.solucao_xilo_frente,
            'q1_area': self.q1_area,
            'q1_furos': self.q1_furos,
            'q1_fios': self.q1_fios,
            'q2_area': self.q2_area,
            'q2_furos': self.q2_furos,
            'q2_fios': self.q2_fios,
            'q3_area': self.q3_area,
            'q3_furos': self.q3_furos,
            'q3_fios': self.q3_fios,
            'q4_area': self.q4_area,
            'q4_furos': self.q4_furos,
            'q4_fios': self.q4_fios,
            'infiltracao': self.infiltracao,
            'sedacao': self.sedacao,
            'sangramento': self.sangramento,
            'implante_secundario': self.implante_secundario,
            'transamin': self.transamin,
            'tadalafila': self.tadalafila,
            'diprospam': self.diprospam,
            'fumante': self.fumante,
            'antecedentes': self.antecedentes,
            'comentarios': self.comentarios,
            'q1_densidade': self.q1_densidade,
            'q2_densidade': self.q2_densidade,
            'q3_densidade': self.q3_densidade,
            'q4_densidade': self.q4_densidade,
            'q1_taxa_quebra': self.q1_taxa_quebra,
            'q2_taxa_quebra': self.q2_taxa_quebra,
            'q3_taxa_quebra': self.q3_taxa_quebra,
            'q4_taxa_quebra': self.q4_taxa_quebra
        }
