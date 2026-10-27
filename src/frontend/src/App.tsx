
import { useEffect, useState } from 'react';
import {
  BrowserRouter,
  Navigate,
  Outlet,
  Route,
  Routes,
} from 'react-router-dom';

import AuthLayout from './components/AuthLayout';
import AppShell from './components/AppShell';
import WorkspaceLayout from './components/layout';
import { AuthProvider, useAuth } from './context/AuthContext';
import { postAuthRoute } from './lib/auth';
import AuthCallbackPage from './pages/AuthCallbackPage';
import DashboardPage from './pages/DashboardPage';
import FeaturePlaceholderPage from './pages/featureplaceholder';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import SkillsAssessmentPage from './pages/skillassessment';

type Theme = 'light' | 'dark';

function LoadingScreen() {
  return <div className="loading-screen">Loading...</div>;
}

function StartingPage() {
  const { user, loading } = useAuth();

  if (loading) return <LoadingScreen />;

  return (
    <Navigate
      to={user ? postAuthRoute(user) : '/login'}
      replace
    />
  );
}

function GuestOnly() {
  const { user, loading } = useAuth();

  if (loading) return <LoadingScreen />;

  return user
    ? <Navigate to={postAuthRoute(user)} replace />
    : <Outlet />;
}

function Protected() {
  const { user, loading } = useAuth();

  if (loading) return <LoadingScreen />;

  return user
    ? <Outlet />
    : <Navigate to="/login" replace />;
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('careerforge-theme');

    return saved === 'light' || saved === 'dark'
      ? saved
      : 'light';
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('careerforge-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((current) =>
      current === 'light' ? 'dark' : 'light'
    );
  };

  const layoutProps = { theme, toggleTheme };

  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route index element={<StartingPage />} />

          <Route element={<GuestOnly />}>
            <Route element={<AuthLayout {...layoutProps} />}>
              <Route path="login" element={<LoginPage />} />
              <Route path="signup" element={<SignupPage />} />
            </Route>
          </Route>

          <Route
            path="auth/callback"
            element={<AuthLayout {...layoutProps} />}
          >
            <Route index element={<AuthCallbackPage />} />
          </Route>

          <Route element={<Protected />}>
            <Route
              element={
                <AppShell {...layoutProps}>
                  <WorkspaceLayout />
                </AppShell>
              }
            >
              <Route
                path="dashboard"
                element={<DashboardPage />}
              />

              <Route
                path="skills-assessment"
                element={<SkillsAssessmentPage />}
              />
              <Route
                path="profile"
                element={
                  <FeaturePlaceholderPage
                    category="MY PROFILE"
                    title="Your career profile."
                    description="Manage your information, interests, and professional experience."
                  />
                }
              />

              <Route
                path="cv"
                element={
                  <FeaturePlaceholderPage
                    category="MY CV"
                    title="Your resume."
                    description="Upload and manage the CV used for career analysis."
                  />
                }
              />

              <Route
                path="settings"
                element={
                  <FeaturePlaceholderPage
                    category="SETTINGS"
                    title="Account settings."
                    description="Manage your preferences and connected accounts."
                  />
                }
              />

              <Route
                path="roadmap"
                element={
                  <FeaturePlaceholderPage
                    category="LEARNING ROADMAP"
                    title="Your learning journey."
                    description="Your interactive skill tree, learning resources, and career milestones will live here."
                  />
                }
              />

              <Route
                path="mentor"
                element={
                  <FeaturePlaceholderPage
                    category="AI MENTOR"
                    title="Start a conversation."
                    description="This is where you'll talk to your AI mentor about careers, skills, and recommendations."
                  />
                }
              />

              <Route
                path="onboarding"
                element={<Navigate to="/dashboard" replace />}
              />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
