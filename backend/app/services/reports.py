import uuid
import math
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from geoalchemy2.functions import ST_SetSRID, ST_MakePoint
from app.models.models import Report, ReportMedia, Issue, IssueReport, IssueStatusHistory
from app.models.enums import (
    IssueType, Severity, ModerationStatus, IssueStatus, MediaType,
)
from app.schemas.schemas import ReportCreateRequest
from app.services.storage import get_public_url
from datetime import datetime, timezone


ISSUE_TYPE_LABELS = {
    IssueType.pothole: "Pothole",
    IssueType.road_surface_broken: "Broken Road Surface",
    IssueType.uneven_resurfacing: "Uneven Resurfacing",
    IssueType.waterlogging: "Waterlogging",
    IssueType.open_manhole: "Open Manhole",
    IssueType.dangerous_speed_breaker: "Dangerous Speed Breaker",
    IssueType.loose_gravel_debris: "Loose Gravel / Debris",
    IssueType.construction_spill: "Construction Spill",
    IssueType.missing_lane_markings: "Missing Lane Markings",
    IssueType.road_shoulder_collapse: "Road Shoulder Collapse",
    IssueType.road_cave_in: "Road Cave-in",
    IssueType.other_road_safety: "Other Road Safety Issue",
}


async def create_report(
    db: AsyncSession,
    data: ReportCreateRequest,
    user_id: uuid.UUID | None = None,
) -> Report:
    geom = ST_SetSRID(ST_MakePoint(float(data.longitude), float(data.latitude)), 4326)

    report = Report(
        id=uuid.uuid4(),
        user_id=user_id,
        latitude=data.latitude,
        longitude=data.longitude,
        geom=geom,
        issue_type=data.issue_type,
        severity=data.severity,
        description=data.description,
        landmark=data.landmark,
        road_name_input=data.road_name_input,
        direction_of_travel=data.direction_of_travel,
        dangerous_for_bikes=data.dangerous_for_bikes,
        worse_in_rain=data.worse_in_rain,
        worse_at_night=data.worse_at_night,
        moderation_status=ModerationStatus.pending_moderation,
    )
    db.add(report)
    await db.flush()

    # Create media records
    for idx, key in enumerate(data.media_keys):
        ext = key.rsplit(".", 1)[-1].lower() if "." in key else ""
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
        mime = mime_map.get(ext, "image/jpeg")

        media = ReportMedia(
            id=uuid.uuid4(),
            report_id=report.id,
            storage_key=key,
            media_type=MediaType.image,
            mime_type=mime,
            sort_order=idx,
        )
        db.add(media)

    await db.flush()

    # Create an Issue from this report (Phase 1: 1 report = 1 issue, dedupe in Phase 2)
    title_label = ISSUE_TYPE_LABELS.get(data.issue_type, "Road Issue")
    location_hint = data.landmark or data.road_name_input or f"{data.latitude:.4f}, {data.longitude:.4f}"
    title = f"{title_label} near {location_hint}"

    issue = Issue(
        id=uuid.uuid4(),
        primary_report_id=report.id,
        title=title,
        canonical_issue_type=data.issue_type,
        canonical_severity=data.severity,
        status=IssueStatus.reported,
        latitude=data.latitude,
        longitude=data.longitude,
        geom=geom,
        first_reported_at=report.submitted_at,
        latest_reported_at=report.submitted_at,
        report_count=1,
        support_count=0,
    )
    db.add(issue)
    await db.flush()

    # Link report to issue
    report.issue_id = issue.id
    ir = IssueReport(
        issue_id=issue.id,
        report_id=report.id,
        link_reason="initial_report",
    )
    db.add(ir)

    # Log status history
    history = IssueStatusHistory(
        id=uuid.uuid4(),
        issue_id=issue.id,
        old_status=None,
        new_status=IssueStatus.reported.value,
        changed_by_user_id=user_id,
        change_reason="Initial report submitted",
    )
    db.add(history)

    await db.flush()
    return report


async def get_report_by_id(db: AsyncSession, report_id: uuid.UUID) -> Report | None:
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.media))
        .where(Report.id == report_id)
    )
    return result.scalar_one_or_none()


async def get_issues_paginated(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    issue_type: IssueType | None = None,
    severity: Severity | None = None,
    status: IssueStatus | None = None,
    sort_by: str = "latest_reported_at",
):
    query = select(Issue).where(Issue.public_visibility.is_(True))

    if issue_type:
        query = query.where(Issue.canonical_issue_type == issue_type)
    if severity:
        query = query.where(Issue.canonical_severity == severity)
    if status:
        query = query.where(Issue.status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sort
    sort_col = {
        "latest_reported_at": Issue.latest_reported_at.desc(),
        "first_reported_at": Issue.first_reported_at.desc(),
        "severity": Issue.canonical_severity.desc(),
        "support_count": Issue.support_count.desc(),
    }.get(sort_by, Issue.latest_reported_at.desc())

    query = query.order_by(sort_col)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    issues = result.scalars().all()

    return {
        "items": issues,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


async def get_issue_by_id(db: AsyncSession, issue_id: uuid.UUID) -> Issue | None:
    result = await db.execute(
        select(Issue)
        .options(
            selectinload(Issue.reports).selectinload(Report.media),
        )
        .where(Issue.id == issue_id)
    )
    return result.scalar_one_or_none()
