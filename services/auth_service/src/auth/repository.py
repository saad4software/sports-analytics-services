from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.auth.models import User, UserCreate


class UserRepository:
    """Direct SQLModel access for the ``user`` table (auth_service only)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def create(self, data: UserCreate) -> User:
        user = User(username=data.username, hashed_password=data.hashed_password)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
