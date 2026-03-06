from __future__ import annotations

import base64
import json

from fastapi import HTTPException

CURSOR_VERSION = 1


def encode_pagination_cursor(*, token: dict[str, str], scope: dict[str, str]) -> str:
    payload = {
        "v": CURSOR_VERSION,
        "token": token,
        "scope": scope,
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def decode_pagination_cursor(
    cursor: str | None,
    *,
    expected_scope: dict[str, str],
) -> dict[str, str] | None:
    if not cursor:
        return None

    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
        payload = json.loads(decoded)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid cursor") from exc

    if payload.get("v") != CURSOR_VERSION:
        raise HTTPException(status_code=400, detail="Unsupported cursor version")

    scope = payload.get("scope")
    if not isinstance(scope, dict):
        raise HTTPException(status_code=400, detail="Invalid cursor payload")
    if scope != expected_scope:
        raise HTTPException(status_code=400, detail="Cursor scope mismatch")

    token = payload.get("token")
    if token is None:
        return None
    if not isinstance(token, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in token.items()):
        raise HTTPException(status_code=400, detail="Invalid cursor payload")
    return token
