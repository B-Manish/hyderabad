import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getAreaDetail } from '../services/api';
import { SeverityBadge, StatusBadge } from '../components/Badges';
import { ISSUE_TYPE_LABELS, SEVERITY_LABELS, SEVERITY_COLORS } from '../types';
import type { Severity, IssueStatus, IssueType } from '../types';

export default function AreaDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: area, isLoading, error } = useQuery({
    queryKey: ['area', id],
    queryFn: () => getAreaDetail(id!),
    enabled: !!id,
  });

  if (isLoading) return <div className="max-w-4xl mx-auto px-4 py-20 text-center text-gray-500">Loading area...</div>;
  if (error || !area) return <div className="max-w-4xl mx-auto px-4 py-20 text-center text-red-500">Area not found.</div>;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <p className="text-xs text-gray-400 uppercase tracking-wide">{area.layer_type}</p>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800">{area.name}</h1>
        {area.code && <p className="text-sm text-gray-500">Code: {area.code}</p>}
        {area.authority_name && (
          <p className="text-sm text-gray-500 mt-1">
            Responsible authority: <span className="font-medium text-primary-700">{area.authority_name}</span>
          </p>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Issues" value={area.total_issues} />
        <StatCard label="Unresolved" value={area.unresolved_count} color="text-red-600" />
        <StatCard
          label="Resolved"
          value={area.total_issues - area.unresolved_count}
          color="text-green-600"
        />
        {area.hotspot_rank && <StatCard label="Hotspot Rank" value={`#${area.hotspot_rank}`} />}
      </div>

      {/* Severity Breakdown */}
      {Object.keys(area.severity_breakdown).length > 0 && (
        <div className="bg-white rounded-lg border p-6 mb-8">
          <h2 className="font-semibold text-gray-800 mb-4">Severity Breakdown</h2>
          <div className="space-y-2">
            {(['critical', 'high', 'medium', 'low'] as Severity[]).map((sev) => {
              const count = area.severity_breakdown[sev] || 0;
              const total = area.total_issues || 1;
              const pct = Math.round((count / total) * 100);
              return (
                <div key={sev} className="flex items-center gap-3">
                  <span className="text-xs w-16 text-right font-medium capitalize">{sev}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                    <div
                      className={`h-full ${sev === 'critical' ? 'bg-red-500' : sev === 'high' ? 'bg-orange-500' : sev === 'medium' ? 'bg-yellow-500' : 'bg-green-500'}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-10">{count}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Top Issues */}
      {area.top_issues.length > 0 && (
        <div className="mb-8">
          <h2 className="font-semibold text-gray-800 mb-4">Top Issues</h2>
          <div className="space-y-3">
            {area.top_issues.map((issue) => (
              <Link
                key={issue.id}
                to={`/issues/${issue.id}`}
                className="block bg-white rounded-lg border p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-800 text-sm">{issue.title}</h3>
                    <p className="text-xs text-gray-500 mt-1">
                      {ISSUE_TYPE_LABELS[issue.canonical_issue_type as IssueType]} &middot;{' '}
                      {issue.report_count} reports &middot; {issue.support_count} supports
                    </p>
                  </div>
                  <SeverityBadge severity={issue.canonical_severity as Severity} />
                  <StatusBadge status={issue.status as IssueStatus} />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* SEO structured data */}
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'Place',
        name: area.name,
        description: `Road issue report area in Hyderabad with ${area.total_issues} reported issues.`,
      })}} />
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: number | string; color?: string }) {
  return (
    <div className="bg-white rounded-lg border p-4 text-center">
      <p className={`text-2xl font-bold ${color || 'text-primary-700'}`}>{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  );
}
