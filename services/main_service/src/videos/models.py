from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TeamColor(str, Enum):
    RED = "red"
    WHITE = "white"
    BLACK = "black"


class VideoSummary(BaseModel):
    id: int
    original_filename: str
    status: str
    first_team_color: TeamColor
    second_team_color: TeamColor
    created_at: datetime
    detail_url: str
    file_url: str


class FrameOut(BaseModel):
    frame_number: int
    time: datetime
    first_team_count: int
    second_team_count: int
    referee_count: int


class VideoDetail(VideoSummary):
    updated_at: datetime
    error_message: Optional[str] = None
    frames: list[FrameOut]
