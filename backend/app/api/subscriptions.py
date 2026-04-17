"""Subscriptions API — watch issue / watch area foundation."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.models import Subscription
from app.auth.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import SubscriptionCreateRequest, SubscriptionResponse

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("", response_model=SubscriptionResponse, status_code=201)
async def create_subscription(
    body: SubscriptionCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check for existing subscription
    existing_q = select(Subscription).where(
        Subscription.user_id == user.id,
        Subscription.entity_type == body.entity_type,
        Subscription.entity_id == uuid.UUID(body.entity_id),
    )
    existing = await db.execute(existing_q)
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already subscribed")

    sub = Subscription(
        id=uuid.uuid4(),
        user_id=user.id,
        entity_type=body.entity_type,
        entity_id=uuid.UUID(body.entity_id),
    )
    db.add(sub)
    await db.flush()

    return SubscriptionResponse(
        id=str(sub.id),
        entity_type=sub.entity_type,
        entity_id=str(sub.entity_id),
        created_at=sub.created_at.isoformat(),
    )


@router.get("", response_model=list[SubscriptionResponse])
async def list_subscriptions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.created_at.desc())
    result = await db.execute(q)
    subs = result.scalars().all()
    return [
        SubscriptionResponse(
            id=str(s.id),
            entity_type=s.entity_type,
            entity_id=str(s.entity_id),
            created_at=s.created_at.isoformat(),
        )
        for s in subs
    ]


@router.delete("/{subscription_id}", status_code=204)
async def delete_subscription(
    subscription_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await db.get(Subscription, subscription_id)
    if not sub or sub.user_id != user.id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    await db.delete(sub)
    await db.flush()
