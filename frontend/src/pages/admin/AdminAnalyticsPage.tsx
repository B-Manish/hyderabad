import { useQuery } from '@tanstack/react-query';
import { getAnalyticsSummary } from '../../services/api';
import { SEVERITY_LABELS, STATUS_LABELS, type IssueStatus } from '../../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

function useToken() { return localStorage.getItem('admin_token') || ''; }

export default function AdminAnalyticsPage() {
    const token = useToken();
    const { data, isLoading, error } = useQuery({
        queryKey: ['admin-analytics-detail'],
        queryFn: () => getAnalyticsSummary(token),
    });

    const handleExport = (type: 'analytics' | 'issues') => {
        const url = type === 'analytics'
            ? `${API_URL}/admin/analytics/export`
            : `${API_URL}/admin/issues/export`;
        // Open in new tab with token in header via a form/link approach
        window.open(`${url}?format=csv`, '_blank');
    };

    if (isLoading) return <div className="text-gray-500">Loading analytics...</div>;
    if (error) return <div className="text-red-600">Error: {(error as Error).message}</div>;
    if (!data) return null;

    const maxSev = Math.max(...Object.values(data.severity_distribution), 1);
    const maxStatus = Math.max(...Object.values(data.status_distribution), 1);

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
                <div className="flex gap-2">
                    <button
                        onClick={() => handleExport('analytics')}
                        className="px-3 py-1.5 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700"
                    >
                        Export Analytics CSV
                    </button>
                    <button
                        onClick={() => handleExport('issues')}
                        className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700"
                    >
                        Export Issues CSV
                    </button>
                </div>
            </div>

            {/* Summary metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <StatCard label="Total Reports" value={data.total_reports} />
                <StatCard label="Total Issues" value={data.total_issues} />
                <StatCard label="Unresolved" value={data.unresolved_issues} />
                <StatCard label="Avg Age (days)" value={data.avg_issue_age_days} />
                <StatCard label="Reports This Week" value={data.reports_this_week} />
                <StatCard label="Resolved This Week" value={data.resolved_this_week} />
                <StatCard label="Duplicate Merge Rate" value={`${(data.duplicate_merge_rate * 100).toFixed(1)}%`} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Severity chart */}
                <div className="bg-white rounded-lg shadow p-5">
                    <h3 className="font-semibold text-gray-900 mb-4">Issues by Severity</h3>
                    <div className="space-y-3">
                        {Object.entries(data.severity_distribution).map(([key, count]) => (
                            <div key={key}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-600">{SEVERITY_LABELS[key as keyof typeof SEVERITY_LABELS] || key}</span>
                                    <span className="font-semibold">{count}</span>
                                </div>
                                <div className="w-full bg-gray-100 rounded-full h-3">
                                    <div
                                        className={`h-3 rounded-full transition-all ${key === 'critical' ? 'bg-red-500' : key === 'high' ? 'bg-orange-500' : key === 'medium' ? 'bg-yellow-400' : 'bg-green-400'}`}
                                        style={{ width: `${(count / maxSev) * 100}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Status chart */}
                <div className="bg-white rounded-lg shadow p-5">
                    <h3 className="font-semibold text-gray-900 mb-4">Issues by Status</h3>
                    <div className="space-y-3">
                        {Object.entries(data.status_distribution).map(([key, count]) => (
                            <div key={key}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-600">{STATUS_LABELS[key as IssueStatus] || key}</span>
                                    <span className="font-semibold">{count}</span>
                                </div>
                                <div className="w-full bg-gray-100 rounded-full h-3">
                                    <div className="h-3 rounded-full bg-primary-500 transition-all" style={{ width: `${(count / maxStatus) * 100}%` }} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Top wards */}
                <div className="bg-white rounded-lg shadow p-5 lg:col-span-2">
                    <h3 className="font-semibold text-gray-900 mb-4">Geographic Breakdown — Top Wards</h3>
                    {data.top_wards.length === 0 ? (
                        <p className="text-gray-400 text-sm">No ward data available</p>
                    ) : (
                        <table className="w-full text-sm">
                            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                                <tr>
                                    <th className="px-3 py-2 text-left">Ward</th>
                                    <th className="px-3 py-2 text-right">Unresolved Issues</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {data.top_wards.map((w, i) => (
                                    <tr key={i}>
                                        <td className="px-3 py-2 text-gray-700">{w.ward}</td>
                                        <td className="px-3 py-2 text-right font-semibold text-orange-600">{w.unresolved_count}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">{label}</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
    );
}
