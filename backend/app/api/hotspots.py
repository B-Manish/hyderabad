"""Hotspot rankings API — severity-weighted ward rankings."""
import math
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, text, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.models import Issue, JurisdictionPolygon
from app.models.enums import IssueStatus, Severity
from app.schemas.schemas import HotspotsResponse, HotspotItem
from app.services.cache import get_redis

router = APIRouter(prefix="/hotspots", tags=["hotspots"])


@router.get("", response_model=HotspotsResponse)
async def get_hotspots(
    limit: int = Query(10, ge=1, le=50),
    period: str = Query("week", pattern="^(week|month|all)$"),
    db: AsyncSession = Depends(get_db),
):
    # Try cache first
    cache_key = f"hotspots:{period}:{limit}"
    try:
        import json
        r = await get_redis()
        cached = await r.get(cache_key)
        if cached:
            return HotspotsResponse(**json.loads(cached))
    except Exception:
        pass

    now = datetime.now(timezone.utc)
    if period == "week":
        date_from = now - timedelta(days=7)
        period_label = f"{now.year}-W{now.isocalendar()[1]:02d}"
    elif period == "month":
        date_from = now - timedelta(days=30)
        period_label = f"{now.year}-{now.month:02d}"
    else:
        date_from = datetime(2020, 1, 1, tzinfo=timezone.utc)
        period_label = "all-time"

    # Query issues grouped by resolved_ward_id with severity counts
    excluded_statuses = [IssueStatus.resolved.value, IssueStatus.rejected.value, IssueStatus.duplicate.value]
    status_placeholders = ", ".join([f":status_{i}" for i in range(len(excluded_statuses))])

    raw_sql = f"""
        SELECT
            jp.id AS ward_id,
            jp.name AS ward_name,
            COUNT(i.id) AS issue_count,
            COUNT(CASE WHEN i.canonical_severity = 'critical' THEN 1 END) AS critical_count,
            COUNT(CASE WHEN i.canonical_severity = 'high' THEN 1 END) AS high_count,
            COUNT(CASE WHEN i.canonical_severity = 'medium' THEN 1 END) AS medium_count,
            COUNT(CASE WHEN i.canonical_severity = 'low' THEN 1 END) AS low_count,
            COALESCE(AVG(EXTRACT(EPOCH FROM (NOW() - i.first_reported_at)) / 86400), 0) AS avg_age_days,
            COALESCE(SUM(i.support_count), 0) AS total_support
        FROM issues i
        JOIN jurisdiction_polygons jp ON i.resolved_ward_id = jp.id
        WHERE i.status NOT IN ({status_placeholders})
          AND i.first_reported_at >= :date_from
          AND i.public_visibility = true
        GROUP BY jp.id, jp.name
        HAVING COUNT(i.id) > 0
        ORDER BY COUNT(i.id) DESC
        LIMIT :limit
    """

    params = {"date_from": date_from, "limit": limit}
    for i, s in enumerate(excluded_statuses):
        params[f"status_{i}"] = s

    result = await db.execute(text(raw_sql), params)
    rows = result.fetchall()

    hotspots = []
    for row in rows:
        score = (
            row.critical_count * 4
            + row.high_count * 3
            + row.medium_count * 2
            + row.low_count * 1
            + float(row.avg_age_days) * 0.1
            + float(row.total_support) * 0.05
        )
        hotspots.append(HotspotItem(
            ward=row.ward_name,
            ward_id=str(row.ward_id),
            issue_count=row.issue_count,
            critical_count=row.critical_count,
            high_count=row.high_count,
            avg_age_days=round(float(row.avg_age_days), 1),
            hotspot_score=round(score, 1),
            map_url=f"/map?ward={row.ward_id}&severity=high,critical",
        ))

    # Sort by hotspot score descending
    hotspots.sort(key=lambda h: h.hotspot_score, reverse=True)

    response = HotspotsResponse(period=period_label, hotspots=hotspots)

    # Cache for 1 hour
    try:
        import json
        r = await get_redis()
        await r.setex(cache_key, 3600, json.dumps(response.model_dump(), default=str))
    except Exception:
        pass

    return response
