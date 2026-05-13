from fastapi import APIRouter, Depends, HTTPException, status

from src.core.security import internal_key_guard
from src.videos.dependencies import VideoServiceDep
from src.videos.models import VideoCreate, VideoFile, VideoStatusUpdate

router = APIRouter(
    prefix="/internal/videos",
    tags=["videos"],
    dependencies=[Depends(internal_key_guard)],
)


@router.post("", response_model=VideoFile, status_code=status.HTTP_201_CREATED)
async def create_video(data: VideoCreate, service: VideoServiceDep) -> VideoFile:
    return await service.create(data)


@router.get("", response_model=list[VideoFile])
async def list_videos(user_id: int, service: VideoServiceDep) -> list[VideoFile]:
    return list(await service.list_for_user(user_id))


@router.get("/{video_id}", response_model=VideoFile)
async def get_video(video_id: int, service: VideoServiceDep) -> VideoFile:
    video = await service.get(video_id)
    if video is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )
    return video


@router.patch("/{video_id}/status", response_model=VideoFile)
async def update_video_status(
    video_id: int, data: VideoStatusUpdate, service: VideoServiceDep
) -> VideoFile:
    return await service.update_status(video_id, data)
