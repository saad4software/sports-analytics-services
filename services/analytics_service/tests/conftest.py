from datetime import UTC, datetime, timedelta

import jwt
import pytest
from src.core.config import config


@pytest.fixture
def jwt_secret(monkeypatch):
    secret = "a" * 32  # satisfy PyJWT HMAC minimum length guidance in tests
    monkeypatch.setattr(config, "jwt_secret", secret)
    monkeypatch.setattr(config, "jwt_algorithm", "HS256")
    return secret


@pytest.fixture
def make_token(jwt_secret: str):
    def _inner(*, user_id: int = 1, username: str = "worker") -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "uid": user_id,
            "username": username,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=60)).timestamp()),
        }
        return jwt.encode(payload, jwt_secret, algorithm="HS256")

    return _inner
