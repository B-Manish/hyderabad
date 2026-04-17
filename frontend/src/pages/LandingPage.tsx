import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getPublicStats, getHotspots } from '../services/api';

export default function LandingPage() {
  const { data: stats } = useQuery({
    queryKey: ['public-stats'],
    queryFn: getPublicStats,
  });

  const { data: hotspots } = useQuery({
    queryKey: ['hotspots'],
    queryFn: () => getHotspots({ limit: 5, period: 'week' }),
  });

  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-700 to-primary-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-28">
          <div className="max-w-3xl">
            <h1 className="text-4xl md:text-5xl font-bold leading-tight">
              Report dangerous roads in Hyderabad.
              <br />
              <span className="text-primary-200">See who is responsible.</span>
            </h1>
            <p className="mt-6 text-lg text-primary-100">
              Upload a photo, mark the location, and help build a public accountability map
              for potholes and unsafe roads in Hyderabad.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row gap-4">
              <Link
                to="/report"
                className="inline-flex items-center justify-center px-8 py-3 bg-white text-primary-700 font-semibold rounded-lg shadow-lg hover:bg-primary-50 transition-colors text-lg"
              >
                Report a road issue
              </Link>
              <Link
                to="/map"
                className="inline-flex items-center justify-center px-8 py-3 border-2 border-white text-white font-semibold rounded-lg hover:bg-white/10 transition-colors text-lg"
              >
                View issue map
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-center text-gray-800 mb-10">Platform Overview</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
            <StatCard number={stats?.total_issues ?? 0} label="Issues Reported" icon="📍" />
            <StatCard number={stats?.unresolved_issues ?? 0} label="Unresolved" icon="⚠️" />
            <StatCard number={stats?.wards_covered ?? 0} label="Wards Covered" icon="🗺️" />
            <StatCard number={stats?.community_confirmations ?? 0} label="Confirmations" icon="👥" />
            <StatCard number={stats?.issues_resolved ?? 0} label="Resolved" icon="✅" />
          </div>
        </div>
      </section>

      {/* Hotspot Section */}
      {hotspots && hotspots.hotspots.length > 0 && (
        <section className="py-16 bg-red-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-2xl font-bold text-center text-gray-800 mb-2">Top Worst Road Areas This Week</h2>
            <p className="text-center text-sm text-gray-500 mb-8">Ranked by severity and issue density</p>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {hotspots.hotspots.map((h, idx) => (
                <Link key={h.ward_id || idx} to={h.map_url || '/map'} className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-2xl font-bold text-red-600">#{idx + 1}</span>
                    <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">
                      Score: {h.hotspot_score}
                    </span>
                  </div>
                  <h3 className="font-semibold text-gray-800 text-sm mb-1">{h.ward}</h3>
                  <p className="text-xs text-gray-500">{h.issue_count} issues &middot; {h.critical_count} critical</p>
                  <p className="text-xs text-gray-400">Avg age: {h.avg_age_days} days</p>
                </Link>
              ))}
            </div>
            <div className="text-center mt-6">
              <Link to="/hotspots" className="text-sm text-primary-600 hover:underline">
                View full hotspot rankings →
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* How It Works */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-center text-gray-800 mb-10">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <StepCard step={1} title="Take a Photo" desc="Capture the road issue from your phone" />
            <StepCard step={2} title="Mark Location" desc="GPS auto-captures or adjust the pin manually" />
            <StepCard step={3} title="Select Type & Severity" desc="Categorize the issue and rate how severe it is" />
            <StepCard step={4} title="Submit" desc="Your report goes live after moderation" />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-primary-800 text-white text-center">
        <div className="max-w-3xl mx-auto px-4">
          <h2 className="text-3xl font-bold mb-4">See a dangerous road? Report it now.</h2>
          <p className="text-primary-200 mb-8">
            Every report helps make Hyderabad roads safer for bikers, commuters, and pedestrians.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/report"
              className="inline-flex items-center justify-center px-8 py-3 bg-white text-primary-700 font-semibold rounded-lg shadow-lg hover:bg-primary-50 transition-colors text-lg"
            >
              Report a road issue
            </Link>
            <Link
              to="/about"
              className="inline-flex items-center justify-center px-8 py-3 border-2 border-white text-white font-semibold rounded-lg hover:bg-white/10 transition-colors text-lg"
            >
              Learn more
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

function StatCard({ number, label, icon }: { number: number; label: string; icon: string }) {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-center">
      <div className="text-3xl mb-2">{icon}</div>
      <div className="text-3xl font-bold text-primary-700">{number}</div>
      <div className="text-sm text-gray-500 mt-1">{label}</div>
    </div>
  );
}

function StepCard({ step, title, desc }: { step: number; title: string; desc: string }) {
  return (
    <div className="text-center p-6">
      <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
        {step}
      </div>
      <h3 className="font-semibold text-gray-800 mb-2">{title}</h3>
      <p className="text-sm text-gray-500">{desc}</p>
    </div>
  );
}
