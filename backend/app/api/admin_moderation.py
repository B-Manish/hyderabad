"""Admin moderation API — report review, approval, rejection."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.auth.dependencies import require_role
from app.models.enums import UserRole, ModerationStatus, IssueType, Severity
from app.models.models import Report, User
from app.services.moderation import approve_report, reject_report
from app.services.storage import get_public_url
from app.schemas.schemas import MediaResponse
from pydantic import BaseModel


router = APIRouter(prefix="/admin/reports", tags=["admin-moderation"])


class AdminReportItem(BaseModel):
    id: uuid.UUID
    latitude: float
    longitude: float
    issue_type: str
    severity: str
    description: str | None = None
    landmark: str | None = None
    road_name_input: str | None = None
    moderation_status: str
    source: str
    submitted_at: str
    user_name: str | None = None
    user_email: str | None = None
    issue_id: uuid.UUID | None = None
    media: list[MediaResponse] = []

    model_config = {"from_attributes": True}


class PaginatedAdminReports(BaseModel):
    items: list[AdminReportItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ApproveRequest(BaseModel):
    notes: str | None = None


class RejectRequest(BaseModel):
    reason: str
    notes: str | None = None


@router.get("", response_model=PaginatedAdminReports)
async def list_reports(
    moderation_status: str | None = Query(None),
    issue_type: str | None = Query(None),
    severity: str | None = Query(None),
    sort_by: str = Query("submitted_at"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.moderator)),
):
    query = select(Report).options(selectinload(Report.media), selectinload(Report.user))

    if moderation_status:
        query = query.where(Report.moderation_status == ModerationStatus(moderation_status))
    if issue_type:
        query = query.where(Report.issue_type == IssueType(issue_type))
    if severity:
        query = query.where(Report.severity == Severity(severity))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    sort_map = {
        "submitted_at": Report.submitted_at.desc(),
        "severity": Report.severity.desc(),
    }
    query = query.order_by(sort_map.get(sort_by, Report.submitted_at.desc()))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    reports = result.scalars().unique().all()

    items = []
    for r in reports:
        media_list = []
        for m in r.media:
            media_list.append(MediaResponse(
                id=m.id,
                storage_key=m.storage_key,
                media_type=m.media_type,
                mime_type=m.mime_type,
                width=m.width,
                height=m.height,
                size_bytes=m.size_bytes,
                url=get_public_url(m.storage_key),
            ))
        items.append(AdminReportItem(
            id=r.id,
            latitude=float(r.latitude),
            longitude=float(r.longitude),
            issue_type=r.issue_type.value,
            severity=r.severity.value,
            description=r.description,
            landmark=r.landmark,
            road_name_input=r.road_name_input,
            moderation_status=r.moderation_status.value,
            source=r.source.value,
            submitted_at=r.submitted_at.isoformat(),
            user_name=r.user.name if r.user else None,
            user_email=r.user.email if r.user else None,
            issue_id=r.issue_id,
            media=media_list,
        ))

    import math
    return PaginatedAdminReports(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )


@router.post("/{report_id}/approve")
async def approve(
    report_id: uuid.UUID,
    body: ApproveRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.moderator)),
):
    try:
        report = await approve_report(db, report_id, user, body.notes)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "approved", "report_id": str(report.id), "issue_id": str(report.issue_id)}


@router.post("/{report_id}/reject")
async def reject(
    report_id: uuid.UUID,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.moderator)),
):
    try:
        report = await reject_report(db, report_id, user, body.reason, body.notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "rejected", "report_id": str(report.id), "reason": body.reason}
