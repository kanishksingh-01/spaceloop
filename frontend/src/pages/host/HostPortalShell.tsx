import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { User, Booking } from '../../types';
import { getHostNotifications, getHostBookings } from '../../services/host';
import { MASTER_DEMO_USER } from '../../services/auth';
import { NotificationsDrawer } from './components/NotificationsDrawer';
import { useI18n } from '../../i18n/I18nContext';

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
  const { t } = useI18n();

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
        } else {
          setActiveSession(null);
        }
      } catch (err) {
        console.warn('Host shell poll error:', err);
      }
    };
    checkState();
    const interval = setInterval(checkState, 15000);
    return () => clearInterval(interval);
  }, [location.pathname]);

  useEffect(() => {
    const handleOpenNotifs = () => setNotificationsOpen(true);
    window.addEventListener('open-host-notifications', handleOpenNotifs);
    return () => window.removeEventListener('open-host-notifications', handleOpenNotifs);
  }, []);

  const navGroups = [
    {
      label: null,
      items: [
        { path: '/host', label: t('host.overview'), icon: 'fa-solid fa-gauge-high', exact: true },
        {
          path: '/host/notifications',
          label: t('host.notifications'),
          icon: 'fa-solid fa-bell',
          badge: unreadNotifsCount > 0 ? `${unreadNotifsCount}` : undefined,
          badgeColor: 'bg-amber-500 text-slate-950 font-black',
        },
      ],
    },
    {
      group: t('host.spacesGroup'),
      items: [
        { path: '/host/spaces', label: t('host.mySpaces'), icon: 'fa-solid fa-building' },
        { path: '/host/spaces/create', label: t('host.createSpace'), icon: 'fa-solid fa-plus-circle' },
      ],
    },
    {
      group: t('host.operationsGroup'),
      items: [
        { path: '/host/bookings', label: t('host.bookings'), icon: 'fa-solid fa-calendar-check' },
        { path: '/host/calendar', label: t('host.calendar'), icon: 'fa-solid fa-calendar-days' },
        {
          path: '/host/live-sessions',
          label: t('host.liveSessions'),
          icon: 'fa-solid fa-satellite-dish',
          badge: activeSession ? t('common.activeSession') : undefined,
          badgeColor: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 animate-pulse',
        },
      ],
    },
    {
      group: t('host.verificationGroup'),
      items: [
        { path: '/host/verification', label: t('host.verification'), icon: 'fa-solid fa-shield-halved' },
        { path: '/host/access', label: t('host.accessSecurity'), icon: 'fa-solid fa-key' },
      ],
    },
    {
      group: t('host.settlementGroup'),
      items: [
        { path: '/host/condition-reports', label: t('host.conditionEscrow'), icon: 'fa-solid fa-clipboard-check' },
        { path: '/host/escrow', label: t('host.escrowManagementTitle'), icon: 'fa-solid fa-vault' },
      ],
    },
    {
      group: t('host.insightsGroup'),
      items: [
        { path: '/host/analytics', label: t('host.analytics'), icon: 'fa-solid fa-chart-line' },
        { path: '/host/activity', label: t('host.activityAudit'), icon: 'fa-solid fa-list-check' },
      ],
    },
    {
      group: t('host.systemGroup'),
      items: [
        { path: '/host/settings', label: t('host.settings'), icon: 'fa-solid fa-gear' },
        { path: '/host/help', label: t('nav.help'), icon: 'fa-solid fa-circle-question' },
      ],
    },
  ];

  const isCurrentPath = (path: string, exact = false) => {
    if (exact) {
      return location.pathname === path || location.pathname === `${path}/` || location.pathname === '/host/dashboard';
    }
    return location.pathname.startsWith(path);
  };

  const effectiveUser = (currentUser && currentUser.is_host) ? currentUser : MASTER_DEMO_USER;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased selection:bg-amber-500 selection:text-slate-950">
      {/* Optional Preview Mode Notice for unauthenticated visitors */}
      {(!currentUser || !currentUser.is_host) && (
        <div className="bg-amber-500/10 border-b border-amber-500/25 px-4 py-2 flex items-center justify-between text-xs text-amber-300 flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse shrink-0" />
            <span>
              <strong>Host Interactive Preview Mode:</strong> Active host telemetry loaded with verified Discom CA and ₹100 UPI Micro-Escrow.
            </span>
          </div>
        </div>
      )}

      {/* Main Container with Sidebar + Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Desktop Sidebar Navigation */}
        <aside className="hidden lg:flex w-60 flex-col bg-slate-950 border-r border-slate-800/80 shrink-0 overflow-y-auto">
          <div className="p-3.5 space-y-5">
            {navGroups.map((group, gIdx) => (
              <div key={gIdx} className="space-y-0.5">
                {group.group && (
                  <div className="px-3 pt-2 text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-1">
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
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                        active
                          ? 'bg-amber-500/10 text-amber-400 font-bold border border-amber-500/25 shadow-sm'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
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
                        <span
                          className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                            item.badgeColor || 'bg-slate-800 text-slate-400'
                          }`}
                        >
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
          <div className="mt-auto p-3.5 border-t border-slate-800/80 bg-slate-950/60">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-1">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-400 font-medium">Sec 52 License</span>
                <span className="text-emerald-400 font-semibold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  Active
                </span>
              </div>
              <div className="text-[10px] text-slate-500 leading-tight">
                Section 52 Indian Easements Act protected day licenses.
              </div>
            </div>
          </div>
        </aside>

        {/* Primary Operational Content Surface */}
        <main className="flex-1 flex flex-col overflow-y-auto bg-slate-950 min-h-0">
          <Outlet context={{ currentUser, onOpenHostAuthModal }} />
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
