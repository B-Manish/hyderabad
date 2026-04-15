"""Phase 1 - Core tables: users, reports, report_media, issues, issue_reports, issue_status_history

Revision ID: 001_phase1_core
Revises: None
Create Date: 2026-04-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
import geoalchemy2

revision: str = '001_phase1_core'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Create enum types idempotently (PostgreSQL 16 compatible)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE userrole AS ENUM ('citizen', 'moderator', 'admin');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE issuetype AS ENUM (
                'pothole', 'road_surface_broken', 'uneven_resurfacing', 'waterlogging',
                'open_manhole', 'dangerous_speed_breaker', 'loose_gravel_debris',
                'construction_spill', 'missing_lane_markings', 'road_shoulder_collapse',
                'road_cave_in', 'other_road_safety'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE severity AS ENUM ('low', 'medium', 'high', 'critical');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE moderationstatus AS ENUM (
                'pending_moderation', 'approved', 'rejected_abuse',
                'low_quality_evidence', 'duplicate_merged'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE issuestatus AS ENUM (
                'reported', 'under_review', 'verified', 'assigned', 'in_progress',
                'resolved', 'rejected', 'duplicate'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE mediatype AS ENUM ('image', 'video');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE reportsource AS ENUM ('web', 'mobile-web', 'admin');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255)),
        sa.Column('email', sa.String(255), nullable=True, unique=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('auth_provider', sa.String(50), server_default='anonymous'),
        sa.Column('is_anonymous_allowed', sa.Boolean(), server_default='true'),
        sa.Column('role', PgEnum(name='userrole', create_type=False), nullable=False, server_default='citizen'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # issues table (created before reports due to FK)
    op.create_table(
        'issues',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('primary_report_id', UUID(as_uuid=True), nullable=True),  # FK added later
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('canonical_issue_type', PgEnum(name='issuetype', create_type=False), nullable=False),
        sa.Column('canonical_severity', PgEnum(name='severity', create_type=False), nullable=False),
        sa.Column('status', PgEnum(name='issuestatus', create_type=False), nullable=False, server_default='reported'),
        sa.Column('latitude', sa.Numeric(10, 7), nullable=False),
        sa.Column('longitude', sa.Numeric(10, 7), nullable=False),
        sa.Column('geom', geoalchemy2.Geography('POINT', srid=4326), nullable=False),
        sa.Column('road_segment_id', UUID(as_uuid=True), nullable=True),
        sa.Column('first_reported_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('latest_reported_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('support_count', sa.Integer(), server_default='0'),
        sa.Column('report_count', sa.Integer(), server_default='1'),
        sa.Column('verification_score', sa.Numeric(5, 4), server_default='0'),
        sa.Column('is_verified', sa.Boolean(), server_default='false'),
        sa.Column('public_visibility', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # GiST index on issues.geom (IF NOT EXISTS because geoalchemy2 may auto-create it)
    op.execute("CREATE INDEX IF NOT EXISTS idx_issues_geom ON issues USING gist (geom)")

    # reports table
    op.create_table(
        'reports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('issue_id', UUID(as_uuid=True), sa.ForeignKey('issues.id'), nullable=True),
        sa.Column('latitude', sa.Numeric(10, 7), nullable=False),
        sa.Column('longitude', sa.Numeric(10, 7), nullable=False),
        sa.Column('geom', geoalchemy2.Geography('POINT', srid=4326), nullable=False),
        sa.Column('issue_type', PgEnum(name='issuetype', create_type=False), nullable=False),
        sa.Column('severity', PgEnum(name='severity', create_type=False), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('landmark', sa.String(255), nullable=True),
        sa.Column('road_name_input', sa.String(255), nullable=True),
        sa.Column('direction_of_travel', sa.String(100), nullable=True),
        sa.Column('dangerous_for_bikes', sa.Boolean(), server_default='false'),
        sa.Column('worse_in_rain', sa.Boolean(), server_default='false'),
        sa.Column('worse_at_night', sa.Boolean(), server_default='false'),
        sa.Column('moderation_status', PgEnum(name='moderationstatus', create_type=False), nullable=False, server_default='pending_moderation'),
        sa.Column('source', PgEnum(name='reportsource', create_type=False), nullable=False, server_default='web'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # GiST index on reports.geom (IF NOT EXISTS because geoalchemy2 may auto-create it)
    op.execute("CREATE INDEX IF NOT EXISTS idx_reports_geom ON reports USING gist (geom)")

    # Add FK from issues.primary_report_id -> reports.id
    op.create_foreign_key('fk_issues_primary_report', 'issues', 'reports', ['primary_report_id'], ['id'])

    # report_media table
    op.create_table(
        'report_media',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('report_id', UUID(as_uuid=True), sa.ForeignKey('reports.id'), nullable=False),
        sa.Column('storage_key', sa.String(512), nullable=False),
        sa.Column('media_type', PgEnum(name='mediatype', create_type=False), nullable=False, server_default='image'),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # issue_reports table
    op.create_table(
        'issue_reports',
        sa.Column('issue_id', UUID(as_uuid=True), sa.ForeignKey('issues.id'), primary_key=True),
        sa.Column('report_id', UUID(as_uuid=True), sa.ForeignKey('reports.id'), primary_key=True),
        sa.Column('linked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('link_reason', sa.String(255), nullable=True),
    )

    # issue_status_history table
    op.create_table(
        'issue_status_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('issue_id', UUID(as_uuid=True), sa.ForeignKey('issues.id'), nullable=False),
        sa.Column('old_status', sa.String(50), nullable=True),
        sa.Column('new_status', sa.String(50), nullable=False),
        sa.Column('changed_by_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('issue_status_history')
    op.drop_table('issue_reports')
    op.drop_table('report_media')
    op.drop_constraint('fk_issues_primary_report', 'issues', type_='foreignkey')
    op.drop_index('idx_reports_geom', table_name='reports')
    op.drop_table('reports')
    op.drop_index('idx_issues_geom', table_name='issues')
    op.drop_table('issues')
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS reportsource")
    op.execute("DROP TYPE IF EXISTS mediatype")
    op.execute("DROP TYPE IF EXISTS issuestatus")
    op.execute("DROP TYPE IF EXISTS moderationstatus")
    op.execute("DROP TYPE IF EXISTS severity")
    op.execute("DROP TYPE IF EXISTS issuetype")
    op.execute("DROP TYPE IF EXISTS userrole")
