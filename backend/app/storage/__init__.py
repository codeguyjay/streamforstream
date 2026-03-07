from __future__ import annotations

import os

from app.storage.base import StreamingStore
from app.storage.in_memory import InMemoryStreamingStore, create_in_memory_storage


def create_storage_from_env() -> StreamingStore:
    backend = os.environ.get("STREAMING_STORE_BACKEND", "in_memory").strip().lower()
    if backend in {"", "in_memory"}:
        return create_in_memory_storage()
    if backend == "dynamodb":
        from app.storage.dynamodb import create_dynamodb_storage

        return create_dynamodb_storage(
            region_name=os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-west-2",
            endpoint_url=os.environ.get("DDB_ENDPOINT_URL") or None,
            streamer_state_table_name=os.environ.get("DDB_STREAMER_STATE_TABLE_NAME", "").strip(),
            view_reports_table_name=os.environ.get("DDB_VIEW_REPORTS_TABLE_NAME", "").strip(),
        )
    raise RuntimeError(f"Unsupported STREAMING_STORE_BACKEND: {backend}")

__all__ = [
    "InMemoryStreamingStore",
    "StreamingStore",
    "create_in_memory_storage",
    "create_storage_from_env",
]
