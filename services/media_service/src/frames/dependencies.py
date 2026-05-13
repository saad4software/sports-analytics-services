from typing import Annotated

from fastapi import Depends

from src.core.db import SessionDep
from src.frames.service import FrameService


def get_frame_service(session: SessionDep) -> FrameService:
    return FrameService(session)


FrameServiceDep = Annotated[FrameService, Depends(get_frame_service)]
