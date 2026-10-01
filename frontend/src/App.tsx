import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { User } from './types';
import { getCurrentUser, MASTER_DEMO_USER } from './services/auth';
import { Header } from './components/common/Header';
import { Footer } from './components/common/Footer';
import { MobileNav } from './components/common/MobileNav';
import { LoopBot } from './components/common/LoopBot';
import { AuthModal } from './components/common/AuthModal';
import { HostAuthModal } from './components/common/HostAuthModal';
import { InitialLoadingScreen } from './components/common/InitialLoadingScreen';

// Lazy-Loaded Page Components for optimized bundle chunking
const LandingPage = React.lazy(() => import('./pages/LandingPage').then(m => ({ default: m.LandingPage })));
const ExplorePage = React.lazy(() => import('./pages/ExplorePage').then(m => ({ default: m.ExplorePage })));
const SpaceDetailPage = React.lazy(() => import('./pages/SpaceDetailPage').then(m => ({ default: m.SpaceDetailPage })));
const DashboardPage = React.lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const HostPortalShell = React.lazy(() => import('./pages/host/HostPortalShell').then(m => ({ default: m.HostPortalShell })));
const SessionPage = React.lazy(() => import('./pages/SessionPage').then(m => ({ default: m.SessionPage })));
const CalculatorPage = React.lazy(() => import('./pages/CalculatorPage').then(m => ({ default: m.CalculatorPage })));
const VerifyPage = React.lazy(() => import('./pages/VerifyPage').then(m => ({ default: m.VerifyPage })));
const HowItWorksPage = React.lazy(() => import('./pages/HowItWorksPage').then(m => ({ default: m.HowItWorksPage })));
const TrustSafetyPage = React.lazy(() => import('./pages/TrustSafetyPage').then(m => ({ default: m.TrustSafetyPage })));
const ArchitecturePage = React.lazy(() => import('./pages/ArchitecturePage').then(m => ({ default: m.ArchitecturePage })));
const VerifyEmailPage = React.lazy(() => import('./pages/VerifyEmailPage').then(m => ({ default: m.VerifyEmailPage })));

// Lazy-Loaded Host Portal Views
const OverviewView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.OverviewView })));
const MySpacesView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.MySpacesView })));
const SpaceDetailView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.SpaceDetailView })));
const CreateSpaceView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.CreateSpaceView })));
const BookingsView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.BookingsView })));
const BookingDetailView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.BookingDetailView })));
const CalendarView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.CalendarView })));
const LiveSessionsView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.LiveSessionsView })));
const SpaceVerificationView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.SpaceVerificationView })));
const AccessSecurityView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.AccessSecurityView })));
const ConditionEscrowView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.ConditionEscrowView })));
const AnalyticsView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.AnalyticsView })));
const ActivityAuditView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.ActivityAuditView })));
const HostSettingsView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.HostSettingsView })));
const NotificationsView = React.lazy(() => import('./pages/host/views').then(m => ({ default: m.NotificationsView })));

import { ErrorBoundary } from './components/common/ErrorBoundary';
import { logoutUser, resendEmailVerification } from './services/auth';

const PageLoadingFallback: React.FC = () => (
  <div className="flex-1 flex items-center justify-center min-h-[50vh] p-8">
    <div className="flex flex-col items-center gap-3">
      <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
      <span className="text-xs font-medium text-slate-400">Loading SpaceLoop...</span>
    </div>
  </div>
);

interface ProtectedRouteProps {
  currentUser: User | null;
  initializing: boolean;
  onRequireAuth: () => void;
  children: React.ReactElement;
}

