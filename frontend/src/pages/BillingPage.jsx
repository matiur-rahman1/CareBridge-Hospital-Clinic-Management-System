import { useCallback, useEffect, useMemo, useState } from 'react';
import { CircleDollarSign, CreditCard, Eye, FilePlus2, Plus, Printer, Receipt, Wallet } from 'lucide-react';
import { api, getErrorMessage, getList, resources } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { dateLabel, money, titleCase } from '../utils/format';
import { Badge, Button, Field, FormActions, Modal, PageHeader, SearchInput, SectionCard, StatCard, Table } from '../components/UI';

const blankItem = () => ({ description: '', quantity: '1', unit_price: '0.00' });
const blankInvoice = { patient: '', appointment: '', consultation_fee: '0.00', discount_amount: '0.00', notes: '', items: [blankItem()] };
const blankPayment = { invoice: '', amount: '', method: 'CASH', reference: '', notes: '' };

export default function BillingPage() {
  const { user } = useAuth();
  const { notify } = useToast();
  const [invoices, setInvoices] = useState([]);
  const [payments, setPayments] = useState([]);
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [invoiceModal, setInvoiceModal] = useState(false);
  const [paymentModal, setPaymentModal] = useState(false);
  const [detail, setDetail] = useState(null);
  const [invoiceForm, setInvoiceForm] = useState(blankInvoice);
  const [paymentForm, setPaymentForm] = useState(blankPayment);
  const [saving, setSaving] = useState(false);
  const canManage = ['ADMIN', 'RECEPTIONIST'].includes(user?.role);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [invoiceRows, paymentRows, patientRows, doctorRows, appointmentRows] = await Promise.all([
        getList(resources.invoices, { search, payment_status: statusFilter || undefined, ordering: '-issue_date' }),
        getList(resources.payments, { search, ordering: '-payment_date' }),
        getList(resources.patients),
        getList(resources.doctors),
        getList(resources.appointments),
      ]);
      setInvoices(invoiceRows); setPayments(paymentRows); setPatients(patientRows); setDoctors(doctorRows); setAppointments(appointmentRows);
    } catch (error) { notify(getErrorMessage(error), 'error'); }
    finally { setLoading(false); }
  }, [search, statusFilter, notify]);
  useEffect(() => { const timer = window.setTimeout(load, 200); return () => window.clearTimeout(timer); }, [load]);

  const calculatedSubtotal = useMemo(() => Number(invoiceForm.consultation_fee || 0) + invoiceForm.items.filter((item) => item.description.trim()).reduce((sum, item) => sum + Number(item.quantity || 0) * Number(item.unit_price || 0), 0), [invoiceForm]);
  const calculatedTotal = Math.max(0, calculatedSubtotal - Number(invoiceForm.discount_amount || 0));
  const setItem = (index, key, value) => setInvoiceForm((current) => ({ ...current, items: current.items.map((item, i) => i === index ? { ...item, [key]: value } : item) }));
  const openInvoice = () => { setInvoiceForm(blankInvoice); setInvoiceModal(true); };
  const saveInvoice = async (event) => {
    event.preventDefault(); setSaving(true);
    const payload = { ...invoiceForm, patient: Number(invoiceForm.patient), appointment: invoiceForm.appointment ? Number(invoiceForm.appointment) : null, consultation_fee: invoiceForm.consultation_fee, discount_amount: invoiceForm.discount_amount, items: invoiceForm.items.filter((item) => item.description.trim()).map((item) => ({ ...item, quantity: Number(item.quantity) })) };
    try { await api.post(resources.invoices, payload); notify('Invoice generated successfully.'); setInvoiceModal(false); await load(); }
    catch (error) { notify(getErrorMessage(error), 'error'); }
    finally { setSaving(false); }
  };
  const openPayment = (invoice = null) => { setPaymentForm({ ...blankPayment, invoice: invoice ? String(invoice.id) : '', amount: invoice ? String(invoice.balance_due) : '' }); setPaymentModal(true); };
  const savePayment = async (event) => {
    event.preventDefault(); setSaving(true);
    try { await api.post(resources.payments, { ...paymentForm, invoice: Number(paymentForm.invoice), amount: paymentForm.amount }); notify('Payment recorded successfully.'); setPaymentModal(false); await load(); }
    catch (error) { notify(getErrorMessage(error), 'error'); }
    finally { setSaving(false); }
  };
  const printInvoice = (invoice) => {
    const content = `<html><head><title>${invoice.invoice_number}</title><style>body{font-family:Arial,sans-serif;padding:42px;color:#25334a}h1{color:#168783}table{width:100%;border-collapse:collapse;margin-top:24px}td,th{padding:12px;border:1px solid #ddd;text-align:left}.total{font-size:20px;font-weight:bold;text-align:right;margin-top:20px}.right{text-align:right}</style></head><body><h1>CareBridge</h1><p>Hospital & Clinic Management</p><hr><h2>Invoice ${invoice.invoice_number}</h2><p><b>Patient:</b> ${invoice.patient_name}</p><p><b>Issue date:</b> ${dateLabel(invoice.issue_date)}</p><table><thead><tr><th>Description</th><th>Qty</th><th>Unit price</th><th>Line total</th></tr></thead><tbody><tr><td>Consultation fee</td><td>1</td><td>${money(invoice.consultation_fee)}</td><td>${money(invoice.consultation_fee)}</td></tr>${(invoice.items || []).map((item) => `<tr><td>${item.description}</td><td>${item.quantity}</td><td>${money(item.unit_price)}</td><td>${money(item.line_total)}</td></tr>`).join('')}</tbody></table><p class="right">Subtotal: ${money(invoice.subtotal)}</p><p class="right">Discount: ${money(invoice.discount_amount)}</p><p class="total">Total: ${money(invoice.total_amount)}</p><p class="right">Paid: ${money(invoice.amount_paid)} · Balance: ${money(invoice.balance_due)}</p><p>Payment status: ${titleCase(invoice.payment_status)}</p><script>window.onload=()=>window.print()</script></body></html>`;
    const win = window.open('', '_blank', 'width=900,height=700'); if (win) { win.document.write(content); win.document.close(); }
  };
  const totalRevenue = payments.reduce((sum, payment) => sum + Number(payment.amount), 0);
  const outstanding = invoices.reduce((sum, invoice) => sum + Number(invoice.balance_due), 0);
  const columns = [
    { key: 'invoice_number', label: 'Invoice', render: (row) => <div><strong>{row.invoice_number}</strong><small>Issued {dateLabel(row.issue_date)}</small></div> },
    { key: 'patient_name', label: 'Patient', render: (row) => row.patient_name },
    { key: 'total_amount', label: 'Amount', render: (row) => <strong>{money(row.total_amount)}</strong> },
    { key: 'amount_paid', label: 'Paid / Due', render: (row) => <div><strong>{money(row.amount_paid)}</strong><small>Due {money(row.balance_due)}</small></div> },
    { key: 'payment_status', label: 'Status', render: (row) => <Badge status={row.payment_status.toLowerCase().replace('_', '-')}>{titleCase(row.payment_status)}</Badge> },
    { key: 'actions', label: '', render: (row) => <div className="row-actions"><button className="icon-btn" title="View invoice" onClick={() => setDetail(row)}><Eye size={16}/></button><button className="icon-btn" title="Print invoice" onClick={() => printInvoice(row)}><Printer size={16}/></button>{canManage && Number(row.balance_due) > 0 && <button className="text-action" onClick={() => openPayment(row)}>Record payment</button>}</div> },
  ];
  const paymentColumns = [
    { key: 'invoice_number', label: 'Invoice', render: (row) => <strong>{row.invoice_number}</strong> },
    { key: 'patient_name', label: 'Patient' },
    { key: 'amount', label: 'Amount', render: (row) => <strong>{money(row.amount)}</strong> },
    { key: 'method', label: 'Method', render: (row) => titleCase(row.method) },
    { key: 'payment_date', label: 'Date', render: (row) => dateLabel(row.payment_date) },
    { key: 'reference', label: 'Reference', render: (row) => row.reference || '—' },
  ];

  return <>
    <PageHeader eyebrow="FINANCE" title="Billing & payments" description="Create clear invoices, track balances and keep patient payments organized." actions={canManage && <><Button variant="outline" onClick={() => openPayment()}><Plus size={16}/> Record payment</Button><Button onClick={openInvoice}><FilePlus2 size={16}/> Create invoice</Button></>} />
    <div className="stats-grid stats-grid-three"><StatCard label="Payments received" value={money(totalRevenue)} detail="Across visible payment records" icon={CircleDollarSign} tone="green"/><StatCard label="Outstanding balance" value={money(outstanding)} detail="Remaining across invoices" icon={Wallet} tone="amber"/><StatCard label="Invoices issued" value={invoices.length} detail={`${invoices.filter((i) => i.payment_status === 'PAID').length} fully paid`} icon={Receipt} tone="blue"/></div>
    <SectionCard title="Invoices" subtitle={`${invoices.length} patient invoices`}><div className="toolbar"><SearchInput value={search} onChange={setSearch} placeholder="Search invoice number or patient..."/><select className="select compact-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}><option value="">All payment statuses</option><option value="PAID">Paid</option><option value="UNPAID">Unpaid</option><option value="PARTIALLY_PAID">Partially paid</option></select></div><Table columns={columns} rows={invoices} loading={loading} emptyTitle="No invoices found" emptyDescription="Generate an invoice when a patient receives a service."/></SectionCard>
    <SectionCard title="Payment history" subtitle={`${payments.length} payment transactions`}><Table columns={paymentColumns} rows={payments.slice(0, 12)} loading={loading} emptyTitle="No payments recorded" emptyDescription="Recorded payments will be listed here."/></SectionCard>

    <Modal open={invoiceModal} onClose={() => setInvoiceModal(false)} title="Create patient invoice" description="Add consultation and service charges. Totals are calculated automatically." wide><form onSubmit={saveInvoice}><div className="form-grid"><Field label="Patient" required><select className="select" required value={invoiceForm.patient} onChange={(e) => setInvoiceForm({ ...invoiceForm, patient: e.target.value, appointment: '' })}><option value="">Select patient</option>{patients.map((p) => <option value={p.id} key={p.id}>{p.full_name} · {p.patient_id}</option>)}</select></Field><Field label="Related appointment"><select className="select" value={invoiceForm.appointment} onChange={(e) => { const appointment = appointments.find((a) => String(a.id) === e.target.value); const doctor = appointment ? doctors.find((item) => String(item.id) === String(appointment.doctor)) : null; setInvoiceForm({ ...invoiceForm, appointment: e.target.value, patient: appointment ? String(appointment.patient) : invoiceForm.patient, consultation_fee: doctor ? String(doctor.consultation_fee) : invoiceForm.consultation_fee }); }}><option value="">No linked appointment</option>{appointments.filter((a) => (!invoiceForm.patient || String(a.patient) === String(invoiceForm.patient)) && !invoices.some((invoice) => String(invoice.appointment_id) === String(a.id))).map((a) => <option key={a.id} value={a.id}>#{a.id} · {a.patient_name} · {dateLabel(a.appointment_date)}</option>)}</select></Field><Field label="Consultation fee (BDT)" required><input className="input" type="number" min="0" step="0.01" required value={invoiceForm.consultation_fee} onChange={(e) => setInvoiceForm({ ...invoiceForm, consultation_fee: e.target.value })}/></Field><Field label="Discount (BDT)"><input className="input" type="number" min="0" step="0.01" value={invoiceForm.discount_amount} onChange={(e) => setInvoiceForm({ ...invoiceForm, discount_amount: e.target.value })}/></Field></div><div className="medicine-builder"><div className="medicine-builder-head"><div><h3>Additional services</h3><p>Optional laboratory, procedure or service charges.</p></div><Button type="button" variant="outline" size="sm" onClick={() => setInvoiceForm({ ...invoiceForm, items: [...invoiceForm.items, blankItem()] })}><Plus size={14}/> Add item</Button></div>{invoiceForm.items.map((item, index) => <div className="invoice-item-row" key={index}><Field label="Description"><input className="input" value={item.description} onChange={(e) => setItem(index, 'description', e.target.value)} placeholder="Service description"/></Field><Field label="Qty"><input className="input" type="number" min="1" value={item.quantity} onChange={(e) => setItem(index, 'quantity', e.target.value)}/></Field><Field label="Unit price (BDT)"><input className="input" type="number" min="0" step="0.01" value={item.unit_price} onChange={(e) => setItem(index, 'unit_price', e.target.value)}/></Field>{invoiceForm.items.length > 1 && <button type="button" className="icon-btn icon-danger" onClick={() => setInvoiceForm({ ...invoiceForm, items: invoiceForm.items.filter((_, i) => i !== index) })}>×</button>}</div>)}</div><Field label="Invoice notes"><textarea className="textarea" rows="2" value={invoiceForm.notes} onChange={(e) => setInvoiceForm({ ...invoiceForm, notes: e.target.value })} placeholder="Optional notes"/></Field><div className="invoice-calculation"><div><span>Subtotal</span><strong>{money(calculatedSubtotal)}</strong></div><div><span>Discount</span><strong>− {money(invoiceForm.discount_amount)}</strong></div><div className="invoice-total"><span>Total due</span><strong>{money(calculatedTotal)}</strong></div></div><FormActions onCancel={() => setInvoiceModal(false)} saving={saving} submitLabel="Generate invoice"/></form></Modal>

    <Modal open={paymentModal} onClose={() => setPaymentModal(false)} title="Record a payment" description="Record an amount received against an outstanding invoice."><form onSubmit={savePayment}><div className="form-stack"><Field label="Invoice" required><select className="select" required value={paymentForm.invoice} onChange={(e) => { const inv = invoices.find((item) => String(item.id) === e.target.value); setPaymentForm({ ...paymentForm, invoice: e.target.value, amount: inv ? String(inv.balance_due) : '' }); }}><option value="">Select invoice</option>{invoices.filter((invoice) => Number(invoice.balance_due) > 0).map((invoice) => <option value={invoice.id} key={invoice.id}>{invoice.invoice_number} · {invoice.patient_name} · Due {money(invoice.balance_due)}</option>)}</select></Field><Field label="Amount received (BDT)" required><input className="input" type="number" min="0.01" step="0.01" required value={paymentForm.amount} onChange={(e) => setPaymentForm({ ...paymentForm, amount: e.target.value })}/></Field><Field label="Payment method"><select className="select" value={paymentForm.method} onChange={(e) => setPaymentForm({ ...paymentForm, method: e.target.value })}><option value="CASH">Cash</option><option value="CARD">Card</option><option value="BANK_TRANSFER">Bank transfer</option><option value="MOBILE_BANKING">Mobile banking</option></select></Field><Field label="Reference"><input className="input" value={paymentForm.reference} onChange={(e) => setPaymentForm({ ...paymentForm, reference: e.target.value })} placeholder="Transaction or receipt reference"/></Field><Field label="Notes"><textarea className="textarea" rows="2" value={paymentForm.notes} onChange={(e) => setPaymentForm({ ...paymentForm, notes: e.target.value })}/></Field></div><FormActions onCancel={() => setPaymentModal(false)} saving={saving} submitLabel="Save payment"/></form></Modal>

    <Modal open={!!detail} onClose={() => setDetail(null)} title="Invoice details" description={detail ? `${detail.invoice_number} · Issued ${dateLabel(detail.issue_date)}` : ''} wide>{detail && <><div className="invoice-preview-head"><div><div className="brand-mark"><Receipt size={20}/></div><h3>CareBridge <span>Patient invoice</span></h3></div><Button variant="outline" size="sm" onClick={() => printInvoice(detail)}><Printer size={15}/> Print invoice</Button></div><div className="invoice-preview-info"><div><span>BILLED TO</span><strong>{detail.patient_name}</strong></div><div><span>ISSUE DATE</span><strong>{dateLabel(detail.issue_date)}</strong></div><div><span>PAYMENT STATUS</span><Badge status={detail.payment_status.toLowerCase().replace('_', '-')}>{titleCase(detail.payment_status)}</Badge></div></div><div className="table-wrap"><table><thead><tr><th>Description</th><th>Qty</th><th>Unit price</th><th>Line total</th></tr></thead><tbody><tr><td>Consultation fee</td><td>1</td><td>{money(detail.consultation_fee)}</td><td>{money(detail.consultation_fee)}</td></tr>{(detail.items || []).map((item) => <tr key={item.id}><td>{item.description}</td><td>{item.quantity}</td><td>{money(item.unit_price)}</td><td>{money(item.line_total)}</td></tr>)}</tbody></table></div><div className="invoice-preview-total"><div><span>Subtotal</span><strong>{money(detail.subtotal)}</strong></div><div><span>Discount</span><strong>− {money(detail.discount_amount)}</strong></div><div className="grand-total"><span>Total</span><strong>{money(detail.total_amount)}</strong></div><div><span>Paid</span><strong>{money(detail.amount_paid)}</strong></div><div><span>Balance due</span><strong>{money(detail.balance_due)}</strong></div></div></>}</Modal>
  </>;
}
