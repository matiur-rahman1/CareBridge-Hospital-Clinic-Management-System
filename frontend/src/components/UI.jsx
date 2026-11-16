import { X, Search, LoaderCircle, Plus, FileSearch } from 'lucide-react';

export function PageHeader({ eyebrow = 'CAREBRIDGE', title, description, actions }) {
  return <div className="page-header"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1>{description && <p>{description}</p>}</div>{actions && <div className="page-actions">{actions}</div>}</div>;
}

export function Button({ children, variant = 'primary', size = 'md', className = '', ...props }) {
  return <button className={`btn btn-${variant} btn-${size} ${className}`} {...props}>{children}</button>;
}

export function Badge({ children, status, className = '' }) {
  const tone = status || String(children || '').toLowerCase().replaceAll(' ', '-');
  return <span className={`badge badge-${tone} ${className}`}>{children}</span>;
}

export function StatCard({ label, value, detail, icon: Icon, tone = 'teal', trend }) {
  return <div className="stat-card"><div className={`stat-icon stat-${tone}`}><Icon size={21} /></div><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-detail">{trend && <span className="trend-up">{trend}</span>} {detail}</div></div>;
}

export function SearchInput({ value, onChange, placeholder = 'Search records...' }) {
  return <label className="search-input"><Search size={17} /><input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} /></label>;
}

export function Modal({ open, onClose, title, description, children, wide = false }) {
  if (!open) return null;
  return <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><div className={`modal ${wide ? 'modal-wide' : ''}`} role="dialog" aria-modal="true" aria-label={title}><div className="modal-head"><div><h2>{title}</h2>{description && <p>{description}</p>}</div><button className="icon-btn" onClick={onClose} aria-label="Close dialog"><X size={19} /></button></div><div className="modal-body">{children}</div></div></div>;
}

export function Loading({ label = 'Loading your workspace...' }) {
  return <div className="loading-state"><LoaderCircle className="spin" size={26} /><span>{label}</span></div>;
}

export function EmptyState({ title = 'Nothing here yet', description = 'Records will appear here when they are added.', action }) {
  return <div className="empty-state"><div className="empty-icon"><FileSearch size={22} /></div><h3>{title}</h3><p>{description}</p>{action && <div className="mt-4">{action}</div>}</div>;
}

export function Table({ columns, rows, loading, emptyTitle, emptyDescription, rowKey = 'id' }) {
  if (loading) return <Loading label="Loading records..." />;
  if (!rows?.length) return <EmptyState title={emptyTitle} description={emptyDescription} />;
  return <div className="table-wrap"><table><thead><tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={row[rowKey] ?? index}>{columns.map((column) => <td key={column.key}>{column.render ? column.render(row) : row[column.key] ?? '—'}</td>)}</tr>)}</tbody></table></div>;
}

export function SectionCard({ title, subtitle, action, children, className = '' }) {
  return <section className={`section-card ${className}`}><div className="section-head"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{action}</div>{children}</section>;
}

export function Field({ label, required, hint, children, className = '' }) {
  return <label className={`field ${className}`}><span className="field-label">{label}{required && <em> *</em>}</span>{children}{hint && <small>{hint}</small>}</label>;
}

export function FormActions({ onCancel, submitLabel = 'Save changes', saving = false }) {
  return <div className="form-actions"><Button variant="ghost" type="button" onClick={onCancel}>Cancel</Button><Button type="submit" disabled={saving}>{saving ? <><LoaderCircle size={16} className="spin" /> Saving...</> : <><Plus size={16} /> {submitLabel}</>}</Button></div>;
}
