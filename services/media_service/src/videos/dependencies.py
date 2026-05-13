from typing import Annotated

from fastapi import Depends

from src.core.db import SessionDep
from src.videos.service import VideoService


def get_video_service(session: SessionDep) -> VideoService:
    return VideoService(session)


VideoServiceDep = Annotated[VideoService, Depends(get_video_service)]
