import { useCallback, useEffect, useState } from 'react';
import { CalendarClock, Pencil, Plus, Stethoscope, ToggleLeft, ToggleRight, Trash2, UserRound } from 'lucide-react';
import { api, getErrorMessage, getList, resources } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { initials, money, titleCase, timeLabel } from '../utils/format';
import { Badge, Button, Field, FormActions, Modal, PageHeader, SearchInput, SectionCard, Table } from '../components/UI';

const blankDoctor = { full_name: '', specialization: '', qualifications: '', email: '', phone: '', consultation_fee: '500', bio: '', is_active: true, user: '' };
const blankAvailability = { doctor: '', weekday: '0', start_time: '09:00', end_time: '17:00', slot_minutes: '30', is_active: true };
const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function DoctorsPage() {
  const { user } = useAuth();
  const { notify } = useToast();
  const [rows, setRows] = useState([]);
  const [availabilities, setAvailabilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [specialization, setSpecialization] = useState('');
  const [doctorModal, setDoctorModal] = useState(false);
  const [availabilityModal, setAvailabilityModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(blankDoctor);
  const [schedule, setSchedule] = useState(blankAvailability);
  const [saving, setSaving] = useState(false);
  const canManage = ['ADMIN', 'RECEPTIONIST'].includes(user?.role);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [doctorRows, availabilityRows] = await Promise.all([
        getList(resources.doctors, { search, specialization: specialization || undefined, ordering: 'full_name' }),
        getList(resources.availabilities),
      ]);
      setRows(doctorRows); setAvailabilities(availabilityRows);
    } catch (error) { notify(getErrorMessage(error), 'error'); }
    finally { setLoading(false); }
  }, [search, specialization, notify]);
  useEffect(() => { const timer = window.setTimeout(load, 220); return () => window.clearTimeout(timer); }, [load]);

  const openCreate = () => { setEditing(null); setForm(blankDoctor); setDoctorModal(true); };
  const openEdit = (doctor) => { setEditing(doctor); setForm({ ...blankDoctor, ...doctor, email: doctor.email || '', user: doctor.user || '' }); setDoctorModal(true); };
  const saveDoctor = async (event) => {
    event.preventDefault(); setSaving(true);
    const payload = { ...form, email: form.email || null, user: form.user === '' ? null : Number(form.user), consultation_fee: form.consultation_fee || '0' };
    try { if (editing) await api.patch(`${resources.doctors}${editing.id}/`, payload); else await api.post(resources.doctors, payload); notify(editing ? 'Doctor profile updated.' : 'Doctor added successfully.'); setDoctorModal(false); await load(); }
    catch (error) { notify(getErrorMessage(error), 'error'); }
    finally { setSaving(false); }
  };
  const toggleActive = async (doctor) => {
    try { await api.patch(`${resources.doctors}${doctor.id}/`, { is_active: !doctor.is_active }); notify(doctor.is_active ? 'Doctor profile deactivated.' : 'Doctor profile activated.'); await load(); }
    catch (error) { notify(getErrorMessage(error), 'error'); }
  };
  const removeDoctor = async (doctor) => {
    if (!window.confirm(`Delete Dr. ${doctor.full_name}? Profiles with medical history cannot be deleted.`)) return;
    try { await api.delete(`${resources.doctors}${doctor.id}/`); notify('Doctor deleted.'); await load(); }
    catch (error) { notify(getErrorMessage(error), 'error'); }
  };
  const openSchedule = (doctor) => { setSchedule({ ...blankAvailability, doctor: String(doctor.id) }); setAvailabilityModal(true); };
  const saveSchedule = async (event) => {
    event.preventDefault(); setSaving(true);
    try { await api.post(resources.availabilities, { ...schedule, doctor: Number(schedule.doctor), weekday: Number(schedule.weekday), slot_minutes: Number(schedule.slot_minutes) }); notify('Doctor availability saved.'); setAvailabilityModal(false); await load(); }
    catch (error) { notify(getErrorMessage(error), 'error'); }
    finally { setSaving(false); }
  };
  const columns = [
    { key: 'doctor', label: 'Doctor', render: (row) => <div className="table-person"><div className="avatar avatar-tiny avatar-blue">{initials(row.full_name)}</div><div><strong>Dr. {row.full_name}</strong><small>{row.doctor_id} · {row.qualifications || 'Qualifications not added'}</small></div></div> },
    { key: 'specialization', label: 'Specialization', render: (row) => <span className="specialty-pill">{row.specialization}</span> },
    { key: 'contact', label: 'Contact', render: (row) => <div><strong>{row.phone || '—'}</strong><small>{row.email || 'No email'}</small></div> },
    { key: 'consultation_fee', label: 'Consultation', render: (row) => <strong>{money(row.consultation_fee)}</strong> },
    { key: 'is_active', label: 'Availability', render: (row) => <Badge status={row.is_active ? 'success' : 'neutral'}>{row.is_active ? 'Active' : 'Inactive'}</Badge> },
    { key: 'actions', label: '', render: (row) => <div className="row-actions">{canManage && <><button className="icon-btn" title="Add availability" onClick={() => openSchedule(row)}><CalendarClock size={16}/></button><button className="icon-btn" title="Edit doctor" onClick={() => openEdit(row)}><Pencil size={15}/></button><button className="icon-btn" title={row.is_active ? 'Deactivate' : 'Activate'} onClick={() => toggleActive(row)}>{row.is_active ? <ToggleRight size={17}/> : <ToggleLeft size={17}/>}</button><button className="icon-btn icon-danger" title="Delete doctor" onClick={() => removeDoctor(row)}><Trash2 size={15}/></button></>}</div> },
  ];
  const scheduleColumns = [{ key: 'doctor_name', label: 'Doctor', render: (row) => rows.find((d) => d.id === row.doctor)?.full_name || `Doctor #${row.doctor}` }, { key: 'weekday_name', label: 'Day' }, { key: 'time', label: 'Hours', render: (row) => `${timeLabel(row.start_time)} – ${timeLabel(row.end_time)}` }, { key: 'slot_minutes', label: 'Slot length', render: (row) => `${row.slot_minutes} min` }, { key: 'is_active', label: 'Status', render: (row) => <Badge status={row.is_active ? 'success' : 'neutral'}>{row.is_active ? 'Active' : 'Inactive'}</Badge> }];
  const specializations = [...new Set(rows.map((row) => row.specialization).filter(Boolean))].sort();

  return <>
    <PageHeader eyebrow="CARE TEAM" title="Doctor directory" description="Manage your clinical team, specialties and consultation availability." actions={canManage && <Button onClick={openCreate}><Plus size={16}/> Add doctor</Button>} />
    <div className="stats-grid stats-grid-three"><div className="stat-card compact-stat"><div className="stat-icon stat-blue"><Stethoscope size={20}/></div><div className="stat-label">Total doctors</div><div className="stat-value">{rows.length}</div><div className="stat-detail">In your directory</div></div><div className="stat-card compact-stat"><div className="stat-icon stat-green"><UserRound size={20}/></div><div className="stat-label">Active doctors</div><div className="stat-value">{rows.filter((d) => d.is_active).length}</div><div className="stat-detail">Available for appointments</div></div><div className="stat-card compact-stat"><div className="stat-icon stat-purple"><CalendarClock size={20}/></div><div className="stat-label">Availability windows</div><div className="stat-value">{availabilities.filter((a) => a.is_active).length}</div><div className="stat-detail">Active weekly schedules</div></div></div>
    <SectionCard title="Doctors" subtitle={`${rows.length} clinical profiles`}><div className="toolbar"><SearchInput value={search} onChange={setSearch} placeholder="Search doctor, specialty or ID..."/><select className="select compact-select" value={specialization} onChange={(e) => setSpecialization(e.target.value)}><option value="">All specialties</option>{specializations.map((item) => <option key={item}>{item}</option>)}</select></div><Table columns={columns} rows={rows} loading={loading} emptyTitle="No doctors found" emptyDescription="Add a doctor profile to begin building your care team." /></SectionCard>
    <SectionCard title="Weekly availability" subtitle="Doctor hours used for appointment planning" action={canManage && <Button variant="outline" size="sm" onClick={() => { setSchedule(blankAvailability); setAvailabilityModal(true); }}><Plus size={15}/> Add schedule</Button>}><Table columns={scheduleColumns} rows={availabilities} loading={loading} emptyTitle="No schedules configured" emptyDescription="Add working hours for doctors to organize appointment slots." /></SectionCard>

    <Modal open={doctorModal} onClose={() => setDoctorModal(false)} title={editing ? 'Edit doctor profile' : 'Add a doctor'} description="Create a clinical profile for your care team." wide><form onSubmit={saveDoctor}><div className="form-grid"><Field label="Full name" required><input className="input" required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} placeholder="e.g. Nadia Karim"/></Field><Field label="Specialization" required><input className="input" required value={form.specialization} onChange={(e) => setForm({ ...form, specialization: e.target.value })} placeholder="e.g. Cardiology"/></Field><Field label="Qualifications"><input className="input" value={form.qualifications} onChange={(e) => setForm({ ...form, qualifications: e.target.value })} placeholder="MBBS, FCPS"/></Field><Field label="Email"><input className="input" type="email" value={form.email || ''} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="doctor@carebridge.demo"/></Field><Field label="Phone"><input className="input" value={form.phone || ''} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="+880 1XXXXXXXXX"/></Field><Field label="Consultation fee (BDT)"><input className="input" type="number" min="0" step="0.01" value={form.consultation_fee} onChange={(e) => setForm({ ...form, consultation_fee: e.target.value })}/></Field><Field label="Linked doctor account ID" hint="Optional. Link an existing user whose role is DOCTOR."><input className="input" type="number" min="1" value={form.user || ''} onChange={(e) => setForm({ ...form, user: e.target.value })} placeholder="Existing user ID"/></Field><Field label="Profile status"><select className="select" value={String(form.is_active)} onChange={(e) => setForm({ ...form, is_active: e.target.value === 'true' })}><option value="true">Active</option><option value="false">Inactive</option></select></Field><Field label="Professional bio" className="field-span-2"><textarea className="textarea" rows="3" value={form.bio || ''} onChange={(e) => setForm({ ...form, bio: e.target.value })} placeholder="A short introduction and clinical interests"/></Field></div><FormActions onCancel={() => setDoctorModal(false)} saving={saving} submitLabel={editing ? 'Save profile' : 'Add doctor'}/></form></Modal>

    <Modal open={availabilityModal} onClose={() => setAvailabilityModal(false)} title="Add doctor availability" description="Define a recurring weekly window for appointments."><form onSubmit={saveSchedule}><div className="form-stack"><Field label="Doctor" required><select className="select" required value={schedule.doctor} onChange={(e) => setSchedule({ ...schedule, doctor: e.target.value })}><option value="">Choose doctor</option>{rows.filter((row) => row.is_active).map((row) => <option key={row.id} value={row.id}>Dr. {row.full_name}</option>)}</select></Field><Field label="Weekday" required><select className="select" value={schedule.weekday} onChange={(e) => setSchedule({ ...schedule, weekday: e.target.value })}>{weekdays.map((day, index) => <option value={index} key={day}>{day}</option>)}</select></Field><div className="form-grid"><Field label="Start time"><input className="input" type="time" required value={schedule.start_time} onChange={(e) => setSchedule({ ...schedule, start_time: e.target.value })}/></Field><Field label="End time"><input className="input" type="time" required value={schedule.end_time} onChange={(e) => setSchedule({ ...schedule, end_time: e.target.value })}/></Field></div><Field label="Slot duration"><select className="select" value={schedule.slot_minutes} onChange={(e) => setSchedule({ ...schedule, slot_minutes: e.target.value })}><option value="15">15 minutes</option><option value="20">20 minutes</option><option value="30">30 minutes</option><option value="45">45 minutes</option><option value="60">60 minutes</option></select></Field></div><FormActions onCancel={() => setAvailabilityModal(false)} saving={saving} submitLabel="Save availability"/></form></Modal>
  </>;
}
