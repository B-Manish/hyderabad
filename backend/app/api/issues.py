import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.schemas import (
    IssueListItem, IssueDetailResponse, PaginatedIssuesResponse, MediaResponse,
    IssueDetailWithAuthority, SupportCreateRequest, SupportResponse, SupportSummaryResponse,
)
from app.services.reports import get_issues_paginated, get_issue_by_id
from app.services.storage import get_public_url
from app.services.authority import resolve_authority
from app.services.support import create_support, get_support_summary
from app.auth.dependencies import get_current_user_optional
from app.models.models import User
from app.models.enums import IssueType, Severity, IssueStatus

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("", response_model=PaginatedIssuesResponse)
async def list_issues(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    issue_type: IssueType | None = None,
    severity: Severity | None = None,
    status: IssueStatus | None = None,
    sort_by: str = Query("latest_reported_at", pattern="^(latest_reported_at|first_reported_at|severity|support_count)$"),
    db: AsyncSession = Depends(get_db),
):
    result = await get_issues_paginated(
        db, page=page, page_size=page_size,
        issue_type=issue_type, severity=severity, status=status, sort_by=sort_by,
    )

    items = []
    for issue in result["items"]:
        items.append(IssueListItem(
            id=issue.id,
            title=issue.title,
            canonical_issue_type=issue.canonical_issue_type,
            canonical_severity=issue.canonical_severity,
            status=issue.status,
            latitude=float(issue.latitude),
            longitude=float(issue.longitude),
            first_reported_at=issue.first_reported_at,
            latest_reported_at=issue.latest_reported_at,
            support_count=issue.support_count,
            report_count=issue.report_count,
            is_verified=issue.is_verified,
            thumbnail_url=None,
        ))

    return PaginatedIssuesResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get("/{issue_id}", response_model=IssueDetailWithAuthority)
async def get_issue(
    issue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    issue = await get_issue_by_id(db, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if not issue.public_visibility:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Gather all media from linked reports
    media_list = []
    for report in issue.reports:
        for m in report.media:
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

    return IssueDetailWithAuthority(
        id=issue.id,
        title=issue.title,
        canonical_issue_type=issue.canonical_issue_type,
        canonical_severity=issue.canonical_severity,
        status=issue.status,
        latitude=float(issue.latitude),
        longitude=float(issue.longitude),
        first_reported_at=issue.first_reported_at,
        latest_reported_at=issue.latest_reported_at,
        resolved_at=issue.resolved_at,
        support_count=issue.support_count,
        report_count=issue.report_count,
        verification_score=float(issue.verification_score),
        is_verified=issue.is_verified,
        public_visibility=issue.public_visibility,
        created_at=issue.created_at,
        media=media_list,
        authority=await resolve_authority(db, float(issue.latitude), float(issue.longitude)),
    )


@router.post("/{issue_id}/support", response_model=SupportResponse)
async def support_issue(
    issue_id: uuid.UUID,
    body: SupportCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    ip_address = request.client.host if request.client else None
    try:
        result = await create_support(
            db,
            issue_id=issue_id,
            support_type=body.support_type,
            user_id=user.id if user else None,
            ip_address=ip_address,
        )
    except ValueError as e:
        raise HTTPException(status_code=429 if "Rate limit" in str(e) else 404, detail=str(e))
    return SupportResponse(**result)


@router.get("/{issue_id}/supports", response_model=SupportSummaryResponse)
async def get_issue_supports(
    issue_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    summary = await get_support_summary(db, issue_id)
    return SupportSummaryResponse(**summary)
