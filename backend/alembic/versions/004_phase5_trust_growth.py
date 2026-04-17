"""Phase 5: Trust & Growth — issue_supports, subscriptions, search indexes"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    # --- issue_supports table ---
    op.create_table(
        "issue_supports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("issue_id", UUID(as_uuid=True), sa.ForeignKey("issues.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("support_type", sa.String(50), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_issue_supports_issue_id", "issue_supports", ["issue_id"])
    op.create_index("idx_issue_supports_user_id", "issue_supports", ["user_id"])
    op.create_index(
        "idx_issue_supports_rate_limit",
        "issue_supports",
        ["issue_id", "user_id", "support_type"],
    )

    # --- subscriptions table ---
    op.create_table(
        "subscriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index(
        "idx_subscriptions_unique",
        "subscriptions",
        ["user_id", "entity_type", "entity_id"],
        unique=True,
    )

    # --- Full-text search index on issues ---
    op.execute("""
        ALTER TABLE issues ADD COLUMN IF NOT EXISTS search_vector tsvector;
    """)
    op.execute("""
        UPDATE issues SET search_vector = to_tsvector('english', coalesce(title, ''));
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_issues_search_vector ON issues USING gin(search_vector);
    """)

    # --- Full-text search index on road_segments ---
    op.execute("""
        ALTER TABLE road_segments ADD COLUMN IF NOT EXISTS search_vector tsvector;
    """)
    op.execute("""
        UPDATE road_segments SET search_vector = to_tsvector('english', coalesce(name, ''));
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_road_segments_search_vector ON road_segments USING gin(search_vector);
    """)

    # --- Full-text search index on jurisdiction_polygons ---
    op.execute("""
        ALTER TABLE jurisdiction_polygons ADD COLUMN IF NOT EXISTS search_vector tsvector;
    """)
    op.execute("""
        UPDATE jurisdiction_polygons SET search_vector = to_tsvector('english', coalesce(name, '') || ' ' || coalesce(code, ''));
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_jurisdiction_polygons_search_vector ON jurisdiction_polygons USING gin(search_vector);
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_jurisdiction_polygons_search_vector;")
    op.execute("ALTER TABLE jurisdiction_polygons DROP COLUMN IF EXISTS search_vector;")
    op.execute("DROP INDEX IF EXISTS idx_road_segments_search_vector;")
    op.execute("ALTER TABLE road_segments DROP COLUMN IF EXISTS search_vector;")
    op.execute("DROP INDEX IF EXISTS idx_issues_search_vector;")
    op.execute("ALTER TABLE issues DROP COLUMN IF EXISTS search_vector;")
    op.drop_table("subscriptions")
    op.drop_table("issue_supports")
