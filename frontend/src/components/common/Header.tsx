import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { User } from '../../types';
import { logoutUser } from '../../services/auth';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from '../../i18n';
import { LanguageSelector } from './LanguageSelector';
import { NavigationDrawer, HamburgerButton } from './NavigationDrawer';

interface HeaderProps {
  currentUser: User | null;
  onOpenAuthModal: () => void;
  onOpenHostAuthModal?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentUser,
  onOpenAuthModal,
  onOpenHostAuthModal,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();
  const { t } = useTranslation();

  const isHostPortal =
    location.pathname.startsWith('/host') ||
    location.pathname === '/list-space' ||
    location.pathname === '/calculator' ||
    location.pathname === '/verify';

  const isVerifiedHost = Boolean(currentUser?.is_host && (currentUser?.is_host_verified ?? true));

  const handleLogout = async () => {
    try {
      await logoutUser();
      window.location.reload();
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  const openHostAuth = () => {
    if (onOpenHostAuthModal) {
      onOpenHostAuthModal();
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-slate-950/90 backdrop-blur-md border-b border-slate-800/80 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Left: Hamburger & Logo */}
        <div className="flex items-center gap-3">
          <HamburgerButton
            isOpen={mobileDrawerOpen}
            onToggle={() => setMobileDrawerOpen((prev) => !prev)}
            className="lg:hidden mr-1"
          />
          <button
            type="button"
            onClick={() => navigate(isHostPortal ? '/host' : '/')}
            className="flex items-center gap-2.5 group focus:outline-none"
          >
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold shadow-sm transition-transform duration-200 group-hover:scale-105 ${
                isHostPortal
                  ? 'bg-amber-500 text-slate-950'
                  : 'bg-indigo-600 text-white'
              }`}
            >
              <i className="fa-solid fa-infinity" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-white">
                SpaceLoop
              </span>
              <span
                className={`hidden sm:inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${
                  isHostPortal
                    ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                    : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                }`}
              >
                {isHostPortal ? 'Host OS' : 'Seeker'}
              </span>
            </div>
          </button>
        </div>

        {/* Center: Clean Nav Links */}
        <nav className="hidden lg:flex items-center gap-1 text-xs font-medium text-slate-300">
          {isHostPortal ? (
            <>
              <button
                onClick={() => navigate('/host')}
                className={`px-3 py-1.5 rounded-lg transition ${
                  location.pathname === '/host' || location.pathname === '/host/overview' || location.pathname === '/host/dashboard'
                    ? 'bg-slate-800 text-white font-semibold'
                    : 'hover:text-white hover:bg-slate-800/60'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => navigate('/host/spaces')}
                className={`px-3 py-1.5 rounded-lg transition ${
                  location.pathname.startsWith('/host/spaces')
                    ? 'bg-slate-800 text-white font-semibold'
                    : 'hover:text-white hover:bg-slate-800/60'
                }`}
              >
                My Spaces
              </button>
              <button
                onClick={() => navigate('/host/bookings')}
                className={`px-3 py-1.5 rounded-lg transition ${
                  location.pathname.startsWith('/host/bookings')
                    ? 'bg-slate-800 text-white font-semibold'
                    : 'hover:text-white hover:bg-slate-800/60'
                }`}
              >
                Bookings
              </button>
              <button
                onClick={() => navigate('/host/live-sessions')}
                className={`px-3 py-1.5 rounded-lg transition ${
                  location.pathname.startsWith('/host/live-sessions')
                    ? 'bg-slate-800 text-white font-semibold'
                    : 'hover:text-white hover:bg-slate-800/60'
                }`}
              >
                Live Sessions
              </button>
              <button
                onClick={() => navigate('/architecture')}
                className={`px-3 py-1.5 rounded-lg transition ${
                  location.pathname === '/architecture'
                    ? 'bg-slate-800 text-white font-semibold'
                    : 'hover:text-white hover:bg-slate-800/60'
                }`}
              >
                Architecture & Team
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => navigate('/explore')}
                className={`px-3 py-1.5 rounded-lg transition ${
                  location.pathname === '/explore'
                    ? 'bg-slate-800 text-white font-semibold'
                    : 'hover:text-white hover:bg-slate-800/60'
                }`}
              >
                Explore Spaces
              </button>
              <button
                onClick={() => navigate('/how-it-works')}
                className={`px-3 py-1.5 rounded-lg transition ${
                  location.pathname === '/how-it-works'
                    ? 'bg-slate-800 text-white font-semibold'
                    : 'hover:text-white hover:bg-slate-800/60'
                }`}
              >
                How It Works
              </button>
              <button
                onClick={() => navigate('/architecture')}
                className={`px-3 py-1.5 rounded-lg transition ${
                  location.pathname === '/architecture'
                    ? 'bg-slate-800 text-white font-semibold'
                    : 'hover:text-white hover:bg-slate-800/60'
                }`}
              >
                Architecture & Team
              </button>
            </>
          )}
        </nav>

        {/* Right: Actions, Switcher, Theme & Auth */}
        <div className="flex items-center gap-2.5 shrink-0">
          {/* Theme Toggle (Clean Icon Button) */}
          <button
            type="button"
            onClick={toggleTheme}
            className="w-8 h-8 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 flex items-center justify-center text-xs transition"
            title={theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
            aria-label="Toggle Theme"
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>

          {/* Single Mode Switcher Button */}
          {isHostPortal ? (
            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 text-xs font-semibold transition"
            >
              <span>Explore as Seeker</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => navigate('/host')}
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-semibold transition"
            >
              <span>🏡 Host Portal</span>
            </button>
          )}

          {/* User Auth Controls */}
          {currentUser ? (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => navigate(isHostPortal ? '/host' : '/dashboard')}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 text-xs font-medium text-slate-200 transition"
              >
                <div className="w-5 h-5 rounded-full bg-indigo-600/30 text-indigo-300 flex items-center justify-center font-bold text-[10px] uppercase">
                  {(currentUser.name || currentUser.email || 'U').charAt(0)}
                </div>
                <span className="max-w-[100px] truncate">{currentUser.name || currentUser.email?.split('@')[0]}</span>
              </button>
              <button
                type="button"
                onClick={handleLogout}
                className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
                title="Sign Out"
                aria-label="Sign Out"
              >
                <i className="fa-solid fa-arrow-right-from-bracket text-xs" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={isHostPortal ? openHostAuth : onOpenAuthModal}
                className="text-xs font-medium text-slate-300 hover:text-white px-2.5 py-1.5 rounded-lg hover:bg-slate-850 transition"
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={isHostPortal ? openHostAuth : onOpenAuthModal}
                className={`text-xs font-semibold px-3.5 py-1.5 rounded-lg transition ${
                  isHostPortal
                    ? 'bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold'
                    : 'bg-indigo-600 hover:bg-indigo-500 text-white'
                }`}
              >
                {isHostPortal ? 'List a Space' : 'Get Started'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Mobile Drawer */}
      <NavigationDrawer
        isOpen={mobileDrawerOpen}
        onClose={() => setMobileDrawerOpen(false)}
        onOpen={() => setMobileDrawerOpen(true)}
        currentUser={currentUser}
        onOpenAuthModal={onOpenAuthModal}
        onOpenHostAuthModal={onOpenHostAuthModal}
      />
    </header>
  );
};
