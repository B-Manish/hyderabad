"""Issue support/confirmation service — same_issue, dangerous, still_exists, fixed_confirmed."""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import IssueSupport, Issue
from app.models.enums import SupportType
from app.services.issues import compute_verification_score, VERIFICATION_THRESHOLD
from app.services.cache import invalidate_map_cache

FIXED_CONFIRM_THRESHOLD = 3


async def check_rate_limit(
    db: AsyncSession,
    issue_id: uuid.UUID,
    support_type: str,
    user_id: uuid.UUID | None,
    ip_address: str | None,
) -> bool:
    """Return True if the action is rate-limited (should be blocked)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    query = select(func.count()).select_from(IssueSupport).where(
        IssueSupport.issue_id == issue_id,
        IssueSupport.support_type == support_type,
        IssueSupport.created_at >= cutoff,
    )
    if user_id:
        query = query.where(IssueSupport.user_id == user_id)
    elif ip_address:
        query = query.where(IssueSupport.ip_address == ip_address)
    else:
        return True  # No identity => block

    result = await db.execute(query)
    count = result.scalar_one()
    return count >= 1  # 1 support per user/IP per issue per type per 24h


async def create_support(
    db: AsyncSession,
    issue_id: uuid.UUID,
    support_type: str,
    user_id: uuid.UUID | None = None,
    ip_address: str | None = None,
) -> dict:
    """Create an issue support entry and update issue aggregates."""
    # Validate issue exists
    issue = await db.get(Issue, issue_id)
    if not issue:
        raise ValueError("Issue not found")

    # Rate limit check
    is_limited = await check_rate_limit(db, issue_id, support_type, user_id, ip_address)
    if is_limited:
        raise ValueError("Rate limit exceeded: you can only support once per type per 24 hours")

    support = IssueSupport(
        id=uuid.uuid4(),
        issue_id=issue_id,
        user_id=user_id,
        support_type=support_type,
        ip_address=ip_address,
    )
    db.add(support)
    await db.flush()

    # Update issue support_count
    total_q = select(func.count()).select_from(IssueSupport).where(IssueSupport.issue_id == issue_id)
    total_result = await db.execute(total_q)
    new_support_count = total_result.scalar_one()
    issue.support_count = new_support_count

    # Recalculate verification score
    unique_users_q = select(func.count(func.distinct(IssueSupport.user_id))).select_from(
        IssueSupport
    ).where(IssueSupport.issue_id == issue_id, IssueSupport.user_id.isnot(None))
    unique_result = await db.execute(unique_users_q)
    unique_supporters = unique_result.scalar_one()

    score = compute_verification_score(
        issue.report_count + new_support_count,
        unique_supporters + 1,  # +1 for original reporter
        issue.latest_reported_at,
    )
    issue.verification_score = Decimal(str(round(score, 4)))
    issue.is_verified = score >= VERIFICATION_THRESHOLD

    # Handle still_exists: update latest_reported_at
    if support_type == SupportType.still_exists.value:
        issue.latest_reported_at = datetime.now(timezone.utc)

    # Handle fixed_confirmed: check threshold
    needs_review = False
    if support_type == SupportType.fixed_confirmed.value:
        fixed_count_q = select(func.count()).select_from(IssueSupport).where(
            IssueSupport.issue_id == issue_id,
            IssueSupport.support_type == SupportType.fixed_confirmed.value,
        )
        fixed_result = await db.execute(fixed_count_q)
        fixed_count = fixed_result.scalar_one()
        if fixed_count >= FIXED_CONFIRM_THRESHOLD:
            needs_review = True

    await db.flush()
    await invalidate_map_cache()

    return {
        "issue_id": str(issue_id),
        "support_count": new_support_count,
        "support_type": support_type,
        "created_at": support.created_at.isoformat(),
        "needs_resolution_review": needs_review,
    }


async def get_support_summary(db: AsyncSession, issue_id: uuid.UUID) -> dict:
    """Get breakdown of support counts by type for an issue."""
    query = select(
        IssueSupport.support_type,
        func.count().label("count"),
    ).where(IssueSupport.issue_id == issue_id).group_by(IssueSupport.support_type)
    result = await db.execute(query)
    rows = result.all()
    summary = {st.value: 0 for st in SupportType}
    for row in rows:
        summary[row.support_type] = row.count
    total = sum(summary.values())
    return {"total": total, "by_type": summary}
