"""Authority resolution engine — the platform's core differentiator.
Given a GPS coordinate, resolve which authority is responsible, which ward/circle/zone
the point belongs to, and provide the full accountability chain with confidence scoring.
"""
import uuid
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.cache import get_redis

# Road class → default authority inference
ROAD_CLASS_AUTHORITY: dict[str, tuple[str, float]] = {
    "national_highway": ("NHAI", 0.85),
    "state_highway": ("R&B", 0.75),
    "municipal": ("GHMC", 0.70),
    "local": ("GHMC", 0.65),
    "unknown": ("GHMC", 0.40),
}

# Step weights for score aggregation
WEIGHT_SPECIAL_ZONE = 1.0
WEIGHT_EXPLICIT_ROAD = 0.9
WEIGHT_WARD_CONTAINMENT = 0.7
WEIGHT_ROAD_CLASS = 0.6


def classify_confidence(score: float) -> str:
    if score >= 0.80:
        return "high"
    elif score >= 0.50:
        return "medium"
    elif score >= 0.20:
        return "low"
    else:
        return "very_low"


async def _get_cached_authority(lat: float, lng: float) -> dict | None:
    """Check Redis cache for authority lookup using geohash-like key."""
    try:
        r = await get_redis()
        # Use 4 decimal places for cache key (~11m precision)
        key = f"authority:{lat:.4f},{lng:.4f}"
        import json
        data = await r.get(key)
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


async def _set_cached_authority(lat: float, lng: float, result: dict, ttl: int = 300):
    """Cache authority lookup result."""
    try:
        r = await get_redis()
        key = f"authority:{lat:.4f},{lng:.4f}"
        import json
        await r.setex(key, ttl, json.dumps(result, default=str))
    except Exception:
        pass


async def invalidate_authority_cache():
    """Invalidate all authority lookup caches."""
    try:
        r = await get_redis()
        cursor = 0
        while True:
            cursor, keys = await r.scan(cursor, match="authority:*", count=100)
            if keys:
                await r.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        pass


async def resolve_authority(db: AsyncSession, lat: float, lng: float) -> dict:
    """
    Full authority resolution pipeline.
    Steps:
    1. Check special road zones
    2. Check road segment explicit mapping
    3. Check municipal ward/circle/zone containment
    4. Road class inference
    5. Apply admin overrides
    6. Compute final weighted score
    """
    # Check cache first
    cached = await _get_cached_authority(lat, lng)
    if cached:
        return cached

    scores: list[tuple[str | None, float, float, str]] = []  # (authority_id, confidence, weight, source)
    ward_info = None
    circle_info = None
    zone_info = None
    nearest_road = None
    accountability_chain = []

    # Step 1: Check special road zones
    step1 = await _step1_special_road_zones(db, lat, lng)
    if step1:
        scores.append((str(step1["authority_id"]), step1["confidence"], WEIGHT_SPECIAL_ZONE, "special_road_zone"))

    # Step 2: Check road segment explicit mapping
    step2 = await _step2_road_segment_mapping(db, lat, lng)
    if step2:
        nearest_road = step2.get("road")
        if step2.get("authority_id"):
            scores.append((str(step2["authority_id"]), step2["confidence"], WEIGHT_EXPLICIT_ROAD, "explicit_road_mapping"))

    # Step 3: Check municipal ward/circle/zone
    step3 = await _step3_ward_containment(db, lat, lng)
    if step3:
        ward_info = step3.get("ward")
        circle_info = step3.get("circle")
        zone_info = step3.get("zone")
        if step3.get("authority_id"):
            scores.append((str(step3["authority_id"]), 0.70, WEIGHT_WARD_CONTAINMENT, "ward_containment"))

    # Step 4: Road class inference
    if nearest_road and not step2.get("authority_id"):
        step4 = _step4_road_class_inference(nearest_road.get("road_class"))
        if step4:
            scores.append((step4["authority_id"], step4["confidence"], WEIGHT_ROAD_CLASS, "road_class_inference"))

    # Step 5: Admin overrides
    step5 = await _step5_admin_overrides(db, lat, lng)
    if step5:
        # Override replaces all other scores
        scores = [(str(step5["authority_id"]), step5["confidence"], 1.0, "admin_override")]

    # Step 6: Compute final score
    primary_authority = None
    alternate_authorities = []
    final_confidence = 0.0
    steps_matched = []

    # Group scores by authority
    authority_scores: dict[str, float] = {}
    for auth_id, conf, weight, source in scores:
        if auth_id:
            weighted = conf * weight
            authority_scores[auth_id] = authority_scores.get(auth_id, 0) + weighted
            steps_matched.append(source)

    if authority_scores:
        # Normalize scores
        max_possible = max(authority_scores.values())
        if max_possible > 0:
            sorted_auths = sorted(authority_scores.items(), key=lambda x: x[1], reverse=True)
            total_score = sum(s for _, s in sorted_auths)

            # Look up authority details
            for auth_id, score in sorted_auths:
                normalized = min(1.0, score / max(1.0, total_score) if total_score > 1.0 else score)
                auth_detail = await _get_authority_detail(db, auth_id)
                if auth_detail:
                    entry = {**auth_detail, "confidence": round(normalized, 4)}
                    if primary_authority is None:
                        primary_authority = entry
                        final_confidence = normalized
                    else:
                        alternate_authorities.append(entry)

    # If no authority found, use default GHMC
    if primary_authority is None:
        primary_authority = await _get_default_authority(db)
        final_confidence = 0.15

    # Get accountability chain
    if primary_authority and primary_authority.get("id"):
        accountability_chain = await _get_accountability_chain(
            db, primary_authority["id"],
            ward_info.get("id") if ward_info else None,
        )

    result = {
        "primary_authority": primary_authority,
        "alternate_authorities": alternate_authorities,
        "ward": ward_info,
        "circle": circle_info,
        "zone": zone_info,
        "nearest_road": nearest_road,
        "accountability_chain": accountability_chain,
        "confidence_level": classify_confidence(final_confidence),
        "resolution_metadata": {
            "steps_matched": steps_matched,
            "data_version": "2026-04",
        },
    }

    # Cache the result
    await _set_cached_authority(lat, lng, result)

    return result


