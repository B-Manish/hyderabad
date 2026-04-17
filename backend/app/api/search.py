"""Search API — full-text + spatial search across issues, wards, roads."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.schemas import SearchResponse, SearchResultItem

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=200),
    type: str | None = Query(None, pattern="^(ward|road|issue|nearby)$"),
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    results = []
    total = 0
    offset = (page - 1) * per_page
    tsquery = " & ".join(q.strip().split())

    # Search wards/jurisdiction_polygons
    if type is None or type == "ward":
        ward_sql = """
            SELECT id, name, code, layer_type,
                   ts_rank(search_vector, to_tsquery('english', :tsq)) AS rank,
                   (SELECT COUNT(*) FROM issues WHERE resolved_ward_id = jp.id AND public_visibility = true) AS issue_count
            FROM jurisdiction_polygons jp
            WHERE search_vector @@ to_tsquery('english', :tsq)
               OR name ILIKE :like_q
            ORDER BY rank DESC
            LIMIT :limit OFFSET :offset
        """
        ward_result = await db.execute(text(ward_sql), {
            "tsq": tsquery, "like_q": f"%{q}%", "limit": per_page, "offset": offset,
        })
        for row in ward_result.fetchall():
            results.append(SearchResultItem(
                type="ward",
                id=str(row.id),
                name=f"{row.name}" + (f" ({row.code})" if row.code else ""),
                issue_count=row.issue_count,
                url=f"/areas/{row.id}",
            ))

    # Search road segments
    if type is None or type == "road":
        road_sql = """
            SELECT id, name, road_class,
                   ts_rank(search_vector, to_tsquery('english', :tsq)) AS rank
            FROM road_segments
            WHERE search_vector @@ to_tsquery('english', :tsq)
               OR name ILIKE :like_q
            ORDER BY rank DESC
            LIMIT :limit OFFSET :offset
        """
        road_result = await db.execute(text(road_sql), {
            "tsq": tsquery, "like_q": f"%{q}%", "limit": per_page, "offset": offset,
        })
        for row in road_result.fetchall():
            results.append(SearchResultItem(
                type="road",
                id=str(row.id),
                name=row.name or "Unnamed Road",
                url=f"/map?road={row.id}",
            ))

    # Search issues
    if type is None or type == "issue":
        issue_sql = """
            SELECT id, title, canonical_severity, canonical_issue_type,
                   ts_rank(search_vector, to_tsquery('english', :tsq)) AS rank
            FROM issues
            WHERE (search_vector @@ to_tsquery('english', :tsq)
                   OR title ILIKE :like_q)
              AND public_visibility = true
            ORDER BY rank DESC
            LIMIT :limit OFFSET :offset
        """
        issue_result = await db.execute(text(issue_sql), {
            "tsq": tsquery, "like_q": f"%{q}%", "limit": per_page, "offset": offset,
        })
        for row in issue_result.fetchall():
            results.append(SearchResultItem(
                type="issue",
                id=str(row.id),
                name=row.title,
                severity=row.canonical_severity,
                url=f"/issues/{row.id}",
            ))

    # Nearby spatial search
    if type == "nearby" and lat is not None and lng is not None:
        nearby_sql = """
            SELECT id, title, canonical_severity, canonical_issue_type,
                   ST_Distance(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) AS distance
            FROM issues
            WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, 2000)
              AND public_visibility = true
            ORDER BY distance ASC
            LIMIT :limit OFFSET :offset
        """
        nearby_result = await db.execute(text(nearby_sql), {
            "lat": lat, "lng": lng, "limit": per_page, "offset": offset,
        })
        for row in nearby_result.fetchall():
            results.append(SearchResultItem(
                type="issue",
                id=str(row.id),
                name=row.title,
                severity=row.canonical_severity,
                url=f"/issues/{row.id}",
            ))

    total = len(results)
    return SearchResponse(results=results, total=total)
