import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, Enum, ForeignKey,
    Integer, Numeric, Text, BigInteger, Index
)
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geography
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.enums import (
    UserRole, IssueType, Severity, ModerationStatus,
    IssueStatus, MediaType, ReportSource,
)


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    email = Column(String(255), nullable=True, unique=True)
    phone = Column(String(50), nullable=True)
    auth_provider = Column(String(50), default="anonymous")
    is_anonymous_allowed = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.citizen, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    reports = relationship("Report", back_populates="user")


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=True)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    geom = Column(Geography("POINT", srid=4326), nullable=False)
    issue_type = Column(Enum(IssueType), nullable=False)
    severity = Column(Enum(Severity), nullable=False)
    description = Column(Text, nullable=True)
    landmark = Column(String(255), nullable=True)
    road_name_input = Column(String(255), nullable=True)
    direction_of_travel = Column(String(100), nullable=True)
    dangerous_for_bikes = Column(Boolean, default=False)
    worse_in_rain = Column(Boolean, default=False)
    worse_at_night = Column(Boolean, default=False)
    moderation_status = Column(
        Enum(ModerationStatus), default=ModerationStatus.pending_moderation, nullable=False
    )
    source = Column(Enum(ReportSource), default=ReportSource.web, nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="reports")
    issue = relationship("Issue", back_populates="reports", foreign_keys=[issue_id])
    media = relationship("ReportMedia", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_reports_geom", geom, postgresql_using="gist"),
    )


class ReportMedia(Base):
    __tablename__ = "report_media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False)
    storage_key = Column(String(512), nullable=False)
    media_type = Column(Enum(MediaType), default=MediaType.image, nullable=False)
    mime_type = Column(String(100), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    report = relationship("Report", back_populates="media")


class Issue(Base):
    __tablename__ = "issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    primary_report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=True)
    title = Column(String(500), nullable=False)
    canonical_issue_type = Column(Enum(IssueType), nullable=False)
    canonical_severity = Column(Enum(Severity), nullable=False)
    status = Column(Enum(IssueStatus), default=IssueStatus.reported, nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    geom = Column(Geography("POINT", srid=4326), nullable=False)
    road_segment_id = Column(UUID(as_uuid=True), nullable=True)
    first_reported_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    latest_reported_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    support_count = Column(Integer, default=0)
    report_count = Column(Integer, default=1)
    verification_score = Column(Numeric(5, 4), default=0)
    is_verified = Column(Boolean, default=False)
    public_visibility = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    reports = relationship("Report", back_populates="issue", foreign_keys=[Report.issue_id])
    primary_report = relationship("Report", foreign_keys=[primary_report_id], uselist=False)
    issue_reports = relationship("IssueReport", back_populates="issue")
    status_history = relationship("IssueStatusHistory", back_populates="issue")

    __table_args__ = (
        Index("idx_issues_geom", geom, postgresql_using="gist"),
    )


class IssueReport(Base):
    __tablename__ = "issue_reports"

    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), primary_key=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), primary_key=True)
    linked_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    link_reason = Column(String(255), nullable=True)

    issue = relationship("Issue", back_populates="issue_reports")
    report = relationship("Report")


class IssueStatusHistory(Base):
    __tablename__ = "issue_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    change_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    issue = relationship("Issue", back_populates="status_history")
