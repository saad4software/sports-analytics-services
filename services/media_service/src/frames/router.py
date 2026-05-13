from fastapi import APIRouter, Depends, Query

from src.core.security import internal_key_guard
from src.frames.dependencies import FrameServiceDep
from src.frames.models import Frame, FrameBulkCreate

router = APIRouter(
    prefix="/internal/frames",
    tags=["frames"],
    dependencies=[Depends(internal_key_guard)],
)


@router.post("/bulk")
async def bulk_create_frames(
    data: FrameBulkCreate, service: FrameServiceDep
) -> dict:
    inserted = await service.bulk_create(data)
    return {"inserted": inserted}


@router.get("", response_model=list[Frame])
async def list_frames(
    video_id: int,
    service: FrameServiceDep,
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
) -> list[Frame]:
    return list(await service.list_for_video(video_id, limit, offset))
