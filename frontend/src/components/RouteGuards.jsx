import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loading } from './UI';

export function RequireAuth({ allowedRoles }) {
  const { user, initializing } = useAuth();
  const location = useLocation();
  if (initializing) return <Loading />;
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;
  if (allowedRoles && !allowedRoles.includes(user.role)) return <Navigate to="/" replace />;
  return <Outlet />;
}
