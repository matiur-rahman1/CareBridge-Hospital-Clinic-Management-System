import { useEffect, useState } from 'react';
import { Activity, ArrowUpRight, CalendarCheck, CalendarClock, ChevronRight, CircleDollarSign, Clock3, FileText, Plus, Stethoscope, Users } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Bar, BarChart } from 'recharts';
import { Link } from 'react-router-dom';
import { api, getErrorMessage } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { money, dateLabel, timeLabel, titleCase, statusTone } from '../utils/format';
import { Badge, Button, PageHeader, SectionCard, StatCard, Table, Loading } from '../components/UI';

export default function DashboardPage() {
  const { user } = useAuth();
  const { notify } = useToast();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    api.get('/dashboard/summary/').then(({ data }) => { if (active) setSummary(data); })
      .catch((error) => notify(getErrorMessage(error), 'error'))
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [notify]);

  if (loading) return <Loading />;
  const appointments = summary?.recent_appointments || [];
  const monthData = summary?.monthly_appointments || [];
  const revenueData = (summary?.monthly_revenue || []).map((row) => ({ ...row, amount: Number(row.amount) }));
  const isPatient = user?.role === 'PATIENT';
  const isDoctor = user?.role === 'DOCTOR';
  const stats = [
    { label: isPatient ? 'Recent appointments' : isDoctor ? 'Recent appointments' : 'Total patients', value: isPatient || isDoctor ? appointments.length : summary?.total_patients ?? 0, detail: isPatient ? 'In your recent activity' : isDoctor ? 'Recent appointments' : 'Registered patient records', icon: Users, tone: 'teal' },
    { label: isPatient ? 'Available doctors' : isDoctor ? 'My patients' : 'Active doctors', value: isDoctor ? (summary?.total_patients ?? 0) : (summary?.total_doctors ?? 0), detail: isPatient ? 'Ready to care for you' : isDoctor ? 'Across your appointments' : 'Care professionals', icon: Stethoscope, tone: 'blue' },
    { label: "Today's appointments", value: summary?.today_appointments ?? 0, detail: 'Scheduled for today', icon: CalendarCheck, tone: 'purple' },
    { label: isPatient ? 'Completed visits' : 'Pending appointments', value: isPatient ? appointments.filter((a) => a.status === 'COMPLETED').length : summary?.pending_appointments ?? 0, detail: isPatient ? 'Your care history' : 'Awaiting confirmation', icon: Clock3, tone: 'amber' },
  ];
  const columns = [
    { key: 'patient_name', label: 'Patient', render: (row) => <div className="table-person"><div className="avatar avatar-tiny">{(row.patient_name || 'P').split(' ').map((p) => p[0]).slice(0, 2).join('')}</div><div><strong>{row.patient_name}</strong><small>{row.patient_code}</small></div></div> },
    { key: 'doctor_name', label: 'Doctor', render: (row) => row.doctor_name },
    { key: 'appointment_date', label: 'Date & time', render: (row) => <div><strong>{dateLabel(row.appointment_date)}</strong><small>{timeLabel(row.start_time)}</small></div> },
    { key: 'status', label: 'Status', render: (row) => <Badge status={statusTone(row.status)}>{titleCase(row.status)}</Badge> },
  ];
  const quickLinks = [
    { label: 'Book appointment', description: 'Schedule a patient visit', icon: CalendarCheck, to: '/appointments', roles: ['ADMIN', 'RECEPTIONIST', 'PATIENT'] },
    { label: 'Register patient', description: 'Add a new patient record', icon: Users, to: '/patients', roles: ['ADMIN', 'RECEPTIONIST'] },
    { label: 'Create prescription', description: 'Write a treatment plan', icon: FileText, to: '/prescriptions', roles: ['ADMIN', 'DOCTOR'] },
    { label: 'Create invoice', description: 'Generate a patient bill', icon: CircleDollarSign, to: '/billing', roles: ['ADMIN', 'RECEPTIONIST'] },
  ].filter((item) => item.roles.includes(user?.role));

  return <>
    <PageHeader eyebrow="YOUR WORKSPACE" title={`Good ${new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'}, ${user?.first_name || 'there'}`} description="Here’s what’s happening across your care workspace today." actions={<Button variant="soft" onClick={() => window.location.reload()}><Activity size={16} /> Refresh data</Button>} />
    <div className="stats-grid">{stats.map((stat) => <StatCard key={stat.label} {...stat} />)}{!isPatient && !isDoctor && <StatCard label="Total revenue" value={money(summary?.total_revenue)} detail="Payments received" icon={CircleDollarSign} tone="green" />}</div>
    <div className="dashboard-grid">
      <SectionCard title="Appointment activity" subtitle="Monthly appointment volume"><div className="chart-area"><ResponsiveContainer width="100%" height={250}><AreaChart data={monthData}><defs><linearGradient id="appointmentFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#1D9C98" stopOpacity={0.23}/><stop offset="95%" stopColor="#1D9C98" stopOpacity={0.01}/></linearGradient></defs><CartesianGrid stroke="#edf1f4" vertical={false}/><XAxis dataKey="month" tickFormatter={(value) => new Date(`${value}-01`).toLocaleDateString('en', { month: 'short' })} axisLine={false} tickLine={false} tick={{ fill: '#8a98a9', fontSize: 11 }}/><YAxis axisLine={false} tickLine={false} tick={{ fill: '#8a98a9', fontSize: 11 }}/><Tooltip labelFormatter={(value) => new Date(`${value}-01`).toLocaleDateString('en', { month: 'long', year: 'numeric' })} contentStyle={{ borderRadius: 12, border: '1px solid #e9eef2', boxShadow: '0 8px 20px rgba(0,0,0,.06)' }}/><Area type="monotone" dataKey="count" stroke="#1D9C98" strokeWidth={2.5} fill="url(#appointmentFill)"/></AreaChart></ResponsiveContainer></div></SectionCard>
      <SectionCard title="Revenue overview" subtitle="Monthly payments received"><div className="revenue-total"><strong>{money(summary?.total_revenue)}</strong><span><ArrowUpRight size={14}/> Lifetime collected</span></div><div className="chart-area"><ResponsiveContainer width="100%" height={185}><BarChart data={revenueData}><CartesianGrid stroke="#edf1f4" vertical={false}/><XAxis dataKey="month" tickFormatter={(value) => new Date(`${value}-01`).toLocaleDateString('en', { month: 'short' })} axisLine={false} tickLine={false} tick={{ fill: '#8a98a9', fontSize: 11 }}/><YAxis hide/><Tooltip formatter={(value) => money(value)} contentStyle={{ borderRadius: 12, border: '1px solid #e9eef2' }}/><Bar dataKey="amount" fill="#6d8fe8" radius={[5,5,0,0]} maxBarSize={26}/></BarChart></ResponsiveContainer></div></SectionCard>
    </div>
    <div className="dashboard-bottom-grid"><SectionCard title="Recent appointments" subtitle="The latest activity in your clinic" action={<Link className="text-link" to="/appointments">View all <ChevronRight size={15}/></Link>}><Table columns={columns} rows={appointments.slice(0, 6)} emptyTitle="No appointments yet" emptyDescription="New appointment activity will show up here." /></SectionCard><SectionCard title="Quick actions" subtitle="Get things done faster"><div className="quick-actions">{quickLinks.map(({ label, description, icon: Icon, to }) => <Link to={to} className="quick-action" key={label}><div className="quick-action-icon"><Icon size={18}/></div><div><strong>{label}</strong><span>{description}</span></div><ChevronRight size={16}/></Link>)}</div></SectionCard></div>
  </>;
}
