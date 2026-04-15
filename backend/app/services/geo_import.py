"""GeoJSON/Shapefile/CSV import pipeline for jurisdiction polygons and road segments."""
import uuid
import json
import io
import csv
from typing import BinaryIO
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def import_geojson(
    db: AsyncSession,
    file_content: bytes,
    layer_type: str,
    source_name: str,
    source_version: str,
    authority_id: str | None = None,
) -> dict:
    """Import GeoJSON features into jurisdiction_polygons or road_segments."""
    data = json.loads(file_content)
    features = data.get("features", [])
    if not features:
        return {"status": "error", "message": "No features found in GeoJSON", "imported": 0, "errors": 0}

    imported = 0
    errors = 0
    error_details = []

    for i, feature in enumerate(features):
        try:
            geom = feature.get("geometry")
            props = feature.get("properties", {})

            if not geom:
                errors += 1
                error_details.append(f"Feature {i}: missing geometry")
                continue

            geom_type = geom.get("type", "")
            geom_json = json.dumps(geom)

            # Route to appropriate import function
            if layer_type == "road_segments":
                await _import_road_segment(db, geom_json, geom_type, props, source_name, source_version)
            else:
                await _import_polygon(
                    db, geom_json, geom_type, props, layer_type,
                    source_name, source_version, authority_id,
                )
            imported += 1
        except Exception as e:
            errors += 1
            error_details.append(f"Feature {i}: {str(e)}")

    await db.flush()
    return {
        "status": "completed",
        "features_found": len(features),
        "imported": imported,
        "errors": errors,
        "error_details": error_details[:20],  # Limit error details
    }


async def import_csv_wkt(
    db: AsyncSession,
    file_content: bytes,
    layer_type: str,
    source_name: str,
    source_version: str,
    authority_id: str | None = None,
) -> dict:
    """Import CSV with WKT geometry column."""
    text_content = file_content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text_content))

    imported = 0
    errors = 0
    error_details = []
    total = 0

    for i, row in enumerate(reader):
        total += 1
        try:
            wkt = row.get("geometry") or row.get("wkt") or row.get("geom")
            if not wkt:
                errors += 1
                error_details.append(f"Row {i}: no geometry column found")
                continue

            name = row.get("name", f"Feature {i}")
            code = row.get("code", "")

            if layer_type == "road_segments":
                road_class = row.get("road_class", "")
                osm_way_id = row.get("osm_way_id")
                alt_names = row.get("alt_names", "").split(";") if row.get("alt_names") else None
                await db.execute(
                    text("""
                        INSERT INTO road_segments (id, name, alt_names, road_class, osm_way_id, geom, source_name, source_version)
                        VALUES (:id, :name, :alt_names, :road_class, :osm_way_id,
                                ST_Multi(ST_GeomFromText(:wkt, 4326)), :source_name, :source_version)
                    """),
                    {
                        "id": str(uuid.uuid4()), "name": name, "alt_names": alt_names,
                        "road_class": road_class, "osm_way_id": int(osm_way_id) if osm_way_id else None,
                        "wkt": wkt, "source_name": source_name, "source_version": source_version,
                    },
                )
            else:
                await db.execute(
                    text("""
                        INSERT INTO jurisdiction_polygons (id, authority_id, layer_type, name, code, geom, source_name, source_version)
                        VALUES (:id, :authority_id, :layer_type, :name, :code,
                                ST_Multi(ST_GeomFromText(:wkt, 4326)), :source_name, :source_version)
                    """),
                    {
                        "id": str(uuid.uuid4()), "authority_id": authority_id,
                        "layer_type": layer_type, "name": name, "code": code,
                        "wkt": wkt, "source_name": source_name, "source_version": source_version,
                    },
                )
            imported += 1
        except Exception as e:
            errors += 1
            error_details.append(f"Row {i}: {str(e)}")

    await db.flush()
    return {
        "status": "completed",
        "features_found": total,
        "imported": imported,
        "errors": errors,
        "error_details": error_details[:20],
    }


