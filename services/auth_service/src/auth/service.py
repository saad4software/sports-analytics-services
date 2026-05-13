from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from pwdlib import PasswordHash
from pydantic import ValidationError

from src.auth.models import (
    AccessToken,
    LoginCredentials,
    RegisterRequest,
    User,
    UserCreate,
    UserPublic,
)
from src.auth.repository import UserRepository
from src.core.config import config

_password_hash = PasswordHash.recommended()
ACCESS_TOKEN_TYPE = "access"


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def register(self, data: RegisterRequest) -> UserPublic:
        if await self.repo.get_by_username(data.username) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        hashed = _password_hash.hash(data.password)
        user = await self.repo.create(
            UserCreate(username=data.username, hashed_password=hashed)
        )
        return UserPublic(id=user.id, username=user.username)

    async def login(self, username: str, password: str) -> AccessToken:
        try:
            creds = LoginCredentials.model_validate(
                {"username": username, "password": password}
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=e.errors(),
            ) from e
        user = await self.repo.get_by_username(creds.username)
        if user is None or not _password_hash.verify(
            creds.password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return AccessToken(access_token=self._encode_token(user))

    @staticmethod
    def _encode_token(user: User) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "uid": user.id,
            "username": user.username,
            "type": ACCESS_TOKEN_TYPE,
            "iat": int(now.timestamp()),
            "exp": int(
                (now + timedelta(minutes=config.jwt_access_exp_minutes)).timestamp()
            ),
        }
        return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)
