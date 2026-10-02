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
    } else {
      onOpenHostAuthModal();
    }
  };

  return (
    <>
      <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/95 border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-3">
        {/* Brand Logo & Active Portal Indicator */}
        <div className="flex items-center gap-2.5">
          <HamburgerButton
            isOpen={mobileDrawerOpen}
            onToggle={() => setMobileDrawerOpen((prev) => !prev)}
            className="mr-1"
          />
          <button
            type="button"
            onClick={() => navigate(isHostPortal ? '/host/dashboard' : '/')}
            className="flex items-center gap-2.5 group shrink-0 focus:outline-none"
          >
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center shadow-lg transition duration-200 group-hover:scale-105 ${
                isHostPortal
                  ? 'bg-gradient-to-tr from-amber-600 via-orange-600 to-amber-400 shadow-amber-500/25'
                  : 'bg-gradient-to-tr from-indigo-600 via-violet-600 to-indigo-400 shadow-indigo-500/25'
              }`}
            >
              <i className="fa-solid fa-infinity text-white text-lg" />
            </div>
            <div className="text-left">
              <span className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
                Space
                <span
                  className={`text-transparent bg-clip-text ${
                    isHostPortal
                      ? 'bg-gradient-to-r from-amber-400 to-orange-400'
                      : 'bg-gradient-to-r from-indigo-400 to-violet-400'
                  }`}
                >
                  Loop
                </span>
              </span>
            </div>
          </button>

          {/* Compact Native Portal Mode Indicator */}
          <div className="hidden sm:flex items-center ml-1">
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-tight border select-none transition-all duration-200 ${
                isHostPortal
                  ? 'bg-amber-500/[0.08] text-amber-300/90 border-amber-500/25 shadow-[0_0_10px_rgba(245,158,11,0.06)]'
                  : 'bg-indigo-500/[0.08] text-indigo-300/90 border-indigo-500/25 shadow-[0_0_10px_rgba(99,102,241,0.06)]'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                  isHostPortal
                    ? 'bg-amber-400 shadow-[0_0_6px_rgba(245,158,11,0.9)]'
                    : 'bg-indigo-400 shadow-[0_0_6px_rgba(99,102,241,0.9)]'
                }`}
              />
              <span className="leading-none">
                {isHostPortal ? 'Host Mode' : 'Seeker Mode'}
              </span>
            </span>
          </div>
        </div>

        {/* Center Role-Aware Nav Links (Desktop & Tablet) */}
        <nav className="hidden lg:flex items-center gap-1 text-xs font-semibold">
          {isHostPortal ? (
            /* HOST PORTAL NAVIGATION */
            <>
              <button
                onClick={() => navigate('/host')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname === '/host' || location.pathname === '/host/overview' || location.pathname === '/host/dashboard'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <i className="fa-solid fa-gauge-high text-amber-400" />
                <span>Overview</span>
              </button>
              <button
                onClick={() => navigate('/host/spaces')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname.startsWith('/host/spaces')
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <i className="fa-solid fa-building text-amber-400" />
                <span>My Spaces</span>
              </button>
              <button
                onClick={() => navigate('/host/live-sessions')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname.startsWith('/host/live-sessions')
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <i className="fa-solid fa-satellite-dish text-emerald-400" />
                <span>Live Sessions</span>
              </button>
              <button
                onClick={() => navigate('/architecture')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname === '/architecture'
                    ? 'bg-amber-500/30 text-amber-200 border border-amber-500/50 shadow-sm shadow-amber-500/20'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/80 border border-transparent hover:border-slate-700/60'
                }`}
                title="System Architecture & Engineering Team"
              >
                <i className="fa-solid fa-cubes text-amber-400" />
                <span>{t('nav.architecture')}</span>
              </button>
            </>
          ) : (
            /* SEEKER PORTAL NAVIGATION */
            <>
              <button
                onClick={() => navigate('/explore')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname === '/explore'
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <i className="fa-solid fa-compass text-indigo-400" />
                <span>{t('nav.explore')}</span>
              </button>
              <button
                onClick={() => navigate('/host')}
                className="px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 text-amber-300 hover:text-white hover:bg-amber-500/10 border border-amber-500/20 font-bold"
                title="Launch SpaceLoop Host Operating System"
              >
                <i className="fa-solid fa-house-chimney-user text-amber-400" />
                <span>Host Portal</span>
              </button>
              <button
                onClick={() => navigate('/architecture')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname === '/architecture'
                    ? 'bg-indigo-600/30 text-indigo-200 border border-indigo-500/50 shadow-sm shadow-indigo-500/20'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/80 border border-transparent hover:border-slate-700/60'
                }`}
                title="System Architecture & Engineering Team"
              >
                <i className="fa-solid fa-cubes text-indigo-400" />
                <span>{t('nav.architecture')}</span>
                <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Team
                </span>
              </button>
            </>
          )}
        </nav>

        {/* Right Controls & Portal Switcher */}
        <div className="flex items-center gap-1.5 sm:gap-2.5 md:gap-3 shrink-0">
          {/* Multilingual Selector (Host Portal on desktop/tablet; Seeker Portal has it inside Hamburger Menu) */}
          {isHostPortal && (
            <div className="hidden sm:block">
              <LanguageSelector />
            </div>
          )}

          {/* Theme Switcher Button (Compact icon on mobile, icon+label on sm+) */}
          <button
            type="button"
            onClick={toggleTheme}
            className="inline-flex items-center justify-center gap-1.5 w-9 h-9 sm:w-auto sm:px-3 sm:py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-xs font-bold transition shadow-sm shrink-0"
            title={theme === 'dark' ? 'Switch to Light Theme (Ocean Breeze)' : 'Switch to Dark Theme (Midnight Neon)'}
            aria-label="Toggle Theme"
          >
            {theme === 'dark' ? (
              <>
                <span className="text-amber-400">☀️</span>
                <span className="hidden sm:inline">Ocean Breeze</span>
              </>
            ) : (
              <>
                <span className="text-indigo-400">🌙</span>
                <span className="hidden sm:inline">Midnight Neon</span>
              </>
            )}
          </button>

          {/* Switch between Seeker and Host portals */}
          {isHostPortal ? (
            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-xl bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-bold transition shrink-0"
              title="Switch to Seeker Marketplace"
            >
              <i className="fa-solid fa-compass text-indigo-400" />
              <span className="hidden sm:inline">{t('nav.switchToSeeker') || 'Seeker'}</span>
              <span className="sm:hidden">Seeker</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => navigate('/host')}
              className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-bold transition shrink-0"
              title="Launch SpaceLoop Host Operating System"
            >
              <i className="fa-solid fa-house-chimney-user text-amber-400" />
              <span className="hidden sm:inline">Host Portal</span>
              <span className="sm:hidden">Host</span>
            </button>
          )}

          {/* Authenticated Controls vs Sign In Buttons */}
          {isHostPortal ? (
            /* HOST PORTAL AUTH CONTROLS */
            isVerifiedHost ? (
              <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
                <div className="flex items-center gap-1.5 px-2 sm:px-2.5 py-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-slate-200">
                  <span>🏡 {currentUser?.name?.split(' ')[0] || 'Host'}</span>
                </div>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="p-2 sm:px-2.5 sm:py-1.5 rounded-xl bg-slate-900 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 border border-slate-800 text-xs font-semibold transition"
                  title="Sign Out"
                >
                  <i className="fa-solid fa-arrow-right-from-bracket" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
                <button
                  type="button"
                  onClick={openHostAuth}
                  className="hidden sm:inline-block text-xs font-bold text-slate-300 hover:text-white px-2.5 sm:px-3 py-1.5 rounded-lg hover:bg-slate-900 transition"
                >
                  Host Sign In
                </button>
                <button
                  type="button"
                  onClick={openHostAuth}
                  className="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs px-2.5 sm:px-3.5 py-1.5 sm:py-2 rounded-xl shadow-md shadow-amber-500/25 transition shrink-0"
                >
                  Register Space
                </button>
              </div>
            )
          ) : (
            /* SEEKER PORTAL AUTH CONTROLS */
            currentUser ? (
              <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => navigate('/dashboard')}
                  className="flex items-center gap-1.5 px-2 sm:px-2.5 py-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-slate-200"
                >
                  <span>🎓 {currentUser.name?.split(' ')[0] || 'Seeker'}</span>
                </button>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="p-2 sm:px-2.5 sm:py-1.5 rounded-xl bg-slate-900 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 border border-slate-800 text-xs font-semibold transition"
                  title="Sign Out"
                >
                  <i className="fa-solid fa-arrow-right-from-bracket" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
                <button
                  type="button"
                  onClick={onOpenAuthModal}
                  className="hidden sm:inline-block text-xs font-bold text-slate-300 hover:text-white px-2.5 sm:px-3 py-1.5 rounded-lg hover:bg-slate-900 transition"
                >
                  Seeker Sign In
                </button>
                <button
                  type="button"
                  onClick={onOpenAuthModal}
                  className="bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-700 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs px-2.5 sm:px-3.5 py-1.5 sm:py-2 rounded-xl shadow-md shadow-indigo-600/30 transition shrink-0"
                >
                  Student SSO
                </button>
              </div>
            )
          )}

        </div>
      </div>
    </header>

    {/* Interactive Physical Navigation Drawer & Edge-Swipe Engine */}
    <NavigationDrawer
      isOpen={mobileDrawerOpen}
      onClose={() => setMobileDrawerOpen(false)}
      onOpen={() => setMobileDrawerOpen(true)}
      currentUser={currentUser}
      onOpenAuthModal={onOpenAuthModal}
      onOpenHostAuthModal={onOpenHostAuthModal}
    />
  </>
);
};
