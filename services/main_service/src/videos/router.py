import logging
import os
import uuid
from pathlib import Path
from typing import Annotated

import aiofiles
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from src.clients.analytics_client import analytics_client
from src.clients.media_client import media_client
from src.core.config import config
from src.core.jwt_auth import CurrentUserDep, oauth2_scheme
from src.videos.models import FrameOut, TeamColor, VideoDetail, VideoSummary

router = APIRouter(prefix="/videos", tags=["videos"])
logger = logging.getLogger(__name__)


def _summary(video: dict) -> VideoSummary:
    base = config.public_base_url.rstrip("/")
    return VideoSummary(
        id=video["id"],
        original_filename=video["original_filename"],
        status=video["status"],
        first_team_color=video["first_team_color"],
        second_team_color=video["second_team_color"],
        created_at=video["created_at"],
        detail_url=f"{base}/videos/{video['id']}",
        file_url=f"{base}/videos/{video['id']}/media",
    )


@router.post("", response_model=VideoSummary, status_code=status.HTTP_201_CREATED)
async def upload_video(
    current_user: CurrentUserDep,
    access_token: Annotated[str, Depends(oauth2_scheme)],
    file: UploadFile = File(...),
    first_team_color: TeamColor = Form(...),
    second_team_color: TeamColor = Form(...),
) -> VideoSummary:
    if first_team_color == second_team_color:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="first_team_color and second_team_color must differ",
        )

    upload_dir = Path(config.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename or "video.mp4").name
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    stored_path = upload_dir / stored_name

    async with aiofiles.open(stored_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            await out.write(chunk)

    video = await media_client.create_video(
        user_id=current_user.id,
        original_filename=safe_name,
        stored_path=str(stored_path.resolve()),
        first_team_color=first_team_color.value,
        second_team_color=second_team_color.value,
    )

    # Hand off to Analytics. If Analytics is down we still return the upload
    # so the client can re-trigger. Status stays ``uploaded`` until the worker
    # picks up the job and calls media_service (see analytics_worker).
    try:
        await analytics_client.submit_job(video["id"], access_token)
    except HTTPException as exc:
        logger.warning(
            "Analytics enqueue failed for video_id=%s user_id=%s: %s %s",
            video["id"],
            current_user.id,
            exc.status_code,
            exc.detail,
        )

    return _summary(video)


@router.get("", response_model=list[VideoSummary])
async def list_videos(current_user: CurrentUserDep) -> list[VideoSummary]:
    videos = await media_client.list_videos(current_user.id)
    return [_summary(v) for v in videos]


@router.get("/{video_id}", response_model=VideoDetail)
async def get_video(
    video_id: int,
    current_user: CurrentUserDep,
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
) -> VideoDetail:
    video = await media_client.get_video(video_id)
    if video["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this video",
        )
    frames = await media_client.list_frames(video_id, limit=limit, offset=offset)
    summary = _summary(video)
    return VideoDetail(
        **summary.model_dump(),
        updated_at=video["updated_at"],
        error_message=video.get("error_message"),
        frames=[FrameOut(**f) for f in frames],
    )


@router.get("/{video_id}/media")
async def stream_video(
    video_id: int, current_user: CurrentUserDep
) -> FileResponse:
    video = await media_client.get_video(video_id)
    if video["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this video",
        )
    path = video["stored_path"]
    if not os.path.exists(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File missing on server"
        )
    return FileResponse(path, filename=video["original_filename"])
