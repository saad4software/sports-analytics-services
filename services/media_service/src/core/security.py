from db_core import require_internal_key

from src.core.config import config

internal_key_guard = require_internal_key(lambda: config.internal_api_key)
