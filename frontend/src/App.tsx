import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { User } from './types';
import { getCurrentUser } from './services/auth';
import { Header } from './components/common/Header';
import { Footer } from './components/common/Footer';
import { MobileNav } from './components/common/MobileNav';
import { LoopBot } from './components/common/LoopBot';
import { AuthModal } from './components/common/AuthModal';
import { HostAuthModal } from './components/common/HostAuthModal';

import { LandingPage } from './pages/LandingPage';
import { ExplorePage } from './pages/ExplorePage';
import { SpaceDetailPage } from './pages/SpaceDetailPage';
import { ListSpacePage } from './pages/ListSpacePage';
import { DashboardPage } from './pages/DashboardPage';
import { HostDashboardPage } from './pages/HostDashboardPage';
import { SessionPage } from './pages/SessionPage';
import { CalculatorPage } from './pages/CalculatorPage';
import { VerifyPage } from './pages/VerifyPage';
import { HowItWorksPage } from './pages/HowItWorksPage';
import { ErrorBoundary } from './components/common/ErrorBoundary';

interface ProtectedRouteProps {
  currentUser: User | null;
  initializing: boolean;
  onRequireAuth: () => void;
  children: React.ReactElement;
}

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

  useEffect(() => {
    const initAuth = async () => {
      try {
        const user = await getCurrentUser();
        if (user) {
          setCurrentUser(user);
        }
      } catch (err) {
        console.error('Failed to restore session:', err);
      } finally {
        setInitializing(false);
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
            <Routes>
              {/* Seeker Routes */}
              <Route path="/" element={<LandingPage currentUser={currentUser} />} />
              <Route path="/explore" element={<ExplorePage />} />
              <Route path="/curated" element={<ExplorePage />} />
              <Route path="/explore-view" element={<ExplorePage />} />
              <Route path="/boutique" element={<ExplorePage />} />
              <Route path="/space/:id" element={<SpaceDetailPage currentUser={currentUser} />} />
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

              {/* Host Dedicated Routes */}
              <Route
                path="/host"
                element={
                  <HostDashboardPage
                    currentUser={currentUser}
                    onOpenHostAuthModal={() => setHostAuthModalOpen(true)}
                  />
                }
              />
              <Route
                path="/host/dashboard"
                element={
                  <HostDashboardPage
                    currentUser={currentUser}
                    onOpenHostAuthModal={() => setHostAuthModalOpen(true)}
                  />
                }
              />
              <Route
                path="/list-space"
                element={
                  <ProtectedRoute
                    currentUser={currentUser}
                    initializing={initializing}
                    onRequireAuth={() => setHostAuthModalOpen(true)}
                  >
                    <ListSpacePage currentUser={currentUser} />
                  </ProtectedRoute>
                }
              />
              <Route path="/calculator" element={<CalculatorPage />} />
              <Route path="/verify" element={<VerifyPage />} />

              {/* Fallback */}
              <Route path="*" element={<LandingPage currentUser={currentUser} />} />
            </Routes>
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
  );
};
