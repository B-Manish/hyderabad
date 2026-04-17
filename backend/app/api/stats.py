"""Public statistics API — real stats for landing page."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.models import Issue, IssueSupport, JurisdictionPolygon
from app.models.enums import IssueStatus
from app.schemas.schemas import PublicStatsResponse
from app.services.cache import get_redis

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=PublicStatsResponse)
async def get_public_stats(
    db: AsyncSession = Depends(get_db),
):
    # Try cache first
    cache_key = "public_stats"
    try:
        import json
        r = await get_redis()
        cached = await r.get(cache_key)
        if cached:
            return PublicStatsResponse(**json.loads(cached))
    except Exception:
        pass

    # Total issues
    total_q = select(func.count()).select_from(Issue).where(Issue.public_visibility.is_(True))
    total_result = await db.execute(total_q)
    total_issues = total_result.scalar_one()

    # Unresolved
    unresolved_q = select(func.count()).select_from(Issue).where(
        Issue.public_visibility.is_(True),
        Issue.status.notin_([IssueStatus.resolved, IssueStatus.rejected, IssueStatus.duplicate]),
    )
    unresolved_result = await db.execute(unresolved_q)
    unresolved_issues = unresolved_result.scalar_one()

    # Wards covered
    wards_q = select(func.count(func.distinct(Issue.resolved_ward_id))).select_from(Issue).where(
        Issue.public_visibility.is_(True), Issue.resolved_ward_id.isnot(None),
    )
    wards_result = await db.execute(wards_q)
    wards_covered = wards_result.scalar_one()

    # Community confirmations (total supports)
    supports_q = select(func.count()).select_from(IssueSupport)
    supports_result = await db.execute(supports_q)
    community_confirmations = supports_result.scalar_one()

    # Resolved
    resolved_q = select(func.count()).select_from(Issue).where(
        Issue.public_visibility.is_(True), Issue.status == IssueStatus.resolved,
    )
    resolved_result = await db.execute(resolved_q)
    issues_resolved = resolved_result.scalar_one()

    response = PublicStatsResponse(
        total_issues=total_issues,
        unresolved_issues=unresolved_issues,
        wards_covered=wards_covered,
        community_confirmations=community_confirmations,
        issues_resolved=issues_resolved,
    )

    # Cache for 15 min
    try:
        import json
        r = await get_redis()
        await r.setex(cache_key, 900, json.dumps(response.model_dump()))
    except Exception:
        pass

    return response
