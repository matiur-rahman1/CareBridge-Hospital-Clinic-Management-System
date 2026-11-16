import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { CheckCircle2, CircleAlert, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const notify = useCallback((message, type = 'success') => {
    const id = `${Date.now()}-${Math.random()}`;
    setToasts((items) => [...items, { id, message, type }]);
    window.setTimeout(() => setToasts((items) => items.filter((item) => item.id !== id)), 4200);
  }, []);
  const remove = (id) => setToasts((items) => items.filter((item) => item.id !== id));
  const value = useMemo(() => ({ notify }), [notify]);
  const icons = { success: CheckCircle2, error: CircleAlert, info: Info };
  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-stack" aria-live="polite">
        {toasts.map((toast) => {
          const Icon = icons[toast.type] || Info;
          return <div className={`toast toast-${toast.type}`} key={toast.id}><Icon size={18} /><span>{toast.message}</span><button onClick={() => remove(toast.id)} aria-label="Dismiss notification"><X size={15} /></button></div>;
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used inside ToastProvider');
  return context;
}
