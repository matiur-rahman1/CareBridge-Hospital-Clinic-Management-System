import { useEffect, useState } from 'react';
import { KeyRound, Save, ShieldCheck, UserRound } from 'lucide-react';
import { api, authApi, getErrorMessage } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { initials, titleCase } from '../utils/format';
import { Badge, Button, Field, PageHeader, SectionCard } from '../components/UI';

export default function ProfilePage() {
  const { user, setUser } = useAuth();
  const { notify } = useToast();
  const [form, setForm] = useState({ first_name: '', last_name: '' });
  const [password, setPassword] = useState({ old_password: '', new_password: '' });
  const [saving, setSaving] = useState(false);
  useEffect(() => { setForm({ first_name: user?.first_name || '', last_name: user?.last_name || '' }); }, [user]);
  const updateProfile = async (event) => {
    event.preventDefault(); setSaving(true);
    try { const { data } = await authApi.updateMe(form); setUser(data); notify('Profile updated successfully.'); }
    catch (error) { notify(getErrorMessage(error), 'error'); }
    finally { setSaving(false); }
  };
  const updatePassword = async (event) => {
    event.preventDefault(); setSaving(true);
    try { await authApi.changePassword(password); setPassword({ old_password: '', new_password: '' }); notify('Password changed successfully.'); }
    catch (error) { notify(getErrorMessage(error), 'error'); }
    finally { setSaving(false); }
  };
  return <>
    <PageHeader eyebrow="ACCOUNT SETTINGS" title="My profile" description="Manage your account details and security settings." />
    <div className="profile-page-grid"><SectionCard title="Personal information" subtitle="Your CareBridge account details"><div className="profile-identity"><div className="avatar avatar-profile">{initials(user?.full_name || user?.first_name)}</div><div><h3>{user?.full_name}</h3><span>{titleCase(user?.role || '')} account</span></div><Badge status="success"><ShieldCheck size={13}/> Active</Badge></div><form onSubmit={updateProfile}><div className="form-grid"><Field label="First name" required><input className="input" required value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })}/></Field><Field label="Last name"><input className="input" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })}/></Field><Field label="Email address"><input className="input" value={user?.email || ''} readOnly disabled/></Field><Field label="Role"><input className="input" value={titleCase(user?.role || '')} readOnly disabled/></Field></div><div className="form-actions"><Button type="submit" disabled={saving}><Save size={15}/> Save profile</Button></div></form></SectionCard><SectionCard title="Password & security" subtitle="Keep your account protected"><div className="security-note"><div className="security-icon"><KeyRound size={19}/></div><div><strong>Choose a strong password</strong><span>Use at least 10 characters and avoid reusing passwords from other accounts.</span></div></div><form onSubmit={updatePassword} className="form-stack"><Field label="Current password" required><input className="input" type="password" required value={password.old_password} onChange={(e) => setPassword({ ...password, old_password: e.target.value })}/></Field><Field label="New password" required><input className="input" type="password" minLength="10" required value={password.new_password} onChange={(e) => setPassword({ ...password, new_password: e.target.value })}/></Field><div className="form-actions"><Button type="submit" disabled={saving}><KeyRound size={15}/> Update password</Button></div></form></SectionCard></div>
  </>;
}
