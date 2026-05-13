from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterator, Literal

import cv2
from ultralytics import YOLO

from .color_classifier import identify_team

logger = logging.getLogger(__name__)

TeamColor = Literal["red", "white", "black"]
DEFAULT_MODEL = "yolo26x.pt"

# The classifier returns these labels; "yellow" is treated as referee.
REFEREE_LABEL = "yellow"


@dataclass
class FrameResult:
    frame_number: int
    time: datetime
    first_team_count: int
    second_team_count: int
    referee_count: int


class VideoProcessor:
    """Headless wrapper around the original FootballCounter loop.

    Yields one FrameResult per video frame so the worker can persist them in
    batches without holding the entire run in memory.
    """

    def __init__(self, model_path: str = DEFAULT_MODEL) -> None:
        self.model_path = model_path
        self._model: YOLO | None = None

    def _ensure_model(self) -> YOLO:
        if self._model is None:
            logger.info("Loading YOLO model from %s", self.model_path)
            self._model = YOLO(self.model_path)
        return self._model

    def iter_frames(
        self,
        video_path: str,
        first_team_color: TeamColor,
        second_team_color: TeamColor,
        started_at: datetime | None = None,
    ) -> Iterator[FrameResult]:
        if first_team_color == second_team_color:
            raise ValueError("first_team_color and second_team_color must differ")

        model = self._ensure_model()
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        base_time = started_at or datetime.now(timezone.utc)
        frame_index = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                results = model(frame, classes=[0], verbose=False)

                first_count = 0
                second_count = 0
                referee_count = 0

                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    crop = frame[y1:y2, x1:x2]
                    if crop.size == 0:
                        continue

                    label = identify_team(crop)
                    if label == first_team_color:
                        first_count += 1
                    elif label == second_team_color:
                        second_count += 1
                    elif label == REFEREE_LABEL:
                        referee_count += 1
                    # background and any unmapped label are ignored.

                offset = (
                    timedelta(seconds=frame_index / fps) if fps > 0 else timedelta(0)
                )
                yield FrameResult(
                    frame_number=frame_index,
                    time=base_time + offset,
                    first_team_count=first_count,
                    second_team_count=second_count,
                    referee_count=referee_count,
                )
                frame_index += 1
        finally:
            cap.release()
