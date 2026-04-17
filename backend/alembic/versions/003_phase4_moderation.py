"""Phase 4: Admin & Moderation — audit_logs and moderation_actions tables.

Revision ID: 003_phase4_moderation
Revises: 002_phase3_jurisdiction
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "003_phase4_moderation"
down_revision = "002_phase3_jurisdiction"
branch_labels = None
depends_on = None


def upgrade():
    # --- audit_logs ---
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("metadata_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_actor", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_created", "audit_logs", ["created_at"])

    # --- moderation_actions ---
    op.create_table(
        "moderation_actions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("report_id", UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=True),
        sa.Column("issue_id", UUID(as_uuid=True), sa.ForeignKey("issues.id"), nullable=True),
        sa.Column("moderator_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_moderation_actions_report", "moderation_actions", ["report_id"])
    op.create_index("ix_moderation_actions_issue", "moderation_actions", ["issue_id"])

    # Add is_active column to users for deactivation support
    op.add_column("users", sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False))


def downgrade():
    op.drop_column("users", "is_active")
    op.drop_table("moderation_actions")
    op.drop_table("audit_logs")
