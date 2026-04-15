"""Issue services: creation, linking, aggregation, duplicate detection, verification scoring."""
import uuid
import math
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import select, func, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from geoalchemy2.functions import ST_SetSRID, ST_MakePoint
from app.models.models import Report, Issue, IssueReport, IssueStatusHistory
from app.models.enums import IssueType, Severity, IssueStatus


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

# Issue type compatibility matrix for duplicate detection
COMPATIBLE_TYPES: dict[IssueType, list[IssueType]] = {
    IssueType.pothole: [IssueType.road_surface_broken, IssueType.road_cave_in],
    IssueType.road_surface_broken: [IssueType.pothole, IssueType.uneven_resurfacing],
    IssueType.uneven_resurfacing: [IssueType.road_surface_broken],
    IssueType.open_manhole: [],
    IssueType.waterlogging: [],
    IssueType.dangerous_speed_breaker: [],
    IssueType.loose_gravel_debris: [IssueType.construction_spill],
    IssueType.construction_spill: [IssueType.loose_gravel_debris],
    IssueType.missing_lane_markings: [],
    IssueType.road_shoulder_collapse: [IssueType.road_cave_in],
    IssueType.road_cave_in: [IssueType.pothole, IssueType.road_shoulder_collapse],
    IssueType.other_road_safety: [],
}

SEVERITY_ORDER = {
    Severity.low: 0,
    Severity.medium: 1,
    Severity.high: 2,
    Severity.critical: 3,
}

# Default configuration
DEFAULT_DUPLICATE_RADIUS_METERS = 30
VERIFICATION_THRESHOLD = 0.6


def get_compatible_types(issue_type: IssueType) -> list[IssueType]:
    """Get list of the issue type itself plus its compatible types."""
    compatible = [issue_type]
    compatible.extend(COMPATIBLE_TYPES.get(issue_type, []))
    return compatible


def generate_issue_title(issue_type: IssueType, landmark: str | None = None, road_name: str | None = None, lat: float = 0, lng: float = 0) -> str:
    """Auto-generate issue title from type and location info."""
    label = ISSUE_TYPE_LABELS.get(issue_type, "Road Issue")
    if road_name:
        return f"{label} — {road_name}"
    if landmark:
        return f"{label} — Near {landmark}"
    return f"{label} — {lat:.4f}, {lng:.4f}"


def compute_verification_score(report_count: int, unique_users: int, latest_reported_at: datetime) -> float:
    """
    Compute verification score using MVP formula:
    score = min(1.0, (report_count * 0.3) + (unique_users * 0.2) + recency_factor)
    recency_factor = 0.5 if reported within last 7 days, decays over time
    """
    now = datetime.now(timezone.utc)
    days_since = (now - latest_reported_at).total_seconds() / 86400
    if days_since <= 7:
        recency_factor = 0.5
    elif days_since <= 30:
        recency_factor = 0.5 * (1.0 - (days_since - 7) / 23.0)
    else:
        recency_factor = 0.0
    score = (report_count * 0.3) + (unique_users * 0.2) + recency_factor
    return min(1.0, score)


