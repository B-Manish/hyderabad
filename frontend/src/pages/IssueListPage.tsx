import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getIssues } from '../services/api';
import { SeverityBadge, StatusBadge } from '../components/Badges';
import { ISSUE_TYPE_LABELS } from '../types';
import type { IssueType, Severity, IssueStatus } from '../types';

export default function IssueListPage() {
  const [page, setPage] = useState(1);
  const [issueType, setIssueType] = useState('');
  const [severity, setSeverity] = useState('');
  const [status, setStatus] = useState('');
  const [sortBy, setSortBy] = useState('latest_reported_at');

  const { data, isLoading, error } = useQuery({
    queryKey: ['issues', page, issueType, severity, status, sortBy],
    queryFn: () =>
      getIssues({
        page,
        page_size: 20,
        issue_type: issueType || undefined,
        severity: severity || undefined,
        status: status || undefined,
        sort_by: sortBy,
      }),
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Reported Issues</h1>
        <Link
          to="/report"
          className="mt-3 sm:mt-0 inline-flex items-center px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
        >
          + Report an Issue
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <select
            value={issueType}
            onChange={(e) => { setIssueType(e.target.value); setPage(1); }}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="">All Types</option>
            {Object.entries(ISSUE_TYPE_LABELS).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
          <select
            value={severity}
            onChange={(e) => { setSeverity(e.target.value); setPage(1); }}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="">All Severities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
          <select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="">All Statuses</option>
            <option value="reported">Reported</option>
            <option value="under_review">Under Review</option>
            <option value="verified">Verified</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
          </select>
          <select
            value={sortBy}
            onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="latest_reported_at">Most Recent</option>
            <option value="severity">Severity</option>
            <option value="support_count">Most Supported</option>
          </select>
        </div>
      </div>

      {/* Loading / Error */}
      {isLoading && (
        <div className="text-center py-20 text-gray-500">Loading issues...</div>
      )}
      {error && (
        <div className="text-center py-20 text-red-500">
          Failed to load issues. Is the backend running?
        </div>
      )}

      {/* Issue Cards */}
      {data && (
        <>
          {data.items.length === 0 ? (
            <div className="text-center py-20 text-gray-500">
              <p className="text-lg mb-2">No issues found.</p>
              <p className="text-sm">Be the first to report a road issue!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.items.map((issue) => (
                <Link
                  key={issue.id}
                  to={`/issues/${issue.id}`}
                  className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow p-4"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-xs text-gray-500 font-medium uppercase">
                      {ISSUE_TYPE_LABELS[issue.canonical_issue_type as IssueType]}
                    </span>
                    <SeverityBadge severity={issue.canonical_severity as Severity} />
                  </div>
                  <h3 className="font-semibold text-gray-800 text-sm leading-snug mb-2 line-clamp-2">
                    {issue.title}
                  </h3>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <StatusBadge status={issue.status as IssueStatus} />
                    <span>{issue.report_count} report{issue.report_count !== 1 ? 's' : ''}</span>
                  </div>
                  <div className="mt-2 text-xs text-gray-400">
                    {new Date(issue.latest_reported_at).toLocaleDateString()}
                  </div>
                </Link>
              ))}
            </div>
          )}

          {/* Pagination */}
          {data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 text-sm border rounded disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {page} of {data.total_pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page === data.total_pages}
                className="px-3 py-1 text-sm border rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
