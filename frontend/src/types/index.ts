export type IssueType =
    | 'pothole'
    | 'road_surface_broken'
    | 'uneven_resurfacing'
    | 'waterlogging'
    | 'open_manhole'
    | 'dangerous_speed_breaker'
    | 'loose_gravel_debris'
    | 'construction_spill'
    | 'missing_lane_markings'
    | 'road_shoulder_collapse'
    | 'road_cave_in'
    | 'other_road_safety';

export type Severity = 'low' | 'medium' | 'high' | 'critical';

export type ModerationStatus =
    | 'pending_moderation'
    | 'approved'
    | 'rejected_abuse'
    | 'low_quality_evidence'
    | 'duplicate_merged';

export type IssueStatus =
    | 'reported'
    | 'under_review'
    | 'verified'
    | 'assigned'
    | 'in_progress'
    | 'resolved'
    | 'rejected'
    | 'duplicate';

export interface MediaItem {
    id: string;
    storage_key: string;
    media_type: 'image' | 'video';
    mime_type: string;
    width: number | null;
    height: number | null;
    size_bytes: number | null;
    url: string | null;
}

export interface ReportResponse {
    id: string;
    latitude: number;
    longitude: number;
    issue_type: IssueType;
    severity: Severity;
    description: string | null;
    landmark: string | null;
    road_name_input: string | null;
    direction_of_travel: string | null;
    dangerous_for_bikes: boolean;
    worse_in_rain: boolean;
    worse_at_night: boolean;
    moderation_status: ModerationStatus;
    source: string;
    submitted_at: string;
    created_at: string;
    media: MediaItem[];
}

export interface IssueListItem {
    id: string;
    title: string;
    canonical_issue_type: IssueType;
    canonical_severity: Severity;
    status: IssueStatus;
    latitude: number;
    longitude: number;
    first_reported_at: string;
    latest_reported_at: string;
    support_count: number;
    report_count: number;
    is_verified: boolean;
    thumbnail_url: string | null;
}

export interface IssueDetail {
    id: string;
    title: string;
    canonical_issue_type: IssueType;
    canonical_severity: Severity;
    status: IssueStatus;
    latitude: number;
    longitude: number;
    first_reported_at: string;
    latest_reported_at: string;
    resolved_at: string | null;
    support_count: number;
    report_count: number;
    verification_score: number;
    is_verified: boolean;
    public_visibility: boolean;
    created_at: string;
    media: MediaItem[];
}