async def find_nearby_duplicates(
    db: AsyncSession,
    lat: float,
    lng: float,
    issue_type: IssueType,
    radius_meters: int = DEFAULT_DUPLICATE_RADIUS_METERS,
    limit: int = 5,
) -> list[dict]:
    """
    Find existing issues within radius that could be duplicates.
    Uses PostGIS ST_DWithin for spatial proximity search.
    """
    compatible_types = get_compatible_types(issue_type)
    type_values = [t.value for t in compatible_types]

    excluded_statuses = [
        IssueStatus.resolved.value,
        IssueStatus.rejected.value,
        IssueStatus.duplicate.value,
    ]

    query = text("""
        SELECT id, title, canonical_issue_type, canonical_severity, status,
               latitude, longitude, report_count, support_count, is_verified,
               first_reported_at, latest_reported_at,
               ST_Distance(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) AS distance
        FROM issues
        WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius)
          AND status NOT IN :excluded_statuses
          AND canonical_issue_type IN :compatible_types
          AND public_visibility = true
        ORDER BY distance ASC
        LIMIT :limit
    """)

    # sqlalchemy text needs bind params handled differently for IN clauses
    # Use raw SQL with proper parameter handling
    type_placeholders = ", ".join([f":type_{i}" for i in range(len(type_values))])
    status_placeholders = ", ".join([f":status_{i}" for i in range(len(excluded_statuses))])

    raw_sql = f"""
        SELECT id, title, canonical_issue_type, canonical_severity, status,
               latitude, longitude, report_count, support_count, is_verified,
               first_reported_at, latest_reported_at,
               ST_Distance(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) AS distance
        FROM issues
        WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius)
          AND status NOT IN ({status_placeholders})
          AND canonical_issue_type IN ({type_placeholders})
          AND public_visibility = true
        ORDER BY distance ASC
        LIMIT :limit
    """

    params = {"lng": lng, "lat": lat, "radius": radius_meters, "limit": limit}
    for i, t in enumerate(type_values):
        params[f"type_{i}"] = t
    for i, s in enumerate(excluded_statuses):
        params[f"status_{i}"] = s

    result = await db.execute(text(raw_sql), params)
    rows = result.fetchall()

    duplicates = []
    for row in rows:
        duplicates.append({
            "id": str(row.id),
            "title": row.title,
            "canonical_issue_type": row.canonical_issue_type,
            "canonical_severity": row.canonical_severity,
            "status": row.status,
            "latitude": float(row.latitude),
            "longitude": float(row.longitude),
            "report_count": row.report_count,
            "support_count": row.support_count,
            "is_verified": row.is_verified,
            "first_reported_at": row.first_reported_at.isoformat() if row.first_reported_at else None,
            "latest_reported_at": row.latest_reported_at.isoformat() if row.latest_reported_at else None,
            "distance_meters": round(row.distance, 1),
        })
    return duplicates


