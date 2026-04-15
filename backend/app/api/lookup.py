"""Authority lookup and reverse geocode API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.authority import resolve_authority, reverse_geocode

router = APIRouter(prefix="/lookup", tags=["lookup"])


@router.get("/authority")
async def authority_lookup(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    db: AsyncSession = Depends(get_db),
):
    """Resolve which authority is responsible for a given GPS location."""
    result = await resolve_authority(db, lat, lng)
    return result


@router.get("/reverse-geocode")
async def reverse_geocode_endpoint(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    db: AsyncSession = Depends(get_db),
):
    """Reverse geocode a point to ward/zone/circle/road information."""
    result = await reverse_geocode(db, lat, lng)
    return result
