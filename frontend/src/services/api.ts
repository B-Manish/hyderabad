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
