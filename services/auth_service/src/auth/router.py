from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.dependencies import AuthServiceDep
from src.auth.models import AccessToken, RegisterRequest, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, service: AuthServiceDep) -> UserPublic:
    return await service.register(data)


@router.post("/login", response_model=AccessToken)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
) -> AccessToken:
    return await service.login(form_data.username, form_data.password)
