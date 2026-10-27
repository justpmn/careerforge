
import type { ReactNode } from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import Brand from './Brand';
import ThemeToggle from './ThemeToggle';
import { useAuth } from '../context/AuthContext';

type Props = {
  children: ReactNode;
  theme: 'light' | 'dark';
  toggleTheme: () => void;
};

export default function AppShell({
  children,
  theme,
  toggleTheme,
}: Props) {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  async function handleLogout() {
    setError('');

    try {
      await logout();
      navigate('/login', { replace: true });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not log out.'
      );
    }
  }

  return (
    <div className="inside-shell">
      <header className="inside-header">
        <Brand />

        <div className="inside-actions">
          <ThemeToggle
            theme={theme}
            toggle={toggleTheme}
          />

          <button
            type="button"
            className="sign-out"
            onClick={handleLogout}
          >
            Log out
          </button>
        </div>
      </header>

      <div className="inside-content">
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}

        {children}
      </div>
    </div>
  );
}
