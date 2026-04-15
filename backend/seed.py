"""Seed script to populate the database with sample data for development."""
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from app.db.session import async_session
from app.models.models import User, Report, ReportMedia, Issue, IssueReport, IssueStatusHistory
from app.models.enums import (
    UserRole, IssueType, Severity, ModerationStatus, IssueStatus, MediaType, ReportSource,
)

SAMPLE_REPORTS = [
    {
        "lat": 17.4400, "lng": 78.3489,
        "issue_type": IssueType.pothole, "severity": Severity.high,
        "description": "Large pothole in front of HITEC City metro station, left lane",
        "landmark": "HITEC City Metro Station",
        "road_name": "Cyber Towers Road",
    },
    {
        "lat": 17.4260, "lng": 78.3351,
        "issue_type": IssueType.road_surface_broken, "severity": Severity.critical,
        "description": "Entire stretch of road broken after recent rains, dangerous for two-wheelers",
        "landmark": "Gachibowli Stadium",
        "road_name": "Gachibowli Main Road",
    },
    {
        "lat": 17.4486, "lng": 78.3908,
        "issue_type": IssueType.waterlogging, "severity": Severity.medium,
        "description": "Water stagnation after every rain, knee-deep in some spots",
        "landmark": "Ameerpet Junction",
        "road_name": "Ameerpet Main Road",
    },
    {
        "lat": 17.3850, "lng": 78.4867,
        "issue_type": IssueType.open_manhole, "severity": Severity.critical,
        "description": "Open manhole without any cover, extremely dangerous at night",
        "landmark": "LB Nagar Crossroads",
        "road_name": "LB Nagar Highway",
    },
    {
        "lat": 17.4375, "lng": 78.4483,
        "issue_type": IssueType.dangerous_speed_breaker, "severity": Severity.high,
        "description": "Unmarked speed breaker, invisible at night. Multiple accidents reported.",
        "landmark": "Secunderabad Railway Station",
        "road_name": "MG Road",
    },
]

ISSUE_TYPE_LABELS = {
    IssueType.pothole: "Pothole",
    IssueType.road_surface_broken: "Broken Road Surface",
    IssueType.waterlogging: "Waterlogging",
    IssueType.open_manhole: "Open Manhole",
    IssueType.dangerous_speed_breaker: "Dangerous Speed Breaker",
}


async def seed():
    async with async_session() as session:
        # Create sample users
        admin_user = User(
            id=uuid.uuid4(), name="Admin", email="admin@hyderabadroads.in",
            auth_provider="email", role=UserRole.admin,
        )
        citizen_user = User(
            id=uuid.uuid4(), name="Test Citizen", email="citizen@example.com",
            auth_provider="email", role=UserRole.citizen,
        )
        session.add_all([admin_user, citizen_user])
        await session.flush()

        for i, data in enumerate(SAMPLE_REPORTS):
            geom_expr = text(f"ST_SetSRID(ST_MakePoint({data['lng']}, {data['lat']}), 4326)::geography")

            report_id = uuid.uuid4()
            report = Report(
                id=report_id,
                user_id=citizen_user.id,
                latitude=data["lat"],
                longitude=data["lng"],
                geom=geom_expr,
                issue_type=data["issue_type"],
                severity=data["severity"],
                description=data["description"],
                landmark=data["landmark"],
                road_name_input=data["road_name"],
                dangerous_for_bikes=True,
                worse_in_rain=i % 2 == 0,
                worse_at_night=i % 3 == 0,
                moderation_status=ModerationStatus.approved,
                source=ReportSource.web,
                submitted_at=datetime.now(timezone.utc) - timedelta(days=i * 3),
            )
            session.add(report)
            await session.flush()

            # Create media placeholder
            media = ReportMedia(
                id=uuid.uuid4(),
                report_id=report_id,
                storage_key=f"reports/2026/04/seed_{i}.jpg",
                media_type=MediaType.image,
                mime_type="image/jpeg",
                sort_order=0,
            )
            session.add(media)

            # Create issue
            label = ISSUE_TYPE_LABELS.get(data["issue_type"], "Road Issue")
            issue = Issue(
                id=uuid.uuid4(),
                primary_report_id=report_id,
                title=f"{label} near {data['landmark']}",
                canonical_issue_type=data["issue_type"],
                canonical_severity=data["severity"],
                status=IssueStatus.reported,
                latitude=data["lat"],
                longitude=data["lng"],
                geom=geom_expr,
                first_reported_at=report.submitted_at,
                latest_reported_at=report.submitted_at,
                report_count=1,
                support_count=i * 2,
                public_visibility=True,
            )
            session.add(issue)
            await session.flush()

            report.issue_id = issue.id
            session.add(IssueReport(
                issue_id=issue.id, report_id=report_id, link_reason="initial_report",
            ))
            session.add(IssueStatusHistory(
                id=uuid.uuid4(), issue_id=issue.id,
                new_status=IssueStatus.reported.value, change_reason="Seed data",
            ))

        await session.commit()
        print(f"Seeded {len(SAMPLE_REPORTS)} reports with issues, 2 users (admin + citizen).")


if __name__ == "__main__":
    asyncio.run(seed())
