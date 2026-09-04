"""create incidents and incident_evidence tables

Revision ID: 99a8d91ef07d
Revises: 70c8d91ef07c
Create Date: 2026-09-04 12:10:00.000000

"""
from typing import Sequence, Union
import geoalchemy2
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '99a8d91ef07d'
down_revision: Union[str, Sequence[str], None] = '70c8d91ef07c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'incidents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('primary_event_id', sa.UUID(), nullable=False),
        sa.Column('incident_type', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), server_default='open', nullable=False),
        sa.Column('suspected_plate', sa.Text(), nullable=True),
        sa.Column('suspected_plate_confidence', sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column('location', geoalchemy2.types.Geography(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeogFromText', name='geography'), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.CheckConstraint("incident_type IN ('suspected_collision', 'suspected_hit_and_run')", name='ck_incidents_type'),
        sa.CheckConstraint("status IN ('open', 'under_review', 'closed', 'dismissed')", name='ck_incidents_status'),
        sa.ForeignKeyConstraint(['primary_event_id'], ['events.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_incidents_status', 'incidents', ['status'])
    op.create_index('ix_incidents_occurred_at', 'incidents', ['occurred_at'])

    op.create_table(
        'incident_evidence',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('incident_id', sa.UUID(), nullable=False),
        sa.Column('evidence_type', sa.Text(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("evidence_type IN ('image', 'vehicle_crop', 'plate_crop', 'video_clip')", name='ck_incident_evidence_type'),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_incident_evidence_incident_id', 'incident_evidence', ['incident_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_incident_evidence_incident_id', table_name='incident_evidence')
    op.drop_table('incident_evidence')

    op.drop_index('ix_incidents_occurred_at', table_name='incidents')
    op.drop_index('ix_incidents_status', table_name='incidents')
    op.drop_table('incidents')
