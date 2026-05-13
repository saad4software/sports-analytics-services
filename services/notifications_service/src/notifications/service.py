from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.notifications.models import Notification, NotificationCreate


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: NotificationCreate) -> Notification:
        notif = Notification(**data.model_dump())
        self.session.add(notif)
        await self.session.commit()
        await self.session.refresh(notif)
        return notif

    async def list_for_user(self, user_id: int) -> Sequence[Notification]:
        result = await self.session.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        return result.scalars().all()
