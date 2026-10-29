
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
import CvPage from './pages/cvpage';
import MentorPage from './pages/mentorpage';
import { MentorJobsProvider } from './context/mentorjobscontext';
import RoadmapPage from './pages/roadmappage';

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
        <MentorJobsProvider>
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
                  element={<CvPage />}
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

                <Route path="roadmap" element={<RoadmapPage />} />

                <Route path="mentor" element={<MentorPage />} />

                <Route
                  path="onboarding"
                  element={<Navigate to="/dashboard" replace />}
                />
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </MentorJobsProvider>
      </BrowserRouter>
    </AuthProvider>
  );
}
