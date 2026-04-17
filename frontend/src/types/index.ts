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

// --- Phase 4: Admin types ---

export type UserRole = 'citizen' | 'moderator' | 'admin';

export interface AdminReportItem {
    id: string;
    latitude: number;
    longitude: number;
    issue_type: IssueType;
    severity: Severity;
    description: string | null;
    landmark: string | null;
    road_name_input: string | null;
    moderation_status: ModerationStatus;
    source: string;
    submitted_at: string;
    user_name: string | null;
    user_email: string | null;
    issue_id: string | null;
    media: MediaItem[];
}

export interface PaginatedAdminReports {
    items: AdminReportItem[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface AdminIssueItem {
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
    resolved_at: string | null;
}

export interface PaginatedAdminIssues {
    items: AdminIssueItem[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface AnalyticsSummary {
    total_reports: number;
    total_issues: number;
    unresolved_issues: number;
    avg_issue_age_days: number;
    reports_this_week: number;
    resolved_this_week: number;
    duplicate_merge_rate: number;
    top_wards: { ward: string; unresolved_count: number }[];
    severity_distribution: Record<string, number>;
    status_distribution: Record<string, number>;
}

export interface AuditLogItem {
    id: string;
    actor_user_id: string | null;
    actor_name: string | null;
    actor_email: string | null;
    entity_type: string;
    entity_id: string | null;
    action: string;
    metadata_json: Record<string, unknown> | null;
    created_at: string;
}

export interface PaginatedAuditLogs {
    items: AuditLogItem[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface AdminUserItem {
    id: string;
    name: string | null;
    email: string | null;
    role: UserRole;
    auth_provider: string;
    is_active: boolean;
    created_at: string;
}

export interface PaginatedUsers {
    items: AdminUserItem[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface AuthorityAdmin {
    id: string;
    name: string;
    authority_type: string;
    parent_authority_id: string | null;
    description: string | null;
    website_url: string | null;
    grievance_url: string | null;
    contact_phone: string | null;
    contact_email: string | null;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface StatusHistoryItem {
    id: string;
    old_status: string | null;
    new_status: string;
    change_reason: string | null;
    created_at: string;
}

export const MODERATION_STATUS_LABELS: Record<ModerationStatus, string> = {
    pending_moderation: 'Pending',
    approved: 'Approved',
    rejected_abuse: 'Rejected (Abuse)',
    low_quality_evidence: 'Low Quality',
    duplicate_merged: 'Duplicate',
};

export const MODERATION_STATUS_COLORS: Record<ModerationStatus, string> = {
    pending_moderation: 'bg-yellow-100 text-yellow-700',
    approved: 'bg-green-100 text-green-700',
    rejected_abuse: 'bg-red-100 text-red-700',
    low_quality_evidence: 'bg-orange-100 text-orange-700',
    duplicate_merged: 'bg-gray-100 text-gray-700',
};

// --- Phase 5: Support types ---
export type SupportType = 'same_issue' | 'dangerous' | 'fixed_confirmed' | 'still_exists';

export interface SupportResponse {
    issue_id: string;
    support_count: number;
    support_type: string;
    created_at: string;
    needs_resolution_review: boolean;
}

export interface SupportSummary {
    total: number;
    by_type: Record<string, number>;
}

export const SUPPORT_TYPE_CONFIG: Record<SupportType, { label: string; icon: string; color: string }> = {
    same_issue: { label: "I've seen this too", icon: '👁️', color: 'bg-blue-50 text-blue-700 hover:bg-blue-100' },
    dangerous: { label: 'This is dangerous', icon: '⚠️', color: 'bg-red-50 text-red-700 hover:bg-red-100' },
    still_exists: { label: 'Still exists', icon: '🔄', color: 'bg-yellow-50 text-yellow-700 hover:bg-yellow-100' },
    fixed_confirmed: { label: 'Fixed', icon: '✅', color: 'bg-green-50 text-green-700 hover:bg-green-100' },
};

// --- Phase 5: Hotspot types ---
export interface HotspotItem {
    ward: string;
    ward_id: string | null;
    zone: string | null;
    issue_count: number;
    critical_count: number;
    high_count: number;
    avg_age_days: number;
    hotspot_score: number;
    map_url: string | null;
}

export interface HotspotsResponse {
    period: string;
    hotspots: HotspotItem[];
}

// --- Phase 5: Search types ---
export interface SearchResultItem {
    type: string;
    id: string;
    name: string;
    issue_count?: number;
    url?: string;
    severity?: string;
}

export interface SearchResponse {
    results: SearchResultItem[];
    total: number;
}

// --- Phase 5: Public stats ---
export interface PublicStats {
    total_issues: number;
    unresolved_issues: number;
    wards_covered: number;
    community_confirmations: number;
    issues_resolved: number;
}

// --- Phase 5: Area / Locality ---
export interface AreaDetail {
    id: string;
    name: string;
    code: string | null;
    layer_type: string;
    total_issues: number;
    unresolved_count: number;
    severity_breakdown: Record<string, number>;
    top_issues: IssueListItem[];
    authority_name: string | null;
    hotspot_rank: number | null;
}

export interface AreaListItem {
    id: string;
    name: string;
    code: string | null;
    layer_type: string;
    issue_count: number;
}

// --- Phase 5: Authority public ---
export interface AuthorityPublic {
    id: string;
    name: string;
    authority_type: string;
    description: string | null;
    website_url: string | null;
    grievance_url: string | null;
    contact_phone: string | null;
    contact_email: string | null;
    total_issues: number;
    unresolved_count: number;
    resolved_count: number;
    severity_breakdown: Record<string, number>;
    covered_wards: string[];
    accountability_chain: AccountabilityChainNode[];
}

// --- Phase 5: Subscriptions ---
export interface SubscriptionItem {
    id: string;
    entity_type: string;
    entity_id: string;
    created_at: string;
}
