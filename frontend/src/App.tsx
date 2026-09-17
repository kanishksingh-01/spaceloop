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
import { DemoModal } from './components/common/DemoModal';

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
import SpaceLoopApp from './SpaceLoopApp';
import ExploreView from './components/common/ExploreView';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [hostAuthModalOpen, setHostAuthModalOpen] = useState(false);
  const [demoModalOpen, setDemoModalOpen] = useState(false);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      try {
        const user = await getCurrentUser();
        setCurrentUser(user);
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
          onOpenDemoModal={() => setDemoModalOpen(true)}
        />

        {/* Application Routes */}
        <main className="flex-1 flex flex-col">
          <Routes>
            {/* Seeker Routes */}
            <Route path="/" element={<LandingPage currentUser={currentUser} />} />
            <Route path="/explore" element={<ExplorePage />} />
            <Route path="/curated" element={<ExploreView />} />
            <Route path="/explore-view" element={<ExploreView />} />
            <Route path="/boutique" element={<SpaceLoopApp />} />
            <Route path="/space/:id" element={<SpaceDetailPage currentUser={currentUser} />} />
            <Route path="/session/:id" element={<SessionPage />} />
            <Route path="/dashboard" element={<DashboardPage currentUser={currentUser} />} />
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
            <Route path="/list-space" element={<ListSpacePage currentUser={currentUser} />} />
            <Route path="/calculator" element={<CalculatorPage />} />
            <Route path="/verify" element={<VerifyPage />} />

            {/* Fallback */}
            <Route path="*" element={<LandingPage currentUser={currentUser} />} />
          </Routes>
        </main>

        {/* Global Footer with Legal Modals & Evaluation Console */}
        <Footer onOpenDemoModal={() => setDemoModalOpen(true)} />

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
          onSuccess={() => setAuthModalOpen(false)}
          onSwitchToHost={() => {
            setAuthModalOpen(false);
            setHostAuthModalOpen(true);
          }}
        />

        {/* Dedicated Property Host Auth Modal (Discom + UPI KYC) */}
        <HostAuthModal
          isOpen={hostAuthModalOpen}
          onClose={() => setHostAuthModalOpen(false)}
          onSuccess={() => setHostAuthModalOpen(false)}
          currentUser={currentUser}
          onSwitchToSeeker={() => {
            setHostAuthModalOpen(false);
            setAuthModalOpen(true);
          }}
        />

        {/* Judge / Demo Evaluation Console Modal */}
        <DemoModal
          isOpen={demoModalOpen}
          onClose={() => setDemoModalOpen(false)}
          currentRole={currentUser?.role}
        />
      </div>
    </BrowserRouter>
  );
};
