"""initial schema: analyses and risk_signals tables

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── analyses ──────────────────────────────────────────────────────────────
    op.create_table(
        "analyses",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("repository", sa.String(255), nullable=False),
        sa.Column("branch", sa.String(255), nullable=False),
        sa.Column("commit_sha", sa.String(40), nullable=False),
        sa.Column("total_files_changed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_additions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_deletions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("severity", sa.String(20), nullable=False, server_default="LOW"),
        sa.Column("explanation_text", sa.Text(), nullable=True),
        sa.Column("explanation_status", sa.String(20), nullable=False, server_default="none"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analyses_repository", "analyses", ["repository"])
    op.create_index("ix_analyses_severity", "analyses", ["severity"])
    op.create_index("ix_analyses_created_at", "analyses", ["created_at"])

    # ── risk_signals ──────────────────────────────────────────────────────────
    op.create_table(
        "risk_signals",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("analysis_id", sa.String(36), nullable=False),
        sa.Column("signal_type", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("score_contribution", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("source_analyzer", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analyses.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_risk_signals_analysis_id", "risk_signals", ["analysis_id"])
    op.create_index("ix_risk_signals_signal_type", "risk_signals", ["signal_type"])


def downgrade() -> None:
    op.drop_index("ix_risk_signals_signal_type", table_name="risk_signals")
    op.drop_index("ix_risk_signals_analysis_id", table_name="risk_signals")
    op.drop_table("risk_signals")

    op.drop_index("ix_analyses_created_at", table_name="analyses")
    op.drop_index("ix_analyses_severity", table_name="analyses")
    op.drop_index("ix_analyses_repository", table_name="analyses")
    op.drop_table("analyses")
