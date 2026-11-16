export const money = (value) => new Intl.NumberFormat('en-BD', { style: 'currency', currency: 'BDT', maximumFractionDigits: 0 }).format(Number(value || 0));
export const dateLabel = (value, options = { day: '2-digit', month: 'short', year: 'numeric' }) => value ? new Date(`${String(value).slice(0, 10)}T00:00:00`).toLocaleDateString('en-GB', options) : '—';
export const timeLabel = (value) => value ? new Date(`1970-01-01T${value}`).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) : '—';
export const initials = (name = '') => name.split(' ').filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase() || 'CB';
export const statusTone = (status = '') => ({ PENDING: 'warning', CONFIRMED: 'info', COMPLETED: 'success', CANCELLED: 'danger', PAID: 'success', UNPAID: 'danger', PARTIALLY_PAID: 'warning' }[status] || 'neutral');
export const titleCase = (value = '') => value.toLowerCase().replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
export const todayISO = () => new Date().toLocaleDateString('en-CA');
