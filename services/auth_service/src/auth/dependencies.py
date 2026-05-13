from typing import Annotated

from fastapi import Depends

from src.auth.repository import UserRepository
from src.auth.service import AuthService
from src.core.db import SessionDep


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def get_auth_service(
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(repo)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