async def create_issue_from_report(
    db: AsyncSession,
    report: Report,
    user_id: uuid.UUID | None = None,
) -> Issue:
    """Create a new Issue from a report (no existing duplicate match)."""
    geom = ST_SetSRID(ST_MakePoint(float(report.longitude), float(report.latitude)), 4326)

    title = generate_issue_title(
        report.issue_type,
        landmark=report.landmark,
        road_name=report.road_name_input,
        lat=float(report.latitude),
        lng=float(report.longitude),
    )

    score = compute_verification_score(1, 1, report.submitted_at)

    issue = Issue(
        id=uuid.uuid4(),
        primary_report_id=report.id,
        title=title,
        canonical_issue_type=report.issue_type,
        canonical_severity=report.severity,
        status=IssueStatus.reported,
        latitude=report.latitude,
        longitude=report.longitude,
        geom=geom,
        first_reported_at=report.submitted_at,
        latest_reported_at=report.submitted_at,
        report_count=1,
        support_count=0,
        verification_score=Decimal(str(round(score, 4))),
        is_verified=score >= VERIFICATION_THRESHOLD,
        public_visibility=True,
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
    return issue


async def link_report_to_existing_issue(
    db: AsyncSession,
    report: Report,
    issue_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> Issue:
    """Link a report to an existing issue and update aggregated fields."""
    issue = await db.get(Issue, issue_id)
    if not issue:
        raise ValueError(f"Issue {issue_id} not found")

    # Link report to issue
    report.issue_id = issue.id
    ir = IssueReport(
        issue_id=issue.id,
        report_id=report.id,
        link_reason="duplicate_linked",
    )
    db.add(ir)
    await db.flush()

    # Re-aggregate canonical fields
    await recalculate_issue_aggregates(db, issue)

    return issue


async def recalculate_issue_aggregates(db: AsyncSession, issue: Issue):
    """Recalculate canonical fields based on all linked reports."""
    # Get all linked reports
    result = await db.execute(
        select(Report).join(IssueReport, IssueReport.report_id == Report.id)
        .where(IssueReport.issue_id == issue.id)
    )
    linked_reports = result.scalars().all()
    if not linked_reports:
        return

    # report_count
    issue.report_count = len(linked_reports)

    # canonical_severity = highest severity
    highest_severity = max(linked_reports, key=lambda r: SEVERITY_ORDER.get(r.severity, 0)).severity
    issue.canonical_severity = highest_severity

    # canonical_issue_type = most common type, or primary report's type
    type_counts: dict[IssueType, int] = {}
    for r in linked_reports:
        type_counts[r.issue_type] = type_counts.get(r.issue_type, 0) + 1
    issue.canonical_issue_type = max(type_counts, key=type_counts.get)

    # latest_reported_at
    issue.latest_reported_at = max(r.submitted_at for r in linked_reports)

    # first_reported_at (should not change, but ensure correctness)
    issue.first_reported_at = min(r.submitted_at for r in linked_reports)

    # Unique users
    unique_users = len(set(r.user_id for r in linked_reports if r.user_id is not None))
    if unique_users == 0:
        unique_users = 1  # at least 1 if all anonymous

    # verification score + is_verified
    score = compute_verification_score(
        issue.report_count, unique_users, issue.latest_reported_at
    )
    issue.verification_score = Decimal(str(round(score, 4)))
    issue.is_verified = score >= VERIFICATION_THRESHOLD

    await db.flush()


async def get_map_issues(
    db: AsyncSession,
    min_lat: float,
    min_lng: float,
    max_lat: float,
    max_lng: float,
    status_filter: list[str] | None = None,
    severity_filter: list[str] | None = None,
    issue_type_filter: list[str] | None = None,
    verified_only: bool = False,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 500,
) -> dict:
    """Query issues within a map viewport using PostGIS ST_Intersects with MakeEnvelope."""
    # Build dynamic WHERE clauses
    conditions = []
    params: dict = {
        "min_lng": min_lng,
        "min_lat": min_lat,
        "max_lng": max_lng,
        "max_lat": max_lat,
        "limit": limit,
    }

    # Viewport spatial filter
    spatial_clause = """
        ST_Intersects(
            geom::geometry,
            ST_MakeEnvelope(:min_lng, :min_lat, :max_lng, :max_lat, 4326)
        )
    """
    conditions.append(spatial_clause)
    conditions.append("public_visibility = true")

    # Exclude rejected/duplicate
    conditions.append("status NOT IN ('rejected', 'duplicate')")

    if status_filter:
        placeholders = ", ".join([f":sf_{i}" for i in range(len(status_filter))])
        conditions.append(f"status IN ({placeholders})")
        for i, s in enumerate(status_filter):
            params[f"sf_{i}"] = s

    if severity_filter:
        placeholders = ", ".join([f":sevf_{i}" for i in range(len(severity_filter))])
        conditions.append(f"canonical_severity IN ({placeholders})")
        for i, s in enumerate(severity_filter):
            params[f"sevf_{i}"] = s

    if issue_type_filter:
        placeholders = ", ".join([f":itf_{i}" for i in range(len(issue_type_filter))])
        conditions.append(f"canonical_issue_type IN ({placeholders})")
        for i, t in enumerate(issue_type_filter):
            params[f"itf_{i}"] = t

    if verified_only:
        conditions.append("is_verified = true")

    if date_from:
        conditions.append("first_reported_at >= :date_from")
        params["date_from"] = date_from

    if date_to:
        conditions.append("first_reported_at <= :date_to")
        params["date_to"] = date_to

    where_clause = " AND ".join(conditions)

    # Count query
    count_sql = f"SELECT COUNT(*) FROM issues WHERE {where_clause}"
    count_result = await db.execute(text(count_sql), params)
    total_count = count_result.scalar() or 0

    # Data query
    data_sql = f"""
        SELECT id, title, canonical_issue_type, canonical_severity, status,
               latitude, longitude, report_count, support_count, is_verified,
               first_reported_at, latest_reported_at
        FROM issues
        WHERE {where_clause}
        ORDER BY canonical_severity DESC, first_reported_at DESC
        LIMIT :limit
    """

    result = await db.execute(text(data_sql), params)
    rows = result.fetchall()

    issues = []
    for row in rows:
        issues.append({
            "id": str(row.id),
            "title": row.title,
            "canonical_issue_type": row.canonical_issue_type,
            "canonical_severity": row.canonical_severity,
            "status": row.status,
            "latitude": float(row.latitude),
            "longitude": float(row.longitude),
            "report_count": row.report_count,
            "support_count": row.support_count,
            "is_verified": row.is_verified,
            "first_reported_at": row.first_reported_at.isoformat() if row.first_reported_at else None,
            "latest_reported_at": row.latest_reported_at.isoformat() if row.latest_reported_at else None,
        })

    return {
        "issues": issues,
        "total_count": total_count,
        "viewport_bounds": {
            "minLat": min_lat,
            "maxLat": max_lat,
            "minLng": min_lng,
            "maxLng": max_lng,
        },
    }
