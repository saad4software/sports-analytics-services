from fastapi import APIRouter

from src.clients.notifications_client import notifications_client
from src.core.jwt_auth import CurrentUserDep

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(current_user: CurrentUserDep) -> list[dict]:
    return await notifications_client.list_notifications(current_user.id)
