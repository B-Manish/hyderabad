"""Admin issue management API — status, metadata, merge, export."""
import uuid
import math
import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.auth.dependencies import require_role
from app.models.enums import UserRole, IssueStatus, IssueType, Severity
from app.models.models import Issue, User, IssueStatusHistory
from app.services.moderation import change_issue_status, update_issue_metadata, merge_issues
from pydantic import BaseModel


router = APIRouter(prefix="/admin/issues", tags=["admin-issues"])


class AdminIssueItem(BaseModel):
    id: uuid.UUID
    title: str
    canonical_issue_type: str
    canonical_severity: str
    status: str
    latitude: float
    longitude: float
    report_count: int
    support_count: int
    is_verified: bool
    first_reported_at: str
    latest_reported_at: str
    resolved_at: str | None = None

    model_config = {"from_attributes": True}


class PaginatedAdminIssues(BaseModel):
    items: list[AdminIssueItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class StatusChangeRequest(BaseModel):
    new_status: str
    reason: str | None = None


class MetadataEditRequest(BaseModel):
    title: str | None = None
    canonical_issue_type: str | None = None
    canonical_severity: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class MergeRequest(BaseModel):
    merge_issue_ids: list[uuid.UUID]
    surviving_issue_id: uuid.UUID
    notes: str | None = None


class StatusHistoryItem(BaseModel):
    id: uuid.UUID
    old_status: str | None
    new_status: str
    change_reason: str | None
    created_at: str


@router.get("", response_model=PaginatedAdminIssues)
async def list_issues(
    status: str | None = Query(None),
    issue_type: str | None = Query(None),
    severity: str | None = Query(None),
    sort_by: str = Query("latest_reported_at"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.moderator)),
):
    query = select(Issue)
    if status:
        query = query.where(Issue.status == IssueStatus(status))
    if issue_type:
        query = query.where(Issue.canonical_issue_type == IssueType(issue_type))
    if severity:
        query = query.where(Issue.canonical_severity == Severity(severity))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    sort_map = {
        "latest_reported_at": Issue.latest_reported_at.desc(),
        "first_reported_at": Issue.first_reported_at.desc(),
        "severity": Issue.canonical_severity.desc(),
        "report_count": Issue.report_count.desc(),
        "support_count": Issue.support_count.desc(),
    }
    query = query.order_by(sort_map.get(sort_by, Issue.latest_reported_at.desc()))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    issues = result.scalars().all()

    items = []
    for i in issues:
        items.append(AdminIssueItem(
            id=i.id,
            title=i.title,
            canonical_issue_type=i.canonical_issue_type.value,
            canonical_severity=i.canonical_severity.value,
            status=i.status.value,
            latitude=float(i.latitude),
            longitude=float(i.longitude),
            report_count=i.report_count,
            support_count=i.support_count,
            is_verified=i.is_verified,
            first_reported_at=i.first_reported_at.isoformat(),
            latest_reported_at=i.latest_reported_at.isoformat(),
            resolved_at=i.resolved_at.isoformat() if i.resolved_at else None,
        ))

    return PaginatedAdminIssues(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )


@router.post("/{issue_id}/status")
async def change_status(
    issue_id: uuid.UUID,
    body: StatusChangeRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.moderator)),
):
    try:
        new_status = IssueStatus(body.new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status value")

    try:
        issue = await change_issue_status(db, issue_id, new_status, user, body.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": issue.status.value, "issue_id": str(issue.id)}


@router.patch("/{issue_id}")
async def edit_metadata(
    issue_id: uuid.UUID,
    body: MetadataEditRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.moderator)),
):
    try:
        issue = await update_issue_metadata(
            db, issue_id, user,
            title=body.title,
            canonical_issue_type=body.canonical_issue_type,
            canonical_severity=body.canonical_severity,
            latitude=body.latitude,
            longitude=body.longitude,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "issue_id": str(issue.id),
        "title": issue.title,
        "canonical_issue_type": issue.canonical_issue_type.value,
        "canonical_severity": issue.canonical_severity.value,
    }


@router.post("/{issue_id}/merge")
async def merge(
    issue_id: uuid.UUID,
    body: MergeRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.moderator)),
):
    try:
        surviving = await merge_issues(
            db, body.surviving_issue_id, body.merge_issue_ids, user, body.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "surviving_issue_id": str(surviving.id),
        "report_count": surviving.report_count,
        "merged_count": len(body.merge_issue_ids),
    }


@router.get("/{issue_id}/history", response_model=list[StatusHistoryItem])
async def get_status_history(
    issue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.moderator)),
):
    result = await db.execute(
        select(IssueStatusHistory)
        .where(IssueStatusHistory.issue_id == issue_id)
        .order_by(IssueStatusHistory.created_at.desc())
    )
    rows = result.scalars().all()
    return [
        StatusHistoryItem(
            id=r.id,
            old_status=r.old_status,
            new_status=r.new_status,
            change_reason=r.change_reason,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.get("/export")
async def export_issues_csv(
    status: str | None = Query(None),
    issue_type: str | None = Query(None),
    severity: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    query = select(Issue)
    if status:
        query = query.where(Issue.status == IssueStatus(status))
    if issue_type:
        query = query.where(Issue.canonical_issue_type == IssueType(issue_type))
    if severity:
        query = query.where(Issue.canonical_severity == Severity(severity))
    query = query.order_by(Issue.latest_reported_at.desc())

    result = await db.execute(query)
    issues = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "title", "issue_type", "severity", "status",
        "latitude", "longitude", "report_count", "support_count",
        "is_verified", "first_reported_at", "latest_reported_at", "resolved_at",
    ])
    for i in issues:
        writer.writerow([
            str(i.id), i.title, i.canonical_issue_type.value,
            i.canonical_severity.value, i.status.value,
            float(i.latitude), float(i.longitude),
            i.report_count, i.support_count, i.is_verified,
            i.first_reported_at.isoformat(), i.latest_reported_at.isoformat(),
            i.resolved_at.isoformat() if i.resolved_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=issues_export.csv"},
    )
