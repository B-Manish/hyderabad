"""Admin analytics API — summary metrics, geographic breakdown, exports."""
import csv
import io
import math
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, case, text, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth.dependencies import require_role
from app.models.enums import UserRole, IssueStatus, Severity
from app.models.models import Issue, Report, User, JurisdictionPolygon, AuditLog
from pydantic import BaseModel


router = APIRouter(prefix="/admin/analytics", tags=["admin-analytics"])


class AnalyticsSummary(BaseModel):
    total_reports: int
    total_issues: int
    unresolved_issues: int
    avg_issue_age_days: float
    reports_this_week: int
    resolved_this_week: int
    duplicate_merge_rate: float
    top_wards: list[dict]
    severity_distribution: dict[str, int]
    status_distribution: dict[str, int]


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.moderator)),
):
    now = datetime.now(timezone.utc)
    one_week_ago = now - timedelta(days=7)

    # Total reports
    total_reports = (await db.execute(select(func.count(Report.id)))).scalar() or 0

    # Total issues
    total_issues = (await db.execute(select(func.count(Issue.id)))).scalar() or 0

    # Unresolved issues
    resolved_statuses = [IssueStatus.resolved, IssueStatus.rejected, IssueStatus.duplicate]
    unresolved = (await db.execute(
        select(func.count(Issue.id)).where(Issue.status.not_in(resolved_statuses))
    )).scalar() or 0

    # Average issue age (unresolved)
    avg_age_result = await db.execute(
        select(func.avg(func.extract("epoch", func.now() - Issue.first_reported_at) / 86400))
        .where(Issue.status.not_in(resolved_statuses))
    )
    avg_age = avg_age_result.scalar() or 0

    # Reports this week
    reports_week = (await db.execute(
        select(func.count(Report.id)).where(Report.submitted_at >= one_week_ago)
    )).scalar() or 0

    # Resolved this week
    resolved_week = (await db.execute(
        select(func.count(Issue.id))
        .where(Issue.status == IssueStatus.resolved)
        .where(Issue.resolved_at >= one_week_ago)
    )).scalar() or 0

    # Duplicate merge rate
    dup_count = (await db.execute(
        select(func.count(Issue.id)).where(Issue.status == IssueStatus.duplicate)
    )).scalar() or 0
    dup_rate = (dup_count / total_issues) if total_issues > 0 else 0

    # Top wards by unresolved count
    ward_query = text("""
        SELECT jp.name as ward_name, COUNT(i.id) as unresolved_count
        FROM issues i
        JOIN jurisdiction_polygons jp ON i.resolved_ward_id = jp.id
        WHERE i.status NOT IN ('resolved', 'rejected', 'duplicate')
        GROUP BY jp.name
        ORDER BY unresolved_count DESC
        LIMIT 5
    """)
    ward_result = await db.execute(ward_query)
    top_wards = [
        {"ward": row[0], "unresolved_count": row[1]}
        for row in ward_result.fetchall()
    ]

    # Severity distribution
    sev_result = await db.execute(
        select(Issue.canonical_severity, func.count(Issue.id))
        .group_by(Issue.canonical_severity)
    )
    severity_dist = {}
    for row in sev_result.fetchall():
        severity_dist[row[0].value if hasattr(row[0], 'value') else str(row[0])] = row[1]

    # Status distribution
    status_result = await db.execute(
        select(Issue.status, func.count(Issue.id))
        .group_by(Issue.status)
    )
    status_dist = {}
    for row in status_result.fetchall():
        status_dist[row[0].value if hasattr(row[0], 'value') else str(row[0])] = row[1]

    return AnalyticsSummary(
        total_reports=total_reports,
        total_issues=total_issues,
        unresolved_issues=unresolved,
        avg_issue_age_days=round(float(avg_age), 1),
        reports_this_week=reports_week,
        resolved_this_week=resolved_week,
        duplicate_merge_rate=round(dup_rate, 4),
        top_wards=top_wards,
        severity_distribution=severity_dist,
        status_distribution=status_dist,
    )


@router.get("/export")
async def export_analytics_csv(
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    query = select(Issue).order_by(Issue.first_reported_at.desc())
    if date_from:
        query = query.where(Issue.first_reported_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.where(Issue.first_reported_at <= datetime.fromisoformat(date_to))

    result = await db.execute(query)
    issues = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "title", "issue_type", "severity", "status",
        "latitude", "longitude", "report_count", "support_count",
        "is_verified", "first_reported_at", "latest_reported_at",
    ])
    for i in issues:
        writer.writerow([
            str(i.id), i.title, i.canonical_issue_type.value,
            i.canonical_severity.value, i.status.value,
            float(i.latitude), float(i.longitude),
            i.report_count, i.support_count, i.is_verified,
            i.first_reported_at.isoformat(), i.latest_reported_at.isoformat(),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analytics_export.csv"},
    )
