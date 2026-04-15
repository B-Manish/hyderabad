import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { createReport } from '../services/api';
import ImageUpload from '../components/ImageUpload';
import { ISSUE_TYPE_LABELS, SEVERITY_LABELS } from '../types';
import type { IssueType, Severity, ReportCreateRequest } from '../types';

type Step = 'upload' | 'location' | 'type' | 'severity' | 'details' | 'review';

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

  const mutation = useMutation({
    mutationFn: (data: ReportCreateRequest) => createReport(data),
    onSuccess: () => {
      setStep('review');
    },
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
        setLocationError(`Location error: ${err.message}. You can enter coordinates manually.`);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleSubmit = () => {
    if (!latitude || !longitude || !issueType || !severity || mediaKeys.length === 0) return;
    mutation.mutate({
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
    });
  };

  const steps: Step[] = ['upload', 'location', 'type', 'severity', 'details'];
  const stepIndex = steps.indexOf(step);

  // Success screen
  if (step === 'review' && mutation.isSuccess) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">
        <div className="text-5xl mb-4">✅</div>
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Report Submitted!</h1>
        <p className="text-gray-500 mb-6">
          Your report has been submitted and is pending moderation. It will appear in the issue list once approved.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={() => navigate('/issues')}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            View Issues
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Submit Another Report
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

      {/* Progress bar */}
      <div className="flex items-center gap-1 mb-8">
        {steps.map((s, i) => (
          <div
            key={s}
            className={`flex-1 h-2 rounded-full ${
              i <= stepIndex ? 'bg-primary-500' : 'bg-gray-200'
            }`}
          />
        ))}
      </div>

      {/* Step 1: Upload */}
      {step === 'upload' && (
        <StepContainer
          title="Step 1: Upload Photos"
          subtitle="Take or select photos of the road issue"
        >
          <ImageUpload maxFiles={5} onKeysChange={setMediaKeys} />
          <StepNav
            canNext={mediaKeys.length > 0}
            onNext={() => { captureLocation(); setStep('location'); }}
          />
        </StepContainer>
      )}

      {/* Step 2: Location */}
      {step === 'location' && (
        <StepContainer
          title="Step 2: Confirm Location"
          subtitle="We'll use your GPS location or you can enter coordinates manually"
        >
          {latitude && longitude ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
              <p className="text-green-700 font-medium">📍 Location captured</p>
              <p className="text-sm text-green-600 mt-1">
                {latitude.toFixed(6)}, {longitude.toFixed(6)}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {locationError && (
                <p className="text-sm text-red-500">{locationError}</p>
              )}
              <button
                onClick={captureLocation}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm"
              >
                📍 Capture My Location
              </button>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Latitude</label>
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
                  <label className="block text-sm font-medium text-gray-700 mb-1">Longitude</label>
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
            </div>
          )}
          <StepNav
            canPrev
            canNext={latitude !== null && longitude !== null}
            onPrev={() => setStep('upload')}
            onNext={() => setStep('type')}
          />
        </StepContainer>
      )}

      {/* Step 3: Issue Type */}
      {step === 'type' && (
        <StepContainer
          title="Step 3: Select Issue Type"
          subtitle="What kind of road issue are you reporting?"
        >
          <div className="grid grid-cols-2 gap-2">
            {(Object.keys(ISSUE_TYPE_LABELS) as IssueType[]).map((type) => (
              <button
                key={type}
                onClick={() => setIssueType(type)}
                className={`p-3 text-left text-sm rounded-lg border transition-colors ${
                  issueType === type
                    ? 'border-primary-500 bg-primary-50 text-primary-700 font-medium'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {ISSUE_TYPE_LABELS[type]}
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
              return (
                <button
                  key={sev}
                  onClick={() => setSeverity(sev)}
                  className={`w-full p-4 text-left rounded-lg border transition-colors ${
                    severity === sev
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
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
          <div className="mt-6 flex items-center justify-between">
            <button
              onClick={() => setStep('severity')}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
            >
              ← Back
            </button>
            <button
              onClick={handleSubmit}
              disabled={mutation.isPending}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 font-medium"
            >
              {mutation.isPending ? 'Submitting...' : 'Submit Report'}
            </button>
          </div>
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
}: {
  canPrev?: boolean;
  canNext?: boolean;
  onPrev?: () => void;
  onNext?: () => void;
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
          className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium"
        >
          Next →
        </button>
      )}
    </div>
  );
}
