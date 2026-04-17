import { Link, useLocation } from 'react-router-dom';

export default function Navbar() {
  const location = useLocation();

  const linkClass = (path: string) =>
    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
      location.pathname === path
        ? 'bg-primary-700 text-white'
        : 'text-gray-200 hover:bg-primary-600 hover:text-white'
    }`;

  return (
    <nav className="bg-primary-800 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-2">
            <Link to="/" className="flex items-center space-x-2">
              <span className="text-white text-xl font-bold">🛣️ HydRoads</span>
            </Link>
          </div>
          <div className="flex items-center space-x-2">
            <Link to="/" className={linkClass('/')}>Home</Link>
            <Link to="/map" className={linkClass('/map')}>Map</Link>
            <Link to="/issues" className={linkClass('/issues')}>Issues</Link>
            <Link to="/hotspots" className={linkClass('/hotspots')}>Hotspots</Link>
            <Link to="/search" className={linkClass('/search')}>Search</Link>
            <Link to="/about" className={linkClass('/about')}>About</Link>
            <Link to="/report" className={linkClass('/report')}>
              <span className="flex items-center space-x-1">
                <span>+</span>
                <span>Report</span>
              </span>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
