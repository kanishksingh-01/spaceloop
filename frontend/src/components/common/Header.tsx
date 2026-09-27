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
    <header className="sticky top-0 z-40 backdrop-blur-md bg-slate-950/95 border-b border-slate-800/80">
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

          {/* Portal Identity Pill */}
          <div className="hidden sm:flex items-center">
            {isHostPortal ? (
              <span className="text-[10px] uppercase font-extrabold tracking-wider px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                🏡 {t('nav.hostPortal')}
              </span>
            ) : (
              <span className="text-[10px] uppercase font-extrabold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 flex items-center gap-1">
                ⚡ {t('nav.seekerPortal')}
              </span>
            )}
          </div>
        </div>

        {/* Center Role-Aware Nav Links (Desktop & Tablet) */}
        <nav className="hidden lg:flex items-center gap-1 text-xs font-semibold">
          {isHostPortal ? (
            /* HOST PORTAL NAVIGATION */
            <>
              <button
                onClick={() => navigate('/host/dashboard')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname === '/host/dashboard' || location.pathname === '/host'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <i className="fa-solid fa-chart-pie text-amber-400" />
                <span>{t('nav.hostDashboard')}</span>
              </button>
              <button
                onClick={() => navigate('/list-space')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname === '/list-space'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <i className="fa-solid fa-plus-circle text-amber-400" />
                <span>{t('nav.listSpace')}</span>
              </button>
              <button
                onClick={() => navigate('/calculator')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname === '/calculator'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <i className="fa-solid fa-calculator text-slate-400" />
                <span>{t('nav.calculator')}</span>
              </button>
              <button
                onClick={() => navigate('/verify')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname === '/verify'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <i className="fa-solid fa-shield-halved text-emerald-400" />
                <span>Discom & KYC</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
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
                <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  Team
                </span>
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
                onClick={() => navigate('/dashboard')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname === '/dashboard'
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <i className="fa-solid fa-calendar-check text-slate-400" />
                <span>{t('nav.myBookings')}</span>
              </button>
              <button
                onClick={() => navigate('/how-it-works')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname === '/how-it-works'
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <i className="fa-solid fa-circle-question text-slate-400" />
                <span>{t('nav.howItWorks')}</span>
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
              <button
                onClick={() => navigate('/admin/trust-safety')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname.includes('trust-safety')
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
                title="Trust & Safety Console"
              >
                <i className="fa-solid fa-shield-halved text-rose-400" />
                <span>{t('nav.trustSafety')}</span>
              </button>
            </>
          )}
        </nav>

        {/* Right Controls & Portal Switcher */}
        <div className="flex items-center gap-1.5 sm:gap-2.5 md:gap-3 shrink-0">
          {/* Multilingual Selector (Desktop & Tablet; also accessible in Drawer on all devices) */}
          <div className="hidden sm:block">
            <LanguageSelector />
          </div>

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

          {/* Portal Switcher Button (Visible on large screens; Drawer has dedicated switcher for mobile/tablet) */}
          {isHostPortal ? (
            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="hidden lg:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-bold transition shrink-0"
              title="Switch to Seeker Portal"
            >
              <span>🎓 {t('nav.switchToSeeker')}</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => navigate('/host/dashboard')}
              className="hidden lg:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-bold transition shrink-0"
              title="Switch to Host Portal"
            >
              <span>🏡 {t('nav.switchToHost')}</span>
            </button>
          )}

          {/* Authenticated Controls vs Sign In Buttons */}
          {isHostPortal ? (
            /* HOST PORTAL AUTH CONTROLS */
            isVerifiedHost ? (
              <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => navigate('/list-space')}
                  className="hidden sm:inline-flex items-center gap-1.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs px-3 py-1.5 rounded-xl shadow-md shadow-amber-500/20 transition"
                >
                  <i className="fa-solid fa-plus text-[10px]" /> Add Space
                </button>
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

      {/* Interactive Physical Navigation Drawer & Edge-Swipe Engine */}
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
