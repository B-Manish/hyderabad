import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MapContainer, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet.markercluster';
import { getMapIssues } from '../services/api';
import { SeverityBadge, StatusBadge } from '../components/Badges';
import {
    ISSUE_TYPE_LABELS,
    SEVERITY_LABELS,
    STATUS_LABELS,
} from '../types';
import type { IssueType, Severity, IssueStatus, MapIssue } from '../types';

// Hyderabad default center
const DEFAULT_CENTER: [number, number] = [17.385, 78.4867];
const DEFAULT_ZOOM = 12;

// Severity-based marker colors
const SEVERITY_MARKER_COLORS: Record<string, string> = {
    low: '#22c55e',
    medium: '#f59e0b',
    high: '#ef4444',
    critical: '#991b1b',
};

function createSeverityIcon(severity: string): L.DivIcon {
    const color = SEVERITY_MARKER_COLORS[severity] || '#6b7280';
    return L.divIcon({
        className: 'custom-marker',
        html: `<div style="
            width: 24px; height: 24px; border-radius: 50%;
            background: ${color}; border: 3px solid white;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            ${severity === 'critical' ? 'animation: pulse 1.5s ease-in-out infinite;' : ''}
        "></div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -14],
    });
}

// Component to handle map events and fetch data
function MapEventHandler({
    onBoundsChange,
}: {
    onBoundsChange: (bounds: L.LatLngBounds) => void;
}) {
    const map = useMapEvents({
        moveend: () => {
            onBoundsChange(map.getBounds());
        },
        zoomend: () => {
            onBoundsChange(map.getBounds());
        },
    });

    useEffect(() => {
        // Initial bounds on mount
        onBoundsChange(map.getBounds());
    }, [map, onBoundsChange]);

    return null;
}

// Locate me button component
function LocateButton() {
    const map = useMap();
    const handleLocate = () => {
        map.locate({ setView: true, maxZoom: 16 });
    };
    return (
        <button
            onClick={handleLocate}
            className="absolute top-20 right-3 z-[1000] bg-white rounded-lg shadow-md p-2 hover:bg-gray-50"
            title="Locate me"
        >
            📍
        </button>
    );
}

// Marker cluster layer
function MarkerClusterGroup({ issues, onIssueClick }: { issues: MapIssue[]; onIssueClick: (issue: MapIssue) => void }) {
    const map = useMap();
    const clusterGroupRef = useRef<L.MarkerClusterGroup | null>(null);

    useEffect(() => {
        if (clusterGroupRef.current) {
            map.removeLayer(clusterGroupRef.current);
        }

        const clusterGroup = (L as any).markerClusterGroup({
            maxClusterRadius: 50,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false,
            iconCreateFunction: (cluster: any) => {
                const childMarkers = cluster.getAllChildMarkers();
                const count = childMarkers.length;
                // Color by worst severity in cluster
                const severities = childMarkers.map((m: any) => m.options.severity || 'low');
                const worstSeverity = severities.includes('critical')
                    ? 'critical'
                    : severities.includes('high')
                    ? 'high'
                    : severities.includes('medium')
                    ? 'medium'
                    : 'low';
                const color = SEVERITY_MARKER_COLORS[worstSeverity];
                return L.divIcon({
                    html: `<div style="
                        background: ${color}; color: white;
                        width: 36px; height: 36px; border-radius: 50%;
                        display: flex; align-items: center; justify-content: center;
                        font-size: 12px; font-weight: bold;
                        border: 3px solid white;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                    ">${count}</div>`,
                    className: 'custom-cluster-icon',
                    iconSize: L.point(36, 36),
                });
            },
        });

        issues.forEach((issue) => {
            const marker = L.marker([issue.latitude, issue.longitude], {
                icon: createSeverityIcon(issue.canonical_severity),
                severity: issue.canonical_severity,
            } as any);

            marker.bindPopup(`
                <div style="min-width: 200px; font-family: system-ui, sans-serif;">
                    <h3 style="font-size: 14px; font-weight: 600; margin: 0 0 6px;">${issue.title}</h3>
                    <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 6px;">
                        <span style="font-size: 11px; padding: 2px 8px; border-radius: 9999px;
                            background: ${issue.canonical_severity === 'critical' ? '#fef2f2' : issue.canonical_severity === 'high' ? '#fff7ed' : issue.canonical_severity === 'medium' ? '#fffbeb' : '#f0fdf4'};
                            color: ${issue.canonical_severity === 'critical' ? '#991b1b' : issue.canonical_severity === 'high' ? '#c2410c' : issue.canonical_severity === 'medium' ? '#a16207' : '#15803d'};">
                            ${issue.canonical_severity.toUpperCase()}
                        </span>
                        ${issue.is_verified ? '<span style="font-size: 11px; padding: 2px 8px; border-radius: 9999px; background: #f0fdf4; color: #15803d;">✓ Verified</span>' : ''}
                    </div>
                    <p style="font-size: 12px; color: #6b7280; margin: 0;">
                        ${issue.report_count} report${issue.report_count !== 1 ? 's' : ''} · ${issue.support_count} supporters
                    </p>
                    <a href="/issues/${issue.id}" style="display: inline-block; margin-top: 8px; font-size: 12px; color: #2563eb; text-decoration: none;">
                        View details →
                    </a>
                </div>
            `);

            marker.on('click', () => onIssueClick(issue));
            clusterGroup.addLayer(marker);
        });

        map.addLayer(clusterGroup);
        clusterGroupRef.current = clusterGroup;

        return () => {
            if (clusterGroupRef.current) {
                map.removeLayer(clusterGroupRef.current);
            }
        };
    }, [issues, map, onIssueClick]);

    return null;
}

