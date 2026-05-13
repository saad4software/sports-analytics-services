from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


class Frame(SQLModel, table=True):
    __tablename__ = "frame"

    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="video_file.id", index=True)
    frame_number: int = Field(index=True)
    time: datetime = Field(sa_type=DateTime(timezone=True))
    first_team_count: int = Field(default=0)
    second_team_count: int = Field(default=0)
    referee_count: int = Field(default=0)


class FrameCreate(SQLModel):
    frame_number: int
    time: datetime
    first_team_count: int = 0
    second_team_count: int = 0
    referee_count: int = 0


class FrameBulkCreate(SQLModel):
    video_id: int
    frames: list[FrameCreate]
