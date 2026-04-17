import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { searchAll } from '../services/api';
import { SeverityBadge } from '../components/Badges';
import type { Severity } from '../types';

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [inputValue, setInputValue] = useState(searchParams.get('q') || '');
  const q = searchParams.get('q') || '';
  const type = searchParams.get('type') || undefined;

  const { data, isLoading } = useQuery({
    queryKey: ['search', q, type],
    queryFn: () => searchAll({ q, type }),
    enabled: q.length > 0,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      setSearchParams({ q: inputValue.trim(), ...(type ? { type } : {}) });
    }
  };

  const typeFilter = (t: string | undefined) => {
    if (t) {
      setSearchParams({ q, type: t });
    } else {
      setSearchParams({ q });
    }
  };

  const typeIcon: Record<string, string> = {
    ward: '🗺️',
    road: '🛣️',
    issue: '📍',
    authority: '🏛️',
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Search</h1>

      {/* Search Input */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Search for wards, roads, issues, or areas..."
            className="flex-1 px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:outline-none text-sm"
          />
          <button
            type="submit"
            className="px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
          >
            Search
          </button>
        </div>
      </form>

      {/* Type Filters */}
      {q && (
        <div className="flex gap-2 mb-6">
          <FilterButton label="All" active={!type} onClick={() => typeFilter(undefined)} />
          <FilterButton label="Wards" active={type === 'ward'} onClick={() => typeFilter('ward')} />
          <FilterButton label="Roads" active={type === 'road'} onClick={() => typeFilter('road')} />
          <FilterButton label="Issues" active={type === 'issue'} onClick={() => typeFilter('issue')} />
        </div>
      )}

      {/* Results */}
      {isLoading && <p className="text-gray-500">Searching...</p>}

      {data && (
        <div>
          <p className="text-sm text-gray-500 mb-4">{data.total} result{data.total !== 1 ? 's' : ''} for "{q}"</p>
          {data.results.length === 0 && (
            <p className="text-gray-500 py-10 text-center">No results found. Try a different search term.</p>
          )}
          <div className="space-y-3">
            {data.results.map((item) => (
              <Link
                key={`${item.type}-${item.id}`}
                to={item.url || '#'}
                className="block bg-white rounded-lg border p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">{typeIcon[item.type] || '📄'}</span>
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-800 text-sm">{item.name}</h3>
                    <p className="text-xs text-gray-400 capitalize">{item.type}</p>
                  </div>
                  {item.issue_count != null && (
                    <span className="text-xs text-gray-500">{item.issue_count} issues</span>
                  )}
                  {item.severity && <SeverityBadge severity={item.severity as Severity} />}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function FilterButton({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
        active ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      }`}
    >
      {label}
    </button>
  );
}
