import { NavLink, Outlet, Navigate } from 'react-router-dom';

const ADMIN_NAV = [
    { path: '/admin', label: 'Dashboard', icon: '📊' },
    { path: '/admin/moderation', label: 'Moderation Queue', icon: '📋' },
    { path: '/admin/issues', label: 'Issue Management', icon: '🔧' },
    { path: '/admin/authorities', label: 'Authorities', icon: '🏛️' },
    { path: '/admin/analytics', label: 'Analytics', icon: '📈' },
    { path: '/admin/users', label: 'Users', icon: '👥' },
    { path: '/admin/audit', label: 'Audit Log', icon: '📜' },
];

export default function AdminLayout() {
    const token = localStorage.getItem('admin_token');
    const role = localStorage.getItem('admin_role');
    if (!token || (role !== 'admin' && role !== 'moderator')) {
        return <Navigate to="/admin/login" replace />;
    }

    const isMod = role === 'moderator';

    return (
        <div className="flex min-h-screen bg-gray-50">
            {/* Sidebar */}
            <aside className="w-56 bg-gray-900 text-gray-300 flex flex-col flex-shrink-0">
                <div className="p-4 border-b border-gray-700">
                    <h2 className="text-white font-bold text-lg">🛣️ HydRoads</h2>
                    <p className="text-xs text-gray-400 mt-1">Admin Panel</p>
                </div>
                <nav className="flex-1 py-4 space-y-1 px-2">
                    {ADMIN_NAV.map((item) => {
                        // Hide admin-only sections from moderators
                        if (isMod && ['/admin/authorities', '/admin/users', '/admin/audit'].includes(item.path)) {
                            return null;
                        }
                        return (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                end={item.path === '/admin'}
                                className={({ isActive }) =>
                                    `flex items-center gap-2 px-3 py-2 rounded text-sm transition-colors ${isActive
                                        ? 'bg-primary-700 text-white'
                                        : 'hover:bg-gray-800 text-gray-300'
                                    }`
                                }
                            >
                                <span>{item.icon}</span>
                                <span>{item.label}</span>
                            </NavLink>
                        );
                    })}
                </nav>
                <div className="p-4 border-t border-gray-700 text-xs">
                    <p className="text-gray-400">Logged in as <span className="text-white">{role}</span></p>
                    <button
                        onClick={() => { localStorage.removeItem('admin_token'); localStorage.removeItem('admin_role'); window.location.href = '/admin/login'; }}
                        className="mt-2 text-red-400 hover:text-red-300"
                    >
                        Sign out
                    </button>
                </div>
            </aside>
            {/* Main Content */}
            <main className="flex-1 p-6 overflow-auto">
                <Outlet />
            </main>
        </div>
    );
}
