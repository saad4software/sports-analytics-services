from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from src.clients.auth_client import auth_client

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


@router.post("/register")
async def register(data: RegisterRequest) -> dict:
    return await auth_client.proxy("/auth/register", json=data.model_dump())


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> dict:
    return await auth_client.proxy(
        "/auth/login",
        data={
            "username": form_data.username,
            "password": form_data.password,
        },
    )