export interface PaginatedIssues {
    items: IssueListItem[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface SignedUploadResponse {
    upload_url: string;
    storage_key: string;
    expires_in: number;
}

export interface ReportCreateRequest {
    latitude: number;
    longitude: number;
    issue_type: IssueType;
    severity: Severity;
    description?: string;
    landmark?: string;
    road_name_input?: string;
    direction_of_travel?: string;
    dangerous_for_bikes: boolean;
    worse_in_rain: boolean;
    worse_at_night: boolean;
    media_keys: string[];
    existing_issue_id?: string;
}

export interface ReportCreateResponse {
    id: string;
    moderation_status: ModerationStatus;
    created_at: string;
}

export interface MapIssue {
    id: string;
    title: string;
    canonical_issue_type: IssueType;
    canonical_severity: Severity;
    status: IssueStatus;
    latitude: number;
    longitude: number;
    report_count: number;
    support_count: number;
    is_verified: boolean;
    first_reported_at: string;
    latest_reported_at: string;
    distance_meters?: number;
}

export interface MapViewportResponse {
    issues: MapIssue[];
    total_count: number;
    viewport_bounds: {
        minLat: number;
        maxLat: number;
        minLng: number;
        maxLng: number;
    };
}

export interface DuplicateCheckResponse {
    duplicates: MapIssue[];
    count: number;
    search_radius_meters: number;
}

export const ISSUE_TYPE_LABELS: Record<IssueType, string> = {
    pothole: 'Pothole',
    road_surface_broken: 'Broken Road Surface',
    uneven_resurfacing: 'Uneven Resurfacing',
    waterlogging: 'Waterlogging',
    open_manhole: 'Open Manhole',
    dangerous_speed_breaker: 'Dangerous Speed Breaker',
    loose_gravel_debris: 'Loose Gravel / Debris',
    construction_spill: 'Construction Spill',
    missing_lane_markings: 'Missing Lane Markings',
    road_shoulder_collapse: 'Road Shoulder Collapse',
    road_cave_in: 'Road Cave-in',
    other_road_safety: 'Other Road Safety Issue',
};

export const SEVERITY_LABELS: Record<Severity, string> = {
    low: 'Low',
    medium: 'Medium',
    high: 'High',
    critical: 'Critical',
};

export const SEVERITY_COLORS: Record<Severity, string> = {
    low: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    high: 'bg-orange-100 text-orange-700',
    critical: 'bg-red-100 text-red-700',
};

export const STATUS_LABELS: Record<IssueStatus, string> = {
    reported: 'Reported',
    under_review: 'Under Review',
    verified: 'Verified',
    assigned: 'Assigned',
    in_progress: 'In Progress',
    resolved: 'Resolved',
    rejected: 'Rejected',
    duplicate: 'Duplicate',
};

// --- Phase 3: Authority & Jurisdiction Types ---

export type AuthorityType = 'municipal' | 'planning' | 'highway' | 'state' | 'ward_level' | 'contractor' | 'other';
export type ConfidenceLevel = 'high' | 'medium' | 'low' | 'very_low';

export interface AuthorityWithConfidence {
    id: string | null;
    name: string;
    authority_type: AuthorityType | null;
    confidence: number;
    website_url?: string | null;
    grievance_url?: string | null;
    contact_phone?: string | null;
    contact_email?: string | null;
}

export interface AreaInfo {
    id?: string;
    name: string;
    code?: string | null;
}

export interface NearestRoad {
    id?: string;
    name: string | null;
    road_class?: string | null;
    distance_meters?: number | null;
}

export interface AccountabilityChainNode {
    type: string;
    title: string | null;
    display_name: string;
    phone?: string | null;
    email?: string | null;
    is_public: boolean;
}

export interface AuthorityLookupResponse {
    primary_authority: AuthorityWithConfidence | null;
    alternate_authorities: AuthorityWithConfidence[];
    ward: AreaInfo | null;
    circle: AreaInfo | null;
    zone: AreaInfo | null;
    nearest_road: NearestRoad | null;
    accountability_chain: AccountabilityChainNode[];
    confidence_level: ConfidenceLevel;
    resolution_metadata: {
        steps_matched: string[];
        data_version: string;
    };
}

export interface ReverseGeocodeResponse {
    ward: AreaInfo | null;
    zone: AreaInfo | null;
    circle: AreaInfo | null;
    nearest_road: NearestRoad | null;
    locality_hint: string | null;
}

export interface IssueDetailWithAuthority extends IssueDetail {
    authority: AuthorityLookupResponse | null;
}

export const CONFIDENCE_LABELS: Record<ConfidenceLevel, string> = {
    high: 'High confidence',
    medium: 'Medium confidence',
    low: 'Low confidence — may need verification',
    very_low: 'Unable to determine with certainty',
};

export const CONFIDENCE_COLORS: Record<ConfidenceLevel, string> = {
    high: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    low: 'bg-orange-100 text-orange-700',
    very_low: 'bg-red-100 text-red-700',
};

export const NODE_TYPE_LABELS: Record<string, string> = {
    field_officer: 'Field Officer',
    engineer: 'Engineer',
    circle_office: 'Circle Office',
    zonal_office: 'Zonal Office',
    elected_rep: 'Elected Representative',
    escalation: 'Escalation',
    grievance_channel: 'Grievance Channel',
};
