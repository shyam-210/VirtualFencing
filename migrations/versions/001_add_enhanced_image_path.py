"""Add enhanced_image_path to FenceCrossEvent

Revision ID: 001
Revises: 
Create Date: 2025-08-27 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add enhanced_image_path column to fence_cross_events table
    op.add_column('fence_cross_events', sa.Column('enhanced_image_path', sa.String(200), nullable=True))

def downgrade():
    # Remove enhanced_image_path column from fence_cross_events table
    op.drop_column('fence_cross_events', 'enhanced_image_path')
