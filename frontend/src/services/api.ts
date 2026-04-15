import type {
    PaginatedIssues,
    IssueDetail,
    ReportCreateRequest,
    ReportCreateResponse,
    ReportResponse,
    SignedUploadResponse,
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

export async function getIssue(issueId: string): Promise<IssueDetail> {
    return apiFetch(`/issues/${issueId}`);
}
