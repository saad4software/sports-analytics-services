from datetime import UTC, datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field as PydField
from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """``users`` row — owned by auth_service.

    No foreign keys point at this table from anywhere else: cross-service
    references (videos, notifications) carry the user id as an opaque
    integer with no DB-enforced constraint, which is the database-per-
    service contract.
    """

    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(min_length=3, max_length=255, unique=True, index=True)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_type=DateTime(timezone=True)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_type=DateTime(timezone=True)
    )


class UserCreate(SQLModel):
    username: str = Field(min_length=3, max_length=255)
    hashed_password: str = Field(max_length=255)


class RegisterRequest(BaseModel):
    username: str = PydField(min_length=3, max_length=255)
    password: str = PydField(min_length=8, max_length=128)


class LoginCredentials(BaseModel):
    """Validates OAuth2 login fields (form body is not validated by FastAPI)."""

    username: str = PydField(min_length=3, max_length=255)
    password: str = PydField(min_length=1, max_length=128)


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    id: int
    username: str