async def _step1_special_road_zones(db: AsyncSession, lat: float, lng: float) -> dict | None:
    """Check if point falls within a special road zone."""
    query = text("""
        SELECT jp.id, jp.authority_id, rm.ownership_confidence
        FROM jurisdiction_polygons jp
        LEFT JOIN responsibility_mappings rm ON rm.polygon_id = jp.id
        WHERE jp.layer_type = 'special_road_zone'
          AND jp.is_active = true
          AND ST_Contains(jp.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))
        LIMIT 1
    """)
    result = await db.execute(query, {"lat": lat, "lng": lng})
    row = result.mappings().first()
    if row and row["authority_id"]:
        return {
            "authority_id": str(row["authority_id"]),
            "confidence": float(row["ownership_confidence"] or 0.85),
        }
    return None


async def _step2_road_segment_mapping(db: AsyncSession, lat: float, lng: float) -> dict | None:
    """Find nearest road segment and check for explicit authority mapping."""
    query = text("""
        SELECT rs.id, rs.name, rs.road_class, rs.osm_way_id,
               ST_Distance(rs.geom::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) AS distance,
               rm.primary_authority_id, rm.ownership_confidence
        FROM road_segments rs
        LEFT JOIN responsibility_mappings rm ON rm.road_segment_id = rs.id
        WHERE ST_DWithin(rs.geom::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, 50)
        ORDER BY distance
        LIMIT 1
    """)
    result = await db.execute(query, {"lat": lat, "lng": lng})
    row = result.mappings().first()
    if row:
        road = {
            "id": str(row["id"]),
            "name": row["name"],
            "road_class": row["road_class"],
            "distance_meters": round(float(row["distance"]), 1),
        }
        auth_id = str(row["primary_authority_id"]) if row["primary_authority_id"] else None
        confidence = float(row["ownership_confidence"]) if row["ownership_confidence"] else 0.0
        return {
            "road": road,
            "authority_id": auth_id,
            "confidence": confidence,
        }
    return None


async def _step3_ward_containment(db: AsyncSession, lat: float, lng: float) -> dict | None:
    """Check ward, circle, zone containment."""
    query = text("""
        SELECT jp.id, jp.layer_type, jp.name, jp.code, jp.authority_id
        FROM jurisdiction_polygons jp
        WHERE jp.is_active = true
          AND jp.layer_type IN ('ward', 'circle', 'zone')
          AND ST_Contains(jp.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))
        ORDER BY jp.layer_type
    """)
    result = await db.execute(query, {"lat": lat, "lng": lng})
    rows = result.mappings().all()

    if not rows:
        return None

    data: dict = {}
    authority_id = None
    for row in rows:
        layer = row["layer_type"]
        info = {
            "id": str(row["id"]),
            "name": row["name"],
            "code": row["code"],
        }
        if layer == "ward":
            data["ward"] = info
            if row["authority_id"]:
                authority_id = str(row["authority_id"])
        elif layer == "circle":
            data["circle"] = info
        elif layer == "zone":
            data["zone"] = info
        # Use ward authority, fallback to circle, then zone
        if not authority_id and row["authority_id"]:
            authority_id = str(row["authority_id"])

    data["authority_id"] = authority_id
    return data


def _step4_road_class_inference(road_class: str | None) -> dict | None:
    """Infer authority from road class."""
    if not road_class:
        road_class = "unknown"
    mapping = ROAD_CLASS_AUTHORITY.get(road_class, ROAD_CLASS_AUTHORITY["unknown"])
    # Return authority name — will be resolved to ID by caller or via lookup
    return {
        "authority_id": None,  # Will be looked up by name
        "authority_name": mapping[0],
        "confidence": mapping[1],
    }


