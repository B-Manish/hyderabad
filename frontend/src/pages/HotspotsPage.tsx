import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getHotspots } from '../services/api';

export default function HotspotsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['hotspots-full'],
    queryFn: () => getHotspots({ limit: 50, period: 'week' }),
  });

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">Hotspot Rankings</h1>
      <p className="text-sm text-gray-500 mb-6">
        Areas with the worst road conditions, ranked by severity and issue density.
        {data && <span className="ml-1">Period: {data.period}</span>}
      </p>

      {isLoading && <p className="text-gray-500">Loading hotspot data...</p>}

      {data && data.hotspots.length === 0 && (
        <p className="text-gray-500 py-10 text-center">No hotspot data available yet.</p>
      )}

      {data && data.hotspots.length > 0 && (
        <div className="space-y-3">
          {data.hotspots.map((h, idx) => (
            <Link
              key={h.ward_id || idx}
              to={h.map_url || '/map'}
              className="block bg-white rounded-lg border p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center gap-4">
                <span className={`text-2xl font-bold w-10 text-center ${idx < 3 ? 'text-red-600' : 'text-gray-400'}`}>
                  #{idx + 1}
                </span>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-800">{h.ward}</h3>
                  {h.zone && <p className="text-xs text-gray-400">{h.zone}</p>}
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-primary-700">{h.issue_count}</p>
                  <p className="text-xs text-gray-500">issues</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-red-600">{h.critical_count}</p>
                  <p className="text-xs text-gray-500">critical</p>
                </div>
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-medium text-gray-700">{h.avg_age_days}d</p>
                  <p className="text-xs text-gray-500">avg age</p>
                </div>
                <div className="text-right">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-700">
                    {h.hotspot_score}
                  </span>
                  <p className="text-xs text-gray-500">score</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
