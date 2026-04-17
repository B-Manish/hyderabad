import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAdminIssues, changeIssueStatus, editIssueMeta, mergeIssues } from '../../services/api';
import {
    ISSUE_TYPE_LABELS, SEVERITY_LABELS, SEVERITY_COLORS, STATUS_LABELS,
    type IssueStatus, type AdminIssueItem,
} from '../../types';

function useToken() { return localStorage.getItem('admin_token') || ''; }

const STATUS_TRANSITIONS: Record<string, string[]> = {
    reported: ['under_review', 'verified', 'rejected', 'duplicate'],
    under_review: ['verified', 'rejected', 'duplicate'],
    verified: ['assigned', 'in_progress', 'resolved', 'rejected'],
    assigned: ['in_progress', 'resolved', 'rejected'],
    in_progress: ['resolved', 'verified'],
    resolved: ['verified'],
    rejected: ['reported'],
    duplicate: ['reported'],
};

export default function AdminIssueManagementPage() {
    const token = useToken();
    const qc = useQueryClient();
    const [statusFilter, setStatusFilter] = useState('');
    const [page, setPage] = useState(1);
    const [selectedIssue, setSelectedIssue] = useState<AdminIssueItem | null>(null);
    const [newStatus, setNewStatus] = useState('');
    const [reason, setReason] = useState('');
    const [editIssue, setEditIssue] = useState<AdminIssueItem | null>(null);
    const [editTitle, setEditTitle] = useState('');
    const [mergeMode, setMergeMode] = useState(false);
    const [mergeIds, setMergeIds] = useState<string[]>([]);
    const [survivingId, setSurvivingId] = useState('');
    const [mergeNotes, setMergeNotes] = useState('');

    const { data, isLoading } = useQuery({
        queryKey: ['admin-issues', statusFilter, page],
        queryFn: () => getAdminIssues(token, { status: statusFilter || undefined, page, page_size: 20 }),
    });

    const statusMut = useMutation({
        mutationFn: () => changeIssueStatus(token, selectedIssue!.id, newStatus, reason),
        onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-issues'] }); setSelectedIssue(null); setNewStatus(''); setReason(''); },
    });

    const editMut = useMutation({
        mutationFn: () => editIssueMeta(token, editIssue!.id, { title: editTitle }),
        onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-issues'] }); setEditIssue(null); },
    });

    const mergeMut = useMutation({
        mutationFn: () => mergeIssues(token, survivingId, mergeIds, survivingId, mergeNotes),
        onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-issues'] }); setMergeMode(false); setMergeIds([]); setSurvivingId(''); setMergeNotes(''); },
    });

    const statuses = ['', 'reported', 'under_review', 'verified', 'assigned', 'in_progress', 'resolved', 'rejected', 'duplicate'];

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <h1 className="text-2xl font-bold text-gray-900">Issue Management</h1>
                <button
                    onClick={() => setMergeMode(!mergeMode)}
                    className={`px-3 py-1.5 rounded text-sm font-medium ${mergeMode ? 'bg-purple-700 text-white' : 'bg-gray-100 text-gray-700'}`}
                >
                    {mergeMode ? 'Cancel Merge' : 'Merge Issues'}
                </button>
            </div>

            {/* Status filter tabs */}
            <div className="flex flex-wrap gap-2 mb-4">
                {statuses.map((s) => (
                    <button
                        key={s}
                        onClick={() => { setStatusFilter(s); setPage(1); }}
                        className={`px-3 py-1 rounded text-xs font-medium ${statusFilter === s ? 'bg-primary-700 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                    >
                        {s ? STATUS_LABELS[s as IssueStatus] : 'All'}
                    </button>
                ))}
            </div>

            {isLoading && <p className="text-gray-500">Loading...</p>}

            {mergeMode && mergeIds.length >= 2 && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 mb-4">
                    <p className="text-sm font-medium text-purple-700">
                        {mergeIds.length} issues selected for merge. Pick surviving issue below.
                    </p>
                    <div className="flex gap-2 mt-2">
                        <select
                            value={survivingId}
                            onChange={(e) => setSurvivingId(e.target.value)}
                            className="border rounded px-2 py-1 text-sm flex-1"
                        >
                            <option value="">Select surviving issue...</option>
                            {mergeIds.map(id => (
                                <option key={id} value={id}>{id.slice(0, 8)}...</option>
                            ))}
                        </select>
                        <input
                            value={mergeNotes}
                            onChange={(e) => setMergeNotes(e.target.value)}
                            placeholder="Notes..."
                            className="border rounded px-2 py-1 text-sm flex-1"
                        />
                        <button
                            disabled={!survivingId || mergeMut.isPending}
                            onClick={() => mergeMut.mutate()}
                            className="px-3 py-1 bg-purple-700 text-white rounded text-sm font-medium disabled:opacity-50"
                        >
                            {mergeMut.isPending ? 'Merging...' : 'Merge'}
                        </button>
                    </div>
                </div>
            )}

            {data && (
                <>
                    <div className="bg-white rounded-lg shadow overflow-hidden">
                        <table className="w-full text-sm">
                            <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                                <tr>
                                    {mergeMode && <th className="px-3 py-2 text-left">Select</th>}
                                    <th className="px-3 py-2 text-left">Title</th>
                                    <th className="px-3 py-2 text-left">Type</th>
                                    <th className="px-3 py-2 text-left">Severity</th>
                                    <th className="px-3 py-2 text-left">Status</th>
                                    <th className="px-3 py-2 text-right">Reports</th>
                                    <th className="px-3 py-2 text-left">Last Activity</th>
                                    <th className="px-3 py-2 text-left">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {data.items.map((i) => (
                                    <tr key={i.id} className="hover:bg-gray-50">
                                        {mergeMode && (
                                            <td className="px-3 py-2">
                                                <input
                                                    type="checkbox"
                                                    checked={mergeIds.includes(i.id)}
                                                    onChange={(e) => {
                                                        setMergeIds(prev => e.target.checked
                                                            ? [...prev, i.id]
                                                            : prev.filter(x => x !== i.id)
                                                        );
                                                    }}
                                                />
                                            </td>
                                        )}
                                        <td className="px-3 py-2 font-medium text-gray-900 max-w-xs truncate">{i.title}</td>
                                        <td className="px-3 py-2 text-gray-600">{ISSUE_TYPE_LABELS[i.canonical_issue_type as keyof typeof ISSUE_TYPE_LABELS]}</td>
                                        <td className="px-3 py-2">
                                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${SEVERITY_COLORS[i.canonical_severity as keyof typeof SEVERITY_COLORS]}`}>
                                                {SEVERITY_LABELS[i.canonical_severity as keyof typeof SEVERITY_LABELS]}
                                            </span>
                                        </td>
                                        <td className="px-3 py-2">
                                            <span className="text-xs font-medium">{STATUS_LABELS[i.status as IssueStatus]}</span>
                                        </td>
                                        <td className="px-3 py-2 text-right">{i.report_count}</td>
                                        <td className="px-3 py-2 text-gray-500 text-xs">{new Date(i.latest_reported_at).toLocaleDateString()}</td>
                                        <td className="px-3 py-2">
                                            <div className="flex gap-1">
                                                <button
                                                    onClick={() => { setSelectedIssue(i); setNewStatus(''); }}
                                                    className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs"
                                                >
                                                    Status
                                                </button>
                                                <button
                                                    onClick={() => { setEditIssue(i); setEditTitle(i.title); }}
                                                    className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs"
                                                >
                                                    Edit
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {data.total_pages > 1 && (
                        <div className="flex justify-center gap-2 mt-4">
                            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 rounded bg-gray-100 text-sm disabled:opacity-50">Prev</button>
                            <span className="px-3 py-1 text-sm text-gray-600">Page {page} of {data.total_pages}</span>
                            <button disabled={page >= data.total_pages} onClick={() => setPage(p => p + 1)} className="px-3 py-1 rounded bg-gray-100 text-sm disabled:opacity-50">Next</button>
                        </div>
                    )}
                </>
            )}

            {/* Status Change Dialog */}
            {selectedIssue && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h3 className="font-bold text-gray-900 mb-3">Change Status: {selectedIssue.title}</h3>
                        <p className="text-sm text-gray-500 mb-3">Current: {STATUS_LABELS[selectedIssue.status as IssueStatus]}</p>
                        <div className="space-y-3">
                            <select
                                value={newStatus}
                                onChange={(e) => setNewStatus(e.target.value)}
                                className="w-full border rounded px-2 py-1.5 text-sm"
                            >
                                <option value="">Select new status...</option>
                                {(STATUS_TRANSITIONS[selectedIssue.status] || []).map((s: string) => (
                                    <option key={s} value={s}>{STATUS_LABELS[s as IssueStatus]}</option>
                                ))}
                            </select>
                            <textarea
                                value={reason}
                                onChange={(e) => setReason(e.target.value)}
                                rows={2}
                                className="w-full border rounded px-2 py-1.5 text-sm"
                                placeholder="Reason (optional)..."
                            />
                            <div className="flex justify-end gap-2">
                                <button onClick={() => setSelectedIssue(null)} className="px-3 py-1.5 bg-gray-100 rounded text-sm">Cancel</button>
                                <button
                                    disabled={!newStatus || statusMut.isPending}
                                    onClick={() => statusMut.mutate()}
                                    className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm font-medium disabled:opacity-50"
                                >
                                    Update
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Edit Dialog */}
            {editIssue && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h3 className="font-bold text-gray-900 mb-3">Edit Issue Metadata</h3>
                        <div className="space-y-3">
                            <div>
                                <label className="text-sm font-medium text-gray-700">Title</label>
                                <input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} className="w-full border rounded px-2 py-1.5 text-sm mt-1" />
                            </div>
                            <div className="flex justify-end gap-2">
                                <button onClick={() => setEditIssue(null)} className="px-3 py-1.5 bg-gray-100 rounded text-sm">Cancel</button>
                                <button
                                    disabled={editMut.isPending}
                                    onClick={() => editMut.mutate()}
                                    className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm font-medium disabled:opacity-50"
                                >
                                    Save
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
