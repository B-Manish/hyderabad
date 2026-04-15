import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getIssue } from '../services/api';
import { SeverityBadge, StatusBadge } from '../components/Badges';
import { ISSUE_TYPE_LABELS } from '../types';
import type { Severity, IssueStatus, IssueType } from '../types';

export default function IssueDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: issue, isLoading, error } = useQuery({
    queryKey: ['issue', id],
    queryFn: () => getIssue(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center text-gray-500">
        Loading issue details...
      </div>
    );
  }

  if (error || !issue) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center text-red-500">
        Failed to load issue. It may not exist or the backend is unavailable.
      </div>
    );
  }

  const daysSinceReported = Math.floor(
    (Date.now() - new Date(issue.first_reported_at).getTime()) / (1000 * 60 * 60 * 24)
  );

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <SeverityBadge severity={issue.canonical_severity as Severity} />
          <StatusBadge status={issue.status as IssueStatus} />
          {issue.is_verified && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
              ✓ Verified
            </span>
          )}
        </div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800">{issue.title}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {ISSUE_TYPE_LABELS[issue.canonical_issue_type as IssueType]} &middot;{' '}
          First reported {new Date(issue.first_reported_at).toLocaleDateString()}
        </p>
      </div>

      {/* Image Gallery */}
      {issue.media.length > 0 && (
        <div className="mb-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {issue.media.map((m) => (
              <div key={m.id} className="rounded-lg overflow-hidden bg-gray-100 aspect-video">
                {m.url ? (
                  <img
                    src={m.url}
                    alt="Issue photo"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400">
                    No image available
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Metadata */}
        <div className="bg-white rounded-lg border p-6">
          <h2 className="font-semibold text-gray-800 mb-4">Issue Details</h2>
          <dl className="space-y-3 text-sm">
            <InfoRow label="Issue Type" value={ISSUE_TYPE_LABELS[issue.canonical_issue_type as IssueType]} />
            <InfoRow label="Severity" value={issue.canonical_severity.toUpperCase()} />
            <InfoRow label="Status" value={issue.status.replace('_', ' ')} />
            <InfoRow label="Reports" value={String(issue.report_count)} />
            <InfoRow label="Supporters" value={String(issue.support_count)} />
            <InfoRow label="Days Open" value={issue.resolved_at ? 'Resolved' : `${daysSinceReported} days`} />
          </dl>
        </div>

        {/* Location */}
        <div className="bg-white rounded-lg border p-6">
          <h2 className="font-semibold text-gray-800 mb-4">Location</h2>
          <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center mb-3">
            <div className="text-center text-gray-400">
              <p className="text-sm">📍 {issue.latitude.toFixed(5)}, {issue.longitude.toFixed(5)}</p>
              <p className="text-xs mt-1">Interactive map coming in Phase 2</p>
            </div>
          </div>
          <p className="text-xs text-gray-500">
            Coordinates: {issue.latitude.toFixed(5)}, {issue.longitude.toFixed(5)}
          </p>
        </div>
      </div>

      {/* Shareable URL */}
      <div className="bg-gray-50 rounded-lg border p-4 text-center">
        <p className="text-sm text-gray-500 mb-1">Share this issue</p>
        <p className="text-xs text-gray-400 font-mono break-all">
          {window.location.href}
        </p>
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <dt className="text-gray-500">{label}</dt>
      <dd className="font-medium text-gray-800">{value}</dd>
    </div>
  );
}
