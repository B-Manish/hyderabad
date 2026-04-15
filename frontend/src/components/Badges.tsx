import type { Severity, IssueStatus } from '../types';
import { SEVERITY_LABELS, SEVERITY_COLORS, STATUS_LABELS } from '../types';

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${SEVERITY_COLORS[severity]}`}>
      {SEVERITY_LABELS[severity]}
    </span>
  );
}

export function StatusBadge({ status }: { status: IssueStatus }) {
  const colorMap: Record<IssueStatus, string> = {
    reported: 'bg-blue-100 text-blue-700',
    under_review: 'bg-purple-100 text-purple-700',
    verified: 'bg-green-100 text-green-700',
    assigned: 'bg-indigo-100 text-indigo-700',
    in_progress: 'bg-yellow-100 text-yellow-700',
    resolved: 'bg-emerald-100 text-emerald-700',
    rejected: 'bg-gray-100 text-gray-700',
    duplicate: 'bg-gray-100 text-gray-500',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorMap[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  );
}
