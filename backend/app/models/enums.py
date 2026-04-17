import enum


class UserRole(str, enum.Enum):
    citizen = "citizen"
    moderator = "moderator"
    admin = "admin"


class IssueType(str, enum.Enum):
    pothole = "pothole"
    road_surface_broken = "road_surface_broken"
    uneven_resurfacing = "uneven_resurfacing"
    waterlogging = "waterlogging"
    open_manhole = "open_manhole"
    dangerous_speed_breaker = "dangerous_speed_breaker"
    loose_gravel_debris = "loose_gravel_debris"
    construction_spill = "construction_spill"
    missing_lane_markings = "missing_lane_markings"
    road_shoulder_collapse = "road_shoulder_collapse"
    road_cave_in = "road_cave_in"
    other_road_safety = "other_road_safety"


class Severity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ModerationStatus(str, enum.Enum):
    pending_moderation = "pending_moderation"
    approved = "approved"
    rejected_abuse = "rejected_abuse"
    low_quality_evidence = "low_quality_evidence"
    duplicate_merged = "duplicate_merged"


class IssueStatus(str, enum.Enum):
    reported = "reported"
    under_review = "under_review"
    verified = "verified"
    assigned = "assigned"
    in_progress = "in_progress"
    resolved = "resolved"
    rejected = "rejected"
    duplicate = "duplicate"


class MediaType(str, enum.Enum):
    image = "image"
    video = "video"


class ReportSource(str, enum.Enum):
    web = "web"
    mobile_web = "mobile-web"
    admin = "admin"


class AuthorityType(str, enum.Enum):
    municipal = "municipal"
    planning = "planning"
    highway = "highway"
    state = "state"
    ward_level = "ward_level"
    contractor = "contractor"
    other = "other"


class LayerType(str, enum.Enum):
    ward = "ward"
    circle = "circle"
    zone = "zone"
    municipality = "municipality"
    constituency = "constituency"
    special_road_zone = "special_road_zone"
    other = "other"


class AccountabilityNodeType(str, enum.Enum):
    field_officer = "field_officer"
    engineer = "engineer"
    circle_office = "circle_office"
    zonal_office = "zonal_office"
    elected_rep = "elected_rep"
    escalation = "escalation"
    grievance_channel = "grievance_channel"


class ConfidenceLevel(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"
    very_low = "very_low"


class SupportType(str, enum.Enum):
    same_issue = "same_issue"
    dangerous = "dangerous"
    fixed_confirmed = "fixed_confirmed"
    still_exists = "still_exists"


class SubscriptionEntityType(str, enum.Enum):
    issue = "issue"
    ward = "ward"
    zone = "zone"
    authority = "authority"
