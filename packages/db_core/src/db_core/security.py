from typing import Callable

from fastapi import Header, HTTPException, status


def require_internal_key(get_expected_key: Callable[[], str]) -> Callable[..., None]:
    """Build a FastAPI dependency that enforces ``X-Internal-Key``.

    Each service supplies its own zero-arg getter so the secret can be
    re-read from its ``Config`` (and overridden in tests via monkeypatch).
    """

    async def _dep(
        x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
    ) -> None:
        expected = get_expected_key()
        if not x_internal_key or x_internal_key != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing internal API key",
            )

    return _dep
