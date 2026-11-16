import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { authApi, tokenStorage, getErrorMessage } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);

  const logout = useCallback(() => {
    tokenStorage.clear();
    setUser(null);
  }, []);

  useEffect(() => {
    const handleExpired = () => setUser(null);
    window.addEventListener('carebridge:session-expired', handleExpired);
    const loadUser = async () => {
      if (!localStorage.getItem(tokenStorage.ACCESS_KEY)) {
        setInitializing(false);
        return;
      }
      try {
        const { data } = await authApi.me();
        setUser(data);
      } catch {
        tokenStorage.clear();
        setUser(null);
      } finally {
        setInitializing(false);
      }
    };
    loadUser();
    return () => window.removeEventListener('carebridge:session-expired', handleExpired);
  }, []);

  const login = useCallback(async (email, password) => {
    try {
      const { data } = await authApi.login({ email, password });
      tokenStorage.set(data.access, data.refresh);
      setUser(data.user);
      return data.user;
    } catch (error) {
      throw new Error(getErrorMessage(error));
    }
  }, []);

  const value = useMemo(() => ({ user, login, logout, initializing, setUser }), [user, login, logout, initializing]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside AuthProvider');
  return context;
}
