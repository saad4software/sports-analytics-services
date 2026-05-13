from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


class Notification(SQLModel, table=True):
    """``notification`` row; ``user_id`` / ``video_id`` are opaque IDs (no cross-DB FKs)."""

    __tablename__ = "notification"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    video_id: Optional[int] = Field(default=None, index=True)
    type: str = Field(max_length=64)
    message: str = Field(max_length=1024)
    read: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_type=DateTime(timezone=True)
    )


class NotificationCreate(SQLModel):
    user_id: int
    video_id: Optional[int] = None
    type: str
    message: str
