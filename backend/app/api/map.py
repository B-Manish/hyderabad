from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.issues import get_map_issues, find_nearby_duplicates
from app.services.cache import get_cached_map, set_cached_map
from app.models.enums import IssueType

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/issues")
async def map_viewport_issues(
    minLat: float = Query(..., ge=-90, le=90),
    minLng: float = Query(..., ge=-180, le=180),
    maxLat: float = Query(..., ge=-90, le=90),
    maxLng: float = Query(..., ge=-180, le=180),
    status: str | None = Query(None, description="Comma-separated statuses"),
    severity: str | None = Query(None, description="Comma-separated severities"),
    issue_type: str | None = Query(None, description="Comma-separated issue types"),
    verified_only: bool = Query(False),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # Parse comma-separated filter values
    status_filter = [s.strip() for s in status.split(",") if s.strip()] if status else None
    severity_filter = [s.strip() for s in severity.split(",") if s.strip()] if severity else None
    issue_type_filter = [s.strip() for s in issue_type.split(",") if s.strip()] if issue_type else None

    # Build cache key
    cache_key = f"map:{minLat:.4f},{minLng:.4f},{maxLat:.4f},{maxLng:.4f}"
    if status_filter:
        cache_key += f":s={','.join(sorted(status_filter))}"
    if severity_filter:
        cache_key += f":sev={','.join(sorted(severity_filter))}"
    if issue_type_filter:
        cache_key += f":t={','.join(sorted(issue_type_filter))}"
    if verified_only:
        cache_key += ":verified"
    if date_from:
        cache_key += f":df={date_from.isoformat()}"
    if date_to:
        cache_key += f":dt={date_to.isoformat()}"

    # Try cache first
    cached = await get_cached_map(cache_key)
    if cached is not None:
        return cached

    result = await get_map_issues(
        db,
        min_lat=minLat,
        min_lng=minLng,
        max_lat=maxLat,
        max_lng=maxLng,
        status_filter=status_filter,
        severity_filter=severity_filter,
        issue_type_filter=issue_type_filter,
        verified_only=verified_only,
        date_from=date_from,
        date_to=date_to,
    )

    # Cache for 60 seconds
    await set_cached_map(cache_key, result, ttl=60)

    return result


@router.get("/duplicates")
async def check_duplicates(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    issue_type: IssueType = Query(...),
    radius: int = Query(30, ge=20, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Check for potential duplicate issues near a given location."""
    duplicates = await find_nearby_duplicates(
        db,
        lat=lat,
        lng=lng,
        issue_type=issue_type,
        radius_meters=radius,
    )
    return {
        "duplicates": duplicates,
        "count": len(duplicates),
        "search_radius_meters": radius,
    }
