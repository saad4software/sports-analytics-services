from datetime import UTC, datetime, timedelta

import jwt
import pytest
from src.core.config import config


@pytest.fixture
def jwt_secret(monkeypatch):
    secret = "b" * 32
    monkeypatch.setattr(config, "jwt_secret", secret)
    monkeypatch.setattr(config, "jwt_algorithm", "HS256")
    return secret


def _access_token(
    *, user_id: int = 1, username: str = "tester", secret: str
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "uid": user_id,
        "username": username,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=60)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def make_token(jwt_secret: str):
    def _inner(*, user_id: int = 1, username: str = "tester") -> str:
        return _access_token(user_id=user_id, username=username, secret=jwt_secret)

    return _inner
