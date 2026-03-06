from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_streaming_store
from app.api.models.views import ReportViewRequest, ReportViewResponse
from app.storage import InMemoryStreamingStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/views", tags=["views"])


@router.post("/report", response_model=ReportViewResponse)
async def report_view(
    request: ReportViewRequest,
    store: InMemoryStreamingStore = Depends(get_streaming_store),
) -> ReportViewResponse:
    logger.info(
        "POST /views/report viewer=%s target=%s minute=%s",
        request.viewer_channel_login,
        request.target_channel_login,
        request.viewed_minute,
    )
    try:
        result = store.credit_view_minute(
            viewer_channel_login=request.viewer_channel_login,
            target_channel_login=request.target_channel_login,
            viewed_minute=request.viewed_minute,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ReportViewResponse(
        credited=result.credited,
        viewer_points_balance=result.viewer_points_balance,
    )