async def _step5_admin_overrides(db: AsyncSession, lat: float, lng: float) -> dict | None:
    """Check for admin overrides at this location."""
    # Check responsibility_mappings with polygon containment or road proximity
    # that have explicit admin-set confidence
    query = text("""
        SELECT rm.primary_authority_id, rm.ownership_confidence, rm.notes
        FROM responsibility_mappings rm
        JOIN jurisdiction_polygons jp ON rm.polygon_id = jp.id
        WHERE jp.is_active = true
          AND rm.ownership_confidence >= 0.9000
          AND rm.notes LIKE '%%admin_override%%'
          AND ST_Contains(jp.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))
        ORDER BY rm.ownership_confidence DESC
        LIMIT 1
    """)
    result = await db.execute(query, {"lat": lat, "lng": lng})
    row = result.mappings().first()
    if row:
        return {
            "authority_id": str(row["primary_authority_id"]),
            "confidence": float(row["ownership_confidence"]),
        }
    return None


async def _get_authority_detail(db: AsyncSession, authority_id: str) -> dict | None:
    """Fetch authority details by ID."""
    query = text("""
        SELECT id, name, authority_type, website_url, grievance_url, contact_phone, contact_email
        FROM authorities
        WHERE id = :id AND is_active = true
    """)
    result = await db.execute(query, {"id": authority_id})
    row = result.mappings().first()
    if row:
        return {
            "id": str(row["id"]),
            "name": row["name"],
            "authority_type": row["authority_type"],
            "website_url": row["website_url"],
            "grievance_url": row["grievance_url"],
            "contact_phone": row["contact_phone"],
            "contact_email": row["contact_email"],
        }
    return None


async def _get_default_authority(db: AsyncSession) -> dict:
    """Get GHMC as default authority."""
    query = text("""
        SELECT id, name, authority_type, website_url, grievance_url, contact_phone, contact_email
        FROM authorities
        WHERE name = 'GHMC' AND is_active = true
        LIMIT 1
    """)
    result = await db.execute(query)
    row = result.mappings().first()
    if row:
        return {
            "id": str(row["id"]),
            "name": row["name"],
            "authority_type": row["authority_type"],
            "confidence": 0.15,
        }
    return {
        "id": None,
        "name": "Unknown",
        "authority_type": "other",
        "confidence": 0.0,
    }


async def _get_accountability_chain(
    db: AsyncSession,
    authority_id: str,
    ward_polygon_id: str | None = None,
) -> list[dict]:
    """Get the accountability chain for an authority, optionally scoped to a ward."""
    query = text("""
        SELECT id, node_type, display_name, title, phone, email, display_order, is_public
        FROM accountability_chain_nodes
        WHERE authority_id = :authority_id
          AND (jurisdiction_polygon_id IS NULL OR jurisdiction_polygon_id = :ward_id)
          AND is_public = true
        ORDER BY display_order ASC
    """)
    result = await db.execute(query, {"authority_id": authority_id, "ward_id": ward_polygon_id})
    rows = result.mappings().all()
    return [
        {
            "type": row["node_type"],
            "title": row["title"],
            "display_name": row["display_name"],
            "phone": row["phone"],
            "email": row["email"],
            "is_public": row["is_public"],
        }
        for row in rows
    ]


async def reverse_geocode(db: AsyncSession, lat: float, lng: float) -> dict:
    """Reverse geocode a point to ward/zone/road info."""
    ward = None
    zone = None
    circle = None
    nearest_road = None

    # Ward/circle/zone containment
    poly_query = text("""
        SELECT jp.layer_type, jp.name, jp.code
        FROM jurisdiction_polygons jp
        WHERE jp.is_active = true
          AND jp.layer_type IN ('ward', 'circle', 'zone')
          AND ST_Contains(jp.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))
        ORDER BY jp.layer_type
    """)
    result = await db.execute(poly_query, {"lat": lat, "lng": lng})
    for row in result.mappings().all():
        info = {"name": row["name"], "code": row["code"]}
        if row["layer_type"] == "ward":
            ward = info
        elif row["layer_type"] == "circle":
            circle = info
        elif row["layer_type"] == "zone":
            zone = info

    # Nearest road
    road_query = text("""
        SELECT rs.name,
               ST_Distance(rs.geom::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) AS distance
        FROM road_segments rs
        WHERE ST_DWithin(rs.geom::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, 200)
        ORDER BY distance
        LIMIT 1
    """)
    result = await db.execute(road_query, {"lat": lat, "lng": lng})
    road_row = result.mappings().first()
    if road_row:
        nearest_road = {
            "name": road_row["name"],
            "distance_meters": round(float(road_row["distance"]), 1),
        }

    # Locality hint from ward name or nearest road
    locality_hint = None
    if ward:
        locality_hint = ward["name"]
    elif nearest_road:
        locality_hint = nearest_road["name"]

    return {
        "ward": ward,
        "zone": zone,
        "circle": circle,
        "nearest_road": nearest_road,
        "locality_hint": locality_hint,
    }
