import type { ReactNode } from 'react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Brand from './Brand';
import ThemeToggle from './ThemeToggle';
import { useAuth } from '../context/AuthContext';

type Props = { children: ReactNode; theme: 'light' | 'dark'; toggleTheme: () => void };

export default function AppShell({ children, theme, toggleTheme }: Props) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  async function handleLogout() {
    setError('');
    try {
      await logout();
      navigate('/login', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not log out.');
    }
  }

  return (
    <div className="inside-shell">
      <header className="inside-header">
        <Brand />
        <div className="inside-actions"><ThemeToggle theme={theme} toggle={toggleTheme} /><button className="sign-out" onClick={handleLogout}>Log out</button></div>
      </header>
      <main className="inside-content">
        {error && <p className="form-error" role="alert">{error}</p>}
        <span className="form-brow">YOUR WORKSPACE <span>↗</span></span>
        <p className="greeting">Hey, {user?.name?.split(' ')[0] || 'there'}.</p>
        {children}
        <p className="workspace-footer"><Link to="/dashboard">Dashboard</Link><span>·</span><Link to="/onboarding">Onboarding</Link></p>
      </main>
    </div>
  );
}
