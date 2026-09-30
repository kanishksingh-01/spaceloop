import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { User, Booking } from '../../types';
import { getHostNotifications, getHostBookings } from '../../services/host';
import { NotificationsDrawer } from './components/NotificationsDrawer';

interface HostPortalShellProps {
  currentUser: User | null;
  onOpenHostAuthModal: () => void;
}

export const HostPortalShell: React.FC<HostPortalShellProps> = ({
  currentUser,
  onOpenHostAuthModal,
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [unreadNotifsCount, setUnreadNotifsCount] = useState(0);
  const [activeSession, setActiveSession] = useState<Booking | null>(null);

  useEffect(() => {
    // Check for active sessions and unread notifications
    const checkState = async () => {
      try {
        const notifData = await getHostNotifications();
        if (notifData) {
          setUnreadNotifsCount(notifData.unread_count || 0);
        }

        const bData = await getHostBookings({ status: 'active' });
        if (bData && bData.bookings && bData.bookings.length > 0) {
          setActiveSession(bData.bookings[0]);
        }
      } catch (err) {
        console.warn('Host shell poll error:', err);
      }
    };
    checkState();
  }, [location.pathname]);

  const navGroups = [
    {
      label: null,
      items: [
        { path: '/host', label: 'Overview', icon: 'fa-solid fa-gauge-high', exact: true },
      ],
    },
    {
      group: 'Spaces',
      items: [
        { path: '/host/spaces', label: 'My Spaces', icon: 'fa-solid fa-building' },
        { path: '/host/spaces/create', label: 'Create Space', icon: 'fa-solid fa-plus-circle' },
      ],
    },
    {
      group: 'Operations',
      items: [
        { path: '/host/bookings', label: 'Bookings', icon: 'fa-solid fa-calendar-check' },
        { path: '/host/calendar', label: 'Calendar', icon: 'fa-solid fa-calendar-days' },
        {
          path: '/host/live-sessions',
          label: 'Live Sessions',
          icon: 'fa-solid fa-satellite-dish',
          badge: activeSession ? 'Active' : undefined,
          badgeColor: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 animate-pulse',
        },
      ],
    },
    {
      group: 'Verification',
      items: [
        { path: '/host/verification', label: 'Space Verification', icon: 'fa-solid fa-shield-halved' },
        { path: '/host/access', label: 'Access & Security', icon: 'fa-solid fa-key' },
      ],
    },
    {
      group: 'Settlement',
      items: [
        { path: '/host/condition-reports', label: 'Condition Reports', icon: 'fa-solid fa-clipboard-check' },
        { path: '/host/escrow', label: 'Escrow', icon: 'fa-solid fa-vault' },
      ],
    },
    {
      group: 'Insights',
      items: [
        { path: '/host/analytics', label: 'Analytics', icon: 'fa-solid fa-chart-line' },
        { path: '/host/activity', label: 'Activity', icon: 'fa-solid fa-list-check' },
      ],
    },
    {
      group: 'System',
      items: [
        { path: '/host/settings', label: 'Settings', icon: 'fa-solid fa-gear' },
        { path: '/host/help', label: 'Help & Support', icon: 'fa-solid fa-circle-question' },
      ],
    },
  ];

  const isCurrentPath = (path: string, exact = false) => {
    if (exact) {
      return location.pathname === path || location.pathname === `${path}/` || location.pathname === '/host/dashboard';
    }
    return location.pathname.startsWith(path);
  };

  // If user is not authenticated or not a host, gate with verification card
  if (!currentUser || !currentUser.is_host) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-4">
        <div className="max-w-xl w-full bg-slate-900 border border-amber-500/30 rounded-3xl p-8 space-y-6 text-center shadow-2xl relative overflow-hidden">
          <div className="w-16 h-16 rounded-2xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 text-3xl mx-auto shadow-inner">
            <i className="fa-solid fa-house-chimney-user" />
          </div>
          <div className="space-y-2">
            <span className="px-3 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Host Portal Access
            </span>
            <h2 className="text-2xl font-black text-white">Host Authentication Required</h2>
            <p className="text-slate-400 text-xs sm:text-sm leading-relaxed max-w-md mx-auto">
              The SpaceLoop Host Portal provides operations, real-time in-room check-in telemetry, CV exit condition verification, and instant UPI micro-escrow payouts under Section 52 of the Indian Easements Act.
            </p>
          </div>
          <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row gap-3 justify-center">
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs border border-slate-700 transition"
            >
              Back to Seeker Portal
            </button>
            <button
              type="button"
              onClick={onOpenHostAuthModal}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/25 transition"
            >
              Sign In as Host / Upgrade Account →
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased selection:bg-amber-500 selection:text-slate-950">
      {/* Top Application Header */}
      <header className="sticky top-0 z-40 h-16 bg-slate-950/95 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-4">
        {/* Left: Mobile hamburger & Logo */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <i className={`fa-solid ${mobileMenuOpen ? 'fa-xmark' : 'fa-bars'} text-lg`} />
          </button>

          <button
            type="button"
            onClick={() => navigate('/host')}
            className="flex items-center gap-2.5 group focus:outline-none"
          >
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-amber-500 via-orange-500 to-amber-400 flex items-center justify-center text-slate-950 font-black text-sm shadow-md shadow-amber-500/25 group-hover:scale-105 transition-transform">
              <i className="fa-solid fa-infinity text-xs" />
            </div>
            <div className="text-left hidden sm:block">
              <span className="text-sm font-bold tracking-tight text-white flex items-center gap-1">
                SpaceLoop
                <span className="text-amber-400 font-black text-[11px] px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">
                  HOST
                </span>
              </span>
            </div>
          </button>
        </div>

        {/* Center: Active Session Live Beacon if active */}
        <div className="hidden md:flex items-center">
          {activeSession ? (
            <button
              type="button"
              onClick={() => navigate(`/host/live-sessions/${activeSession.id}`)}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-bold shadow-[0_0_15px_rgba(16,185,129,0.15)] hover:bg-emerald-500/20 transition cursor-pointer"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span>Active In-Room Session #{activeSession.id}</span>
              <span className="text-[10px] text-emerald-400/80 font-mono">→ View Cockpit</span>
            </button>
          ) : (
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Discom Meter & NPCI Verified Host Environment</span>
            </div>
          )}
        </div>

        {/* Right Action Icons & Controls */}
        <div className="flex items-center gap-2.5">
          {/* Quick Create Space */}
          <button
            type="button"
            onClick={() => navigate('/host/spaces/create')}
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md shadow-amber-500/20 transition"
          >
            <i className="fa-solid fa-plus text-[10px]" />
            <span>List Space</span>
          </button>

          {/* Notifications Button */}
          <button
            type="button"
            onClick={() => setNotificationsOpen(true)}
            className="relative p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-900 border border-slate-800 transition"
            title="Operational Notifications"
          >
            <i className="fa-solid fa-bell text-sm" />
            {unreadNotifsCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-amber-500 text-slate-950 text-[10px] font-black flex items-center justify-center shadow">
                {unreadNotifsCount}
              </span>
            )}
          </button>

          {/* Seeker Switcher */}
          <button
            type="button"
            onClick={() => navigate('/explore')}
            className="px-2.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs font-semibold transition hidden sm:flex items-center gap-1.5"
            title="Switch to Seeker Portal"
          >
            <i className="fa-solid fa-compass text-indigo-400 text-xs" />
            <span>Seeker Mode</span>
          </button>

          {/* Host Profile & OTI Pill */}
          <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
            <button
              type="button"
              onClick={() => navigate('/host/settings')}
              className="flex items-center gap-2 p-1 rounded-xl hover:bg-slate-900 transition text-left"
            >
              <div className="w-7 h-7 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-400 font-bold text-xs flex items-center justify-center">
                {currentUser.name ? currentUser.name.charAt(0).toUpperCase() : 'H'}
              </div>
              <div className="hidden xl:block">
                <div className="text-xs font-bold text-white line-clamp-1">{currentUser.name || 'Host'}</div>
                <div className="text-[10px] text-amber-400 font-mono font-semibold">
                  OTI {(currentUser as any)?.objective_trust_score ?? 99.2}/100
                </div>
              </div>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container with Sidebar + Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Desktop Sidebar Navigation */}
        <aside className="hidden lg:flex w-64 flex-col bg-slate-950 border-r border-slate-800/80 shrink-0 overflow-y-auto">
          <div className="p-4 space-y-6">
            {navGroups.map((group, gIdx) => (
              <div key={gIdx} className="space-y-1">
                {group.group && (
                  <div className="px-3 text-[10px] font-extrabold uppercase tracking-wider text-slate-500 mb-1.5">
                    {group.group}
                  </div>
                )}
                {group.items.map((item) => {
                  const active = isCurrentPath(item.path, item.exact);
                  return (
                    <button
                      key={item.path}
                      type="button"
                      onClick={() => navigate(item.path)}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                        active
                          ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-[0_0_12px_rgba(245,158,11,0.06)]'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/80 border border-transparent'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <i
                          className={`${item.icon} text-xs ${
                            active ? 'text-amber-400' : 'text-slate-500'
                          }`}
                        />
                        <span className="truncate">{item.label}</span>
                      </div>
                      {item.badge && (
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${item.badgeColor || 'bg-slate-800 text-slate-300'}`}>
                          {item.badge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>

          {/* Sidebar Host Status Footnote */}
          <div className="mt-auto p-4 border-t border-slate-800/80 bg-slate-950/60">
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-400 font-medium">Sec 52 License</span>
                <span className="text-emerald-400 font-bold">Active</span>
              </div>
              <div className="text-[10px] text-slate-500 leading-tight">
                Section 52 Indian Easements Act protected day licenses.
              </div>
            </div>
          </div>
        </aside>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="lg:hidden fixed inset-0 z-50 flex">
            <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={() => setMobileMenuOpen(false)} />
            <div className="relative w-72 max-w-[85vw] bg-slate-900 border-r border-slate-800 flex flex-col p-4 overflow-y-auto">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
                <span className="text-sm font-bold text-white">SpaceLoop Host Portal</span>
                <button
                  type="button"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4 flex-1">
                {navGroups.map((group, gIdx) => (
                  <div key={gIdx} className="space-y-1">
                    {group.group && (
                      <div className="px-2 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                        {group.group}
                      </div>
                    )}
                    {group.items.map((item) => {
                      const active = isCurrentPath(item.path, item.exact);
                      return (
                        <button
                          key={item.path}
                          type="button"
                          onClick={() => {
                            navigate(item.path);
                            setMobileMenuOpen(false);
                          }}
                          className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition ${
                            active
                              ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                          }`}
                        >
                          <div className="flex items-center gap-2.5">
                            <i className={`${item.icon} text-xs ${active ? 'text-amber-400' : 'text-slate-500'}`} />
                            <span>{item.label}</span>
                          </div>
                          {item.badge && (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500/20 text-amber-300">
                              {item.badge}
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Primary Operational Content Surface */}
        <main className="flex-1 flex flex-col overflow-y-auto bg-slate-950">
          <Outlet />
        </main>
      </div>

      {/* Global Notifications Drawer */}
      <NotificationsDrawer
        isOpen={notificationsOpen}
        onClose={() => setNotificationsOpen(false)}
        onNotificationsUpdated={(cnt) => setUnreadNotifsCount(cnt)}
      />
    </div>
  );
};
