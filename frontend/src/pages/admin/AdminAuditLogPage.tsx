import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getAuditLogs } from '../../services/api';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

function useToken() { return localStorage.getItem('admin_token') || ''; }

const ENTITY_TYPES = ['', 'report', 'issue', 'authority', 'accountability_chain', 'user', 'jurisdiction'];
const ACTIONS = ['', 'approve', 'reject', 'status_change', 'merge', 'metadata_edit', 'create', 'update', 'delete', 'role_change', 'deactivation'];

export default function AdminAuditLogPage() {
    const token = useToken();
    const [entityType, setEntityType] = useState('');
    const [action, setAction] = useState('');
    const [page, setPage] = useState(1);

    const { data, isLoading } = useQuery({
        queryKey: ['admin-audit-logs', entityType, action, page],
        queryFn: () => getAuditLogs(token, { entity_type: entityType || undefined, action: action || undefined, page }),
    });

    const handleExport = () => {
        const sp = new URLSearchParams();
        if (entityType) sp.set('entity_type', entityType);
        window.open(`${API_URL}/admin/audit-logs/export?${sp.toString()}`, '_blank');
    };

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>
                <button
                    onClick={handleExport}
                    className="px-3 py-1.5 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700"
                >
                    Export CSV
                </button>
            </div>

            {/* Filters */}
            <div className="flex gap-3 mb-4">
                <select value={entityType} onChange={e => { setEntityType(e.target.value); setPage(1); }} className="border rounded px-2 py-1.5 text-sm">
                    {ENTITY_TYPES.map(t => <option key={t} value={t}>{t || 'All entities'}</option>)}
                </select>
                <select value={action} onChange={e => { setAction(e.target.value); setPage(1); }} className="border rounded px-2 py-1.5 text-sm">
                    {ACTIONS.map(a => <option key={a} value={a}>{a || 'All actions'}</option>)}
                </select>
            </div>

            {isLoading && <p className="text-gray-500">Loading...</p>}

            {data && (
                <>
                    <div className="bg-white rounded-lg shadow overflow-hidden">
                        <table className="w-full text-sm">
                            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                                <tr>
                                    <th className="px-3 py-2 text-left">Timestamp</th>
                                    <th className="px-3 py-2 text-left">Actor</th>
                                    <th className="px-3 py-2 text-left">Entity</th>
                                    <th className="px-3 py-2 text-left">Action</th>
                                    <th className="px-3 py-2 text-left">Details</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {data.items.map((log) => (
                                    <tr key={log.id} className="hover:bg-gray-50">
                                        <td className="px-3 py-2 text-xs text-gray-500 whitespace-nowrap">
                                            {new Date(log.created_at).toLocaleString()}
                                        </td>
                                        <td className="px-3 py-2 text-gray-700">
                                            {log.actor_email || log.actor_name || 'system'}
                                        </td>
                                        <td className="px-3 py-2">
                                            <span className="px-2 py-0.5 bg-gray-100 rounded text-xs font-medium">{log.entity_type}</span>
                                            {log.entity_id && (
                                                <span className="text-xs text-gray-400 ml-1">{log.entity_id.slice(0, 8)}...</span>
                                            )}
                                        </td>
                                        <td className="px-3 py-2">
                                            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium">{log.action}</span>
                                        </td>
                                        <td className="px-3 py-2 text-xs text-gray-500 max-w-xs truncate">
                                            {log.metadata_json ? JSON.stringify(log.metadata_json) : '—'}
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
        </div>
    );
}
