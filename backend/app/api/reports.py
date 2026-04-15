import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.db.session import get_db
from app.schemas.schemas import (
    ReportCreateRequest, ReportCreateResponse, ReportResponse, MediaResponse,
)
from app.services.reports import create_report, get_report_by_id
from app.services.storage import get_public_url
from app.auth.dependencies import get_current_user_optional
from app.models.models import User
from app.models.enums import ModerationStatus

router = APIRouter(prefix="/reports", tags=["reports"])
limiter = Limiter(key_func=get_remote_address)


@router.post("", response_model=ReportCreateResponse)
@limiter.limit("10/hour")
async def create_report_endpoint(
    request: Request,
    data: ReportCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    user_id = user.id if user else None
    report = await create_report(db, data, user_id=user_id)
    return ReportCreateResponse(
        id=report.id,
        moderation_status=report.moderation_status,
        created_at=report.created_at,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    report = await get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Only show approved reports publicly
    if report.moderation_status != ModerationStatus.approved and report.moderation_status != ModerationStatus.pending_moderation:
        raise HTTPException(status_code=404, detail="Report not found")

    media_list = [
        MediaResponse(
            id=m.id,
            storage_key=m.storage_key,
            media_type=m.media_type,
            mime_type=m.mime_type,
            width=m.width,
            height=m.height,
            size_bytes=m.size_bytes,
            url=get_public_url(m.storage_key),
        )
        for m in report.media
    ]

    return ReportResponse(
        id=report.id,
        latitude=float(report.latitude),
        longitude=float(report.longitude),
        issue_type=report.issue_type,
        severity=report.severity,
        description=report.description,
        landmark=report.landmark,
        road_name_input=report.road_name_input,
        direction_of_travel=report.direction_of_travel,
        dangerous_for_bikes=report.dangerous_for_bikes,
        worse_in_rain=report.worse_in_rain,
        worse_at_night=report.worse_at_night,
        moderation_status=report.moderation_status,
        source=report.source,
        submitted_at=report.submitted_at,
        created_at=report.created_at,
        media=media_list,
    )
