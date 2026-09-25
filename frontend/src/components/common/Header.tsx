import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { User } from '../../types';
import { logoutUser } from '../../services/auth';

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
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('spaceloop-theme');
      if (saved === 'light' || saved === 'dark') return saved;
      return document.documentElement.classList.contains('light') ? 'light' : 'dark';
    }
    return 'dark';
  });

  React.useEffect(() => {
    if (typeof document !== 'undefined') {
      if (theme === 'light') {
        document.documentElement.classList.add('light');
        document.documentElement.classList.remove('dark');
        localStorage.setItem('spaceloop-theme', 'light');
      } else {
        document.documentElement.classList.add('dark');
        document.documentElement.classList.remove('light');
        localStorage.setItem('spaceloop-theme', 'dark');
      }
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

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
      onOpenAuthModal();
    }
  };

  return (
    <header className="sticky top-0 z-40 backdrop-blur-md bg-slate-950/95 border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-3">
        {/* Brand Logo & Active Portal Indicator */}
        <div className="flex items-center gap-2.5">
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
                🏡 Host Portal
              </span>
            ) : (
              <span className="text-[10px] uppercase font-extrabold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 flex items-center gap-1">
                ⚡ Seeker Portal
              </span>
            )}
          </div>
        </div>

        {/* Center Role-Aware Nav Links (Desktop) */}
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
                <span>Host Dashboard</span>
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
                <span>List Space</span>
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
                <span>Earnings Calculator</span>
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
                <span>Explore Spaces</span>
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
                <span>My Bookings</span>
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
                <span>How It Works</span>
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
                <span>Trust & Safety</span>
              </button>
            </>
          )}
        </nav>

        {/* Right Controls & Portal Switcher */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {/* Theme Switcher Button */}
          <button
            type="button"
            onClick={toggleTheme}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-xs font-bold transition shadow-sm"
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

          {/* Portal Switcher Button */}
          {isHostPortal ? (
            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-bold transition"
              title="Switch to Seeker Portal"
            >
              <span>🎓 Switch to Seeker</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => navigate('/host/dashboard')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-bold transition"
              title="Switch to Host Portal"
            >
              <span>🏡 Switch to Host</span>
            </button>
          )}

          {/* Authenticated Controls vs Sign In Buttons */}
          {isHostPortal ? (
            /* HOST PORTAL AUTH CONTROLS */
            isVerifiedHost ? (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => navigate('/list-space')}
                  className="hidden sm:inline-flex items-center gap-1.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs px-3.5 py-1.5 rounded-xl shadow-md shadow-amber-500/20 transition"
                >
                  <i className="fa-solid fa-plus text-[10px]" /> Add Space
                </button>
                <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-slate-200">
                  <span>🏡 {currentUser?.name?.split(' ')[0] || 'Host'}</span>
                </div>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="px-2.5 py-1.5 rounded-xl bg-slate-900 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 border border-slate-800 text-xs font-semibold transition"
                  title="Sign Out"
                >
                  <i className="fa-solid fa-arrow-right-from-bracket" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={openHostAuth}
                  className="text-xs font-bold text-slate-300 hover:text-white px-3 py-1.5 rounded-lg hover:bg-slate-900 transition"
                >
                  Host Sign In
                </button>
                <button
                  type="button"
                  onClick={openHostAuth}
                  className="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs px-3.5 py-2 rounded-xl shadow-md shadow-amber-500/25 transition"
                >
                  Register Property
                </button>
              </div>
            )
          ) : (
            /* SEEKER PORTAL AUTH CONTROLS */
            currentUser ? (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => navigate('/dashboard')}
                  className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-slate-200"
                >
                  <span>🎓 {currentUser.name?.split(' ')[0] || 'Seeker'}</span>
                </button>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="px-2.5 py-1.5 rounded-xl bg-slate-900 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 border border-slate-800 text-xs font-semibold transition"
                  title="Sign Out"
                >
                  <i className="fa-solid fa-arrow-right-from-bracket" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={onOpenAuthModal}
                  className="text-xs font-bold text-slate-300 hover:text-white px-3 py-1.5 rounded-lg hover:bg-slate-900 transition"
                >
                  Seeker Sign In
                </button>
                <button
                  type="button"
                  onClick={onOpenAuthModal}
                  className="bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-700 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs px-3.5 py-2 rounded-xl shadow-md shadow-indigo-600/30 transition"
                >
                  Student SSO
                </button>
              </div>
            )
          )}

          {/* Mobile Menu Toggle Button */}
          <button
            type="button"
            onClick={() => setMobileDrawerOpen(!mobileDrawerOpen)}
            className="lg:hidden p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white focus:outline-none"
            aria-label="Toggle Navigation Menu"
          >
            <i className="fa-solid fa-bars text-sm" />
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileDrawerOpen && (
        <div className="lg:hidden border-t border-slate-800/80 bg-slate-950/95 backdrop-blur-xl px-4 py-4 space-y-3 shadow-2xl">
          {currentUser && (
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <div>
                  <div className="text-xs font-bold text-white">{currentUser.name}</div>
                  <div className="text-[10px] text-slate-400">
                    {currentUser.email} • {currentUser.role}
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="text-xs text-rose-400 font-semibold"
              >
                Sign Out
              </button>
            </div>
          )}

          {/* Mobile Portal Navigation Links */}
          <div className="grid grid-cols-2 gap-2 text-xs font-medium">
            {isHostPortal ? (
              <>
                <button
                  onClick={() => {
                    navigate('/host/dashboard');
                    setMobileDrawerOpen(false);
                  }}
                  className="p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800 text-slate-200 flex items-center gap-2 text-left"
                >
                  <i className="fa-solid fa-chart-pie text-amber-400" /> Host Dashboard
                </button>
                <button
                  onClick={() => {
                    navigate('/list-space');
                    setMobileDrawerOpen(false);
                  }}
                  className="p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800 text-slate-200 flex items-center gap-2 text-left"
                >
                  <i className="fa-solid fa-plus text-amber-400" /> List Space
                </button>
                <button
                  onClick={() => {
                    navigate('/calculator');
                    setMobileDrawerOpen(false);
                  }}
                  className="p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800 text-slate-200 flex items-center gap-2 text-left"
                >
                  <i className="fa-solid fa-calculator text-slate-400" /> Calculator
                </button>
                <button
                  onClick={() => {
                    navigate('/verify');
                    setMobileDrawerOpen(false);
                  }}
                  className="p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800 text-slate-200 flex items-center gap-2 text-left"
                >
                  <i className="fa-solid fa-shield-halved text-emerald-400" /> KYC Verify
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => {
                    navigate('/explore');
                    setMobileDrawerOpen(false);
                  }}
                  className="p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800 text-slate-200 flex items-center gap-2 text-left"
                >
                  <i className="fa-solid fa-compass text-indigo-400" /> Explore
                </button>
                <button
                  onClick={() => {
                    navigate('/dashboard');
                    setMobileDrawerOpen(false);
                  }}
                  className="p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800 text-slate-200 flex items-center gap-2 text-left"
                >
                  <i className="fa-solid fa-calendar-check text-slate-400" /> My Bookings
                </button>
                <button
                  onClick={() => {
                    navigate('/how-it-works');
                    setMobileDrawerOpen(false);
                  }}
                  className="p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800 text-slate-200 flex items-center gap-2 text-left"
                >
                  <i className="fa-solid fa-circle-question text-slate-400" /> How It Works
                </button>
                <button
                  onClick={() => {
                    navigate('/admin/trust-safety');
                    setMobileDrawerOpen(false);
                  }}
                  className="p-2 rounded-lg bg-rose-950/30 hover:bg-rose-900/50 text-rose-300 flex items-center gap-2 text-left"
                >
                  <i className="fa-solid fa-shield-halved text-rose-400" /> Trust & Safety
                </button>
              </>
            )}
          </div>

          {/* Theme & Switch Portal Buttons in Mobile */}
          <div className="pt-2 border-t border-slate-800 space-y-2">
            <button
              type="button"
              onClick={toggleTheme}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-bold text-center flex items-center justify-center gap-2"
            >
              <span>{theme === 'dark' ? '☀️ Switch to Light Theme (Ocean Breeze)' : '🌙 Switch to Dark Theme (Midnight Neon)'}</span>
            </button>

            {isHostPortal ? (
              <button
                type="button"
                onClick={() => {
                  navigate('/explore');
                  setMobileDrawerOpen(false);
                }}
                className="w-full py-2.5 rounded-xl bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-bold text-center"
              >
                ⚡ Switch to Seeker Portal
              </button>
            ) : (
              <button
                type="button"
                onClick={() => {
                  navigate('/host/dashboard');
                  setMobileDrawerOpen(false);
                }}
                className="w-full py-2.5 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-bold text-center"
              >
                🏡 Switch to Host Portal
              </button>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
