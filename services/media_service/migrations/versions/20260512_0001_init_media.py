"""init media (videos + frames)

Revision ID: 20260512_0001_media
Revises:
Create Date: 2026-05-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "20260512_0001_media"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "video_file",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "original_filename",
            sqlmodel.sql.sqltypes.AutoString(length=512),
            nullable=False,
        ),
        sa.Column(
            "stored_path",
            sqlmodel.sql.sqltypes.AutoString(length=1024),
            nullable=False,
        ),
        sa.Column(
            "first_team_color",
            sa.Enum("RED", "WHITE", "BLACK", name="teamcolor"),
            nullable=False,
        ),
        sa.Column(
            "second_team_color",
            sa.Enum("RED", "WHITE", "BLACK", name="teamcolor"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "UPLOADED", "PROCESSING", "DONE", "FAILED", name="videostatus"
            ),
            nullable=False,
        ),
        sa.Column(
            "error_message",
            sqlmodel.sql.sqltypes.AutoString(length=2048),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_video_file_user_id"), "video_file", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_video_file_status"), "video_file", ["status"], unique=False
    )
    op.create_table(
        "frame",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("frame_number", sa.Integer(), nullable=False),
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("first_team_count", sa.Integer(), nullable=False),
        sa.Column("second_team_count", sa.Integer(), nullable=False),
        sa.Column("referee_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["video_file.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_frame_video_id"), "frame", ["video_id"], unique=False)
    op.create_index(
        op.f("ix_frame_frame_number"), "frame", ["frame_number"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_frame_frame_number"), table_name="frame")
    op.drop_index(op.f("ix_frame_video_id"), table_name="frame")
    op.drop_table("frame")
    op.drop_index(op.f("ix_video_file_status"), table_name="video_file")
    op.drop_index(op.f("ix_video_file_user_id"), table_name="video_file")
    op.drop_table("video_file")
    op.execute(sa.text("DROP TYPE IF EXISTS videostatus"))
    op.execute(sa.text("DROP TYPE IF EXISTS teamcolor"))
