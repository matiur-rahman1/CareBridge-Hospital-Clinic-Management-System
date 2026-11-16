import { useCallback, useEffect, useState } from 'react';
import { Eye, Pencil, Plus, Search, Trash2, UserPlus } from 'lucide-react';
import { api, getErrorMessage, getList, resources } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { dateLabel, initials, titleCase } from '../utils/format';
import { Badge, Button, EmptyState, Field, FormActions, Modal, PageHeader, SearchInput, SectionCard, Table } from '../components/UI';

const emptyForm = { full_name: '', email: '', phone: '', date_of_birth: '', gender: '', address: '', blood_group: 'UNKNOWN' };

export default function PatientsPage() {
  const { user } = useAuth();
  const { notify } = useToast();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [gender, setGender] = useState('');
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [detail, setDetail] = useState(null);
  const [history, setHistory] = useState({ appointments: [], prescriptions: [], invoices: [] });
  const canManage = ['ADMIN', 'RECEPTIONIST'].includes(user?.role);

  const load = useCallback(async () => {
    setLoading(true);
    try { setRows(await getList(resources.patients, { search, gender: gender || undefined, ordering: '-registration_date' })); }
    catch (error) { notify(getErrorMessage(error), 'error'); }
    finally { setLoading(false); }
  }, [search, gender, notify]);
  useEffect(() => { const timer = window.setTimeout(load, 220); return () => window.clearTimeout(timer); }, [load]);

  const openCreate = () => { setEditing(null); setForm(emptyForm); setModal(true); };
  const openEdit = (row) => { setEditing(row); setForm({ ...emptyForm, ...row, date_of_birth: row.date_of_birth || '', email: row.email || '' }); setModal(true); };
  const submit = async (event) => {
    event.preventDefault(); setSaving(true);
    const payload = { ...form, email: form.email || null, date_of_birth: form.date_of_birth || null };
    try { if (editing) await api.patch(`${resources.patients}${editing.id}/`, payload); else await api.post(resources.patients, payload); notify(editing ? 'Patient profile updated.' : 'Patient registered successfully.'); setModal(false); await load(); }
    catch (error) { notify(getErrorMessage(error), 'error'); }
    finally { setSaving(false); }
  };
  const remove = async (row) => {
    if (!window.confirm(`Delete ${row.full_name}? This cannot be undone.`)) return;
    try { await api.delete(`${resources.patients}${row.id}/`); notify('Patient record deleted.'); await load(); }
    catch (error) { notify(getErrorMessage(error), 'error'); }
  };
  const openDetail = async (row) => {
    setDetail(row); setHistory({ appointments: [], prescriptions: [], invoices: [] });
    try {
      const [appointments, prescriptions, invoices] = await Promise.all([
        getList(resources.appointments, { patient: row.id, ordering: '-appointment_date' }),
        getList(resources.prescriptions, { patient: row.id }),
        getList(resources.invoices, { patient: row.id }),
      ]);
      setHistory({ appointments, prescriptions, invoices });
    } catch (error) { notify(getErrorMessage(error), 'error'); }
  };
  const columns = [
    { key: 'patient', label: 'Patient', render: (row) => <div className="table-person"><div className="avatar avatar-tiny">{initials(row.full_name)}</div><div><strong>{row.full_name}</strong><small>{row.patient_id}</small></div></div> },
    { key: 'phone', label: 'Contact', render: (row) => <div><strong>{row.phone || '—'}</strong><small>{row.email || 'No email'}</small></div> },
    { key: 'gender', label: 'Gender', render: (row) => row.gender ? titleCase(row.gender) : '—' },
    { key: 'blood_group', label: 'Blood group', render: (row) => <Badge status="neutral">{row.blood_group === 'UNKNOWN' ? 'Unknown' : row.blood_group}</Badge> },
    { key: 'registration_date', label: 'Registered', render: (row) => dateLabel(row.registration_date) },
    { key: 'actions', label: '', render: (row) => <div className="row-actions"><button className="icon-btn" onClick={() => openDetail(row)} title="View patient"><Eye size={16}/></button>{canManage && <><button className="icon-btn" onClick={() => openEdit(row)} title="Edit patient"><Pencil size={15}/></button><button className="icon-btn icon-danger" onClick={() => remove(row)} title="Delete patient"><Trash2 size={15}/></button></>}</div> },
  ];

  return <>
    <PageHeader eyebrow="PEOPLE & RECORDS" title="Patient management" description="A clear, connected view of every patient in your care." actions={canManage && <Button onClick={openCreate}><UserPlus size={16}/> Register patient</Button>} />
    <SectionCard title="Patient directory" subtitle={`${rows.length} patient records`}>
      <div className="toolbar"><SearchInput value={search} onChange={setSearch} placeholder="Search by name, patient ID, email or phone..."/><select className="select compact-select" value={gender} onChange={(e) => setGender(e.target.value)}><option value="">All genders</option><option value="MALE">Male</option><option value="FEMALE">Female</option><option value="OTHER">Other</option><option value="PREFER_NOT_TO_SAY">Prefer not to say</option></select></div>
      <Table columns={columns} rows={rows} loading={loading} emptyTitle="No patients found" emptyDescription="Try adjusting your search or register a new patient." />
    </SectionCard>

    <Modal open={modal} onClose={() => setModal(false)} title={editing ? 'Edit patient profile' : 'Register a patient'} description="Patient details are securely stored in your CareBridge records." wide>
      <form onSubmit={submit}><div className="form-grid"><Field label="Full name" required><input className="input" required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} placeholder="e.g. Ayesha Rahman" /></Field><Field label="Email address"><input className="input" type="email" value={form.email || ''} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="patient@email.com" /></Field><Field label="Phone number"><input className="input" value={form.phone || ''} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="+880 1XXXXXXXXX" /></Field><Field label="Date of birth"><input className="input" type="date" value={form.date_of_birth || ''} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} /></Field><Field label="Gender"><select className="select" value={form.gender || ''} onChange={(e) => setForm({ ...form, gender: e.target.value })}><option value="">Select gender</option><option value="MALE">Male</option><option value="FEMALE">Female</option><option value="OTHER">Other</option><option value="PREFER_NOT_TO_SAY">Prefer not to say</option></select></Field><Field label="Blood group"><select className="select" value={form.blood_group || 'UNKNOWN'} onChange={(e) => setForm({ ...form, blood_group: e.target.value })}>{['UNKNOWN','A+','A-','B+','B-','AB+','AB-','O+','O-'].map((v) => <option key={v} value={v}>{v === 'UNKNOWN' ? 'Unknown' : v}</option>)}</select></Field><Field label="Address" className="field-span-2"><textarea className="textarea" rows="3" value={form.address || ''} onChange={(e) => setForm({ ...form, address: e.target.value })} placeholder="Street, city, postal code" /></Field></div><FormActions onCancel={() => setModal(false)} saving={saving} submitLabel={editing ? 'Save patient' : 'Register patient'} /></form>
    </Modal>

    <Modal open={!!detail} onClose={() => setDetail(null)} title="Patient record" description={detail ? `${detail.patient_id} · Registered ${dateLabel(detail.registration_date)}` : ''} wide>
      {detail && <><div className="patient-detail-head"><div className="avatar avatar-large">{initials(detail.full_name)}</div><div><h3>{detail.full_name}</h3><p>{detail.email || 'No email provided'} · {detail.phone || 'No phone provided'}</p><span>{detail.gender ? titleCase(detail.gender) : 'Gender not specified'} · {detail.blood_group === 'UNKNOWN' ? 'Blood group unknown' : detail.blood_group}</span></div></div><div className="detail-stats"><div><strong>{history.appointments.length}</strong><span>Appointments</span></div><div><strong>{history.prescriptions.length}</strong><span>Prescriptions</span></div><div><strong>{history.invoices.length}</strong><span>Invoices</span></div></div><div className="detail-columns"><div><h4>Recent appointments</h4>{history.appointments.slice(0, 5).map((item) => <div className="mini-record" key={item.id}><span>{dateLabel(item.appointment_date)} · {item.doctor_name}</span><Badge status={item.status.toLowerCase()}>{titleCase(item.status)}</Badge></div>)}{!history.appointments.length && <small className="muted">No appointment history.</small>}</div><div><h4>Recent prescriptions</h4>{history.prescriptions.slice(0, 5).map((item) => <div className="mini-record" key={item.id}><span>{item.diagnosis || 'Prescription'} · {dateLabel(item.prescription_date)}</span></div>)}{!history.prescriptions.length && <small className="muted">No prescriptions recorded.</small>}<h4 className="mt-5">Billing history</h4>{history.invoices.slice(0, 4).map((item) => <div className="mini-record" key={item.id}><span>{item.invoice_number} · ৳{item.total_amount}</span><Badge status={item.payment_status.toLowerCase()}>{titleCase(item.payment_status)}</Badge></div>)}{!history.invoices.length && <small className="muted">No invoices recorded.</small>}</div></div></>}
    </Modal>
  </>;
}
