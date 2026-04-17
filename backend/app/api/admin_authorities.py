"""Admin authority & accountability chain management API."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth.dependencies import require_role
from app.models.enums import UserRole, AuthorityType, AccountabilityNodeType
from app.models.models import Authority, AccountabilityChainNode, User
from app.services.audit import write_audit_log
from pydantic import BaseModel


router = APIRouter(prefix="/admin/authorities", tags=["admin-authorities"])


class AuthorityCreateRequest(BaseModel):
    name: str
    authority_type: str
    parent_authority_id: uuid.UUID | None = None
    description: str | None = None
    website_url: str | None = None
    grievance_url: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None


class AuthorityUpdateRequest(BaseModel):
    name: str | None = None
    authority_type: str | None = None
    description: str | None = None
    website_url: str | None = None
    grievance_url: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    is_active: bool | None = None


class AuthorityAdminResponse(BaseModel):
    id: uuid.UUID
    name: str
    authority_type: str
    parent_authority_id: uuid.UUID | None = None
    description: str | None = None
    website_url: str | None = None
    grievance_url: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    is_active: bool
    created_at: str
    updated_at: str


class ChainNodeCreateRequest(BaseModel):
    authority_id: uuid.UUID
    jurisdiction_polygon_id: uuid.UUID | None = None
    node_type: str
    display_name: str
    title: str | None = None
    phone: str | None = None
    email: str | None = None
    display_order: int = 0
    is_public: bool = True


class ChainNodeResponse(BaseModel):
    id: uuid.UUID
    authority_id: uuid.UUID
    jurisdiction_polygon_id: uuid.UUID | None = None
    node_type: str
    display_name: str
    title: str | None = None
    phone: str | None = None
    email: str | None = None
    display_order: int
    is_public: bool


@router.get("", response_model=list[AuthorityAdminResponse])
async def list_authorities(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    result = await db.execute(select(Authority).order_by(Authority.name))
    authorities = result.scalars().all()
    return [
        AuthorityAdminResponse(
            id=a.id,
            name=a.name,
            authority_type=a.authority_type.value,
            parent_authority_id=a.parent_authority_id,
            description=a.description,
            website_url=a.website_url,
            grievance_url=a.grievance_url,
            contact_phone=a.contact_phone,
            contact_email=a.contact_email,
            is_active=a.is_active,
            created_at=a.created_at.isoformat(),
            updated_at=a.updated_at.isoformat(),
        )
        for a in authorities
    ]


@router.post("", response_model=AuthorityAdminResponse)
async def create_authority(
    body: AuthorityCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    auth = Authority(
        id=uuid.uuid4(),
        name=body.name,
        authority_type=AuthorityType(body.authority_type),
        parent_authority_id=body.parent_authority_id,
        description=body.description,
        website_url=body.website_url,
        grievance_url=body.grievance_url,
        contact_phone=body.contact_phone,
        contact_email=body.contact_email,
    )
    db.add(auth)
    await db.flush()

    await write_audit_log(
        db,
        actor_user_id=user.id,
        entity_type="authority",
        entity_id=auth.id,
        action="create",
        metadata_json={"name": body.name, "authority_type": body.authority_type},
    )

    return AuthorityAdminResponse(
        id=auth.id,
        name=auth.name,
        authority_type=auth.authority_type.value,
        parent_authority_id=auth.parent_authority_id,
        description=auth.description,
        website_url=auth.website_url,
        grievance_url=auth.grievance_url,
        contact_phone=auth.contact_phone,
        contact_email=auth.contact_email,
        is_active=auth.is_active,
        created_at=auth.created_at.isoformat(),
        updated_at=auth.updated_at.isoformat(),
    )


@router.patch("/{authority_id}", response_model=AuthorityAdminResponse)
async def update_authority(
    authority_id: uuid.UUID,
    body: AuthorityUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    result = await db.execute(select(Authority).where(Authority.id == authority_id))
    auth = result.scalar_one_or_none()
    if not auth:
        raise HTTPException(status_code=404, detail="Authority not found")

    old_values = {}
    new_values = {}

    if body.name is not None:
        old_values["name"] = auth.name
        auth.name = body.name
        new_values["name"] = body.name
    if body.authority_type is not None:
        old_values["authority_type"] = auth.authority_type.value
        auth.authority_type = AuthorityType(body.authority_type)
        new_values["authority_type"] = body.authority_type
    if body.description is not None:
        old_values["description"] = auth.description
        auth.description = body.description
        new_values["description"] = body.description
    if body.website_url is not None:
        auth.website_url = body.website_url
    if body.grievance_url is not None:
        auth.grievance_url = body.grievance_url
    if body.contact_phone is not None:
        auth.contact_phone = body.contact_phone
    if body.contact_email is not None:
        auth.contact_email = body.contact_email
    if body.is_active is not None:
        old_values["is_active"] = auth.is_active
        auth.is_active = body.is_active
        new_values["is_active"] = body.is_active

    await write_audit_log(
        db,
        actor_user_id=user.id,
        entity_type="authority",
        entity_id=authority_id,
        action="update",
        metadata_json={"old": old_values, "new": new_values},
    )

    await db.flush()

    return AuthorityAdminResponse(
        id=auth.id,
        name=auth.name,
        authority_type=auth.authority_type.value,
        parent_authority_id=auth.parent_authority_id,
        description=auth.description,
        website_url=auth.website_url,
        grievance_url=auth.grievance_url,
        contact_phone=auth.contact_phone,
        contact_email=auth.contact_email,
        is_active=auth.is_active,
        created_at=auth.created_at.isoformat(),
        updated_at=auth.updated_at.isoformat(),
    )


# --- Accountability Chain ---

chain_router = APIRouter(prefix="/admin/accountability-chain", tags=["admin-accountability"])


@chain_router.get("", response_model=list[ChainNodeResponse])
async def list_chain_nodes(
    authority_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    query = select(AccountabilityChainNode).order_by(
        AccountabilityChainNode.authority_id,
        AccountabilityChainNode.display_order,
    )
    if authority_id:
        query = query.where(AccountabilityChainNode.authority_id == authority_id)

    result = await db.execute(query)
    nodes = result.scalars().all()
    return [
        ChainNodeResponse(
            id=n.id,
            authority_id=n.authority_id,
            jurisdiction_polygon_id=n.jurisdiction_polygon_id,
            node_type=n.node_type.value,
            display_name=n.display_name,
            title=n.title,
            phone=n.phone,
            email=n.email,
            display_order=n.display_order,
            is_public=n.is_public,
        )
        for n in nodes
    ]


@chain_router.post("", response_model=ChainNodeResponse)
async def create_chain_node(
    body: ChainNodeCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    node = AccountabilityChainNode(
        id=uuid.uuid4(),
        authority_id=body.authority_id,
        jurisdiction_polygon_id=body.jurisdiction_polygon_id,
        node_type=AccountabilityNodeType(body.node_type),
        display_name=body.display_name,
        title=body.title,
        phone=body.phone,
        email=body.email,
        display_order=body.display_order,
        is_public=body.is_public,
    )
    db.add(node)
    await db.flush()

    await write_audit_log(
        db,
        actor_user_id=user.id,
        entity_type="accountability_chain",
        entity_id=node.id,
        action="create",
        metadata_json={"display_name": body.display_name, "node_type": body.node_type},
    )

    return ChainNodeResponse(
        id=node.id,
        authority_id=node.authority_id,
        jurisdiction_polygon_id=node.jurisdiction_polygon_id,
        node_type=node.node_type.value,
        display_name=node.display_name,
        title=node.title,
        phone=node.phone,
        email=node.email,
        display_order=node.display_order,
        is_public=node.is_public,
    )


@chain_router.delete("/{node_id}")
async def delete_chain_node(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin)),
):
    result = await db.execute(
        select(AccountabilityChainNode).where(AccountabilityChainNode.id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Chain node not found")

    await write_audit_log(
        db,
        actor_user_id=user.id,
        entity_type="accountability_chain",
        entity_id=node_id,
        action="delete",
        metadata_json={"display_name": node.display_name},
    )

    await db.delete(node)
    await db.flush()
    return {"deleted": True, "node_id": str(node_id)}
