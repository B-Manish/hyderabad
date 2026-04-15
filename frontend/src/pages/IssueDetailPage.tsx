import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getIssue } from '../services/api';
import { SeverityBadge, StatusBadge } from '../components/Badges';
import { ISSUE_TYPE_LABELS, CONFIDENCE_LABELS, CONFIDENCE_COLORS, NODE_TYPE_LABELS } from '../types';
import type { Severity, IssueStatus, IssueType, ConfidenceLevel, AuthorityLookupResponse } from '../types';

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
          <div className="aspect-video rounded-lg overflow-hidden mb-3">
            <MapContainer
              center={[issue.latitude, issue.longitude]}
              zoom={16}
              className="h-full w-full"
              style={{ height: '100%', minHeight: '200px' }}
              scrollWheelZoom={false}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <Marker
                position={[issue.latitude, issue.longitude]}
                icon={L.divIcon({
                  className: 'custom-marker',
                  html: `<div style="width:24px;height:24px;border-radius:50%;background:#ef4444;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);"></div>`,
                  iconSize: [24, 24],
                  iconAnchor: [12, 12],
                })}
              />
            </MapContainer>
          </div>
          <p className="text-xs text-gray-500">
            Coordinates: {issue.latitude.toFixed(5)}, {issue.longitude.toFixed(5)}
          </p>
          <Link
            to={`/map?lat=${issue.latitude}&lng=${issue.longitude}`}
            className="inline-block mt-2 text-xs text-primary-600 hover:underline"
          >
            View on full map →
          </Link>
        </div>
      </div>

      {/* Accountability Section - Phase 3 */}
      {issue.authority && issue.authority.primary_authority && (
        <AccountabilitySection authority={issue.authority} />
      )}

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

function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  const colorClass = CONFIDENCE_COLORS[level] || 'bg-gray-100 text-gray-700';
  const label = CONFIDENCE_LABELS[level] || level;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
      {label}
    </span>
  );
}

function AccountabilitySection({ authority }: { authority: AuthorityLookupResponse }) {
  const primary = authority.primary_authority;
  if (!primary) return null;

  return (
    <div className="bg-white rounded-lg border p-6 mb-8">
      <h2 className="font-semibold text-gray-800 mb-1 text-lg">Who is likely responsible?</h2>
      <p className="text-xs text-gray-400 mb-4">
        This location <strong>likely</strong> falls under the authority below.
        The mapping has{' '}
        <ConfidenceBadge level={authority.confidence_level} /> confidence.
      </p>

      {/* Primary Authority */}
      <div className="bg-blue-50 rounded-lg p-4 mb-4">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-bold text-blue-900 text-lg">{primary.name}</h3>
            <p className="text-sm text-blue-700 capitalize">{primary.authority_type?.replace('_', ' ')}</p>
          </div>
          <div className="text-right">
            <span className="text-sm font-medium text-blue-800">
              {Math.round((primary.confidence || 0) * 100)}% match
            </span>
          </div>
        </div>
        {(primary.website_url || primary.grievance_url) && (
          <div className="mt-2 flex gap-3">
            {primary.website_url && (
              <a href={primary.website_url} target="_blank" rel="noopener noreferrer"
                 className="text-xs text-blue-600 hover:underline">Website →</a>
            )}
            {primary.grievance_url && (
              <a href={primary.grievance_url} target="_blank" rel="noopener noreferrer"
                 className="text-xs text-blue-600 hover:underline">File Grievance →</a>
            )}
          </div>
        )}
        {primary.contact_phone && (
          <p className="text-xs text-blue-600 mt-1">Phone: {primary.contact_phone}</p>
        )}
      </div>

      {/* Area Hierarchy */}
      {(authority.ward || authority.circle || authority.zone) && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-600 mb-2">Administrative Area</h4>
          <div className="grid grid-cols-3 gap-2">
            {authority.zone && (
              <div className="bg-gray-50 rounded p-2 text-center">
                <p className="text-xs text-gray-400">Zone</p>
                <p className="text-sm font-medium text-gray-800">{authority.zone.name}</p>
              </div>
            )}
            {authority.circle && (
              <div className="bg-gray-50 rounded p-2 text-center">
                <p className="text-xs text-gray-400">Circle</p>
                <p className="text-sm font-medium text-gray-800">{authority.circle.name}</p>
              </div>
            )}
            {authority.ward && (
              <div className="bg-gray-50 rounded p-2 text-center">
                <p className="text-xs text-gray-400">Ward</p>
                <p className="text-sm font-medium text-gray-800">{authority.ward.name}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Nearest Road */}
      {authority.nearest_road && authority.nearest_road.name && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-600 mb-1">Nearest Road</h4>
          <p className="text-sm text-gray-800">
            {authority.nearest_road.name}
            {authority.nearest_road.distance_meters != null && (
              <span className="text-gray-400 ml-1">
                ({authority.nearest_road.distance_meters.toFixed(0)}m away)
              </span>
            )}
            {authority.nearest_road.road_class && (
              <span className="ml-2 text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                {authority.nearest_road.road_class.replace('_', ' ')}
              </span>
            )}
          </p>
        </div>
      )}

      {/* Accountability Chain */}
      {authority.accountability_chain.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-600 mb-2">Accountability Chain</h4>
          <ol className="space-y-2">
            {authority.accountability_chain.map((node, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center text-xs font-bold text-gray-600">
                  {idx + 1}
                </span>
                <div>
                  <p className="text-sm font-medium text-gray-800">{node.display_name}</p>
                  <p className="text-xs text-gray-500">
                    {node.title && <span>{node.title}</span>}
                    {node.type && (
                      <span className="ml-1 text-gray-400">
                        · {NODE_TYPE_LABELS[node.type] || node.type}
                      </span>
                    )}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Alternate Authorities */}
      {authority.alternate_authorities.length > 0 && (
        <div className="border-t pt-3">
          <h4 className="text-xs font-medium text-gray-400 mb-1">Other possible authorities</h4>
          <div className="flex flex-wrap gap-2">
            {authority.alternate_authorities.map((alt, idx) => (
              <span key={idx} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                {alt.name} ({Math.round((alt.confidence || 0) * 100)}%)
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <p className="text-xs text-gray-400 mt-4 italic">
        This authority mapping is based on available geographic data and has{' '}
        {authority.confidence_level} confidence. The actual responsible authority may differ.
      </p>
    </div>
  );
}
