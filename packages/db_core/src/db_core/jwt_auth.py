from typing import Annotated, Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

ACCESS_TOKEN_TYPE = "access"


class CurrentUser(BaseModel):
    id: int
    username: str


def make_oauth2_scheme(token_url: str = "/auth/login") -> OAuth2PasswordBearer:
    return OAuth2PasswordBearer(tokenUrl=token_url, auto_error=True)


def decode_access_token(
    token: str, secret: str, algorithm: str = "HS256"
) -> CurrentUser:
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )
    return CurrentUser(id=payload["uid"], username=payload["username"])


def make_current_user_dependency(
    get_secret: Callable[[], str],
    get_algorithm: Callable[[], str] = lambda: "HS256",
    token_url: str = "/auth/login",
) -> tuple[OAuth2PasswordBearer, Callable[..., CurrentUser]]:
    """Build the ``(oauth2_scheme, get_current_user)`` pair for a service.

    Returning both lets callers depend on ``oauth2_scheme`` directly (for
    routes that need the raw token, e.g. main_service forwarding the token
    to analytics) while reusing the same instance for the user resolver.
    """
    scheme = make_oauth2_scheme(token_url)

    async def _get_current_user(
        token: Annotated[str, Depends(scheme)],
    ) -> CurrentUser:
        return decode_access_token(token, get_secret(), get_algorithm())

    return scheme, _get_current_user
