from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.frames.models import Frame, FrameBulkCreate


class FrameService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_create(self, data: FrameBulkCreate) -> int:
        rows = [
            Frame(
                video_id=data.video_id,
                frame_number=f.frame_number,
                time=f.time,
                first_team_count=f.first_team_count,
                second_team_count=f.second_team_count,
                referee_count=f.referee_count,
            )
            for f in data.frames
        ]
        self.session.add_all(rows)
        await self.session.commit()
        return len(rows)

    async def list_for_video(
        self, video_id: int, limit: int, offset: int
    ) -> Sequence[Frame]:
        result = await self.session.execute(
            select(Frame)
            .where(Frame.video_id == video_id)
            .order_by(Frame.frame_number.asc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
