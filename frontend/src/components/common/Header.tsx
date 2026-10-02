import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { User } from '../../types';
import { logoutUser } from '../../services/auth';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from '../../i18n';
import { NavigationDrawer, HamburgerButton } from './NavigationDrawer';
import { getHostNotifications } from '../../services/host';
import { AccountDropdown } from './AccountDropdown';

interface HeaderProps {
  currentUser: User | null;
  onOpenAuthModal: () => void;
  onOpenHostAuthModal?: () => void;
}

const getUserBadgeName = (name: string | undefined | null, fallback: string): string => {
  if (!name) return fallback;
  const stripped = name.replace(/^SpaceLoop\s*/i, '').trim();
  const first = stripped.split(' ')[0];
  if (!first || first.toLowerCase() === 'spaceloop') return fallback;
  return first;
};

export const Header: React.FC<HeaderProps> = ({
  currentUser,
  onOpenAuthModal,
  onOpenHostAuthModal,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [unreadNotifsCount, setUnreadNotifsCount] = useState(0);
  const { theme, toggleTheme } = useTheme();
  const { t } = useTranslation();

  const isHostPortal =
    location.pathname.startsWith('/host') ||
    location.pathname === '/list-space' ||
    location.pathname === '/calculator' ||
    location.pathname === '/verify';

  const isVerifiedHost = Boolean(currentUser?.is_host && (currentUser?.is_host_verified ?? true));

  useEffect(() => {
    if (!isHostPortal) return;
    const fetchNotifs = async () => {
      try {
        const notifData = await getHostNotifications();
        if (notifData) {
          setUnreadNotifsCount(notifData.unread_count || 0);
        }
      } catch (err) {
        // silent
      }
    };
    fetchNotifs();
    const interval = setInterval(fetchNotifs, 15000);
    const handleUpdate = (e: any) => {
      if (typeof e?.detail?.unread_count === 'number') {
        setUnreadNotifsCount(e.detail.unread_count);
      } else {
        fetchNotifs();
      }
    };
    window.addEventListener('host-notifications-updated', handleUpdate);
    return () => {
      clearInterval(interval);
      window.removeEventListener('host-notifications-updated', handleUpdate);
    };
  }, [isHostPortal, location.pathname]);

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

  const handleNav = (targetPath: string) => {
    if (location.pathname === targetPath) {
      window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
    } else {
      navigate(targetPath);
    }
  };

  return (
    <>
      <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/95 border-b border-slate-800/80">
        <div className={`${isHostPortal ? 'w-full px-2.5 sm:px-3 lg:px-4' : 'w-full px-3 sm:px-4 lg:px-6'} h-16 flex items-center justify-between gap-3`}>
          {/* Brand Logo & Active Portal Indicator with Far-Left Hamburger */}
          <div className={`flex items-center ${isHostPortal ? 'gap-2 shrink-0' : 'gap-2.5 sm:gap-3 shrink-0'}`}>
            <HamburgerButton
              isOpen={mobileDrawerOpen}
              onToggle={() => setMobileDrawerOpen((prev) => !prev)}
              className={isHostPortal ? '' : 'mr-0.5'}
            />
            <button
              type="button"
              onClick={() => handleNav(isHostPortal ? '/host' : '/')}
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
            <div className={`hidden ${isHostPortal ? 'xl:flex' : 'sm:flex'} items-center ml-1`}>
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
                  {isHostPortal ? (t('nav.hostPortal') || 'Host Mode') : (t('nav.seekerPortal') || 'Seeker Mode')}
                </span>
              </span>
            </div>

            {/* Host Portal Navigation: Left-aligned group beside Logo with clean spacing */}
            {isHostPortal && (
              <nav className="hidden lg:flex items-center gap-2 text-xs font-semibold ml-4 sm:ml-5 lg:ml-6 shrink-0">
                <button
                  onClick={() => handleNav('/host')}
                  className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                    location.pathname === '/host' || location.pathname === '/host/' || location.pathname === '/host/overview' || location.pathname === '/host/dashboard'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <i className="fa-solid fa-gauge-high text-amber-400" />
                  <span>{t('host.overview') || 'Overview'}</span>
                </button>
                <button
                  onClick={() => handleNav('/architecture')}
                  className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                    location.pathname === '/architecture'
                      ? 'bg-amber-500/30 text-amber-200 border border-amber-500/50 shadow-sm shadow-amber-500/20'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80 border border-transparent hover:border-slate-700/60'
                  }`}
                  title="System Architecture & Engineering Team"
                >
                  <i className="fa-solid fa-cubes text-amber-400" />
                  <span>{t('nav.architecture') || 'Architecture'}</span>
                </button>
              </nav>
            )}
            {/* Seeker Portal Navigation: Left-aligned group beside Logo / Badge */}
            {!isHostPortal && (
              <nav className="hidden lg:flex items-center gap-2 text-xs font-semibold ml-3 sm:ml-4 lg:ml-5 shrink-0">
                <button
                  onClick={() => handleNav('/explore')}
                  className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                    location.pathname === '/explore'
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <i className="fa-solid fa-compass text-indigo-400" />
                  <span>{t('nav.explore') || 'Explore Spaces'}</span>
                </button>
              </nav>
            )}
          </div>

          {/* Right Controls & Portal Switcher */}
          <div className="flex items-center gap-1.5 sm:gap-2.5 md:gap-3 shrink-0 ml-auto">
            {/* Architecture link - Right Group */}
            {!isHostPortal && (
              <button
                type="button"
                onClick={() => handleNav('/architecture')}
                className={`hidden lg:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition text-xs font-semibold shrink-0 ${
                  location.pathname === '/architecture'
                    ? 'bg-indigo-600/30 text-indigo-200 border border-indigo-500/50 shadow-sm shadow-indigo-500/20'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/80 border border-transparent hover:border-slate-700/60'
                }`}
                title="System Architecture & Engineering Team"
              >
                <i className="fa-solid fa-cubes text-indigo-400" />
                <span>{t('nav.architecture') || 'Architecture'}</span>
                <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Team
                </span>
              </button>
            )}

            {/* Theme Switcher Button */}
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

            {/* Switch to Seeker marketplace (Host mode only) */}
            {isHostPortal && (
              <button
                type="button"
                onClick={() => handleNav('/explore')}
                className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-xl bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-bold transition shrink-0"
                title="Switch to Seeker Marketplace"
              >
                <i className="fa-solid fa-compass text-indigo-400" />
                <span className="hidden sm:inline">{t('nav.switchToSeeker') || 'Seeker'}</span>
                <span className="sm:hidden">{t('nav.switchToSeeker') || 'Seeker'}</span>
              </button>
            )}

            {/* Notification Bell in Main Header (Host Interface) */}
            {isHostPortal && (
              <button
                type="button"
                onClick={() => {
                  const ev = new CustomEvent('open-host-notifications');
                  window.dispatchEvent(ev);
                  if (!location.pathname.startsWith('/host')) {
                    navigate('/host/notifications');
                  }
                }}
                className="relative p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-900 border border-slate-800 transition shrink-0"
                title={t('host.notifications') || 'Notifications'}
                aria-label="Host Notifications"
              >
                <i className="fa-solid fa-bell text-sm text-slate-300 hover:text-amber-400 transition" />
                {unreadNotifsCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-amber-500 text-slate-950 text-[10px] font-black flex items-center justify-center shadow">
                    {unreadNotifsCount}
                  </span>
                )}
              </button>
            )}

            {/* Authenticated Controls vs Single Host Sign In */}
            {isHostPortal ? (
              /* HOST PORTAL AUTH CONTROLS */
              isVerifiedHost && currentUser ? (
                <AccountDropdown
                  currentUser={currentUser}
                  isHostPortal={true}
                  onOpenAuthModal={onOpenAuthModal}
                  onOpenHostAuthModal={onOpenHostAuthModal}
                  onLogout={handleLogout}
                />
              ) : (
                <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={openHostAuth}
                    className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition shadow-md shadow-amber-500/20 shrink-0"
                  >
                    <i className="fa-solid fa-right-to-bracket text-xs" />
                    <span>Host Sign In</span>
                  </button>
                </div>
              )
            ) : (
              /* SEEKER PORTAL AUTH CONTROLS */
              currentUser ? (
                <AccountDropdown
                  currentUser={currentUser}
                  isHostPortal={false}
                  onOpenAuthModal={onOpenAuthModal}
                  onOpenHostAuthModal={onOpenHostAuthModal}
                  onLogout={handleLogout}
                />
              ) : (
                <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={onOpenAuthModal}
                    className="hidden sm:inline-block text-xs font-bold text-slate-300 hover:text-white px-2.5 sm:px-3 py-1.5 rounded-lg hover:bg-slate-900 transition"
                  >
                    {t('nav.signIn') || 'Sign In'}
                  </button>
                  <button
                    type="button"
                    onClick={onOpenAuthModal}
                    className="bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-700 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs px-2.5 sm:px-3.5 py-1.5 sm:py-2 rounded-xl shadow-md shadow-indigo-600/30 transition shrink-0"
                  >
                    {t('nav.signUp') || 'Sign Up'}
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
