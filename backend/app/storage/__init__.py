from __future__ import annotations

import os

from app.storage.base import StreamingStore
from app.storage.in_memory import InMemoryStreamingStore, create_in_memory_storage


def _clean_env_value(raw: str | None, default: str = "") -> str:
    value = (raw if raw is not None else default).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1].strip()
    return value


def create_storage_from_env() -> StreamingStore:
    backend = _clean_env_value(os.environ.get("STREAMING_STORE_BACKEND"), "in_memory").lower()
    if backend in {"", "in_memory"}:
        return create_in_memory_storage()
    if backend == "dynamodb":
        from app.storage.dynamodb import create_dynamodb_storage

        return create_dynamodb_storage(
            region_name=(
                _clean_env_value(os.environ.get("AWS_REGION"))
                or _clean_env_value(os.environ.get("AWS_DEFAULT_REGION"))
                or "us-west-2"
            ),
            endpoint_url=_clean_env_value(os.environ.get("DDB_ENDPOINT_URL")) or None,
            streamer_state_table_name=_clean_env_value(os.environ.get("DDB_STREAMER_STATE_TABLE_NAME")),
            view_reports_table_name=_clean_env_value(os.environ.get("DDB_VIEW_REPORTS_TABLE_NAME")),
            aws_access_key_id=_clean_env_value(os.environ.get("AWS_ACCESS_KEY_ID")) or None,
            aws_secret_access_key=_clean_env_value(os.environ.get("AWS_SECRET_ACCESS_KEY")) or None,
            aws_session_token=_clean_env_value(os.environ.get("AWS_SESSION_TOKEN")) or None,
        )
    raise RuntimeError(f"Unsupported STREAMING_STORE_BACKEND: {backend}")

__all__ = [
    "InMemoryStreamingStore",
    "StreamingStore",
    "create_in_memory_storage",
    "create_storage_from_env",
]
