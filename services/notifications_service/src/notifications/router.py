"""Internal HTTP surface for notifications (list for BFF; create for analytics_worker)."""

from fastapi import APIRouter, Depends, status

from src.core.security import internal_key_guard
from src.notifications.dependencies import NotificationServiceDep
from src.notifications.models import Notification, NotificationCreate

router = APIRouter(
    prefix="/internal/notifications",
    tags=["notifications"],
    dependencies=[Depends(internal_key_guard)],
)


@router.post("", response_model=Notification, status_code=status.HTTP_201_CREATED)
async def create_notification(
    data: NotificationCreate, service: NotificationServiceDep
) -> Notification:
    return await service.create(data)


@router.get("", response_model=list[Notification])
async def list_notifications(
    user_id: int, service: NotificationServiceDep
) -> list[Notification]:
    return list(await service.list_for_user(user_id))
