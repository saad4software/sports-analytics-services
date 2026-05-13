from datetime import UTC, datetime
from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.videos.models import VideoCreate, VideoFile, VideoStatus, VideoStatusUpdate


class VideoService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: VideoCreate) -> VideoFile:
        if data.first_team_color == data.second_team_color:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="first_team_color and second_team_color must differ",
            )
        video = VideoFile(**data.model_dump())
        self.session.add(video)
        await self.session.commit()
        await self.session.refresh(video)
        return video

    async def get(self, video_id: int) -> Optional[VideoFile]:
        return await self.session.get(VideoFile, video_id)

    async def list_for_user(self, user_id: int) -> Sequence[VideoFile]:
        result = await self.session.execute(
            select(VideoFile)
            .where(VideoFile.user_id == user_id)
            .order_by(VideoFile.created_at.desc())
        )
        return result.scalars().all()

    async def update_status(
        self, video_id: int, data: VideoStatusUpdate
    ) -> VideoFile:
        video = await self.get(video_id)
        if video is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
            )
        video.status = data.status
        video.error_message = data.error_message
        video.updated_at = datetime.now(UTC)
        self.session.add(video)
        await self.session.commit()
        await self.session.refresh(video)
        return video

    async def set_status_idempotent(
        self,
        video_id: int,
        new_status: VideoStatus,
        *,
        error_message: Optional[str] = None,
    ) -> Optional[VideoFile]:
        """Update status if the row exists; no-op (returns None) otherwise.

        Callers that cannot treat a missing row as an error (for example
        idempotent background updates) use this instead of ``update_status``.
        """
        video = await self.get(video_id)
        if video is None:
            return None
        video.status = new_status
        if error_message is not None:
            video.error_message = error_message
        video.updated_at = datetime.now(UTC)
        self.session.add(video)
        await self.session.commit()
        await self.session.refresh(video)
        return video