const UnverifiedEmailNotice: React.FC<{ email: string; onLogout?: () => void }> = ({ email, onLogout }) => {
  const [resending, setResending] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleResend = async () => {
    setResending(true);
    setStatus(null);
    setError(null);
    try {
      const res = await resendEmailVerification(email);
      setStatus(res.message || 'Verification email resent via Resend! Check your inbox.');
    } catch (e: any) {
      setError(e.message || 'Failed to resend verification email.');
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center py-20 px-4 text-center max-w-lg mx-auto">
      <div className="w-16 h-16 rounded-2xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 text-3xl mb-5 shadow-inner">
        <i className="fa-solid fa-envelope-circle-check" />
      </div>
      <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 mb-3">
        Action Required
      </span>
      <h2 className="text-2xl font-black text-white mb-2">Email Verification Required</h2>
      <p className="text-slate-300 text-sm mb-6 leading-relaxed">
        Your account (<strong className="text-amber-300">{email}</strong>) has not been verified yet. Check your inbox for the verification email sent via Resend, or click below to request a new link to access the SpaceLoop portal.
      </p>

      {status && (
        <div className="w-full mb-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs text-emerald-300 text-center">
          ✓ {status}
        </div>
      )}
      {error && (
        <div className="w-full mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300 text-center">
          ⚠️ {error}
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-3 w-full justify-center">
        <button
          type="button"
          disabled={resending}
          onClick={handleResend}
          className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/25 transition disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <i className="fa-solid fa-paper-plane text-xs" />
          <span>{resending ? 'Sending with Resend...' : 'Resend Verification Email'}</span>
        </button>

        <button
          type="button"
          onClick={async () => {
            try {
              await logoutUser();
            } catch {}
            localStorage.removeItem('spaceloop_user');
            if (onLogout) onLogout();
            window.location.reload();
          }}
          className="px-5 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs border border-slate-700 transition"
        >
          Sign Out / Switch User
        </button>
      </div>
    </div>
  );
};

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  currentUser,
  initializing,
  onRequireAuth,
  children,
}) => {
  if (initializing) {
    return (
      <div className="flex-1 flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  if (!currentUser) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center py-24 px-4 text-center max-w-lg mx-auto">
        <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 text-2xl mb-5 shadow-inner">
          <i className="fa-solid fa-lock" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Authentication Required</h2>
        <p className="text-slate-400 text-sm mb-6">
          This portal contains private user records, bookings, or property controls. Please sign in to verify your identity.
        </p>
        <button
          onClick={onRequireAuth}
          className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-all shadow-lg shadow-indigo-600/20"
        >
          Sign In to Access
        </button>
      </div>
    );
  }
  if (!currentUser.is_email_verified) {
    return <UnverifiedEmailNotice email={currentUser.email} />;
  }
  return children;
};

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    if (typeof window !== 'undefined') {
      try {
        const cached = localStorage.getItem('spaceloop_user');
        if (cached) return JSON.parse(cached);
      } catch {}
    }
    return null;
  });
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [hostAuthModalOpen, setHostAuthModalOpen] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [showLoadingScreen, setShowLoadingScreen] = useState(true);
  const [loadingScreenFading, setLoadingScreenFading] = useState(false);

  useEffect(() => {
    const startTime = Date.now();
    const initAuth = async () => {
      try {
        const user = await getCurrentUser();
        if (user) {
          setCurrentUser(user);
        } else {
          setCurrentUser(null);
        }
      } catch (err) {
        console.error('Failed to restore session:', err);
        setCurrentUser(null);
      } finally {
        setInitializing(false);
        // Ensure entrance animation completes gracefully before initiating smooth fade-out
        const elapsed = Date.now() - startTime;
        const minDisplayTime = 600;
        const remainingTime = Math.max(0, minDisplayTime - elapsed);

        setTimeout(() => {
          setLoadingScreenFading(true);
          setTimeout(() => {
            setShowLoadingScreen(false);
          }, 700);
        }, remainingTime);
      }
    };
    initAuth();
  }, []);

  const pathname = typeof window !== 'undefined' ? window.location.pathname : '';
  const basename = pathname.startsWith('/react')
    ? '/react'
    : pathname.startsWith('/app')
    ? '/app'
    : '/';

  return (
    <>
      {showLoadingScreen && (
        <InitialLoadingScreen isFading={loadingScreenFading} />
      )}
      <BrowserRouter basename={basename}>
        <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white pb-16 md:pb-0">
        {/* Clean Startup Navigation Header with Portal Switcher */}
        <Header
          currentUser={currentUser}
          onOpenAuthModal={() => setAuthModalOpen(true)}
          onOpenHostAuthModal={() => setHostAuthModalOpen(true)}
        />

        {/* Application Routes */}
        <main className="flex-1 flex flex-col">
          <ErrorBoundary>
            <React.Suspense fallback={<PageLoadingFallback />}>
              <Routes>
                {/* Seeker Routes */}
                <Route path="/" element={<LandingPage currentUser={currentUser} />} />
                <Route path="/explore" element={<ExplorePage />} />
                <Route path="/curated" element={<ExplorePage />} />
                <Route path="/explore-view" element={<ExplorePage />} />
                <Route path="/boutique" element={<ExplorePage />} />
                <Route path="/space/:id" element={<SpaceDetailPage currentUser={currentUser} onUserChange={setCurrentUser} />} />
                <Route path="/session/:id" element={<SessionPage />} />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute
                      currentUser={currentUser}
                      initializing={initializing}
                      onRequireAuth={() => setAuthModalOpen(true)}
                    >
                      <DashboardPage currentUser={currentUser} />
                    </ProtectedRoute>
                  }
                />
                <Route path="/how-it-works" element={<HowItWorksPage />} />

                {/* Host Dedicated Portal Routes */}
                <Route
                  path="/host"
                  element={
                    <HostPortalShell
                      currentUser={currentUser || MASTER_DEMO_USER}
                      onOpenHostAuthModal={() => setHostAuthModalOpen(true)}
                    />
                  }
                >
                  <Route index element={<OverviewView currentUser={currentUser || MASTER_DEMO_USER} />} />
                  <Route path="overview" element={<OverviewView currentUser={currentUser || MASTER_DEMO_USER} />} />
                  <Route path="dashboard" element={<OverviewView currentUser={currentUser || MASTER_DEMO_USER} />} />
                  <Route path="spaces" element={<MySpacesView />} />
                  <Route path="spaces/create" element={<CreateSpaceView />} />
                  <Route path="spaces/:id" element={<SpaceDetailView />} />
                  <Route path="bookings" element={<BookingsView />} />
                  <Route path="bookings/:id" element={<BookingDetailView />} />
                  <Route path="calendar" element={<CalendarView />} />
                  <Route path="live-sessions" element={<LiveSessionsView />} />
                  <Route path="live-sessions/:id" element={<LiveSessionsView />} />
                  <Route path="verification" element={<SpaceVerificationView />} />
                  <Route path="access" element={<AccessSecurityView />} />
                  <Route path="condition-reports" element={<ConditionEscrowView />} />
                  <Route path="escrow" element={<ConditionEscrowView />} />
                  <Route path="analytics" element={<AnalyticsView />} />
                  <Route path="activity" element={<ActivityAuditView />} />
                  <Route path="notifications" element={<NotificationsView />} />
                  <Route path="settings" element={<HostSettingsView />} />
                  <Route path="help" element={<HostSettingsView />} />
                </Route>

                {/* Email Verification Routes (Resend Link Handlers) */}
                <Route
                  path="/auth/verify-email/:token"
                  element={<VerifyEmailPage onUserVerified={(u) => setCurrentUser(u)} />}
                />
                <Route
                  path="/verify-email/:token"
                  element={<VerifyEmailPage onUserVerified={(u) => setCurrentUser(u)} />}
                />
                <Route
                  path="/verify-email"
                  element={<VerifyEmailPage onUserVerified={(u) => setCurrentUser(u)} />}
                />
                <Route
                  path="/list-space"
                  element={<Navigate to="/host/spaces/create" replace />}
                />
                <Route path="/calculator" element={<CalculatorPage />} />
                <Route path="/verify" element={<VerifyPage />} />
                <Route
                  path="/admin/trust-safety"
                  element={
                    <ProtectedRoute
                      currentUser={currentUser}
                      initializing={initializing}
                      onRequireAuth={() => setAuthModalOpen(true)}
                    >
                      <TrustSafetyPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/trust-safety"
                  element={
                    <ProtectedRoute
                      currentUser={currentUser}
                      initializing={initializing}
                      onRequireAuth={() => setAuthModalOpen(true)}
                    >
                      <TrustSafetyPage />
                    </ProtectedRoute>
                  }
                />
                <Route path="/architecture" element={<ArchitecturePage />} />

                {/* Fallback */}
                <Route path="*" element={<LandingPage currentUser={currentUser} />} />
              </Routes>
            </React.Suspense>
          </ErrorBoundary>
        </main>

        {/* Global Footer with Legal Modals & Trust Badges */}
        <Footer />

        {/* Mobile App Bottom Navigation Bar */}
        <MobileNav
          currentUser={currentUser}
          onOpenAuthModal={() => setAuthModalOpen(true)}
        />

        {/* Non-intrusive AI Concierge */}
        <LoopBot />

        {/* Seeker / Student Auth Modal */}
        <AuthModal
          isOpen={authModalOpen}
          onClose={() => setAuthModalOpen(false)}
          onSuccess={(user) => {
            if (user) setCurrentUser(user);
            setAuthModalOpen(false);
          }}
          onSwitchToHost={() => {
            setAuthModalOpen(false);
            setHostAuthModalOpen(true);
          }}
        />

        {/* Dedicated Property Host Auth Modal (Discom + UPI KYC) */}
        <HostAuthModal
          isOpen={hostAuthModalOpen}
          onClose={() => setHostAuthModalOpen(false)}
          onSuccess={(user) => {
            if (user) setCurrentUser(user);
            setHostAuthModalOpen(false);
          }}
          currentUser={currentUser}
          onSwitchToSeeker={() => {
            setHostAuthModalOpen(false);
            setAuthModalOpen(true);
          }}
        />
      </div>
    </BrowserRouter>
    </>
  );
};
