"""Public authority page API — accountability data for public viewing."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.models import Authority, Issue, JurisdictionPolygon, AccountabilityChainNode
from app.models.enums import IssueStatus

router = APIRouter(prefix="/authorities", tags=["authorities-public"])


@router.get("/{authority_id}")
async def get_authority_public(
    authority_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    authority = await db.get(Authority, authority_id)
    if not authority or not authority.is_active:
        raise HTTPException(status_code=404, detail="Authority not found")

    # Issue counts
    total_q = select(func.count()).select_from(Issue).where(
        Issue.resolved_authority_id == authority_id, Issue.public_visibility.is_(True),
    )
    total_result = await db.execute(total_q)
    total_issues = total_result.scalar_one()

    unresolved_q = select(func.count()).select_from(Issue).where(
        Issue.resolved_authority_id == authority_id,
        Issue.public_visibility.is_(True),
        Issue.status.notin_([IssueStatus.resolved, IssueStatus.rejected, IssueStatus.duplicate]),
    )
    unresolved_result = await db.execute(unresolved_q)
    unresolved_count = unresolved_result.scalar_one()

    resolved_q = select(func.count()).select_from(Issue).where(
        Issue.resolved_authority_id == authority_id,
        Issue.public_visibility.is_(True),
        Issue.status == IssueStatus.resolved,
    )
    resolved_result = await db.execute(resolved_q)
    resolved_count = resolved_result.scalar_one()

    # Severity breakdown
    sev_q = select(Issue.canonical_severity, func.count()).where(
        Issue.resolved_authority_id == authority_id, Issue.public_visibility.is_(True),
    ).group_by(Issue.canonical_severity)
    sev_result = await db.execute(sev_q)
    severity_breakdown = {row[0].value: row[1] for row in sev_result.all()}

    # Covered wards
    wards_q = select(JurisdictionPolygon.name).where(
        JurisdictionPolygon.authority_id == authority_id,
        JurisdictionPolygon.is_active.is_(True),
    )
    wards_result = await db.execute(wards_q)
    covered_wards = [row[0] for row in wards_result.all()]

    # Public accountability chain
    chain_q = select(AccountabilityChainNode).where(
        AccountabilityChainNode.authority_id == authority_id,
        AccountabilityChainNode.is_public.is_(True),
    ).order_by(AccountabilityChainNode.display_order)
    chain_result = await db.execute(chain_q)
    chain_nodes = chain_result.scalars().all()

    chain = [
        {
            "type": node.node_type.value,
            "display_name": node.display_name,
            "title": node.title,
            "phone": node.phone if node.is_public else None,
            "email": node.email if node.is_public else None,
        }
        for node in chain_nodes
    ]

    return {
        "id": str(authority.id),
        "name": authority.name,
        "authority_type": authority.authority_type.value,
        "description": authority.description,
        "website_url": authority.website_url,
        "grievance_url": authority.grievance_url,
        "contact_phone": authority.contact_phone,
        "contact_email": authority.contact_email,
        "total_issues": total_issues,
        "unresolved_count": unresolved_count,
        "resolved_count": resolved_count,
        "severity_breakdown": severity_breakdown,
        "covered_wards": covered_wards,
        "accountability_chain": chain,
    }


@router.get("")
async def list_authorities_public(
    db: AsyncSession = Depends(get_db),
):
    """List all active authorities for public reference."""
    q = select(Authority).where(Authority.is_active.is_(True)).order_by(Authority.name)
    result = await db.execute(q)
    authorities = result.scalars().all()

    items = []
    for a in authorities:
        issue_q = select(func.count()).select_from(Issue).where(
            Issue.resolved_authority_id == a.id, Issue.public_visibility.is_(True),
        )
        issue_result = await db.execute(issue_q)
        issue_count = issue_result.scalar_one()

        items.append({
            "id": str(a.id),
            "name": a.name,
            "authority_type": a.authority_type.value,
            "issue_count": issue_count,
        })
    return items
