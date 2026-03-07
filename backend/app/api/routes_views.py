from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_streaming_store
from app.api.models.views import ReportViewRequest, ReportViewResponse
from app.domain.streaming import UNREGISTERED_VIEWER
from app.storage import StreamingStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/views", tags=["views"])


def _extract_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


@router.post("/report", response_model=ReportViewResponse)
async def report_view(
    body: ReportViewRequest,
    request: Request,
    store: StreamingStore = Depends(get_streaming_store),
) -> ReportViewResponse:
    client_ip = _extract_client_ip(request)
    viewer_id = f"{body.earning_channel_login.strip().lower()}+{client_ip}"

    logger.info(
        "POST /views/report viewer_id=%s earning=%s viewed=%s minute=%s",
        viewer_id,
        body.earning_channel_login,
        body.viewed_channel_login,
        body.viewed_minute,
    )
    try:
        result = store.apply_view_report(
            viewer_id=viewer_id,
            viewer_type=UNREGISTERED_VIEWER,
            earning_channel_login=body.earning_channel_login,
            viewed_channel_login=body.viewed_channel_login,
            viewed_minute=body.viewed_minute,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ReportViewResponse(
        credited=result.credited,
        viewer_total_points=result.viewer_total_points,
    )
