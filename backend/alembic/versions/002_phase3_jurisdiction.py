"""Phase 3 - Jurisdiction & Authority tables: authorities, jurisdiction_polygons,
road_segments, responsibility_mappings, accountability_chain_nodes

Revision ID: 002_phase3_jurisdiction
Revises: 001_phase1_core
Create Date: 2026-04-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, ARRAY
import geoalchemy2

revision: str = '002_phase3_jurisdiction'
down_revision: Union[str, None] = '001_phase1_core'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE authoritytype AS ENUM (
                'municipal', 'planning', 'highway', 'state', 'ward_level', 'contractor', 'other'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE layertype AS ENUM (
                'ward', 'circle', 'zone', 'municipality', 'constituency', 'special_road_zone', 'other'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE accountabilitynodetype AS ENUM (
                'field_officer', 'engineer', 'circle_office', 'zonal_office',
                'elected_rep', 'escalation', 'grievance_channel'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # authorities table
    op.create_table(
        'authorities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('authority_type', PgEnum(name='authoritytype', create_type=False), nullable=False),
        sa.Column('parent_authority_id', UUID(as_uuid=True), sa.ForeignKey('authorities.id'), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website_url', sa.String(512), nullable=True),
        sa.Column('grievance_url', sa.String(512), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # jurisdiction_polygons table
    op.create_table(
        'jurisdiction_polygons',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('authority_id', UUID(as_uuid=True), sa.ForeignKey('authorities.id'), nullable=True),
        sa.Column('layer_type', PgEnum(name='layertype', create_type=False), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=True),
        sa.Column('geom', geoalchemy2.Geometry('MULTIPOLYGON', srid=4326), nullable=False),
        sa.Column('source_name', sa.String(255), nullable=True),
        sa.Column('source_version', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_jurisdiction_polygons_geom ON jurisdiction_polygons USING gist (geom)")

    # road_segments table
    op.create_table(
        'road_segments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('alt_names', ARRAY(sa.Text()), nullable=True),
        sa.Column('road_class', sa.String(50), nullable=True),
        sa.Column('osm_way_id', sa.BigInteger(), nullable=True),
        sa.Column('geom', geoalchemy2.Geometry('MULTILINESTRING', srid=4326), nullable=False),
        sa.Column('source_name', sa.String(255), nullable=True),
        sa.Column('source_version', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_road_segments_geom ON road_segments USING gist (geom)")

    # responsibility_mappings table
    op.create_table(
        'responsibility_mappings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('polygon_id', UUID(as_uuid=True), sa.ForeignKey('jurisdiction_polygons.id'), nullable=True),
        sa.Column('road_segment_id', UUID(as_uuid=True), sa.ForeignKey('road_segments.id'), nullable=True),
        sa.Column('primary_authority_id', UUID(as_uuid=True), sa.ForeignKey('authorities.id'), nullable=False),
        sa.Column('secondary_authority_id', UUID(as_uuid=True), sa.ForeignKey('authorities.id'), nullable=True),
        sa.Column('ownership_confidence', sa.Numeric(5, 4), server_default='0', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # accountability_chain_nodes table
    op.create_table(
        'accountability_chain_nodes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('authority_id', UUID(as_uuid=True), sa.ForeignKey('authorities.id'), nullable=False),
        sa.Column('jurisdiction_polygon_id', UUID(as_uuid=True), sa.ForeignKey('jurisdiction_polygons.id'), nullable=True),
        sa.Column('node_type', PgEnum(name='accountabilitynodetype', create_type=False), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Add resolved_authority columns to issues table
    op.add_column('issues', sa.Column('resolved_authority_id', UUID(as_uuid=True), sa.ForeignKey('authorities.id'), nullable=True))
    op.add_column('issues', sa.Column('resolved_ward_id', UUID(as_uuid=True), sa.ForeignKey('jurisdiction_polygons.id'), nullable=True))
    op.add_column('issues', sa.Column('authority_confidence', sa.Numeric(5, 4), nullable=True))


def downgrade() -> None:
    op.drop_column('issues', 'authority_confidence')
    op.drop_column('issues', 'resolved_ward_id')
    op.drop_column('issues', 'resolved_authority_id')
    op.drop_table('accountability_chain_nodes')
    op.drop_table('responsibility_mappings')
    op.drop_index('idx_road_segments_geom', table_name='road_segments')
    op.drop_table('road_segments')
    op.drop_index('idx_jurisdiction_polygons_geom', table_name='jurisdiction_polygons')
    op.drop_table('jurisdiction_polygons')
    op.drop_table('authorities')
    op.execute("DROP TYPE IF EXISTS accountabilitynodetype")
    op.execute("DROP TYPE IF EXISTS layertype")
    op.execute("DROP TYPE IF EXISTS authoritytype")
