import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAdminAuthorities, createAuthority, updateAuthority } from '../../services/api';
import type { AuthorityAdmin } from '../../types';

function useToken() { return localStorage.getItem('admin_token') || ''; }

const AUTHORITY_TYPES = ['municipal', 'planning', 'highway', 'state', 'ward_level', 'contractor', 'other'];

export default function AdminAuthorityPage() {
    const token = useToken();
    const qc = useQueryClient();
    const [showCreate, setShowCreate] = useState(false);
    const [editAuth, setEditAuth] = useState<AuthorityAdmin | null>(null);
    const [form, setForm] = useState({ name: '', authority_type: 'municipal', description: '', contact_phone: '', contact_email: '' });

    const { data: authorities, isLoading } = useQuery({
        queryKey: ['admin-authorities'],
        queryFn: () => getAdminAuthorities(token),
    });

    const createMut = useMutation({
        mutationFn: () => createAuthority(token, form),
        onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-authorities'] }); setShowCreate(false); resetForm(); },
    });

    const updateMut = useMutation({
        mutationFn: (data: { id: string; updates: Partial<AuthorityAdmin> }) => updateAuthority(token, data.id, data.updates),
        onSuccess: () => { qc.invalidateQueries({ queryKey: ['admin-authorities'] }); setEditAuth(null); },
    });

    function resetForm() {
        setForm({ name: '', authority_type: 'municipal', description: '', contact_phone: '', contact_email: '' });
    }

    if (isLoading) return <div className="text-gray-500">Loading authorities...</div>;

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <h1 className="text-2xl font-bold text-gray-900">Authority Management</h1>
                <button
                    onClick={() => { setShowCreate(true); resetForm(); }}
                    className="px-3 py-1.5 bg-primary-700 text-white rounded text-sm font-medium"
                >
                    + Add Authority
                </button>
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                        <tr>
                            <th className="px-3 py-2 text-left">Name</th>
                            <th className="px-3 py-2 text-left">Type</th>
                            <th className="px-3 py-2 text-left">Contact</th>
                            <th className="px-3 py-2 text-left">Status</th>
                            <th className="px-3 py-2 text-left">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y">
                        {authorities?.map((a) => (
                            <tr key={a.id} className="hover:bg-gray-50">
                                <td className="px-3 py-2 font-medium text-gray-900">{a.name}</td>
                                <td className="px-3 py-2 text-gray-600">{a.authority_type}</td>
                                <td className="px-3 py-2 text-gray-500 text-xs">{a.contact_phone || a.contact_email || '—'}</td>
                                <td className="px-3 py-2">
                                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${a.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                        {a.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                </td>
                                <td className="px-3 py-2">
                                    <div className="flex gap-1">
                                        <button
                                            onClick={() => setEditAuth(a)}
                                            className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs"
                                        >
                                            Edit
                                        </button>
                                        <button
                                            onClick={() => updateMut.mutate({ id: a.id, updates: { is_active: !a.is_active } })}
                                            className={`px-2 py-0.5 rounded text-xs ${a.is_active ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}
                                        >
                                            {a.is_active ? 'Deactivate' : 'Activate'}
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Create Dialog */}
            {showCreate && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h3 className="font-bold text-gray-900 mb-3">Add Authority</h3>
                        <div className="space-y-3">
                            <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Name" className="w-full border rounded px-2 py-1.5 text-sm" />
                            <select value={form.authority_type} onChange={e => setForm({ ...form, authority_type: e.target.value })} className="w-full border rounded px-2 py-1.5 text-sm">
                                {AUTHORITY_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                            </select>
                            <input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Description" className="w-full border rounded px-2 py-1.5 text-sm" />
                            <input value={form.contact_phone} onChange={e => setForm({ ...form, contact_phone: e.target.value })} placeholder="Phone" className="w-full border rounded px-2 py-1.5 text-sm" />
                            <input value={form.contact_email} onChange={e => setForm({ ...form, contact_email: e.target.value })} placeholder="Email" className="w-full border rounded px-2 py-1.5 text-sm" />
                            <div className="flex justify-end gap-2">
                                <button onClick={() => setShowCreate(false)} className="px-3 py-1.5 bg-gray-100 rounded text-sm">Cancel</button>
                                <button onClick={() => createMut.mutate()} disabled={!form.name || createMut.isPending} className="px-3 py-1.5 bg-primary-700 text-white rounded text-sm font-medium disabled:opacity-50">Create</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Edit Dialog */}
            {editAuth && (
                <EditAuthorityDialog
                    authority={editAuth}
                    onClose={() => setEditAuth(null)}
                    onSave={(updates) => updateMut.mutate({ id: editAuth.id, updates })}
                    isPending={updateMut.isPending}
                />
            )}
        </div>
    );
}

function EditAuthorityDialog({ authority, onClose, onSave, isPending }: { authority: AuthorityAdmin; onClose: () => void; onSave: (u: Partial<AuthorityAdmin>) => void; isPending: boolean }) {
    const [name, setName] = useState(authority.name);
    const [desc, setDesc] = useState(authority.description || '');
    const [phone, setPhone] = useState(authority.contact_phone || '');
    const [email, setEmail] = useState(authority.contact_email || '');

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
                <h3 className="font-bold text-gray-900 mb-3">Edit: {authority.name}</h3>
                <div className="space-y-3">
                    <input value={name} onChange={e => setName(e.target.value)} placeholder="Name" className="w-full border rounded px-2 py-1.5 text-sm" />
                    <input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Description" className="w-full border rounded px-2 py-1.5 text-sm" />
                    <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="Phone" className="w-full border rounded px-2 py-1.5 text-sm" />
                    <input value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" className="w-full border rounded px-2 py-1.5 text-sm" />
                    <div className="flex justify-end gap-2">
                        <button onClick={onClose} className="px-3 py-1.5 bg-gray-100 rounded text-sm">Cancel</button>
                        <button
                            disabled={isPending}
                            onClick={() => onSave({ name, description: desc, contact_phone: phone, contact_email: email })}
                            className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm font-medium disabled:opacity-50"
                        >
                            Save
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
