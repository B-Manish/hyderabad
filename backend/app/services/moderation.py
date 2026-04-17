"""Moderation service — approve/reject reports, merge issues, status management."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select, func, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.models import (
    Report, Issue, IssueReport, IssueStatusHistory, ModerationAction, User,
)
from app.models.enums import ModerationStatus, IssueStatus, Severity
from app.services.issues import (
    create_issue_from_report, recalculate_issue_aggregates, compute_verification_score,
    SEVERITY_ORDER,
)
from app.services.audit import write_audit_log
from app.services.cache import invalidate_map_cache


# Valid status transitions
STATUS_TRANSITIONS: dict[IssueStatus, list[IssueStatus]] = {
    IssueStatus.reported: [
        IssueStatus.under_review, IssueStatus.verified,
        IssueStatus.rejected, IssueStatus.duplicate,
    ],
    IssueStatus.under_review: [
        IssueStatus.verified, IssueStatus.rejected, IssueStatus.duplicate,
    ],
    IssueStatus.verified: [
        IssueStatus.assigned, IssueStatus.in_progress,
        IssueStatus.resolved, IssueStatus.rejected,
    ],
    IssueStatus.assigned: [
        IssueStatus.in_progress, IssueStatus.resolved, IssueStatus.rejected,
    ],
    IssueStatus.in_progress: [
        IssueStatus.resolved, IssueStatus.verified,
    ],
    IssueStatus.resolved: [
        IssueStatus.verified,
    ],
    IssueStatus.rejected: [
        IssueStatus.reported,
    ],
    IssueStatus.duplicate: [
        IssueStatus.reported,
    ],
}


async def approve_report(
    db: AsyncSession,
    report_id: uuid.UUID,
    moderator: User,
    notes: str | None = None,
) -> Report:
    result = await db.execute(
        select(Report).options(selectinload(Report.media)).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise ValueError("Report not found")

    old_status = report.moderation_status.value
    report.moderation_status = ModerationStatus.approved

    # If report has no linked issue yet, create one
    if not report.issue_id:
        await create_issue_from_report(db, report, report.user_id)
    else:
        # Make the linked issue publicly visible
        issue_result = await db.execute(select(Issue).where(Issue.id == report.issue_id))
        issue = issue_result.scalar_one_or_none()
        if issue:
            issue.public_visibility = True

    # Log moderation action
    mod_action = ModerationAction(
        id=uuid.uuid4(),
        report_id=report_id,
        issue_id=report.issue_id,
        moderator_user_id=moderator.id,
        action_type="approve",
        notes=notes,
    )
    db.add(mod_action)

    await write_audit_log(
        db,
        actor_user_id=moderator.id,
        entity_type="report",
        entity_id=report_id,
        action="approve",
        metadata_json={"old_status": old_status, "notes": notes},
    )

    await db.flush()
    await invalidate_map_cache()
    return report


async def reject_report(
    db: AsyncSession,
    report_id: uuid.UUID,
    moderator: User,
    reason: str,
    notes: str | None = None,
) -> Report:
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise ValueError("Report not found")

    valid_reasons = [
        ModerationStatus.rejected_abuse.value,
        ModerationStatus.low_quality_evidence.value,
        ModerationStatus.duplicate_merged.value,
    ]
    if reason not in valid_reasons:
        raise ValueError(f"Invalid rejection reason. Must be one of {valid_reasons}")

    old_status = report.moderation_status.value
    report.moderation_status = ModerationStatus(reason)

    mod_action = ModerationAction(
        id=uuid.uuid4(),
        report_id=report_id,
        issue_id=report.issue_id,
        moderator_user_id=moderator.id,
        action_type="reject",
        notes=f"{reason}: {notes}" if notes else reason,
    )
    db.add(mod_action)

    await write_audit_log(
        db,
        actor_user_id=moderator.id,
        entity_type="report",
        entity_id=report_id,
        action="reject",
        metadata_json={"old_status": old_status, "reason": reason, "notes": notes},
    )

    await db.flush()
    return report


async def change_issue_status(
    db: AsyncSession,
    issue_id: uuid.UUID,
    new_status: IssueStatus,
    user: User,
    reason: str | None = None,
) -> Issue:
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise ValueError("Issue not found")

    old_status = issue.status
    allowed = STATUS_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition from {old_status.value} to {new_status.value}. "
            f"Allowed: {[s.value for s in allowed]}"
        )

    issue.status = new_status
    if new_status == IssueStatus.resolved:
        issue.resolved_at = datetime.now(timezone.utc)

    # Record in status history
    history = IssueStatusHistory(
        id=uuid.uuid4(),
        issue_id=issue_id,
        old_status=old_status.value,
        new_status=new_status.value,
        changed_by_user_id=user.id,
        change_reason=reason,
    )
    db.add(history)

    await write_audit_log(
        db,
        actor_user_id=user.id,
        entity_type="issue",
        entity_id=issue_id,
        action="status_change",
        metadata_json={
            "old_status": old_status.value,
            "new_status": new_status.value,
            "reason": reason,
        },
    )

    await db.flush()
    await invalidate_map_cache()
    return issue


async def update_issue_metadata(
    db: AsyncSession,
    issue_id: uuid.UUID,
    user: User,
    *,
    title: str | None = None,
    canonical_issue_type: str | None = None,
    canonical_severity: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> Issue:
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise ValueError("Issue not found")

    old_values = {}
    new_values = {}

    if title is not None:
        old_values["title"] = issue.title
        issue.title = title
        new_values["title"] = title

    if canonical_issue_type is not None:
        from app.models.enums import IssueType
        old_values["canonical_issue_type"] = issue.canonical_issue_type.value
        issue.canonical_issue_type = IssueType(canonical_issue_type)
        new_values["canonical_issue_type"] = canonical_issue_type

    if canonical_severity is not None:
        old_values["canonical_severity"] = issue.canonical_severity.value
        issue.canonical_severity = Severity(canonical_severity)
        new_values["canonical_severity"] = canonical_severity

    if latitude is not None and longitude is not None:
        from geoalchemy2.functions import ST_SetSRID, ST_MakePoint
        old_values["latitude"] = float(issue.latitude)
        old_values["longitude"] = float(issue.longitude)
        issue.latitude = Decimal(str(latitude))
        issue.longitude = Decimal(str(longitude))
        issue.geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        new_values["latitude"] = latitude
        new_values["longitude"] = longitude

    await write_audit_log(
        db,
        actor_user_id=user.id,
        entity_type="issue",
        entity_id=issue_id,
        action="metadata_edit",
        metadata_json={"old": old_values, "new": new_values},
    )

    await db.flush()
    await invalidate_map_cache()
    return issue


async def merge_issues(
    db: AsyncSession,
    surviving_issue_id: uuid.UUID,
    merge_issue_ids: list[uuid.UUID],
    user: User,
    notes: str | None = None,
) -> Issue:
    """Merge multiple issues into a surviving issue."""
    # Load surviving issue
    result = await db.execute(select(Issue).where(Issue.id == surviving_issue_id))
    surviving = result.scalar_one_or_none()
    if not surviving:
        raise ValueError("Surviving issue not found")

    blocked_statuses = [IssueStatus.resolved, IssueStatus.rejected, IssueStatus.duplicate]

    for merge_id in merge_issue_ids:
        if merge_id == surviving_issue_id:
            continue

        result = await db.execute(select(Issue).where(Issue.id == merge_id))
        merged_issue = result.scalar_one_or_none()
        if not merged_issue:
            raise ValueError(f"Issue {merge_id} not found")
        if merged_issue.status in blocked_statuses:
            raise ValueError(f"Issue {merge_id} has status {merged_issue.status.value} and cannot be merged")

        # Re-link all reports from merged issue to surviving issue
        await db.execute(
            update(IssueReport)
            .where(IssueReport.issue_id == merge_id)
            .values(issue_id=surviving_issue_id)
        )
        await db.execute(
            update(Report)
            .where(Report.issue_id == merge_id)
            .values(issue_id=surviving_issue_id)
        )

        # Set merged issue to duplicate
        old_status = merged_issue.status
        merged_issue.status = IssueStatus.duplicate
        merged_issue.public_visibility = False

        # Status history for merged issue
        history = IssueStatusHistory(
            id=uuid.uuid4(),
            issue_id=merge_id,
            old_status=old_status.value,
            new_status=IssueStatus.duplicate.value,
            changed_by_user_id=user.id,
            change_reason=f"Merged into {surviving_issue_id}",
        )
        db.add(history)

        # Moderation action
        mod = ModerationAction(
            id=uuid.uuid4(),
            issue_id=merge_id,
            moderator_user_id=user.id,
            action_type="merge",
            notes=f"Merged into {surviving_issue_id}: {notes or ''}",
        )
        db.add(mod)

    # Recalculate surviving issue aggregates
    # Count linked reports
    count_result = await db.execute(
        select(func.count()).select_from(IssueReport).where(IssueReport.issue_id == surviving_issue_id)
    )
    report_count = count_result.scalar() or 1

    # Get earliest and latest report dates
    dates_result = await db.execute(
        select(
            func.min(Report.submitted_at),
            func.max(Report.submitted_at),
        )
        .select_from(Report)
        .join(IssueReport, IssueReport.report_id == Report.id)
        .where(IssueReport.issue_id == surviving_issue_id)
    )
    dates_row = dates_result.first()
    if dates_row and dates_row[0]:
        surviving.first_reported_at = dates_row[0]
        surviving.latest_reported_at = dates_row[1]

    # Get highest severity
    sev_result = await db.execute(
        select(Report.severity)
        .join(IssueReport, IssueReport.report_id == Report.id)
        .where(IssueReport.issue_id == surviving_issue_id)
    )
    severities = [row[0] for row in sev_result.fetchall()]
    if severities:
        surviving.canonical_severity = max(severities, key=lambda s: SEVERITY_ORDER.get(s, 0))

    surviving.report_count = report_count

    # Unique users
    users_result = await db.execute(
        select(func.count(func.distinct(Report.user_id)))
        .join(IssueReport, IssueReport.report_id == Report.id)
        .where(IssueReport.issue_id == surviving_issue_id)
    )
    unique_users = users_result.scalar() or 1

    score = compute_verification_score(report_count, unique_users, surviving.latest_reported_at)
    surviving.verification_score = Decimal(str(round(score, 4)))
    surviving.is_verified = score >= 0.6

    await write_audit_log(
        db,
        actor_user_id=user.id,
        entity_type="issue",
        entity_id=surviving_issue_id,
        action="merge",
        metadata_json={
            "merged_issue_ids": [str(mid) for mid in merge_issue_ids],
            "new_report_count": report_count,
            "notes": notes,
        },
    )

    await db.flush()
    await invalidate_map_cache()
    return surviving
