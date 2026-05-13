import logging


def setup_logging(level: int = logging.INFO) -> None:
    """Worker-local logging setup.

    Kept independent of ``db_core`` so the worker image stays free of
    SQLModel / FastAPI runtime dependencies.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
