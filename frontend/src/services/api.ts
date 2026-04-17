import type {
    PaginatedIssues,
    IssueDetail,
    IssueDetailWithAuthority,
    ReportCreateRequest,
    ReportCreateResponse,
    ReportResponse,
    SignedUploadResponse,
    MapViewportResponse,
    DuplicateCheckResponse,
    AuthorityLookupResponse,
    ReverseGeocodeResponse,
    IssueType,
    PaginatedAdminReports,
    PaginatedAdminIssues,
    AnalyticsSummary,
    PaginatedAuditLogs,
    PaginatedUsers,
    AuthorityAdmin,
    StatusHistoryItem,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_URL}${path}`, {
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
        ...options,
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || `API Error: ${res.status}`);
    }
    return res.json();
}

// Uploads
export async function signUpload(
    filename: string,
    contentType: string,
    fileSize: number,
): Promise<SignedUploadResponse> {
    return apiFetch('/uploads/sign', {
        method: 'POST',
        body: JSON.stringify({ filename, content_type: contentType, file_size: fileSize }),
    });
}

export async function uploadFileToS3(uploadUrl: string, file: File): Promise<void> {
    const res = await fetch(uploadUrl, {
        method: 'PUT',
        headers: { 'Content-Type': file.type },
        body: file,
    });
    if (!res.ok) {
        throw new Error('Upload to storage failed');
    }
}

// Reports
export async function createReport(data: ReportCreateRequest): Promise<ReportCreateResponse> {
    return apiFetch('/reports', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

export async function getReport(reportId: string): Promise<ReportResponse> {
    return apiFetch(`/reports/${reportId}`);
}

// Issues
export async function getIssues(params: {
    page?: number;
    page_size?: number;
    issue_type?: string;
    severity?: string;
    status?: string;
    sort_by?: string;
} = {}): Promise<PaginatedIssues> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
            searchParams.set(key, String(value));
        }
    });
    const query = searchParams.toString();
    return apiFetch(`/issues${query ? `?${query}` : ''}`);
}

export async function getIssue(issueId: string): Promise<IssueDetailWithAuthority> {
    return apiFetch(`/issues/${issueId}`);
}

// Map
export async function getMapIssues(params: {
    minLat: number;
    minLng: number;
    maxLat: number;
    maxLng: number;
    status?: string;
    severity?: string;
    issue_type?: string;
    verified_only?: boolean;
    date_from?: string;
    date_to?: string;
}): Promise<MapViewportResponse> {
    const searchParams = new URLSearchParams();
    searchParams.set('minLat', String(params.minLat));
    searchParams.set('minLng', String(params.minLng));
    searchParams.set('maxLat', String(params.maxLat));
    searchParams.set('maxLng', String(params.maxLng));
    if (params.status) searchParams.set('status', params.status);
    if (params.severity) searchParams.set('severity', params.severity);
    if (params.issue_type) searchParams.set('issue_type', params.issue_type);
    if (params.verified_only) searchParams.set('verified_only', 'true');
    if (params.date_from) searchParams.set('date_from', params.date_from);
    if (params.date_to) searchParams.set('date_to', params.date_to);
    return apiFetch(`/map/issues?${searchParams.toString()}`);
}

export async function checkDuplicates(
    lat: number,
    lng: number,
    issueType: IssueType,
    radius?: number,
): Promise<DuplicateCheckResponse> {
    const searchParams = new URLSearchParams();
    searchParams.set('lat', String(lat));
    searchParams.set('lng', String(lng));
    searchParams.set('issue_type', issueType);
    if (radius) searchParams.set('radius', String(radius));
    return apiFetch(`/map/duplicates?${searchParams.toString()}`);
}

// Authority & Jurisdiction
export async function lookupAuthority(lat: number, lng: number): Promise<AuthorityLookupResponse> {
    return apiFetch(`/lookup/authority?lat=${lat}&lng=${lng}`);
}

export async function reverseGeocode(lat: number, lng: number): Promise<ReverseGeocodeResponse> {
    return apiFetch(`/lookup/reverse-geocode?lat=${lat}&lng=${lng}`);
}

export async function getJurisdictionPolygons(layerType: string = 'ward'): Promise<GeoJSON.FeatureCollection> {
    return apiFetch(`/admin/jurisdictions/polygons?layer_type=${layerType}`);
}

// --- Admin: auth helper ---
function authHeaders(token: string): HeadersInit {
    return { Authorization: `Bearer ${token}` };
}

// --- Admin: Moderation ---
export async function getAdminReports(
    token: string,
    params: { moderation_status?: string; issue_type?: string; severity?: string; sort_by?: string; page?: number; page_size?: number } = {},
): Promise<PaginatedAdminReports> {
    const sp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '') sp.set(k, String(v)); });
    return apiFetch(`/admin/reports?${sp.toString()}`, { headers: authHeaders(token) });
}

export async function approveReport(token: string, reportId: string, notes?: string): Promise<{ status: string; report_id: string; issue_id: string }> {
    return apiFetch(`/admin/reports/${reportId}/approve`, {
        method: 'POST',
        headers: authHeaders(token),
        body: JSON.stringify({ notes: notes || null }),
    });
}

export async function rejectReport(token: string, reportId: string, reason: string, notes?: string): Promise<{ status: string }> {
    return apiFetch(`/admin/reports/${reportId}/reject`, {
        method: 'POST',
        headers: authHeaders(token),
        body: JSON.stringify({ reason, notes: notes || null }),
    });
}

// --- Admin: Issues ---
export async function getAdminIssues(
    token: string,
    params: { status?: string; issue_type?: string; severity?: string; sort_by?: string; page?: number; page_size?: number } = {},
): Promise<PaginatedAdminIssues> {
    const sp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '') sp.set(k, String(v)); });
    return apiFetch(`/admin/issues?${sp.toString()}`, { headers: authHeaders(token) });
}

export async function changeIssueStatus(token: string, issueId: string, newStatus: string, reason?: string): Promise<{ status: string }> {
    return apiFetch(`/admin/issues/${issueId}/status`, {
        method: 'POST',
        headers: authHeaders(token),
        body: JSON.stringify({ new_status: newStatus, reason }),
    });
}

export async function editIssueMeta(token: string, issueId: string, data: { title?: string; canonical_issue_type?: string; canonical_severity?: string; latitude?: number; longitude?: number }): Promise<unknown> {
    return apiFetch(`/admin/issues/${issueId}`, {
        method: 'PATCH',
        headers: authHeaders(token),
        body: JSON.stringify(data),
    });
}

export async function mergeIssues(token: string, issueId: string, mergeIds: string[], survivingId: string, notes?: string): Promise<unknown> {
    return apiFetch(`/admin/issues/${issueId}/merge`, {
        method: 'POST',
        headers: authHeaders(token),
        body: JSON.stringify({ merge_issue_ids: mergeIds, surviving_issue_id: survivingId, notes }),
    });
}

export async function getIssueHistory(token: string, issueId: string): Promise<StatusHistoryItem[]> {
    return apiFetch(`/admin/issues/${issueId}/history`, { headers: authHeaders(token) });
}

// --- Admin: Analytics ---
export async function getAnalyticsSummary(token: string): Promise<AnalyticsSummary> {
    return apiFetch('/admin/analytics/summary', { headers: authHeaders(token) });
}

// --- Admin: Audit Logs ---
export async function getAuditLogs(
    token: string,
    params: { entity_type?: string; action?: string; page?: number; page_size?: number } = {},
): Promise<PaginatedAuditLogs> {
    const sp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '') sp.set(k, String(v)); });
    return apiFetch(`/admin/audit-logs?${sp.toString()}`, { headers: authHeaders(token) });
}

// --- Admin: Users ---
export async function getAdminUsers(
    token: string,
    params: { search?: string; role?: string; page?: number; page_size?: number } = {},
): Promise<PaginatedUsers> {
    const sp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '') sp.set(k, String(v)); });
    return apiFetch(`/admin/users?${sp.toString()}`, { headers: authHeaders(token) });
}

export async function changeUserRole(token: string, userId: string, role: string): Promise<{ user_id: string; role: string }> {
    return apiFetch(`/admin/users/${userId}/role`, {
        method: 'PATCH',
        headers: authHeaders(token),
        body: JSON.stringify({ role }),
    });
}

export async function deactivateUser(token: string, userId: string, isActive: boolean): Promise<{ user_id: string; is_active: boolean }> {
    return apiFetch(`/admin/users/${userId}/deactivate`, {
        method: 'PATCH',
        headers: authHeaders(token),
        body: JSON.stringify({ is_active: isActive }),
    });
}

// --- Admin: Authorities ---
export async function getAdminAuthorities(token: string): Promise<AuthorityAdmin[]> {
    return apiFetch('/admin/authorities', { headers: authHeaders(token) });
}

export async function createAuthority(token: string, data: { name: string; authority_type: string; description?: string; contact_phone?: string; contact_email?: string }): Promise<AuthorityAdmin> {
    return apiFetch('/admin/authorities', {
        method: 'POST',
        headers: authHeaders(token),
        body: JSON.stringify(data),
    });
}

export async function updateAuthority(token: string, id: string, data: Partial<AuthorityAdmin>): Promise<AuthorityAdmin> {
    return apiFetch(`/admin/authorities/${id}`, {
        method: 'PATCH',
        headers: authHeaders(token),
        body: JSON.stringify(data),
    });
}
