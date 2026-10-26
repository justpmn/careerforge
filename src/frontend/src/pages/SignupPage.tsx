import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import OAuthButtons from '../components/OAuthButtons';
import PasswordField from '../components/PasswordField';
import { useAuth } from '../context/AuthContext';

export default function SignupPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    if (name.trim().length < 2) {
      setError('Please enter your name (at least 2 characters).');
      return;
    }
    if (password.length < 8) {
      setError('Use a password of at least 8 characters.');
      return;
    }
    if (password !== confirm) {
      setError('Your passwords do not match.');
      return;
    }
    setBusy(true);
    try {
      await register({
        name: name.trim(),
        email: email.trim(),
        password,
      });

      navigate('/login', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed. Please try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="auth-card" aria-labelledby="signup-heading">
      <div className="form-brow">THE FIRST STEP <span>↗</span></div>
      <h2 id="signup-heading">Create your account</h2>
      <p className="auth-subtitle">A clear direction for your career starts with knowing where you stand.</p>

      <OAuthButtons onError={setError} />
      <div className="form-divider"><span>or with email</span></div>

      <form onSubmit={submit} className="auth-form">
        <div className="field-group">
          <label htmlFor="name">Full name</label>
          <input id="name" name="name" type="text" autoComplete="name" minLength={2} maxLength={100} required
            placeholder="Your name" value={name} onChange={(event) => setName(event.target.value)} />
        </div>
        <div className="field-group">
          <label htmlFor="email">Email address</label>
          <input id="email" name="email" type="email" required autoComplete="email" placeholder="you@example.com"
            value={email} onChange={(event) => setEmail(event.target.value)} />
        </div>
        <PasswordField id="password" label="Password" autoComplete="new-password" minLength={8} value={password}
          onChange={(event) => setPassword(event.target.value)} placeholder="At least 8 characters" />
        <PasswordField id="confirm" label="Confirm password" autoComplete="new-password" minLength={8} value={confirm}
          onChange={(event) => setConfirm(event.target.value)} placeholder="Repeat your password" />
        {error && <p className="form-error" role="alert">{error}</p>}
        <button className="primary-button" disabled={busy} type="submit">{busy ? 'Creating account…' : 'Create account'} <span aria-hidden="true">→</span></button>
      </form>
      <p className="form-bottom">Already have an account? <Link to="/login">Log in</Link></p>
    </section>
  );
}
