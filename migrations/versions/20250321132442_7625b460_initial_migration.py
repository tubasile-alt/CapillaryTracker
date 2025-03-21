"""Initial migration

Revision ID: 20250321132442_7625b460
Revises: 
Create Date: 2025-03-21 13:24:42.787268

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250321132442_7625b460'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Este é um arquivo de migração inicial gerado manualmente.
    # As tabelas já foram criadas diretamente com db.create_all()
    pass


def downgrade():
    # Não implementado para migração inicial
    pass
