"""Locality/Area pages API — ward-level issue data for SEO-friendly pages."""
import uuid
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.models import Issue, JurisdictionPolygon
from app.models.enums import IssueStatus, Severity, LayerType
from app.schemas.schemas import (
    AreaDetailResponse, IssueListItem, PaginatedIssuesResponse,
)

router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("/{ward_id}", response_model=AreaDetailResponse)
async def get_area_detail(
    ward_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    # Get ward/area info
    result = await db.execute(
        select(JurisdictionPolygon)
        .options(selectinload(JurisdictionPolygon.authority))
        .where(JurisdictionPolygon.id == ward_id)
    )
    ward = result.scalar_one_or_none()
    if not ward:
        raise HTTPException(status_code=404, detail="Area not found")

    # Count issues
    excluded_statuses = [IssueStatus.rejected.value, IssueStatus.duplicate.value]

    total_q = select(func.count()).select_from(Issue).where(
        Issue.resolved_ward_id == ward_id,
        Issue.public_visibility.is_(True),
    )
    total_result = await db.execute(total_q)
    total_issues = total_result.scalar_one()

    unresolved_q = select(func.count()).select_from(Issue).where(
        Issue.resolved_ward_id == ward_id,
        Issue.public_visibility.is_(True),
        Issue.status.notin_([IssueStatus.resolved, IssueStatus.rejected, IssueStatus.duplicate]),
    )
    unresolved_result = await db.execute(unresolved_q)
    unresolved_count = unresolved_result.scalar_one()

    # Severity breakdown
    sev_q = select(
        Issue.canonical_severity, func.count()
    ).where(
        Issue.resolved_ward_id == ward_id,
        Issue.public_visibility.is_(True),
    ).group_by(Issue.canonical_severity)
    sev_result = await db.execute(sev_q)
    severity_breakdown = {row[0].value: row[1] for row in sev_result.all()}

    # Top issues (by severity + support)
    top_sql = text("""
        SELECT id, title, canonical_issue_type, canonical_severity, status,
               latitude, longitude, first_reported_at, latest_reported_at,
               support_count, report_count, is_verified
        FROM issues
        WHERE resolved_ward_id = :ward_id
          AND public_visibility = true
        ORDER BY
            CASE canonical_severity
                WHEN 'critical' THEN 4
                WHEN 'high' THEN 3
                WHEN 'medium' THEN 2
                ELSE 1
            END DESC,
            support_count DESC
        LIMIT 10
    """)
    top_result = await db.execute(top_sql, {"ward_id": str(ward_id)})
    top_issues = []
    for row in top_result.fetchall():
        top_issues.append(IssueListItem(
            id=row.id,
            title=row.title,
            canonical_issue_type=row.canonical_issue_type,
            canonical_severity=row.canonical_severity,
            status=row.status,
            latitude=float(row.latitude),
            longitude=float(row.longitude),
            first_reported_at=row.first_reported_at,
            latest_reported_at=row.latest_reported_at,
            support_count=row.support_count,
            report_count=row.report_count,
            is_verified=row.is_verified,
            thumbnail_url=None,
        ))

    # Authority name
    authority_name = None
    if ward.authority:
        authority_name = ward.authority.name

    return AreaDetailResponse(
        id=str(ward.id),
        name=ward.name,
        code=ward.code,
        layer_type=ward.layer_type.value,
        total_issues=total_issues,
        unresolved_count=unresolved_count,
        severity_breakdown=severity_breakdown,
        top_issues=top_issues,
        authority_name=authority_name,
    )


@router.get("/{ward_id}/issues", response_model=PaginatedIssuesResponse)
async def get_area_issues(
    ward_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    ward = await db.get(JurisdictionPolygon, ward_id)
    if not ward:
        raise HTTPException(status_code=404, detail="Area not found")

    total_q = select(func.count()).select_from(Issue).where(
        Issue.resolved_ward_id == ward_id, Issue.public_visibility.is_(True),
    )
    total_result = await db.execute(total_q)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    issues_q = select(Issue).where(
        Issue.resolved_ward_id == ward_id, Issue.public_visibility.is_(True),
    ).order_by(Issue.latest_reported_at.desc()).offset(offset).limit(page_size)
    issues_result = await db.execute(issues_q)
    issues = issues_result.scalars().all()

    items = [IssueListItem(
        id=i.id,
        title=i.title,
        canonical_issue_type=i.canonical_issue_type,
        canonical_severity=i.canonical_severity,
        status=i.status,
        latitude=float(i.latitude),
        longitude=float(i.longitude),
        first_reported_at=i.first_reported_at,
        latest_reported_at=i.latest_reported_at,
        support_count=i.support_count,
        report_count=i.report_count,
        is_verified=i.is_verified,
        thumbnail_url=None,
    ) for i in issues]

    import math
    total_pages = max(1, math.ceil(total / page_size))

    return PaginatedIssuesResponse(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages,
    )


@router.get("", response_model=list[dict])
async def list_areas(
    layer_type: str = Query("ward"),
    db: AsyncSession = Depends(get_db),
):
    """List all areas/wards for navigation."""
    q = select(JurisdictionPolygon).where(
        JurisdictionPolygon.layer_type == layer_type,
        JurisdictionPolygon.is_active.is_(True),
    ).order_by(JurisdictionPolygon.name)
    result = await db.execute(q)
    wards = result.scalars().all()

    items = []
    for w in wards:
        issue_q = select(func.count()).select_from(Issue).where(
            Issue.resolved_ward_id == w.id, Issue.public_visibility.is_(True),
        )
        issue_result = await db.execute(issue_q)
        issue_count = issue_result.scalar_one()
        items.append({
            "id": str(w.id),
            "name": w.name,
            "code": w.code,
            "layer_type": w.layer_type.value,
            "issue_count": issue_count,
        })
    return items
