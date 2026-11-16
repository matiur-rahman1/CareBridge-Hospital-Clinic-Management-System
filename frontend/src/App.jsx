import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { RequireAuth } from './components/RouteGuards';
import AppLayout from './layouts/AppLayout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import PatientsPage from './pages/PatientsPage';
import DoctorsPage from './pages/DoctorsPage';
import AppointmentsPage from './pages/AppointmentsPage';
import PrescriptionsPage from './pages/PrescriptionsPage';
import BillingPage from './pages/BillingPage';
import PortalPage from './pages/PortalPage';
import ProfilePage from './pages/ProfilePage';
import { EmptyState } from './components/UI';

function NotFound() {
  return <div className="not-found"><EmptyState title="Page not found" description="The page you are looking for does not exist." action={<a className="text-link" href="/">Return to dashboard</a>} /></div>;
}

export default function App() {
  return <BrowserRouter><AuthProvider><ToastProvider><Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route element={<RequireAuth />}>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route element={<RequireAuth allowedRoles={['ADMIN', 'RECEPTIONIST', 'DOCTOR']} />}><Route path="patients" element={<PatientsPage />} /></Route>
        <Route element={<RequireAuth allowedRoles={['ADMIN', 'RECEPTIONIST', 'PATIENT']} />}><Route path="doctors" element={<DoctorsPage />} /></Route>
        <Route path="appointments" element={<AppointmentsPage />} />
        <Route path="prescriptions" element={<PrescriptionsPage />} />
        <Route path="billing" element={<BillingPage />} />
        <Route element={<RequireAuth allowedRoles={['DOCTOR', 'PATIENT']} />}><Route path="portal" element={<PortalPage />} /></Route>
        <Route path="profile" element={<ProfilePage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Route>
  </Routes></ToastProvider></AuthProvider></BrowserRouter>;
}
