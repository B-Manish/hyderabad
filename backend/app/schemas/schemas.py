from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from app.models.enums import (
    IssueType, Severity, ModerationStatus, IssueStatus, MediaType, ReportSource,
    AuthorityType, LayerType, AccountabilityNodeType,
)
import re


# --- Upload ---
class SignedUploadRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str
    file_size: int = Field(..., gt=0)

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v):
        allowed = ["image/jpeg", "image/png", "image/webp"]
        if v not in allowed:
            raise ValueError(f"Content type must be one of {allowed}")
        return v

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v):
        if not re.match(r'^[\w\-. ]+$', v):
            raise ValueError("Invalid filename characters")
        return v


class SignedUploadResponse(BaseModel):
    upload_url: str
    storage_key: str
    expires_in: int


# --- Report ---
class ReportCreateRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    issue_type: IssueType
    severity: Severity
    description: str | None = Field(None, max_length=2000)
    landmark: str | None = Field(None, max_length=255)
    road_name_input: str | None = Field(None, max_length=255)
    direction_of_travel: str | None = Field(None, max_length=100)
    dangerous_for_bikes: bool = False
    worse_in_rain: bool = False
    worse_at_night: bool = False
    media_keys: list[str] = Field(..., min_length=1, max_length=5)
    existing_issue_id: str | None = Field(None, description="Link to existing issue (duplicate)")

    @field_validator("description", "landmark", "road_name_input", "direction_of_travel")
    @classmethod
    def sanitize_text(cls, v):
        if v is None:
            return v
        # Strip leading/trailing whitespace
        v = v.strip()
        # Remove any HTML tags
        v = re.sub(r'<[^>]+>', '', v)
        return v

    @field_validator("media_keys")
    @classmethod
    def validate_media_keys(cls, v):
        for key in v:
            if not key.startswith("reports/"):
                raise ValueError("Invalid media key format")
            if ".." in key or "//" in key:
                raise ValueError("Invalid media key path")
        return v


class MediaResponse(BaseModel):
    id: UUID
    storage_key: str
    media_type: MediaType
    mime_type: str
    width: int | None
    height: int | None
    size_bytes: int | None
    url: str | None = None

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    id: UUID
    latitude: float
    longitude: float
    issue_type: IssueType
    severity: Severity
    description: str | None
    landmark: str | None
    road_name_input: str | None
    direction_of_travel: str | None
    dangerous_for_bikes: bool
    worse_in_rain: bool
    worse_at_night: bool
    moderation_status: ModerationStatus
    source: ReportSource
    submitted_at: datetime
    created_at: datetime
    media: list[MediaResponse] = []

    model_config = {"from_attributes": True}


class ReportCreateResponse(BaseModel):
    id: UUID
    moderation_status: ModerationStatus
    created_at: datetime


# --- Issue ---
class IssueListItem(BaseModel):
    id: UUID
    title: str
    canonical_issue_type: IssueType
    canonical_severity: Severity
    status: IssueStatus
    latitude: float
    longitude: float
    first_reported_at: datetime
    latest_reported_at: datetime
    support_count: int
    report_count: int
    is_verified: bool
    thumbnail_url: str | None = None

    model_config = {"from_attributes": True}


class IssueDetailResponse(BaseModel):
    id: UUID
    title: str
    canonical_issue_type: IssueType
    canonical_severity: Severity
    status: IssueStatus
    latitude: float
    longitude: float
    first_reported_at: datetime
    latest_reported_at: datetime
    resolved_at: datetime | None
    support_count: int
    report_count: int
    verification_score: float
    is_verified: bool
    public_visibility: bool
    created_at: datetime
    media: list[MediaResponse] = []

    model_config = {"from_attributes": True}


class PaginatedIssuesResponse(BaseModel):
    items: list[IssueListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# --- Authority & Jurisdiction ---
class AuthorityResponse(BaseModel):
    id: UUID
    name: str
    authority_type: AuthorityType
    description: str | None = None
    website_url: str | None = None
    grievance_url: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    is_active: bool = True

    model_config = {"from_attributes": True}


class AccountabilityChainNodeResponse(BaseModel):
    type: str
    title: str | None = None
    display_name: str
    phone: str | None = None
    email: str | None = None
    is_public: bool = True


class AreaInfoResponse(BaseModel):
    id: str | None = None
    name: str
    code: str | None = None


class NearestRoadResponse(BaseModel):
    id: str | None = None
    name: str | None = None
    road_class: str | None = None
    distance_meters: float | None = None


class AuthorityWithConfidence(BaseModel):
    id: str | None = None
    name: str
    authority_type: str | None = None
    confidence: float = 0.0
    website_url: str | None = None
    grievance_url: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None


class ResolutionMetadata(BaseModel):
    steps_matched: list[str] = []
    data_version: str = "2026-04"


class AuthorityLookupResponse(BaseModel):
    primary_authority: AuthorityWithConfidence | None = None
    alternate_authorities: list[AuthorityWithConfidence] = []
    ward: AreaInfoResponse | None = None
    circle: AreaInfoResponse | None = None
    zone: AreaInfoResponse | None = None
    nearest_road: NearestRoadResponse | None = None
    accountability_chain: list[AccountabilityChainNodeResponse] = []
    confidence_level: str = "very_low"
    resolution_metadata: ResolutionMetadata = ResolutionMetadata()


class ReverseGeocodeResponse(BaseModel):
    ward: AreaInfoResponse | None = None
    zone: AreaInfoResponse | None = None
    circle: AreaInfoResponse | None = None
    nearest_road: NearestRoadResponse | None = None
    locality_hint: str | None = None


class JurisdictionImportResponse(BaseModel):
    status: str
    features_found: int = 0
    imported: int = 0
    errors: int = 0
    error_details: list[str] = []


class ResponsibilityMappingCreate(BaseModel):
    polygon_id: UUID | None = None
    road_segment_id: UUID | None = None
    primary_authority_id: UUID
    secondary_authority_id: UUID | None = None
    ownership_confidence: float = Field(0.5, ge=0, le=1)
    notes: str | None = None


class ResponsibilityMappingResponse(BaseModel):
    id: UUID
    polygon_id: UUID | None = None
    road_segment_id: UUID | None = None
    primary_authority_id: UUID
    secondary_authority_id: UUID | None = None
    ownership_confidence: float
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IssueDetailWithAuthority(IssueDetailResponse):
    authority: AuthorityLookupResponse | None = None
