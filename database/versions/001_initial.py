"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cities table
    op.create_table(
        'cities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('country_code', sa.String(10), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('timezone', sa.String(50), nullable=True, server_default='UTC'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('is_monitored', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cities_id', 'cities', ['id'])
    op.create_index('ix_cities_name', 'cities', ['name'])

    # Air quality records table
    op.create_table(
        'air_quality_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('city_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('aqi', sa.Integer(), nullable=False),
        sa.Column('aqi_category', sa.String(50), nullable=False),
        sa.Column('pm2_5', sa.Float(), nullable=True),
        sa.Column('pm10', sa.Float(), nullable=True),
        sa.Column('co', sa.Float(), nullable=True),
        sa.Column('no2', sa.Float(), nullable=True),
        sa.Column('so2', sa.Float(), nullable=True),
        sa.Column('o3', sa.Float(), nullable=True),
        sa.Column('nh3', sa.Float(), nullable=True),
        sa.Column('no', sa.Float(), nullable=True),
        sa.Column('nox', sa.Float(), nullable=True),
        sa.Column('ow_aqi', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_air_quality_records_id', 'air_quality_records', ['id'])
    op.create_index('ix_aqr_city_timestamp', 'air_quality_records', ['city_id', 'timestamp'])
    op.create_index('ix_aqr_timestamp', 'air_quality_records', ['timestamp'])
    op.create_index('ix_aqr_aqi', 'air_quality_records', ['aqi'])

    # Alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('city_id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(20), nullable=False),
        sa.Column('channel', sa.String(20), nullable=False),
        sa.Column('aqi_value', sa.Integer(), nullable=False),
        sa.Column('aqi_category', sa.String(50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_sent', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_alerts_id', 'alerts', ['id'])
    op.create_index('ix_alerts_city_id', 'alerts', ['city_id'])


def downgrade() -> None:
    op.drop_table('alerts')
    op.drop_table('air_quality_records')
    op.drop_table('cities')
