"""Admin user management API."""
import uuid
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth.dependencies import require_role
from app.models.enums import UserRole
from app.models.models import User
from app.services.audit import write_audit_log
from pydantic import BaseModel


router = APIRouter(prefix="/admin/users", tags=["admin-users"])


class AdminUserItem(BaseModel):
    id: uuid.UUID
    name: str | None = None
    email: str | None = None
    role: str
    auth_provider: str
    is_active: bool
    created_at: str


class PaginatedUsers(BaseModel):
    items: list[AdminUserItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class RoleChangeRequest(BaseModel):
    role: str


class DeactivateRequest(BaseModel):
    is_active: bool


@router.get("", response_model=PaginatedUsers)
async def list_users(
    search: str | None = Query(None),
    role: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    query = select(User)

    if search:
        query = query.where(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
        )
    if role:
        query = query.where(User.role == UserRole(role))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    items = [
        AdminUserItem(
            id=u.id,
            name=u.name,
            email=u.email,
            role=u.role.value,
            auth_provider=u.auth_provider,
            is_active=u.is_active,
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]

    return PaginatedUsers(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )


@router.patch("/{user_id}/role")
async def change_user_role(
    user_id: uuid.UUID,
    body: RoleChangeRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.admin)),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        new_role = UserRole(body.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    old_role = target_user.role.value
    target_user.role = new_role

    await write_audit_log(
        db,
        actor_user_id=admin.id,
        entity_type="user",
        entity_id=user_id,
        action="role_change",
        metadata_json={"old_role": old_role, "new_role": body.role},
    )

    await db.flush()
    return {"user_id": str(user_id), "role": body.role}


@router.patch("/{user_id}/deactivate")
async def deactivate_user(
    user_id: uuid.UUID,
    body: DeactivateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.admin)),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user.is_active = body.is_active

    await write_audit_log(
        db,
        actor_user_id=admin.id,
        entity_type="user",
        entity_id=user_id,
        action="deactivation" if not body.is_active else "reactivation",
        metadata_json={"is_active": body.is_active},
    )

    await db.flush()
    return {"user_id": str(user_id), "is_active": body.is_active}
