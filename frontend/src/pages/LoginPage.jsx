import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, Eye, EyeOff, HeartPulse, ShieldCheck, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { user, login, initializing } = useAuth();
  const [email, setEmail] = useState('admin@carebridge.demo');
  const [password, setPassword] = useState('Admin@12345');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  if (!initializing && user) return <Navigate to="/" replace />;

  const submit = async (event) => {
    event.preventDefault(); setError(''); setBusy(true);
    try { await login(email.trim(), password); navigate(location.state?.from?.pathname || '/', { replace: true }); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  return <div className="login-page">
    <div className="login-visual"><div className="login-brand"><div className="brand-mark"><HeartPulse size={23} /></div><span>carebridge<span>.</span></span></div><div className="login-visual-content"><div className="visual-pill"><Sparkles size={14} /> YOUR HEALTHCARE, CONNECTED</div><h1>Better care.<br /><em>One connected</em><br />experience.</h1><p>Bring your care teams, patients and everyday operations together in one thoughtful workspace.</p><div className="visual-stats"><div><strong>24/7</strong><span>Care visibility</span></div><div><strong>One place</strong><span>For every patient</span></div><div><strong>Secure</strong><span>By design</span></div></div></div><div className="visual-orb orb-one"/><div className="visual-orb orb-two"/><div className="login-visual-footer"><span>Designed for people who care.</span><span>© CareBridge Health Systems</span></div></div>
    <div className="login-form-side"><div className="login-form-wrap"><div className="mobile-login-brand"><div className="brand-mark"><HeartPulse size={21} /></div><b>carebridge<span>.</span></b></div><div className="login-welcome"><div className="eyebrow">WELCOME BACK</div><h2>Sign in to your workspace</h2><p>Enter your account details to continue.</p></div>
      <form onSubmit={submit} className="login-form"><label className="field"><span className="field-label">Email address</span><input className="input" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@clinic.com" required /></label><label className="field"><span className="field-label">Password</span><div className="password-wrap"><input className="input" type={showPassword ? 'text' : 'password'} autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" required /><button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label>
        {error && <div className="form-error">{error}</div>}<button className="btn btn-primary btn-lg login-submit" type="submit" disabled={busy}>{busy ? 'Signing in...' : 'Sign in'} <ArrowRight size={17} /></button>
      </form><div className="login-secure"><ShieldCheck size={17} /><span>Your information is protected with secure authentication.</span></div><div className="demo-access"><div className="demo-head"><span>DEMO ACCESS</span><span className="demo-tag">LOCAL DEVELOPMENT</span></div><p>Use the prefilled administrator account, or switch to another demo role:</p><div className="demo-buttons"><button onClick={() => { setEmail('reception@carebridge.demo'); setPassword('Reception@12345'); }}>Receptionist</button><button onClick={() => { setEmail('doctor@carebridge.demo'); setPassword('Doctor@12345'); }}>Doctor</button><button onClick={() => { setEmail('patient@carebridge.demo'); setPassword('Patient@12345'); }}>Patient</button></div></div></div></div>
  </div>;
}
