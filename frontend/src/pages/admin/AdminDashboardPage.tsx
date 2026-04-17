import { useQuery } from '@tanstack/react-query';
import { getAnalyticsSummary } from '../../services/api';
import { SEVERITY_LABELS, STATUS_LABELS } from '../../types';

function useToken() {
    return localStorage.getItem('admin_token') || '';
}

export default function AdminDashboardPage() {
    const token = useToken();
    const { data, isLoading, error } = useQuery({
        queryKey: ['admin-analytics'],
        queryFn: () => getAnalyticsSummary(token),
    });

    if (isLoading) return <div className="p-8 text-gray-500">Loading dashboard...</div>;
    if (error) return <div className="p-8 text-red-600">Error loading analytics: {(error as Error).message}</div>;
    if (!data) return null;

    return (
        <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

            {/* Metric cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <MetricCard label="Total Reports" value={data.total_reports} color="blue" />
                <MetricCard label="Total Issues" value={data.total_issues} color="indigo" />
                <MetricCard label="Unresolved" value={data.unresolved_issues} color="orange" />
                <MetricCard label="Avg Age (days)" value={data.avg_issue_age_days} color="red" />
                <MetricCard label="Reports This Week" value={data.reports_this_week} color="green" />
                <MetricCard label="Resolved This Week" value={data.resolved_this_week} color="emerald" />
                <MetricCard label="Merge Rate" value={`${(data.duplicate_merge_rate * 100).toFixed(1)}%`} color="purple" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Top Wards */}
                <div className="bg-white rounded-lg shadow p-5">
                    <h3 className="font-semibold text-gray-900 mb-4">Top Hotspot Wards</h3>
                    {data.top_wards.length === 0 ? (
                        <p className="text-gray-400 text-sm">No ward data available yet</p>
                    ) : (
                        <div className="space-y-2">
                            {data.top_wards.map((w, i) => (
                                <div key={i} className="flex items-center justify-between text-sm">
                                    <span className="text-gray-700">{w.ward}</span>
                                    <span className="font-semibold text-orange-600">{w.unresolved_count} unresolved</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Severity Distribution */}
                <div className="bg-white rounded-lg shadow p-5">
                    <h3 className="font-semibold text-gray-900 mb-4">Severity Distribution</h3>
                    <div className="space-y-2">
                        {Object.entries(data.severity_distribution).map(([key, count]) => (
                            <div key={key} className="flex items-center justify-between text-sm">
                                <span className="text-gray-700">{SEVERITY_LABELS[key as keyof typeof SEVERITY_LABELS] || key}</span>
                                <div className="flex items-center gap-2">
                                    <div className="w-32 bg-gray-100 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full ${key === 'critical' ? 'bg-red-500' : key === 'high' ? 'bg-orange-500' : key === 'medium' ? 'bg-yellow-500' : 'bg-green-500'}`}
                                            style={{ width: `${Math.min(100, (count / Math.max(...Object.values(data.severity_distribution), 1)) * 100)}%` }}
                                        />
                                    </div>
                                    <span className="font-semibold w-8 text-right">{count}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Status Distribution */}
                <div className="bg-white rounded-lg shadow p-5 lg:col-span-2">
                    <h3 className="font-semibold text-gray-900 mb-4">Status Distribution</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {Object.entries(data.status_distribution).map(([key, count]) => (
                            <div key={key} className="bg-gray-50 rounded-lg p-3 text-center">
                                <p className="text-2xl font-bold text-gray-900">{count}</p>
                                <p className="text-xs text-gray-500">{STATUS_LABELS[key as keyof typeof STATUS_LABELS] || key}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

function MetricCard({ label, value, color }: { label: string; value: string | number; color: string }) {
    const colorMap: Record<string, string> = {
        blue: 'bg-blue-50 text-blue-700 border-blue-200',
        indigo: 'bg-indigo-50 text-indigo-700 border-indigo-200',
        orange: 'bg-orange-50 text-orange-700 border-orange-200',
        red: 'bg-red-50 text-red-700 border-red-200',
        green: 'bg-green-50 text-green-700 border-green-200',
        emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        purple: 'bg-purple-50 text-purple-700 border-purple-200',
    };
    return (
        <div className={`rounded-lg border p-4 ${colorMap[color] || colorMap.blue}`}>
            <p className="text-sm font-medium opacity-80">{label}</p>
            <p className="text-2xl font-bold mt-1">{value}</p>
        </div>
    );
}
