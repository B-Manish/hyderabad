import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAdminUsers, changeUserRole, deactivateUser } from '../../services/api';

function useToken() { return localStorage.getItem('admin_token') || ''; }

export default function AdminUserManagementPage() {
    const token = useToken();
    const qc = useQueryClient();
    const [search, setSearch] = useState('');
    const [roleFilter, setRoleFilter] = useState('');
    const [page, setPage] = useState(1);

    const { data, isLoading } = useQuery({
        queryKey: ['admin-users', search, roleFilter, page],
        queryFn: () => getAdminUsers(token, { search: search || undefined, role: roleFilter || undefined, page }),
    });

    const roleMut = useMutation({
        mutationFn: ({ userId, role }: { userId: string; role: string }) => changeUserRole(token, userId, role),
        onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-users'] }),
    });

    const deactivateMut = useMutation({
        mutationFn: ({ userId, active }: { userId: string; active: boolean }) => deactivateUser(token, userId, active),
        onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-users'] }),
    });

    return (
        <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">User Management</h1>

            <div className="flex gap-3 mb-4">
                <input
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                    placeholder="Search name or email..."
                    className="border rounded px-3 py-1.5 text-sm flex-1"
                />
                <select
                    value={roleFilter}
                    onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }}
                    className="border rounded px-3 py-1.5 text-sm"
                >
                    <option value="">All roles</option>
                    <option value="citizen">Citizen</option>
                    <option value="moderator">Moderator</option>
                    <option value="admin">Admin</option>
                </select>
            </div>

            {isLoading && <p className="text-gray-500">Loading...</p>}

            {data && (
                <>
                    <div className="bg-white rounded-lg shadow overflow-hidden">
                        <table className="w-full text-sm">
                            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                                <tr>
                                    <th className="px-3 py-2 text-left">Name</th>
                                    <th className="px-3 py-2 text-left">Email</th>
                                    <th className="px-3 py-2 text-left">Role</th>
                                    <th className="px-3 py-2 text-left">Status</th>
                                    <th className="px-3 py-2 text-left">Joined</th>
                                    <th className="px-3 py-2 text-left">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {data.items.map((u) => (
                                    <tr key={u.id} className="hover:bg-gray-50">
                                        <td className="px-3 py-2 font-medium text-gray-900">{u.name || '—'}</td>
                                        <td className="px-3 py-2 text-gray-600">{u.email || '—'}</td>
                                        <td className="px-3 py-2">
                                            <select
                                                value={u.role}
                                                onChange={(e) => roleMut.mutate({ userId: u.id, role: e.target.value })}
                                                className="border rounded px-2 py-0.5 text-xs"
                                            >
                                                <option value="citizen">Citizen</option>
                                                <option value="moderator">Moderator</option>
                                                <option value="admin">Admin</option>
                                            </select>
                                        </td>
                                        <td className="px-3 py-2">
                                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${u.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                                {u.is_active ? 'Active' : 'Inactive'}
                                            </span>
                                        </td>
                                        <td className="px-3 py-2 text-gray-500 text-xs">{new Date(u.created_at).toLocaleDateString()}</td>
                                        <td className="px-3 py-2">
                                            <button
                                                onClick={() => deactivateMut.mutate({ userId: u.id, active: !u.is_active })}
                                                className={`px-2 py-0.5 rounded text-xs ${u.is_active ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}
                                            >
                                                {u.is_active ? 'Deactivate' : 'Activate'}
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {data.total_pages > 1 && (
                        <div className="flex justify-center gap-2 mt-4">
                            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 rounded bg-gray-100 text-sm disabled:opacity-50">Prev</button>
                            <span className="px-3 py-1 text-sm text-gray-600">Page {page} of {data.total_pages}</span>
                            <button disabled={page >= data.total_pages} onClick={() => setPage(p => p + 1)} className="px-3 py-1 rounded bg-gray-100 text-sm disabled:opacity-50">Next</button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
