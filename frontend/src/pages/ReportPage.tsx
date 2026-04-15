import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { createReport, checkDuplicates } from '../services/api';
import ImageUpload from '../components/ImageUpload';
import { SeverityBadge } from '../components/Badges';
import { ISSUE_TYPE_LABELS, SEVERITY_LABELS } from '../types';
import type { IssueType, Severity, ReportCreateRequest, MapIssue } from '../types';

const STEPS = ['upload', 'location', 'type', 'severity', 'details', 'duplicates', 'submit'] as const;
type Step = typeof STEPS[number];

const STEP_LABELS: Record<Step, string> = {
    upload: 'Photos',
    location: 'Location',
    type: 'Type',
    severity: 'Severity',
    details: 'Details',
    duplicates: 'Check',
    submit: 'Submit',
};

// Draggable marker component
function DraggableMarker({
    position,
    onPositionChange,
}: {
    position: [number, number];
    onPositionChange: (lat: number, lng: number) => void;
}) {
    const markerIcon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="
            width: 32px; height: 32px; border-radius: 50%;
            background: #2563eb; border: 4px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            cursor: grab;
        "></div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
    });

    return (
        <Marker
            position={position}
            icon={markerIcon}
            draggable={true}
            eventHandlers={{
                dragend: (e) => {
                    const latlng = e.target.getLatLng();
                    onPositionChange(latlng.lat, latlng.lng);
                },
            }}
        />
    );
}

// Map click handler
function MapClickHandler({ onClick }: { onClick: (lat: number, lng: number) => void }) {
    useMapEvents({
        click: (e) => {
            onClick(e.latlng.lat, e.latlng.lng);
        },
    });
    return null;
}

// Issue type icons/emojis
const ISSUE_TYPE_ICONS: Record<IssueType, string> = {
    pothole: '🕳️',
    road_surface_broken: '💥',
    uneven_resurfacing: '📐',
    waterlogging: '🌊',
    open_manhole: '⚠️',
    dangerous_speed_breaker: '🚧',
    loose_gravel_debris: '🪨',
    construction_spill: '🏗️',
    missing_lane_markings: '🚸',
    road_shoulder_collapse: '⛰️',
    road_cave_in: '🕳️',
    other_road_safety: '🛣️',
};

