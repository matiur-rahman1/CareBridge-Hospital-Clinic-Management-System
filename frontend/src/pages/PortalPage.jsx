import { useCallback, useEffect, useState } from 'react';
import { ArrowUpRight, CalendarCheck, CalendarPlus, ClipboardList, Clock3, CreditCard, HeartPulse, Users } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api, getErrorMessage, getList, resources } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { Badge, Button, PageHeader, SectionCard, StatCard, Table, Loading } from '../components/UI';
import { dateLabel, money, timeLabel, titleCase } from '../utils/format';

export default function PortalPage() {
  const { user } = useAuth();
  const { notify } = useToast();
  const isPatient = user?.role === 'PATIENT';
  const [profile, setProfile] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const tasks = isPatient
        ? [getList(resources.patients), getList(resources.appointments, { ordering: '-appointment_date' }), getList(resources.prescriptions), getList(resources.invoices)]
        : [getList(resources.doctors), getList(resources.appointments, { ordering: 'appointment_date' }), getList(resources.prescriptions), getList(resources.patients)];
      const result = await Promise.all(tasks);
      setProfile(result[0][0] || null); setAppointments(result[1]); setPrescriptions(result[2]);
      if (isPatient) setInvoices(result[3]); else setPatients(result[3]);
    } catch (error) { notify(getErrorMessage(error), 'error'); }
    finally { setLoading(false); }
  }, [isPatient, notify]);
  useEffect(() => { load(); }, [load]);

  if (loading) return <Loading label="Loading your personal portal..." />;
  const today = new Date().toLocaleDateString('en-CA');
  const futureAppointments = appointments.filter((item) => item.appointment_date >= today && !['CANCELLED', 'COMPLETED'].includes(item.status));
  const pastAppointments = appointments.filter((item) => item.appointment_date < today || ['CANCELLED', 'COMPLETED'].includes(item.status));
  const patientColumns = [
    { key: 'appointment_date', label: 'Date & time', render: (row) => <div><strong>{dateLabel(row.appointment_date)}</strong><small>{timeLabel(row.start_time)}</small></div> },
    { key: 'doctor_name', label: 'Doctor' },
    { key: 'reason', label: 'Visit reason', render: (row) => row.reason || 'General consultation' },
    { key: 'status', label: 'Status', render: (row) => <Badge status={row.status.toLowerCase()}>{titleCase(row.status)}</Badge> },
  ];
  const doctorColumns = [
    { key: 'appointment_date', label: 'Date & time', render: (row) => <div><strong>{dateLabel(row.appointment_date)}</strong><small>{timeLabel(row.start_time)}</small></div> },
    { key: 'patient_name', label: 'Patient', render: (row) => <div><strong>{row.patient_name}</strong><small>{row.patient_code}</small></div> },
    { key: 'reason', label: 'Visit reason', render: (row) => row.reason || 'General consultation' },
    { key: 'status', label: 'Status', render: (row) => <Badge status={row.status.toLowerCase()}>{titleCase(row.status)}</Badge> },
  ];

  return <>
    <PageHeader eyebrow={isPatient ? 'PATIENT PORTAL' : 'DOCTOR PORTAL'} title={isPatient ? `Hello, ${user?.first_name}` : `Welcome, Dr. ${profile?.full_name || user?.first_name}`} description={isPatient ? 'Your health journey, appointments and care documents in one place.' : 'Your daily schedule, assigned patients and clinical work at a glance.'} actions={isPatient ? <Link to="/appointments"><Button><CalendarPlus size={16}/> Book a visit</Button></Link> : <Link to="/appointments"><Button variant="outline"><CalendarCheck size={16}/> View schedule</Button></Link>} />
    <div className="portal-welcome-card"><div className="portal-welcome-content"><div className="portal-welcome-icon"><HeartPulse size={22}/></div><div><span>{isPatient ? 'YOUR CARE, AT A GLANCE' : 'YOUR CLINICAL WORKSPACE'}</span><h2>{isPatient ? 'Stay close to your care.' : 'Every visit makes a difference.'}</h2><p>{isPatient ? 'Find upcoming visits, keep track of prescriptions and know where your payments stand.' : 'Your appointments and patient care are organized to help you focus on what matters.'}</p></div></div><div className="portal-welcome-decoration"><div className="portal-ring ring-a"/><div className="portal-ring ring-b"/><HeartPulse size={82}/></div></div>
    <div className="stats-grid stats-grid-three">{isPatient ? <><StatCard label="Upcoming visits" value={futureAppointments.length} detail="Scheduled appointments" icon={CalendarCheck} tone="teal"/><StatCard label="Prescriptions" value={prescriptions.length} detail="Available treatment records" icon={ClipboardList} tone="purple"/><StatCard label="Outstanding balance" value={money(invoices.reduce((sum, invoice) => sum + Number(invoice.balance_due), 0))} detail="Across your invoices" icon={CreditCard} tone="amber"/></> : <><StatCard label="Upcoming appointments" value={futureAppointments.length} detail="In your schedule" icon={CalendarCheck} tone="teal"/><StatCard label="Assigned patients" value={patients.length} detail="Patients connected to your care" icon={Users} tone="blue"/><StatCard label="Prescriptions written" value={prescriptions.length} detail="Your treatment records" icon={ClipboardList} tone="purple"/></>}</div>
    <SectionCard title={isPatient ? 'Upcoming appointments' : 'Your upcoming schedule'} subtitle="Your next scheduled visits" action={<Link className="text-link" to="/appointments">Open appointments <ArrowUpRight size={14}/></Link>}><Table columns={isPatient ? patientColumns : doctorColumns} rows={futureAppointments.slice(0, 8)} emptyTitle="No upcoming appointments" emptyDescription={isPatient ? 'When you book a visit, the details will appear here.' : 'Your upcoming appointments will appear here.'}/></SectionCard>
    <div className="dashboard-bottom-grid"><SectionCard title={isPatient ? 'Recent prescriptions' : 'Recently written prescriptions'} subtitle="Treatment history"><div className="portal-record-list">{prescriptions.slice(0, 5).map((item) => <div className="portal-record" key={item.id}><div className="portal-record-icon"><ClipboardList size={17}/></div><div><strong>{item.diagnosis || 'Prescription'}</strong><span>{isPatient ? `Dr. ${item.doctor_name}` : item.patient_name} · {dateLabel(item.prescription_date)}</span></div><span className="record-count">{item.medicines?.length || 0} meds</span></div>)}{!prescriptions.length && <div className="muted py-5">No prescription records yet.</div>}</div><Link className="text-link mt-3 inline-flex" to="/prescriptions">View all prescriptions <ArrowUpRight size={14}/></Link></SectionCard>{isPatient ? <SectionCard title="Billing summary" subtitle="Your latest invoice activity"><div className="portal-record-list">{invoices.slice(0, 5).map((item) => <div className="portal-record" key={item.id}><div className="portal-record-icon"><CreditCard size={17}/></div><div><strong>{item.invoice_number}</strong><span>{dateLabel(item.issue_date)} · {money(item.total_amount)}</span></div><Badge status={item.payment_status.toLowerCase().replace('_','-')}>{titleCase(item.payment_status)}</Badge></div>)}{!invoices.length && <div className="muted py-5">No invoices available.</div>}</div><Link className="text-link mt-3 inline-flex" to="/billing">View billing history <ArrowUpRight size={14}/></Link></SectionCard> : <SectionCard title="Care team shortcuts" subtitle="Quick access to your clinical tasks"><div className="quick-actions"><Link to="/prescriptions" className="quick-action"><div className="quick-action-icon"><ClipboardList size={18}/></div><div><strong>Create a prescription</strong><span>Prepare a patient's treatment plan</span></div><ArrowUpRight size={15}/></Link><Link to="/appointments" className="quick-action"><div className="quick-action-icon"><CalendarCheck size={18}/></div><div><strong>Review appointments</strong><span>Check visit details and mark complete</span></div><ArrowUpRight size={15}/></Link><Link to="/patients" className="quick-action"><div className="quick-action-icon"><Users size={18}/></div><div><strong>Assigned patients</strong><span>Open patient records and history</span></div><ArrowUpRight size={15}/></Link></div></SectionCard>}</div>
    <SectionCard title="Appointment history" subtitle="Previously completed or cancelled visits"><Table columns={isPatient ? patientColumns : doctorColumns} rows={pastAppointments.slice(0, 6)} emptyTitle="No visit history yet" emptyDescription="Previous visits will appear here."/></SectionCard>
  </>;
}
