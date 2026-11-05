
import {
  BrowserRouter, Navigate, Outlet, Route, Routes,
} from 'react-router-dom';

import AuthLayout from './components/AuthLayout';
import AppShell from './components/AppShell';
import WorkspaceLayout from './components/layout';

import { AuthProvider, useAuth } from './context/AuthContext';
import { MentorJobsProvider } from './context/mentorjobscontext';
import { AppearanceProvider, useAppearance } from './context/appearancecontext';

import { postAuthRoute } from './lib/auth';

import AuthCallbackPage from './pages/AuthCallbackPage';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import SkillsAssessmentPage from './pages/skillassessment';
import CvPage from './pages/cvpage';
import MentorPage from './pages/mentorpage';
import RoadmapPage from './pages/roadmappage';
import ProfilePage from './pages/profilepage';
import SettingsPage from './pages/settingpage';
import AdminPage from './pages/adminpage';
import VerifyEmailPage from './pages/verifyemailpage';
import AdminMfaPage from './pages/adminmfapage';
import AdminResourcesPage from './pages/adminresourcespage';
import HomePage from './pages/homepage';
import './neon.css';
import './responsive.css';
import ConfirmAccountDeletionPage from './pages/ConfirmAccountDeletionPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';

function LoadingScreen() {
  return <div className="loading-screen">Loading...</div>;
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

function AppRoutes() {
  const { theme, toggleTheme } = useAppearance();
  const layoutProps = { theme, toggleTheme };

  return (
    <AuthProvider>
      <BrowserRouter>
        <MentorJobsProvider>
          <Routes>

            {/* Public homepage */}
            <Route
              index
              element={<HomePage {...layoutProps} />}
            />

            {/* Public authentication */}
            <Route element={<GuestOnly />}>
              <Route element={<AuthLayout {...layoutProps} />}>
                <Route
                  path="login"
                  element={<LoginPage />}
                />

                <Route
                  path="signup"
                  element={<SignupPage />}
                />
              </Route>
              <Route
                path="verify-email"
                element={<VerifyEmailPage />}
              />
            </Route>
            <Route element={<AuthLayout {...layoutProps} />}>
            <Route
              path="delete-account"
              element={<ConfirmAccountDeletionPage />}
            />
          </Route>
          <Route element={<AuthLayout {...layoutProps} />}>
          <Route
            path="forgot-password"
            element={<ForgotPasswordPage />}
          />
          <Route
            path="reset-password"
            element={<ResetPasswordPage />}
          />
        </Route>

            {/* Administrator MFA */}
            <Route
              path="auth/mfa"
              element={<AdminMfaPage />}
            />

            {/* OAuth callback */}
            <Route
              path="auth/callback"
              element={<AuthLayout {...layoutProps} />}
            >
              <Route
                index
                element={<AuthCallbackPage />}
              />
            </Route>

            {/* Authenticated application */}
            <Route element={<Protected />}>

              {/* Administrator workspace */}
              <Route
                path="admin"
                element={
                  <AppShell {...layoutProps}>
                    <AdminPage />
                  </AppShell>
                }
              />

              <Route
                path="admin/resources"
                element={<AdminResourcesPage />}
              />

              {/* Standard workspace */}
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
                  path="profile"
                  element={<ProfilePage />}
                />

                <Route
                  path="cv"
                  element={<CvPage />}
                />

                <Route
                  path="skills-assessment"
                  element={<SkillsAssessmentPage />}
                />

                <Route
                  path="roadmap"
                  element={<RoadmapPage />}
                />

                <Route
                  path="mentor"
                  element={<MentorPage />}
                />

                <Route
                  path="settings"
                  element={<SettingsPage />}
                />

                <Route
                  path="onboarding"
                  element={
                    <Navigate to="/dashboard" replace />
                  }
                />
              </Route>
            </Route>

            {/* Unknown routes */}
            <Route
              path="*"
              element={<Navigate to="/" replace />}
            />

          </Routes>
        </MentorJobsProvider>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppearanceProvider>
        <AppRoutes />
      </AppearanceProvider>
    </AuthProvider>
  );
}
