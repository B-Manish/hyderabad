"""Admin audit log viewer API."""
import uuid
import math
import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.auth.dependencies import require_role
from app.models.enums import UserRole
from app.models.models import AuditLog, User
from pydantic import BaseModel
from datetime import datetime


router = APIRouter(prefix="/admin/audit-logs", tags=["admin-audit"])


class AuditLogItem(BaseModel):
    id: uuid.UUID
    actor_user_id: uuid.UUID | None = None
    actor_name: str | None = None
    actor_email: str | None = None
    entity_type: str
    entity_id: uuid.UUID | None = None
    action: str
    metadata_json: dict | None = None
    created_at: str


class PaginatedAuditLogs(BaseModel):
    items: list[AuditLogItem]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("", response_model=PaginatedAuditLogs)
async def list_audit_logs(
    entity_type: str | None = Query(None),
    action: str | None = Query(None),
    actor_id: uuid.UUID | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    query = select(AuditLog).options(selectinload(AuditLog.actor))

    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if action:
        query = query.where(AuditLog.action == action)
    if actor_id:
        query = query.where(AuditLog.actor_user_id == actor_id)
    if date_from:
        query = query.where(AuditLog.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.where(AuditLog.created_at <= datetime.fromisoformat(date_to))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().unique().all()

    items = []
    for log in logs:
        items.append(AuditLogItem(
            id=log.id,
            actor_user_id=log.actor_user_id,
            actor_name=log.actor.name if log.actor else None,
            actor_email=log.actor.email if log.actor else None,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            action=log.action,
            metadata_json=log.metadata_json,
            created_at=log.created_at.isoformat(),
        ))

    return PaginatedAuditLogs(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )


@router.get("/export")
async def export_audit_logs_csv(
    entity_type: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    query = select(AuditLog).options(selectinload(AuditLog.actor)).order_by(AuditLog.created_at.desc())
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if date_from:
        query = query.where(AuditLog.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.where(AuditLog.created_at <= datetime.fromisoformat(date_to))

    result = await db.execute(query)
    logs = result.scalars().unique().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "actor_email", "entity_type", "entity_id", "action", "metadata", "created_at"])
    for log in logs:
        writer.writerow([
            str(log.id),
            log.actor.email if log.actor else "",
            log.entity_type,
            str(log.entity_id) if log.entity_id else "",
            log.action,
            str(log.metadata_json) if log.metadata_json else "",
            log.created_at.isoformat(),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs_export.csv"},
    )