async def _import_polygon(
    db: AsyncSession,
    geom_json: str,
    geom_type: str,
    props: dict,
    layer_type: str,
    source_name: str,
    source_version: str,
    authority_id: str | None,
):
    """Insert a single polygon feature."""
    name = props.get("name") or props.get("NAME") or props.get("ward_name") or props.get("zone_name") or f"Unnamed {layer_type}"
    code = props.get("code") or props.get("CODE") or props.get("ward_no") or props.get("ward_code") or ""

    # Ensure MultiPolygon
    convert_expr = "ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326))"
    if geom_type == "MultiPolygon":
        convert_expr = "ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)"

    await db.execute(
        text(f"""
            INSERT INTO jurisdiction_polygons (id, authority_id, layer_type, name, code, geom, source_name, source_version)
            VALUES (:id, :authority_id, :layer_type, :name, :code,
                    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)),
                    :source_name, :source_version)
        """),
        {
            "id": str(uuid.uuid4()), "authority_id": authority_id,
            "layer_type": layer_type, "name": name, "code": code,
            "geom": geom_json, "source_name": source_name, "source_version": source_version,
        },
    )


async def _import_road_segment(
    db: AsyncSession,
    geom_json: str,
    geom_type: str,
    props: dict,
    source_name: str,
    source_version: str,
):
    """Insert a single road segment feature."""
    name = props.get("name") or props.get("NAME") or props.get("road_name") or None
    road_class = props.get("road_class") or props.get("highway") or props.get("road_type") or None
    osm_way_id = props.get("osm_id") or props.get("osm_way_id") or None
    alt_names_raw = props.get("alt_names") or props.get("alt_name") or None
    alt_names = alt_names_raw.split(";") if isinstance(alt_names_raw, str) else alt_names_raw

    # Map OSM highway tags to our road classes
    if road_class:
        road_class = _normalize_road_class(road_class)

    await db.execute(
        text("""
            INSERT INTO road_segments (id, name, alt_names, road_class, osm_way_id, geom, source_name, source_version)
            VALUES (:id, :name, :alt_names, :road_class, :osm_way_id,
                    ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)),
                    :source_name, :source_version)
        """),
        {
            "id": str(uuid.uuid4()), "name": name, "alt_names": alt_names,
            "road_class": road_class, "osm_way_id": int(osm_way_id) if osm_way_id else None,
            "geom": geom_json, "source_name": source_name, "source_version": source_version,
        },
    )


def _normalize_road_class(raw: str) -> str:
    """Map OSM highway tags and other formats to standard road classes."""
    mapping = {
        "trunk": "national_highway",
        "trunk_link": "national_highway",
        "motorway": "national_highway",
        "motorway_link": "national_highway",
        "primary": "state_highway",
        "primary_link": "state_highway",
        "secondary": "municipal",
        "secondary_link": "municipal",
        "tertiary": "municipal",
        "tertiary_link": "municipal",
        "residential": "local",
        "living_street": "local",
        "unclassified": "local",
        "service": "local",
    }
    return mapping.get(raw.lower(), raw.lower())


async def deactivate_layer(
    db: AsyncSession,
    layer_type: str,
    source_name: str | None = None,
) -> int:
    """Deactivate polygons for a given layer (used before re-importing updated data)."""
    if source_name:
        result = await db.execute(
            text("""
                UPDATE jurisdiction_polygons SET is_active = false, updated_at = now()
                WHERE layer_type = :layer_type AND source_name = :source_name AND is_active = true
            """),
            {"layer_type": layer_type, "source_name": source_name},
        )
    else:
        result = await db.execute(
            text("""
                UPDATE jurisdiction_polygons SET is_active = false, updated_at = now()
                WHERE layer_type = :layer_type AND is_active = true
            """),
            {"layer_type": layer_type},
        )
    return result.rowcount


async def get_ward_polygons_geojson(db: AsyncSession, layer_type: str = "ward") -> dict:
    """Export ward/zone/circle polygons as GeoJSON for frontend map overlay."""
    query = text("""
        SELECT jp.id, jp.name, jp.code, jp.layer_type,
               ST_AsGeoJSON(jp.geom)::json AS geometry
        FROM jurisdiction_polygons jp
        WHERE jp.is_active = true AND jp.layer_type = :layer_type
    """)
    result = await db.execute(query, {"layer_type": layer_type})
    rows = result.mappings().all()

    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "properties": {
                "id": str(row["id"]),
                "name": row["name"],
                "code": row["code"],
                "layer_type": row["layer_type"],
            },
            "geometry": row["geometry"],
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }
