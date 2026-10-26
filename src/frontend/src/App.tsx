import { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom';
import AuthLayout from './components/AuthLayout';
import AppShell from './components/AppShell';
import { AuthProvider, useAuth } from './context/AuthContext';
import { postAuthRoute } from './lib/auth';
import AuthCallbackPage from './pages/AuthCallbackPage';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import OnboardingPage from './pages/OnboardingPage';
import SignupPage from './pages/SignupPage';

type Theme = 'light' | 'dark';

function StartingPage() {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-screen">Loading…</div>;
  return <Navigate to={user ? postAuthRoute(user) : '/login'} replace />;
}

function GuestOnly() {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-screen">Loading…</div>;
  return user ? <Navigate to={postAuthRoute(user)} replace /> : <Outlet />;
}

function Protected() {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-screen">Loading…</div>;
  return user ? <Outlet /> : <Navigate to="/login" replace />;
}

function OnboardingGuard() {
  const { user } = useAuth();
  return user?.onboarding_completed ? <Navigate to="/dashboard" replace /> : <Outlet />;
}

function DashboardGuard() {
  const { user } = useAuth();
  return user?.onboarding_completed ? <Outlet /> : <Navigate to="/onboarding" replace />;
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('careerforge-theme');
    return saved === 'light' || saved === 'dark' ? saved : 'light';
  });
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('careerforge-theme', theme);
  }, [theme]);
  const toggleTheme = () => setTheme((current) => current === 'light' ? 'dark' : 'light');
  const props = { theme, toggleTheme };

  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route index element={<StartingPage />} />
          <Route element={<GuestOnly />}>
            <Route element={<AuthLayout {...props} />}>
              <Route path="login" element={<LoginPage />} />
              <Route path="signup" element={<SignupPage />} />
            </Route>
          </Route>
          <Route path="auth/callback" element={<AuthLayout {...props} />}>
            <Route index element={<AuthCallbackPage />} />
          </Route>
          <Route element={<Protected />}>
            <Route element={<OnboardingGuard />}>
              <Route path="onboarding" element={<AppShell {...props}><OnboardingPage /></AppShell>} />
            </Route>
            <Route element={<DashboardGuard />}>
              <Route path="dashboard" element={<AppShell {...props}><DashboardPage /></AppShell>} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
