import { useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity, Bell, CalendarDays, ChevronDown, ClipboardList, CreditCard, FileText,
  LayoutDashboard, LogOut, Menu, Stethoscope, Users, UserRound, X, HeartPulse,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { initials, titleCase } from '../utils/format';

const commonItems = [
  { label: 'Overview', to: '/', icon: LayoutDashboard, roles: ['ADMIN', 'RECEPTIONIST', 'DOCTOR', 'PATIENT'] },
  { label: 'Appointments', to: '/appointments', icon: CalendarDays, roles: ['ADMIN', 'RECEPTIONIST', 'DOCTOR', 'PATIENT'] },
  { label: 'Patients', to: '/patients', icon: Users, roles: ['ADMIN', 'RECEPTIONIST', 'DOCTOR'] },
  { label: 'Doctors', to: '/doctors', icon: Stethoscope, roles: ['ADMIN', 'RECEPTIONIST', 'PATIENT'] },
  { label: 'Prescriptions', to: '/prescriptions', icon: ClipboardList, roles: ['ADMIN', 'RECEPTIONIST', 'DOCTOR', 'PATIENT'] },
  { label: 'Billing & payments', to: '/billing', icon: CreditCard, roles: ['ADMIN', 'RECEPTIONIST', 'DOCTOR', 'PATIENT'] },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const { notify } = useToast();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const items = [...commonItems, { label: user?.role === 'PATIENT' ? 'Patient portal' : 'Doctor portal', to: '/portal', icon: UserRound, roles: ['DOCTOR', 'PATIENT'] }].filter((item) => item.roles.includes(user?.role));
  const pageTitle = [...commonItems, { to: '/profile', label: 'My profile' }].find((item) => item.to === location.pathname)?.label || 'CareBridge';

  const handleLogout = () => { logout(); navigate('/login', { replace: true }); };
  const sidebar = <>
    <div className="brand-lockup"><div className="brand-mark"><HeartPulse size={22} /></div><div><div className="brand-name">carebridge<span>.</span></div><div className="brand-caption">CARE, CONNECTED.</div></div><button className="sidebar-close" onClick={() => setMobileOpen(false)} aria-label="Close menu"><X size={18} /></button></div>
    <div className="sidebar-label">WORKSPACE</div>
    <nav className="side-nav">
      {items.map(({ label, to, icon: Icon }) => <NavLink key={to} to={to} end={to === '/'} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><Icon size={18} /><span>{label}</span>{label === 'Appointments' && <span className="nav-dot" />}</NavLink>)}
    </nav>
    <div className="sidebar-bottom"><div className="help-card"><div className="help-icon"><Activity size={17} /></div><strong>Need a hand?</strong><span>Our support team is here to help.</span><a href="mailto:support@carebridge.demo">Contact support <span>↗</span></a></div><div className="sidebar-user"><div className="avatar avatar-small">{initials(user?.full_name || user?.first_name)}</div><div className="sidebar-user-info"><strong>{user?.full_name || user?.first_name}</strong><span>{titleCase(user?.role || '')}</span></div><button className="icon-btn logout-btn" onClick={handleLogout} title="Sign out"><LogOut size={17} /></button></div></div>
  </>;

  return <div className="app-shell">
    {mobileOpen && <div className="mobile-scrim" onClick={() => setMobileOpen(false)} />}
    <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>{sidebar}</aside>
    <div className="main-shell">
      <header className="topbar"><div className="topbar-left"><button className="mobile-menu icon-btn" onClick={() => setMobileOpen(true)} aria-label="Open menu"><Menu size={20} /></button><div className="breadcrumbs"><span>Workspace</span><b>/</b><strong>{pageTitle}</strong></div></div><div className="topbar-right"><div className="topbar-date">{new Date().toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })}</div><button className="icon-btn notification-btn" aria-label="Notifications" title="Notifications" onClick={() => notify('You are all caught up. No new notifications.', 'info')}><Bell size={18} /></button><div className="profile-wrap"><button className="profile-trigger" onClick={() => setProfileOpen((open) => !open)}><div className="avatar avatar-small">{initials(user?.full_name || user?.first_name)}</div><span>{user?.first_name}</span><ChevronDown size={15} /></button>{profileOpen && <div className="profile-menu"><button onClick={() => { setProfileOpen(false); navigate('/profile'); }}><UserRound size={16} /> My profile</button><button onClick={handleLogout}><LogOut size={16} /> Sign out</button></div>}</div></div></header>
      <main className="page-content"><Outlet /></main>
      <footer className="app-footer"><span>© {new Date().getFullYear()} CareBridge Health Systems</span><span>Built for better care <HeartPulse size={13} /></span></footer>
    </div>
  </div>;
}
