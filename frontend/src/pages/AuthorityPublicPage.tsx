import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getAuthorityPublic } from '../services/api';
import { NODE_TYPE_LABELS, SEVERITY_LABELS } from '../types';
import type { Severity } from '../types';

export default function AuthorityPublicPage() {
  const { id } = useParams<{ id: string }>();

  const { data: authority, isLoading, error } = useQuery({
    queryKey: ['authority-public', id],
    queryFn: () => getAuthorityPublic(id!),
    enabled: !!id,
  });

  if (isLoading) return <div className="max-w-4xl mx-auto px-4 py-20 text-center text-gray-500">Loading authority...</div>;
  if (error || !authority) return <div className="max-w-4xl mx-auto px-4 py-20 text-center text-red-500">Authority not found.</div>;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <p className="text-xs text-gray-400 uppercase tracking-wide">{authority.authority_type.replace('_', ' ')}</p>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800">{authority.name}</h1>
        {authority.description && <p className="text-sm text-gray-500 mt-1">{authority.description}</p>}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-lg border p-4 text-center">
          <p className="text-2xl font-bold text-primary-700">{authority.total_issues}</p>
          <p className="text-xs text-gray-500">Total Issues</p>
        </div>
        <div className="bg-white rounded-lg border p-4 text-center">
          <p className="text-2xl font-bold text-red-600">{authority.unresolved_count}</p>
          <p className="text-xs text-gray-500">Unresolved</p>
        </div>
        <div className="bg-white rounded-lg border p-4 text-center">
          <p className="text-2xl font-bold text-green-600">{authority.resolved_count}</p>
          <p className="text-xs text-gray-500">Resolved</p>
        </div>
      </div>

      {/* Severity Breakdown */}
      {Object.keys(authority.severity_breakdown).length > 0 && (
        <div className="bg-white rounded-lg border p-6 mb-8">
          <h2 className="font-semibold text-gray-800 mb-4">Severity Breakdown</h2>
          <div className="space-y-2">
            {(['critical', 'high', 'medium', 'low'] as Severity[]).map((sev) => {
              const count = authority.severity_breakdown[sev] || 0;
              const total = authority.total_issues || 1;
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

      {/* Contact & Links */}
      <div className="bg-white rounded-lg border p-6 mb-8">
        <h2 className="font-semibold text-gray-800 mb-4">Contact Information</h2>
        <div className="space-y-2 text-sm">
          {authority.website_url && (
            <p>Website: <a href={authority.website_url} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">{authority.website_url}</a></p>
          )}
          {authority.grievance_url && (
            <p>Grievance Portal: <a href={authority.grievance_url} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">File a grievance →</a></p>
          )}
          {authority.contact_phone && <p>Phone: {authority.contact_phone}</p>}
          {authority.contact_email && <p>Email: {authority.contact_email}</p>}
        </div>
      </div>

      {/* Covered Wards */}
      {authority.covered_wards.length > 0 && (
        <div className="bg-white rounded-lg border p-6 mb-8">
          <h2 className="font-semibold text-gray-800 mb-4">Covered Wards / Zones</h2>
          <div className="flex flex-wrap gap-2">
            {authority.covered_wards.map((ward, idx) => (
              <span key={idx} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">{ward}</span>
            ))}
          </div>
        </div>
      )}

      {/* Accountability Chain */}
      {authority.accountability_chain.length > 0 && (
        <div className="bg-white rounded-lg border p-6 mb-8">
          <h2 className="font-semibold text-gray-800 mb-4">Accountability Chain</h2>
          <ol className="space-y-3">
            {authority.accountability_chain.map((node, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center text-xs font-bold text-gray-600">
                  {idx + 1}
                </span>
                <div>
                  <p className="text-sm font-medium text-gray-800">{node.display_name}</p>
                  <p className="text-xs text-gray-500">
                    {NODE_TYPE_LABELS[node.type] || node.type}
                    {node.phone && <span className="ml-2">{node.phone}</span>}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      <p className="text-xs text-gray-400 italic">
        This page shows public accountability data. The actual responsible jurisdiction may differ
        from the mapped data.
      </p>
    </div>
  );
}
