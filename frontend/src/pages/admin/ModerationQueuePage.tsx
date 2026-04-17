import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAdminReports, approveReport, rejectReport } from '../../services/api';
import {
    ISSUE_TYPE_LABELS, SEVERITY_LABELS, SEVERITY_COLORS,
    MODERATION_STATUS_LABELS, MODERATION_STATUS_COLORS,
    type ModerationStatus, type AdminReportItem,
} from '../../types';

function useToken() {
    return localStorage.getItem('admin_token') || '';
}

export default function ModerationQueuePage() {
    const token = useToken();
    const qc = useQueryClient();
    const [statusFilter, setStatusFilter] = useState('pending_moderation');
    const [page, setPage] = useState(1);
    const [actionReport, setActionReport] = useState<AdminReportItem | null>(null);
    const [rejectReason, setRejectReason] = useState('rejected_abuse');
    const [notes, setNotes] = useState('');

    const { data, isLoading } = useQuery({
        queryKey: ['admin-reports', statusFilter, page],
        queryFn: () => getAdminReports(token, { moderation_status: statusFilter, page, page_size: 15 }),
    });

    const approveMut = useMutation({
        mutationFn: (reportId: string) => approveReport(token, reportId, notes),
        onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-reports'] }); setActionReport(null); setNotes(''); },
    });

    const rejectMut = useMutation({
        mutationFn: (reportId: string) => rejectReport(token, reportId, rejectReason, notes),
        onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-reports'] }); setActionReport(null); setNotes(''); },
    });

    return (
        <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Moderation Queue</h1>

            {/* Filters */}
            <div className="flex items-center gap-3 mb-4">
                {(['pending_moderation', 'approved', 'rejected_abuse', 'low_quality_evidence'] as ModerationStatus[]).map((s) => (
                    <button
                        key={s}
                        onClick={() => { setStatusFilter(s); setPage(1); }}
                        className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${statusFilter === s ? 'bg-primary-700 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                    >
                        {MODERATION_STATUS_LABELS[s]}
                    </button>
                ))}
            </div>

            {isLoading && <p className="text-gray-500">Loading...</p>}

            {data && (
                <>
                    <p className="text-sm text-gray-500 mb-3">{data.total} report{data.total !== 1 && 's'} found</p>

                    <div className="space-y-3">
                        {data.items.map((r) => (
                            <div key={r.id} className="bg-white rounded-lg shadow p-4 flex gap-4">
                                {/* Thumbnail */}
                                <div className="w-20 h-20 flex-shrink-0 bg-gray-100 rounded overflow-hidden">
                                    {r.media.length > 0 && r.media[0].url ? (
                                        <img src={r.media[0].url} alt="" className="w-full h-full object-cover" />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center text-gray-300 text-2xl">📷</div>
                                    )}
                                </div>

                                {/* Info */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="font-medium text-gray-900 text-sm">{ISSUE_TYPE_LABELS[r.issue_type as keyof typeof ISSUE_TYPE_LABELS]}</span>
                                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${SEVERITY_COLORS[r.severity as keyof typeof SEVERITY_COLORS]}`}>
                                            {SEVERITY_LABELS[r.severity as keyof typeof SEVERITY_LABELS]}
                                        </span>
                                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${MODERATION_STATUS_COLORS[r.moderation_status as ModerationStatus]}`}>
                                            {MODERATION_STATUS_LABELS[r.moderation_status as ModerationStatus]}
                                        </span>
                                    </div>
                                    {r.description && <p className="text-xs text-gray-600 truncate">{r.description}</p>}
                                    <p className="text-xs text-gray-400 mt-1">
                                        {r.landmark || r.road_name_input || `${r.latitude.toFixed(4)}, ${r.longitude.toFixed(4)}`}
                                        {' · '}{new Date(r.submitted_at).toLocaleDateString()}
                                        {r.user_name && ` · ${r.user_name}`}
                                        {!r.user_name && ' · anonymous'}
                                    </p>
                                </div>

                                {/* Actions */}
                                {r.moderation_status === 'pending_moderation' && (
                                    <div className="flex flex-col gap-1 flex-shrink-0">
                                        <button
                                            onClick={() => approveMut.mutate(r.id)}
                                            disabled={approveMut.isPending}
                                            className="px-3 py-1 bg-green-600 text-white rounded text-xs font-medium hover:bg-green-700"
                                        >
                                            Approve
                                        </button>
                                        <button
                                            onClick={() => setActionReport(r)}
                                            className="px-3 py-1 bg-red-600 text-white rounded text-xs font-medium hover:bg-red-700"
                                        >
                                            Reject
                                        </button>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>

                    {/* Pagination */}
                    {data.total_pages > 1 && (
                        <div className="flex justify-center gap-2 mt-4">
                            <button
                                disabled={page <= 1}
                                onClick={() => setPage(p => p - 1)}
                                className="px-3 py-1 rounded bg-gray-100 text-sm disabled:opacity-50"
                            >
                                Prev
                            </button>
                            <span className="px-3 py-1 text-sm text-gray-600">Page {page} of {data.total_pages}</span>
                            <button
                                disabled={page >= data.total_pages}
                                onClick={() => setPage(p => p + 1)}
                                className="px-3 py-1 rounded bg-gray-100 text-sm disabled:opacity-50"
                            >
                                Next
                            </button>
                        </div>
                    )}
                </>
            )}

            {/* Reject Dialog */}
            {actionReport && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h3 className="font-bold text-gray-900 mb-3">Reject Report</h3>
                        <div className="space-y-3">
                            <div>
                                <label className="text-sm font-medium text-gray-700">Reason</label>
                                <select
                                    value={rejectReason}
                                    onChange={(e) => setRejectReason(e.target.value)}
                                    className="w-full border rounded px-2 py-1.5 text-sm mt-1"
                                >
                                    <option value="rejected_abuse">Abuse / Offensive</option>
                                    <option value="low_quality_evidence">Low Quality Evidence</option>
                                    <option value="duplicate_merged">Duplicate</option>
                                </select>
                            </div>
                            <div>
                                <label className="text-sm font-medium text-gray-700">Notes</label>
                                <textarea
                                    value={notes}
                                    onChange={(e) => setNotes(e.target.value)}
                                    rows={3}
                                    className="w-full border rounded px-2 py-1.5 text-sm mt-1"
                                    placeholder="Optional notes..."
                                />
                            </div>
                            <div className="flex justify-end gap-2">
                                <button onClick={() => { setActionReport(null); setNotes(''); }} className="px-3 py-1.5 bg-gray-100 rounded text-sm">Cancel</button>
                                <button
                                    onClick={() => rejectMut.mutate(actionReport.id)}
                                    disabled={rejectMut.isPending}
                                    className="px-3 py-1.5 bg-red-600 text-white rounded text-sm font-medium"
                                >
                                    {rejectMut.isPending ? 'Rejecting...' : 'Reject'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
