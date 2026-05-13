from datetime import UTC, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


class VideoStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class TeamColor(str, Enum):
    RED = "red"
    WHITE = "white"
    BLACK = "black"


class VideoFile(SQLModel, table=True):
    """``video_file`` row; ``user_id`` has no FK (users live in auth_service)."""

    __tablename__ = "video_file"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    original_filename: str = Field(max_length=512)
    stored_path: str = Field(max_length=1024)
    first_team_color: TeamColor
    second_team_color: TeamColor
    status: VideoStatus = Field(default=VideoStatus.UPLOADED, index=True)
    error_message: Optional[str] = Field(default=None, max_length=2048)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_type=DateTime(timezone=True)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_type=DateTime(timezone=True)
    )


class VideoCreate(SQLModel):
    user_id: int
    original_filename: str
    stored_path: str
    first_team_color: TeamColor
    second_team_color: TeamColor


class VideoStatusUpdate(SQLModel):
    status: VideoStatus
    error_message: Optional[str] = None
