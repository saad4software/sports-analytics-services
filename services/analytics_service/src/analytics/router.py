from fastapi import APIRouter, status
from pydantic import BaseModel

from src.analytics.queue import enqueue_job
from src.core.jwt_auth import CurrentUserDep

router = APIRouter(prefix="/analytics", tags=["analytics"])


class ProcessRequest(BaseModel):
    video_id: int


@router.post("/process", status_code=status.HTTP_202_ACCEPTED)
async def submit_process_job(
    data: ProcessRequest, current_user: CurrentUserDep
) -> dict:
    await enqueue_job({"video_id": data.video_id, "requested_by": current_user.id})
    return {"queued": True, "video_id": data.video_id}
