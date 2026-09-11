from __future__ import annotations

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.social.x.config import get_x_settings
from app.social.x.prospecting import (
    XReplyOpportunityNotFoundError,
    XReplyOpportunityStateError,
    approve_opportunity,
    list_opportunities,
    reject_opportunity,
)
from app.social.x.schemas import (
    ApproveXReplyOpportunityRequest,
    ScheduleXPostRequest,
    ScheduledXPostResponse,
    XReplyOpportunityResponse,
)
from app.social.x.service import (
    XScheduledPostNotFoundError,
    XScheduledPostStateError,
    x_schedule_service,
)


router = APIRouter(prefix="/api/social/x", tags=["X Scheduler"])


def _require_admin(authorization: str | None = Header(default=None)) -> None:
    expected = get_x_settings().admin_token
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="X_SCHEDULER_ADMIN_TOKEN is not configured.",
        )
    prefix = "Bearer "
    supplied = authorization[len(prefix):].strip() if authorization and authorization.startswith(prefix) else ""
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid scheduler admin token.")


@router.post(
    "/scheduled",
    response_model=ScheduledXPostResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_require_admin)],
)
def schedule_x_post(
    request: ScheduleXPostRequest,
    db: Session = Depends(get_db),
) -> ScheduledXPostResponse:
    try:
        return x_schedule_service.schedule(
            db=db,
            text=request.text,
            scheduled_at=request.scheduled_at,
            language=request.language,
            media_path=request.media_path,
            parent_source_key=request.parent_source_key,
            source_key=request.source_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/scheduled",
    response_model=list[ScheduledXPostResponse],
    dependencies=[Depends(_require_admin)],
)
def list_x_posts(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ScheduledXPostResponse]:
    return x_schedule_service.list(db=db, status=status_filter, limit=limit)


@router.delete(
    "/scheduled/{post_id}",
    response_model=ScheduledXPostResponse,
    dependencies=[Depends(_require_admin)],
)
def cancel_x_post(
    post_id: int,
    db: Session = Depends(get_db),
) -> ScheduledXPostResponse:
    try:
        return x_schedule_service.cancel(db=db, post_id=post_id)
    except XScheduledPostNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except XScheduledPostStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/scheduled/{post_id}/retry",
    response_model=ScheduledXPostResponse,
    dependencies=[Depends(_require_admin)],
)
def retry_x_post(
    post_id: int,
    db: Session = Depends(get_db),
) -> ScheduledXPostResponse:
    try:
        return x_schedule_service.retry(db=db, post_id=post_id)
    except XScheduledPostNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except XScheduledPostStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get(
    "/opportunities",
    response_model=list[XReplyOpportunityResponse],
    dependencies=[Depends(_require_admin)],
)
def list_x_reply_opportunities(
    status_filter: str | None = Query(default="GENERATED", alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[XReplyOpportunityResponse]:
    return list_opportunities(db=db, status=status_filter, limit=limit)


@router.post(
    "/opportunities/{opportunity_id}/approve",
    response_model=XReplyOpportunityResponse,
    dependencies=[Depends(_require_admin)],
)
def approve_x_reply_opportunity(
    opportunity_id: int,
    request: ApproveXReplyOpportunityRequest,
    db: Session = Depends(get_db),
) -> XReplyOpportunityResponse:
    try:
        return approve_opportunity(
            db=db,
            opportunity_id=opportunity_id,
            reply_text=request.reply_text,
        )
    except XReplyOpportunityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except XReplyOpportunityStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post(
    "/opportunities/{opportunity_id}/reject",
    response_model=XReplyOpportunityResponse,
    dependencies=[Depends(_require_admin)],
)
def reject_x_reply_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
) -> XReplyOpportunityResponse:
    try:
        return reject_opportunity(db=db, opportunity_id=opportunity_id)
    except XReplyOpportunityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except XReplyOpportunityStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