export default function ReportPage() {
    const navigate = useNavigate();
    const [step, setStep] = useState<Step>('upload');
    const [mediaKeys, setMediaKeys] = useState<string[]>([]);
    const [latitude, setLatitude] = useState<number | null>(null);
    const [longitude, setLongitude] = useState<number | null>(null);
    const [locationError, setLocationError] = useState('');
    const [issueType, setIssueType] = useState<IssueType | ''>('');
    const [severity, setSeverity] = useState<Severity | ''>('');
    const [description, setDescription] = useState('');
    const [landmark, setLandmark] = useState('');
    const [roadName, setRoadName] = useState('');
    const [dangerousForBikes, setDangerousForBikes] = useState(false);
    const [worseInRain, setWorseInRain] = useState(false);
    const [worseAtNight, setWorseAtNight] = useState(false);
    const [selectedDuplicateId, setSelectedDuplicateId] = useState<string | null>(null);
    const [duplicateChoice, setDuplicateChoice] = useState<'link' | 'new' | null>(null);

    // Duplicate check query
    const {
        data: duplicateData,
        isLoading: duplicateLoading,
    } = useQuery({
        queryKey: ['duplicates', latitude, longitude, issueType],
        queryFn: () => {
            if (!latitude || !longitude || !issueType) return Promise.resolve({ duplicates: [], count: 0, search_radius_meters: 30 });
            return checkDuplicates(latitude, longitude, issueType as IssueType);
        },
        enabled: step === 'duplicates' && !!latitude && !!longitude && !!issueType,
    });

    const mutation = useMutation({
        mutationFn: (data: ReportCreateRequest) => createReport(data),
    });

    const captureLocation = () => {
        if (!navigator.geolocation) {
            setLocationError('Geolocation is not supported by your browser');
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                setLatitude(pos.coords.latitude);
                setLongitude(pos.coords.longitude);
                setLocationError('');
            },
            (err) => {
                setLocationError(`Location error: ${err.message}. Tap the map or enter coordinates manually.`);
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    };

    useEffect(() => {
        if (step === 'location' && latitude === null) {
            captureLocation();
        }
    }, [step]);

    const handleSubmit = () => {
        if (!latitude || !longitude || !issueType || !severity || mediaKeys.length === 0) return;

        const existingIssueId = duplicateChoice === 'link' && selectedDuplicateId ? selectedDuplicateId : undefined;

        mutation.mutate(
            {
                latitude,
                longitude,
                issue_type: issueType as IssueType,
                severity: severity as Severity,
                description: description || undefined,
                landmark: landmark || undefined,
                road_name_input: roadName || undefined,
                dangerous_for_bikes: dangerousForBikes,
                worse_in_rain: worseInRain,
                worse_at_night: worseAtNight,
                media_keys: mediaKeys,
                existing_issue_id: existingIssueId,
            },
            {
                onSuccess: () => {
                    setStep('submit');
                },
            }
        );
    };

    const stepIndex = STEPS.indexOf(step);

    // Success screen
    if (step === 'submit' && mutation.isSuccess) {
        return (
            <div className="max-w-2xl mx-auto px-4 py-20 text-center">
                <div className="text-5xl mb-4">✅</div>
                <h1 className="text-2xl font-bold text-gray-800 mb-2">Report Submitted!</h1>
                <p className="text-gray-500 mb-6">
                    {duplicateChoice === 'link'
                        ? 'Your report has been linked to an existing issue. This helps verify the problem!'
                        : 'Your report has been submitted and is pending moderation. It will appear on the map once approved.'}
                </p>
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <button
                        onClick={() => navigate('/map')}
                        className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                    >
                        View on Map
                    </button>
                    <button
                        onClick={() => navigate('/issues')}
                        className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                        View Issues
                    </button>
                    <button
                        onClick={() => window.location.reload()}
                        className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                        Report Another
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
            <h1 className="text-2xl font-bold text-gray-800 mb-2">Report a Road Issue</h1>
            <p className="text-gray-500 text-sm mb-6">
                Help make Hyderabad roads safer by reporting potholes and dangerous conditions.
            </p>

            {/* Progress bar with labels */}
            <div className="flex items-center gap-0.5 mb-8">
                {STEPS.filter((s) => s !== 'submit').map((s, i) => (
                    <div key={s} className="flex-1 flex flex-col items-center">
                        <div
                            className={`w-full h-2 rounded-full ${
                                i <= stepIndex ? 'bg-primary-500' : 'bg-gray-200'
                            }`}
                        />
                        <span
                            className={`text-[10px] mt-1 ${
                                i <= stepIndex ? 'text-primary-600 font-medium' : 'text-gray-400'
                            }`}
                        >
                            {STEP_LABELS[s]}
                        </span>
                    </div>
                ))}
            </div>

            {/* Step 1: Upload */}
            {step === 'upload' && (
                <StepContainer
                    title="Step 1: Upload Photos"
                    subtitle="Take or select 1–5 photos of the road issue"
                >
                    <ImageUpload maxFiles={5} onKeysChange={setMediaKeys} />
                    <StepNav
                        canNext={mediaKeys.length > 0}
                        onNext={() => setStep('location')}
                    />
                </StepContainer>
            )}

            {/* Step 2: Location with map */}
            {step === 'location' && (
                <StepContainer
                    title="Step 2: Confirm Location"
                    subtitle="Drag the pin to the exact location, or tap the map"
                >
                    <div className="rounded-lg overflow-hidden border mb-4" style={{ height: '300px' }}>
                        <MapContainer
                            center={
                                latitude && longitude
                                    ? [latitude, longitude]
                                    : [17.385, 78.4867]
                            }
                            zoom={latitude && longitude ? 16 : 12}
                            className="h-full w-full"
                            style={{ height: '100%' }}
                        >
                            <TileLayer
                                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                            />
                            {latitude && longitude && (
                                <DraggableMarker
                                    position={[latitude, longitude]}
                                    onPositionChange={(lat, lng) => {
                                        setLatitude(lat);
                                        setLongitude(lng);
                                    }}
                                />
                            )}
                            <MapClickHandler
                                onClick={(lat, lng) => {
                                    setLatitude(lat);
                                    setLongitude(lng);
                                }}
                            />
                        </MapContainer>
                    </div>

                    {latitude && longitude ? (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-3">
                            <p className="text-green-700 font-medium text-sm">📍 Location set</p>
                            <p className="text-xs text-green-600 mt-0.5">
                                {latitude.toFixed(6)}, {longitude.toFixed(6)}
                            </p>
                            <p className="text-xs text-green-500 mt-0.5">
                                Drag the pin or tap the map to adjust
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {locationError && (
                                <p className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg">{locationError}</p>
                            )}
                            <button
                                onClick={captureLocation}
                                className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm"
                            >
                                📍 Use My Current Location
                            </button>
                            <p className="text-xs text-gray-400">Or tap anywhere on the map above to set the location</p>
                        </div>
                    )}

                    <details className="mt-3">
                        <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                            Enter coordinates manually
                        </summary>
                        <div className="grid grid-cols-2 gap-3 mt-2">
                            <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Latitude</label>
                                <input
                                    type="number"
                                    step="any"
                                    value={latitude ?? ''}
                                    onChange={(e) => setLatitude(parseFloat(e.target.value) || null)}
                                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                                    placeholder="17.4400"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Longitude</label>
                                <input
                                    type="number"
                                    step="any"
                                    value={longitude ?? ''}
                                    onChange={(e) => setLongitude(parseFloat(e.target.value) || null)}
                                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                                    placeholder="78.3489"
                                />
                            </div>
                        </div>
                    </details>

                    <StepNav
                        canPrev
                        canNext={latitude !== null && longitude !== null}
                        onPrev={() => setStep('upload')}
                        onNext={() => setStep('type')}
                    />
                </StepContainer>
            )}

            {/* Step 3: Issue Type (visual grid) */}
            {step === 'type' && (
                <StepContainer
                    title="Step 3: Select Issue Type"
                    subtitle="What kind of road issue are you reporting?"
                >
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {(Object.keys(ISSUE_TYPE_LABELS) as IssueType[]).map((type) => (
                            <button
                                key={type}
                                onClick={() => setIssueType(type)}
                                className={`p-3 text-center rounded-lg border transition-all ${
                                    issueType === type
                                        ? 'border-primary-500 bg-primary-50 text-primary-700 ring-2 ring-primary-200'
                                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                                }`}
                            >
                                <div className="text-2xl mb-1">{ISSUE_TYPE_ICONS[type]}</div>
                                <div className="text-xs font-medium">{ISSUE_TYPE_LABELS[type]}</div>
                            </button>
                        ))}
                    </div>
                    <StepNav
                        canPrev
                        canNext={issueType !== ''}
                        onPrev={() => setStep('location')}
                        onNext={() => setStep('severity')}
                    />
                </StepContainer>
            )}

            {/* Step 4: Severity */}
            {step === 'severity' && (
                <StepContainer
                    title="Step 4: Rate Severity"
                    subtitle="How dangerous or severe is this issue?"
                >
                    <div className="space-y-2">
                        {(Object.keys(SEVERITY_LABELS) as Severity[]).map((sev) => {
                            const descriptions: Record<Severity, string> = {
                                low: 'Minor issue, not immediately dangerous',
                                medium: 'Noticeable issue, caution needed',
                                high: 'Significant hazard, dangerous for two-wheelers',
                                critical: 'Extreme danger, risk of serious accident',
                            };
                            const colors: Record<Severity, string> = {
                                low: 'border-l-green-500',
                                medium: 'border-l-yellow-500',
                                high: 'border-l-orange-500',
                                critical: 'border-l-red-500',
                            };
                            return (
                                <button
                                    key={sev}
                                    onClick={() => setSeverity(sev)}
                                    className={`w-full p-4 text-left rounded-lg border border-l-4 transition-all ${colors[sev]} ${
                                        severity === sev
                                            ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200'
                                            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                                    }`}
                                >
                                    <span className="font-medium">{SEVERITY_LABELS[sev]}</span>
                                    <span className="block text-sm text-gray-500 mt-0.5">{descriptions[sev]}</span>
                                </button>
                            );
                        })}
                    </div>
                    <StepNav
                        canPrev
                        canNext={severity !== ''}
                        onPrev={() => setStep('type')}
                        onNext={() => setStep('details')}
                    />
                </StepContainer>
            )}

            {/* Step 5: Optional Details */}
            {step === 'details' && (
                <StepContainer
                    title="Step 5: Additional Details (Optional)"
                    subtitle="Help us understand the issue better"
                >
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                maxLength={2000}
                                rows={3}
                                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                                placeholder="Describe the issue in detail..."
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Landmark</label>
                                <input
                                    type="text"
                                    value={landmark}
                                    onChange={(e) => setLandmark(e.target.value)}
                                    maxLength={255}
                                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                                    placeholder="Near XYZ junction"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Road Name</label>
                                <input
                                    type="text"
                                    value={roadName}
                                    onChange={(e) => setRoadName(e.target.value)}
                                    maxLength={255}
                                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                                    placeholder="Gachibowli Main Road"
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <label className="flex items-center gap-2 text-sm">
                                <input
                                    type="checkbox"
                                    checked={dangerousForBikes}
                                    onChange={(e) => setDangerousForBikes(e.target.checked)}
                                    className="rounded border-gray-300"
                                />
                                Dangerous for bikes / two-wheelers
                            </label>
                            <label className="flex items-center gap-2 text-sm">
                                <input
                                    type="checkbox"
                                    checked={worseInRain}
                                    onChange={(e) => setWorseInRain(e.target.checked)}
                                    className="rounded border-gray-300"
                                />
                                Worse in rain
                            </label>
                            <label className="flex items-center gap-2 text-sm">
                                <input
                                    type="checkbox"
                                    checked={worseAtNight}
                                    onChange={(e) => setWorseAtNight(e.target.checked)}
                                    className="rounded border-gray-300"
                                />
                                Worse at night
                            </label>
                        </div>
                    </div>
                    <StepNav
                        canPrev
                        canNext
                        onPrev={() => setStep('severity')}
                        onNext={() => setStep('duplicates')}
                    />
                </StepContainer>
            )}

            {/* Step 6: Duplicate Check */}
            {step === 'duplicates' && (
                <StepContainer
                    title="Step 6: Check for Similar Issues"
                    subtitle="We're checking if this issue has already been reported nearby"
                >
                    {duplicateLoading ? (
                        <div className="text-center py-8 text-gray-500">
                            <div className="animate-spin inline-block w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full mb-2" />
                            <p className="text-sm">Checking for similar issues nearby...</p>
                        </div>
                    ) : duplicateData && duplicateData.count > 0 ? (
                        <div>
                            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
                                <p className="text-amber-700 font-medium text-sm">
                                    ⚠️ {duplicateData.count} similar issue{duplicateData.count !== 1 ? 's' : ''} found nearby
                                </p>
                                <p className="text-xs text-amber-600 mt-1">
                                    If this is the same issue, linking your report helps verify it faster.
                                </p>
                            </div>

                            <div className="space-y-2 mb-4">
                                {duplicateData.duplicates.map((dup: MapIssue) => (
                                    <button
                                        key={dup.id}
                                        onClick={() => {
                                            setSelectedDuplicateId(dup.id);
                                            setDuplicateChoice('link');
                                        }}
                                        className={`w-full p-3 text-left rounded-lg border transition-all ${
                                            selectedDuplicateId === dup.id
                                                ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200'
                                                : 'border-gray-200 hover:border-gray-300'
                                        }`}
                                    >
                                        <div className="flex items-start justify-between">
                                            <div>
                                                <h4 className="font-medium text-sm text-gray-800">{dup.title}</h4>
                                                <p className="text-xs text-gray-500 mt-0.5">
                                                    {dup.report_count} report{dup.report_count !== 1 ? 's' : ''} ·{' '}
                                                    {dup.distance_meters ? `${dup.distance_meters}m away` : ''}
                                                </p>
                                            </div>
                                            <SeverityBadge severity={dup.canonical_severity as Severity} />
                                        </div>
                                        {selectedDuplicateId === dup.id && (
                                            <p className="text-xs text-primary-600 mt-2 font-medium">
                                                ✓ Same issue — will add your report to this
                                            </p>
                                        )}
                                    </button>
                                ))}
                            </div>

                            <button
                                onClick={() => {
                                    setSelectedDuplicateId(null);
                                    setDuplicateChoice('new');
                                }}
                                className={`w-full p-3 text-left rounded-lg border transition-all ${
                                    duplicateChoice === 'new'
                                        ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200'
                                        : 'border-gray-200 hover:border-gray-300'
                                }`}
                            >
                                <span className="font-medium text-sm text-gray-800">
                                    Different issue — create new
                                </span>
                                <span className="block text-xs text-gray-500 mt-0.5">
                                    This is a separate problem, not already listed above
                                </span>
                                {duplicateChoice === 'new' && (
                                    <p className="text-xs text-primary-600 mt-2 font-medium">
                                        ✓ Will create a new issue
                                    </p>
                                )}
                            </button>
                        </div>
                    ) : (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                            <p className="text-green-700 font-medium text-sm">✓ No similar issues found nearby</p>
                            <p className="text-xs text-green-600 mt-1">A new issue will be created.</p>
                        </div>
                    )}

                    <StepNav
                        canPrev
                        canNext={
                            !duplicateLoading &&
                            (!duplicateData?.count || duplicateChoice !== null)
                        }
                        onPrev={() => setStep('details')}
                        onNext={handleSubmit}
                        nextLabel={mutation.isPending ? 'Submitting...' : 'Submit Report'}
                        nextDisabled={mutation.isPending}
                    />
                    {mutation.isError && (
                        <p className="text-red-500 text-sm mt-3">
                            Failed to submit report. Please check your connection and try again.
                        </p>
                    )}
                </StepContainer>
            )}
        </div>
    );
}

function StepContainer({
    title,
    subtitle,
    children,
}: {
    title: string;
    subtitle: string;
    children: React.ReactNode;
}) {
    return (
        <div className="bg-white rounded-lg border p-6">
            <h2 className="font-semibold text-gray-800 text-lg mb-1">{title}</h2>
            <p className="text-sm text-gray-500 mb-4">{subtitle}</p>
            {children}
        </div>
    );
}

function StepNav({
    canPrev = false,
    canNext = false,
    onPrev,
    onNext,
    nextLabel = 'Next →',
    nextDisabled = false,
}: {
    canPrev?: boolean;
    canNext?: boolean;
    onPrev?: () => void;
    onNext?: () => void;
    nextLabel?: string;
    nextDisabled?: boolean;
}) {
    return (
        <div className="mt-6 flex items-center justify-between">
            {canPrev ? (
                <button
                    onClick={onPrev}
                    className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
                >
                    ← Back
                </button>
            ) : (
                <div />
            )}
            {canNext && (
                <button
                    onClick={onNext}
                    disabled={nextDisabled}
                    className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium disabled:opacity-50"
                >
                    {nextLabel}
                </button>
            )}
        </div>
    );
}