export default function MapPage() {
    const [searchParams, setSearchParams] = useSearchParams();

    // View toggle
    const [viewMode, setViewMode] = useState<'map' | 'list'>('map');

    // Filters from URL
    const [filterType, setFilterType] = useState(searchParams.get('issue_type') || '');
    const [filterSeverity, setFilterSeverity] = useState(searchParams.get('severity') || '');
    const [filterStatus, setFilterStatus] = useState(searchParams.get('status') || '');
    const [filterDateFrom, setFilterDateFrom] = useState(searchParams.get('date_from') || '');
    const [filterDateTo, setFilterDateTo] = useState(searchParams.get('date_to') || '');
    const [filterVerified, setFilterVerified] = useState(searchParams.get('verified_only') === 'true');
    const [showFilters, setShowFilters] = useState(false);

    // Map bounds
    const [bounds, setBounds] = useState<{
        minLat: number; minLng: number; maxLat: number; maxLng: number;
    } | null>(null);

    // Selected issue
    const [selectedIssue, setSelectedIssue] = useState<MapIssue | null>(null);

    const handleBoundsChange = useCallback((b: L.LatLngBounds) => {
        setBounds({
            minLat: b.getSouth(),
            minLng: b.getWest(),
            maxLat: b.getNorth(),
            maxLng: b.getEast(),
        });
    }, []);

    // Update URL when filters change
    useEffect(() => {
        const params = new URLSearchParams();
        if (filterType) params.set('issue_type', filterType);
        if (filterSeverity) params.set('severity', filterSeverity);
        if (filterStatus) params.set('status', filterStatus);
        if (filterDateFrom) params.set('date_from', filterDateFrom);
        if (filterDateTo) params.set('date_to', filterDateTo);
        if (filterVerified) params.set('verified_only', 'true');
        setSearchParams(params, { replace: true });
    }, [filterType, filterSeverity, filterStatus, filterDateFrom, filterDateTo, filterVerified, setSearchParams]);

    const { data, isLoading, error } = useQuery({
        queryKey: ['mapIssues', bounds, filterType, filterSeverity, filterStatus, filterDateFrom, filterDateTo, filterVerified],
        queryFn: () => {
            if (!bounds) return Promise.resolve({ issues: [], total_count: 0, viewport_bounds: bounds! });
            return getMapIssues({
                ...bounds,
                issue_type: filterType || undefined,
                severity: filterSeverity || undefined,
                status: filterStatus || undefined,
                verified_only: filterVerified || undefined,
                date_from: filterDateFrom || undefined,
                date_to: filterDateTo || undefined,
            });
        },
        enabled: !!bounds,
        staleTime: 10000,
    });

    const issues = data?.issues || [];

    const clearFilters = () => {
        setFilterType('');
        setFilterSeverity('');
        setFilterStatus('');
        setFilterDateFrom('');
        setFilterDateTo('');
        setFilterVerified(false);
    };

    const hasFilters = filterType || filterSeverity || filterStatus || filterDateFrom || filterDateTo || filterVerified;

    return (
        <div className="h-[calc(100vh-64px)] flex flex-col">
            {/* Top bar */}
            <div className="bg-white border-b px-4 py-2 flex items-center justify-between shrink-0 z-10">
                <div className="flex items-center gap-3">
                    <h1 className="text-lg font-bold text-gray-800">Issue Map</h1>
                    {data && (
                        <span className="text-xs text-gray-500">
                            {data.total_count} issue{data.total_count !== 1 ? 's' : ''} in view
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {/* Filter toggle */}
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
                            hasFilters
                                ? 'bg-primary-50 border-primary-300 text-primary-700'
                                : 'border-gray-300 hover:bg-gray-50'
                        }`}
                    >
                        🔍 Filters {hasFilters ? '•' : ''}
                    </button>
                    {/* Map/List toggle */}
                    <div className="flex rounded-lg border overflow-hidden">
                        <button
                            onClick={() => setViewMode('map')}
                            className={`px-3 py-1.5 text-xs ${
                                viewMode === 'map'
                                    ? 'bg-primary-600 text-white'
                                    : 'bg-white text-gray-600 hover:bg-gray-50'
                            }`}
                        >
                            🗺️ Map
                        </button>
                        <button
                            onClick={() => setViewMode('list')}
                            className={`px-3 py-1.5 text-xs ${
                                viewMode === 'list'
                                    ? 'bg-primary-600 text-white'
                                    : 'bg-white text-gray-600 hover:bg-gray-50'
                            }`}
                        >
                            📋 List
                        </button>
                    </div>
                    {/* Report CTA */}
                    <Link
                        to="/report"
                        className="px-3 py-1.5 bg-primary-600 text-white text-xs rounded-lg hover:bg-primary-700"
                    >
                        + Report
                    </Link>
                </div>
            </div>

            {/* Filter Panel */}
            {showFilters && (
                <div className="bg-white border-b px-4 py-3 shrink-0 z-10">
                    <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
                        <select
                            value={filterType}
                            onChange={(e) => setFilterType(e.target.value)}
                            className="border border-gray-300 rounded-md px-2 py-1.5 text-xs"
                        >
                            <option value="">All Types</option>
                            {Object.entries(ISSUE_TYPE_LABELS).map(([key, label]) => (
                                <option key={key} value={key}>{label}</option>
                            ))}
                        </select>
                        <select
                            value={filterSeverity}
                            onChange={(e) => setFilterSeverity(e.target.value)}
                            className="border border-gray-300 rounded-md px-2 py-1.5 text-xs"
                        >
                            <option value="">All Severities</option>
                            {Object.entries(SEVERITY_LABELS).map(([key, label]) => (
                                <option key={key} value={key}>{label}</option>
                            ))}
                        </select>
                        <select
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value)}
                            className="border border-gray-300 rounded-md px-2 py-1.5 text-xs"
                        >
                            <option value="">All Statuses</option>
                            {(Object.entries(STATUS_LABELS) as [IssueStatus, string][])
                                .filter(([key]) => key !== 'rejected' && key !== 'duplicate')
                                .map(([key, label]) => (
                                    <option key={key} value={key}>{label}</option>
                                ))}
                        </select>
                        <input
                            type="date"
                            value={filterDateFrom}
                            onChange={(e) => setFilterDateFrom(e.target.value)}
                            className="border border-gray-300 rounded-md px-2 py-1.5 text-xs"
                            placeholder="From date"
                        />
                        <input
                            type="date"
                            value={filterDateTo}
                            onChange={(e) => setFilterDateTo(e.target.value)}
                            className="border border-gray-300 rounded-md px-2 py-1.5 text-xs"
                            placeholder="To date"
                        />
                        <div className="flex items-center gap-2">
                            <label className="flex items-center gap-1 text-xs">
                                <input
                                    type="checkbox"
                                    checked={filterVerified}
                                    onChange={(e) => setFilterVerified(e.target.checked)}
                                    className="rounded border-gray-300"
                                />
                                Verified only
                            </label>
                            {hasFilters && (
                                <button
                                    onClick={clearFilters}
                                    className="text-xs text-primary-600 hover:underline"
                                >
                                    Clear
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Content area */}
            <div className="flex-1 relative">
                {viewMode === 'map' ? (
                    <>
                        <MapContainer
                            center={DEFAULT_CENTER}
                            zoom={DEFAULT_ZOOM}
                            className="h-full w-full"
                            zoomControl={true}
                        >
                            <TileLayer
                                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                            />
                            <MapEventHandler onBoundsChange={handleBoundsChange} />
                            <LocateButton />
                            <MarkerClusterGroup
                                issues={issues}
                                onIssueClick={setSelectedIssue}
                            />
                        </MapContainer>

                        {/* Report here floating button */}
                        <Link
                            to="/report"
                            className="absolute bottom-6 right-6 z-[1000] bg-primary-600 text-white px-4 py-3 rounded-full shadow-lg hover:bg-primary-700 text-sm font-medium md:hidden"
                        >
                            + Report Here
                        </Link>

                        {/* Selected issue bottom sheet (mobile) */}
                        {selectedIssue && (
                            <div className="absolute bottom-0 left-0 right-0 z-[1000] bg-white rounded-t-xl shadow-2xl p-4 md:max-w-sm md:left-4 md:bottom-4 md:rounded-xl">
                                <button
                                    onClick={() => setSelectedIssue(null)}
                                    className="absolute top-2 right-3 text-gray-400 hover:text-gray-600 text-lg"
                                >
                                    ×
                                </button>
                                <div className="flex items-center gap-2 mb-2">
                                    <SeverityBadge severity={selectedIssue.canonical_severity as Severity} />
                                    <StatusBadge status={selectedIssue.status as IssueStatus} />
                                    {selectedIssue.is_verified && (
                                        <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">
                                            ✓ Verified
                                        </span>
                                    )}
                                </div>
                                <h3 className="font-semibold text-gray-800 text-sm mb-1">
                                    {selectedIssue.title}
                                </h3>
                                <p className="text-xs text-gray-500 mb-3">
                                    {selectedIssue.report_count} report{selectedIssue.report_count !== 1 ? 's' : ''} · {selectedIssue.support_count} supporters ·{' '}
                                    {new Date(selectedIssue.first_reported_at).toLocaleDateString()}
                                </p>
                                <Link
                                    to={`/issues/${selectedIssue.id}`}
                                    className="block text-center px-4 py-2 bg-primary-600 text-white rounded-lg text-xs font-medium hover:bg-primary-700"
                                >
                                    View Details
                                </Link>
                            </div>
                        )}
                    </>
                ) : (
                    /* List View */
                    <div className="h-full overflow-y-auto bg-gray-50">
                        <div className="max-w-4xl mx-auto px-4 py-4">
                            {isLoading && (
                                <div className="text-center py-10 text-gray-500">Loading issues...</div>
                            )}
                            {error && (
                                <div className="text-center py-10 text-red-500">Failed to load issues.</div>
                            )}
                            {issues.length === 0 && !isLoading && (
                                <div className="text-center py-10 text-gray-500">
                                    No issues found in this area. Try zooming out or adjusting filters.
                                </div>
                            )}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {issues.map((issue) => (
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
                                            <span>
                                                {issue.report_count} report{issue.report_count !== 1 ? 's' : ''}
                                            </span>
                                        </div>
                                        <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
                                            <span>{new Date(issue.first_reported_at).toLocaleDateString()}</span>
                                            {issue.is_verified && (
                                                <span className="text-green-600">✓ Verified</span>
                                            )}
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
