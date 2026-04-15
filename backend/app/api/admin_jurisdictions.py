"""Admin jurisdiction management APIs: import, override, CRUD."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth.dependencies import require_role
from app.models.enums import UserRole, LayerType
from app.models.models import User, ResponsibilityMapping
from app.services.geo_import import import_geojson, import_csv_wkt, deactivate_layer, get_ward_polygons_geojson
from app.services.authority import invalidate_authority_cache
from app.schemas.schemas import (
    ResponsibilityMappingCreate, ResponsibilityMappingResponse, JurisdictionImportResponse,
)

router = APIRouter(prefix="/admin/jurisdictions", tags=["admin-jurisdictions"])

MAX_IMPORT_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/import", response_model=JurisdictionImportResponse)
async def import_jurisdiction_data(
    file: UploadFile = File(...),
    layer_type: str = Form(...),
    source_name: str = Form(...),
    source_version: str = Form("v1"),
    authority_id: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    """Import GeoJSON or CSV jurisdiction/road data."""
    # Validate layer_type
    valid_layer_types = [lt.value for lt in LayerType] + ["road_segments"]
    if layer_type not in valid_layer_types:
        raise HTTPException(status_code=400, detail=f"Invalid layer_type. Must be one of {valid_layer_types}")

    # Validate file type
    filename = file.filename or ""
    content = await file.read()
    if len(content) > MAX_IMPORT_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum 50MB.")

    if filename.endswith(".geojson") or filename.endswith(".json"):
        result = await import_geojson(
            db, content, layer_type, source_name, source_version, authority_id,
        )
    elif filename.endswith(".csv"):
        result = await import_csv_wkt(
            db, content, layer_type, source_name, source_version, authority_id,
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Use .geojson, .json, or .csv")

    # Invalidate authority cache after import
    await invalidate_authority_cache()

    # Log the admin action
    await db.execute(
        text("""
            INSERT INTO issue_status_history (id, issue_id, new_status, changed_by_user_id, change_reason, created_at)
            SELECT :log_id, '00000000-0000-0000-0000-000000000000'::uuid, 'admin_action', :user_id,
                   :reason, now()
            WHERE false
        """),
        {"log_id": str(uuid.uuid4()), "user_id": str(user.id), "reason": f"Imported {layer_type} from {source_name}"},
    )

    return JurisdictionImportResponse(**result)


@router.get("/polygons")
async def get_polygons_geojson(
    layer_type: str = Query("ward"),
    db: AsyncSession = Depends(get_db),
):
    """Get jurisdiction polygons as GeoJSON (for map overlay)."""
    return await get_ward_polygons_geojson(db, layer_type)


@router.post("/deactivate")
async def deactivate_layer_data(
    layer_type: str = Form(...),
    source_name: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    """Deactivate all polygons for a layer type (before re-import)."""
    count = await deactivate_layer(db, layer_type, source_name)
    await invalidate_authority_cache()
    return {"deactivated": count, "layer_type": layer_type}


# -- Responsibility Mapping / Override APIs --

override_router = APIRouter(prefix="/admin/responsibility-mappings", tags=["admin-overrides"])


@override_router.post("", response_model=ResponsibilityMappingResponse)
async def create_responsibility_mapping(
    data: ResponsibilityMappingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    """Create or override a responsibility mapping (admin override)."""
    mapping = ResponsibilityMapping(
        id=uuid.uuid4(),
        polygon_id=data.polygon_id,
        road_segment_id=data.road_segment_id,
        primary_authority_id=data.primary_authority_id,
        secondary_authority_id=data.secondary_authority_id,
        ownership_confidence=data.ownership_confidence,
        notes=f"admin_override: set by {user.email or user.id}" + (f" — {data.notes}" if data.notes else ""),
    )
    db.add(mapping)
    await db.flush()
    await invalidate_authority_cache()
    return ResponsibilityMappingResponse(
        id=mapping.id,
        polygon_id=mapping.polygon_id,
        road_segment_id=mapping.road_segment_id,
        primary_authority_id=mapping.primary_authority_id,
        secondary_authority_id=mapping.secondary_authority_id,
        ownership_confidence=float(mapping.ownership_confidence),
        notes=mapping.notes,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at,
    )


@override_router.patch("/{mapping_id}", response_model=ResponsibilityMappingResponse)
async def update_responsibility_mapping(
    mapping_id: uuid.UUID,
    data: ResponsibilityMappingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    """Update an existing responsibility mapping."""
    result = await db.execute(
        text("SELECT * FROM responsibility_mappings WHERE id = :id"),
        {"id": str(mapping_id)},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Mapping not found")

    await db.execute(
        text("""
            UPDATE responsibility_mappings
            SET primary_authority_id = :primary_authority_id,
                secondary_authority_id = :secondary_authority_id,
                ownership_confidence = :ownership_confidence,
                notes = :notes,
                updated_at = now()
            WHERE id = :id
        """),
        {
            "id": str(mapping_id),
            "primary_authority_id": str(data.primary_authority_id),
            "secondary_authority_id": str(data.secondary_authority_id) if data.secondary_authority_id else None,
            "ownership_confidence": data.ownership_confidence,
            "notes": f"admin_override: updated by {user.email or user.id}" + (f" — {data.notes}" if data.notes else ""),
        },
    )
    await invalidate_authority_cache()

    updated = await db.execute(
        text("SELECT * FROM responsibility_mappings WHERE id = :id"),
        {"id": str(mapping_id)},
    )
    row = updated.mappings().first()
    return ResponsibilityMappingResponse(
        id=row["id"],
        polygon_id=row["polygon_id"],
        road_segment_id=row["road_segment_id"],
        primary_authority_id=row["primary_authority_id"],
        secondary_authority_id=row["secondary_authority_id"],
        ownership_confidence=float(row["ownership_confidence"]),
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
