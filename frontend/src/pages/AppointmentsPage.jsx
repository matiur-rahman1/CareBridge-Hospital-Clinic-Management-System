import { useCallback, useEffect, useMemo, useState } from 'react';
import { addDays, format, isSameMonth, isToday, startOfMonth, startOfWeek } from 'date-fns';
import { CalendarDays, ChevronLeft, ChevronRight, Clock3, Plus } from 'lucide-react';
import { api, getErrorMessage, getList, resources } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { dateLabel, timeLabel, titleCase } from '../utils/format';
import { buildAvailableSlots } from '../utils/schedule';
import { Badge, Button, Field, FormActions, Modal, PageHeader, SearchInput, SectionCard, Table } from '../components/UI';

const blank = { patient: '', doctor: '', appointment_date: '', slot: '', reason: '' };
const statusOptions = ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED'];

export default function AppointmentsPage() {
  const { user } = useAuth();
  const { notify } = useToast();
  const [rows, setRows] = useState([]);
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [availability, setAvailability] = useState([]);
  const [slotAppointments, setSlotAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [month, setMonth] = useState(startOfMonth(new Date()));
  const [selectedDay, setSelectedDay] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [calendarMode, setCalendarMode] = useState('month');
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState(blank);
  const [saving, setSaving] = useState(false);
  const canBook = ['ADMIN', 'RECEPTIONIST', 'PATIENT'].includes(user?.role);
  const isPatient = user?.role === 'PATIENT';
  const canManage = ['ADMIN', 'RECEPTIONIST'].includes(user?.role);
  const canComplete = user?.role === 'DOCTOR';

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [appointmentRows, patientRows, doctorRows, availabilityRows] = await Promise.all([
        getList(resources.appointments, { search, status: statusFilter || undefined, ordering: 'appointment_date' }),
        getList(resources.patients), getList(resources.doctors), getList(resources.availabilities, { is_active: true }),
      ]);
      setRows(appointmentRows); setPatients(patientRows); setDoctors(doctorRows); setAvailability(availabilityRows);
    } catch (error) { notify(getErrorMessage(error), 'error'); }
    finally { setLoading(false); }
  }, [search, statusFilter, notify]);
  useEffect(() => { const timer = window.setTimeout(load, 200); return () => window.clearTimeout(timer); }, [load]);

  const openBooking = () => {
    setForm({ ...blank, patient: isPatient ? String(patients[0]?.id || '') : '', doctor: String(doctors.find((doctor) => doctor.is_active)?.id || '') });
    setModal(true);
  };
  useEffect(() => {
    let active = true;
    if (!modal || !form.doctor || !form.appointment_date) {
      setSlotAppointments([]);
      return () => { active = false; };
    }
    getList(resources.appointments, { doctor: form.doctor, appointment_date: form.appointment_date })
      .then((items) => { if (active) setSlotAppointments(items); })
      .catch((error) => { if (active) notify(getErrorMessage(error), 'error'); });
    return () => { active = false; };
  }, [modal, form.doctor, form.appointment_date, notify]);

  const slots = useMemo(() => buildAvailableSlots({
    availability,
    appointments: slotAppointments,
    doctorId: form.doctor,
    date: form.appointment_date,
  }).map((slot) => ({
    ...slot,
    label: `${timeLabel(slot.start_time)} – ${timeLabel(slot.end_time)}`,
  })), [availability, slotAppointments, form.doctor, form.appointment_date]);
  const saveBooking = async (event) => {
    event.preventDefault();
    if (!form.slot) { notify('Choose an available appointment slot.', 'error'); return; }
    const [start_time, end_time] = form.slot.split('|');
    setSaving(true);
    try { await api.post(resources.appointments, { patient: Number(form.patient), doctor: Number(form.doctor), appointment_date: form.appointment_date, start_time, end_time, reason: form.reason }); notify('Appointment booked successfully.'); setModal(false); await load(); }
    catch (error) { notify(getErrorMessage(error), 'error'); }
    finally { setSaving(false); }
  };
  const updateStatus = async (row, status) => {
    try { await api.patch(`${resources.appointments}${row.id}/`, { status }); notify(`Appointment marked ${titleCase(status).toLowerCase()}.`); await load(); }
    catch (error) { notify(getErrorMessage(error), 'error'); }
  };
  const deleteAppointment = async (row) => {
    if (!window.confirm('Delete this appointment?')) return;
    try { await api.delete(`${resources.appointments}${row.id}/`); notify('Appointment removed.'); await load(); }
    catch (error) { notify(getErrorMessage(error), 'error'); }
  };

  const calendarStart = startOfWeek(startOfMonth(month), { weekStartsOn: 1 });
  const calendarDays = Array.from({ length: 42 }, (_, index) => addDays(calendarStart, index));
  const dayAppointments = rows.filter((row) => row.appointment_date === selectedDay);
  const columns = [
    { key: 'patient_name', label: 'Patient', render: (row) => <div><strong>{row.patient_name}</strong><small>{row.patient_code}</small></div> },
    { key: 'doctor_name', label: 'Doctor', render: (row) => row.doctor_name },
    { key: 'appointment_date', label: 'Date & time', render: (row) => <div><strong>{dateLabel(row.appointment_date)}</strong><small>{timeLabel(row.start_time)} – {timeLabel(row.end_time)}</small></div> },
    { key: 'reason', label: 'Reason', render: (row) => row.reason || 'General consultation' },
    { key: 'status', label: 'Status', render: (row) => <Badge status={row.status.toLowerCase()}>{titleCase(row.status)}</Badge> },
    { key: 'actions', label: '', render: (row) => <div className="row-actions">{canManage && row.status !== 'CANCELLED' && <select className="mini-select" aria-label="Change appointment status" value={row.status} onChange={(e) => updateStatus(row, e.target.value)}>{statusOptions.map((option) => <option value={option} key={option}>{titleCase(option)}</option>)}</select>}{canComplete && row.status !== 'COMPLETED' && row.status !== 'CANCELLED' && <button className="text-action" onClick={() => updateStatus(row, 'COMPLETED')}>Complete</button>}{isPatient && ['PENDING', 'CONFIRMED'].includes(row.status) && <button className="text-action text-danger" onClick={() => updateStatus(row, 'CANCELLED')}>Cancel</button>}{canManage && <button className="icon-btn icon-danger" onClick={() => deleteAppointment(row)} title="Delete appointment"><span>×</span></button>}</div> },
  ];

  return <>
    <PageHeader eyebrow="SCHEDULING" title="Appointments" description="Plan visits, manage schedules and keep every care team in sync." actions={canBook && <Button onClick={openBooking}><Plus size={16}/> Book appointment</Button>} />
    <div className="appointment-summary"><div><span>All appointments</span><strong>{rows.length}</strong></div><div><span>Pending</span><strong>{rows.filter((r) => r.status === 'PENDING').length}</strong></div><div><span>Confirmed</span><strong>{rows.filter((r) => r.status === 'CONFIRMED').length}</strong></div><div><span>Completed</span><strong>{rows.filter((r) => r.status === 'COMPLETED').length}</strong></div></div>
    <SectionCard title="Appointment calendar" subtitle="Select a date to review scheduled visits" action={<div className="calendar-switch"><button className={calendarMode === 'month' ? 'selected' : ''} onClick={() => setCalendarMode('month')}>Month</button><button className={calendarMode === 'list' ? 'selected' : ''} onClick={() => setCalendarMode('list')}>List</button></div>}>
      <div className="calendar-toolbar"><div className="calendar-month"><button className="icon-btn" onClick={() => setMonth((m) => new Date(m.getFullYear(), m.getMonth() - 1, 1))}><ChevronLeft size={18}/></button><strong>{format(month, 'MMMM yyyy')}</strong><button className="icon-btn" onClick={() => setMonth((m) => new Date(m.getFullYear(), m.getMonth() + 1, 1))}><ChevronRight size={18}/></button></div><Button variant="outline" size="sm" onClick={() => { setMonth(startOfMonth(new Date())); setSelectedDay(format(new Date(), 'yyyy-MM-dd')); }}>Today</Button></div>
      {calendarMode === 'month' && <div className="calendar-grid"><div className="calendar-weekdays">{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map((day) => <span key={day}>{day}</span>)}</div><div className="calendar-days">{calendarDays.map((day) => { const iso = format(day, 'yyyy-MM-dd'); const dayRows = rows.filter((r) => r.appointment_date === iso); return <button key={iso} className={`calendar-day ${!isSameMonth(day, month) ? 'outside-month' : ''} ${selectedDay === iso ? 'day-selected' : ''} ${isToday(day) ? 'day-today' : ''}`} onClick={() => setSelectedDay(iso)}><span>{format(day, 'd')}</span>{dayRows.slice(0, 3).map((r) => <i key={r.id} className={`calendar-event event-${r.status.toLowerCase()}`}>{r.patient_name}</i>)}{dayRows.length > 3 && <small>+{dayRows.length - 3} more</small>}</button>; })}</div></div>}
      {calendarMode === 'list' && <div className="toolbar"><SearchInput value={search} onChange={setSearch} placeholder="Search patients, doctors or reason..."/><select className="select compact-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}><option value="">All statuses</option>{statusOptions.map((s) => <option value={s} key={s}>{titleCase(s)}</option>)}</select></div>}
      {calendarMode === 'month' && <div className="selected-day-panel"><div className="selected-day-title"><div><strong>{dateLabel(selectedDay)}</strong><span>{dayAppointments.length} appointment{dayAppointments.length === 1 ? '' : 's'} scheduled</span></div></div>{dayAppointments.length ? dayAppointments.map((row) => <div className="day-appointment" key={row.id}><div className="day-time"><Clock3 size={15}/><span>{timeLabel(row.start_time)}</span></div><div className="day-appointment-main"><strong>{row.patient_name}</strong><span>with {row.doctor_name} · {row.reason || 'Consultation'}</span></div><Badge status={row.status.toLowerCase()}>{titleCase(row.status)}</Badge></div>) : <div className="calendar-empty">No appointments scheduled for this date.</div>}</div>}
      {calendarMode === 'list' && <Table columns={columns} rows={rows} loading={loading} emptyTitle="No appointments found" emptyDescription="Appointments will appear here when booked." />}
    </SectionCard>
    {calendarMode === 'month' && <SectionCard title="All appointments" subtitle="Your latest scheduled visits"><div className="toolbar"><SearchInput value={search} onChange={setSearch} placeholder="Search patients, doctors or reason..."/><select className="select compact-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}><option value="">All statuses</option>{statusOptions.map((s) => <option value={s} key={s}>{titleCase(s)}</option>)}</select></div><Table columns={columns} rows={rows} loading={loading} emptyTitle="No appointments found" emptyDescription="Appointments will appear here when booked."/></SectionCard>}

    <Modal open={modal} onClose={() => setModal(false)} title="Book an appointment" description="Choose a doctor and an available appointment slot." wide><form onSubmit={saveBooking}><div className="form-grid"><Field label="Patient" required><select className="select" required value={form.patient} disabled={isPatient} onChange={(e) => setForm({ ...form, patient: e.target.value })}><option value="">Select patient</option>{patients.map((p) => <option key={p.id} value={p.id}>{p.full_name} · {p.patient_id}</option>)}</select></Field><Field label="Doctor" required><select className="select" required value={form.doctor} onChange={(e) => setForm({ ...form, doctor: e.target.value, slot: '' })}><option value="">Select doctor</option>{doctors.filter((d) => d.is_active).map((d) => <option key={d.id} value={d.id}>Dr. {d.full_name} · {d.specialization}</option>)}</select></Field><Field label="Appointment date" required><input className="input" type="date" min={format(new Date(), 'yyyy-MM-dd')} required value={form.appointment_date} onChange={(e) => setForm({ ...form, appointment_date: e.target.value, slot: '' })}/></Field><Field label="Available time slot" required><select className="select" required value={form.slot} onChange={(e) => setForm({ ...form, slot: e.target.value })} disabled={!form.appointment_date || !form.doctor}><option value="">{!form.appointment_date ? 'Select a date first' : slots.length ? 'Choose a time' : 'No availability for this date'}</option>{slots.map((slot) => <option key={slot.value} value={slot.value}>{slot.label}</option>)}</select><small>Time slots are generated from the doctor's active weekly availability.</small></Field><Field label="Reason for visit" className="field-span-2"><textarea className="textarea" rows="3" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} placeholder="Briefly describe the reason for this appointment"/></Field></div>{form.doctor && form.appointment_date && !slots.length && <div className="form-hint-warning">No active availability is configured for this doctor on the selected weekday. Please choose another date or doctor.</div>}<FormActions onCancel={() => setModal(false)} saving={saving} submitLabel="Confirm booking"/></form></Modal>
  </>;
}
