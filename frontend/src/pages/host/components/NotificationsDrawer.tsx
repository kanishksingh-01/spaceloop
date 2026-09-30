import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { HostNotification, getHostNotifications } from '../../../services/host';

interface NotificationsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onNotificationsUpdated?: (unreadCount: number) => void;
}

export const NotificationsDrawer: React.FC<NotificationsDrawerProps> = ({
  isOpen,
  onClose,
  onNotificationsUpdated,
}) => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<HostNotification[]>([]);
  const [filter, setFilter] = useState<'all' | 'new_booking' | 'check_in' | 'active_session' | 'verification'>('all');
  const [loading, setLoading] = useState(false);

  const fetchNotifs = async () => {
    setLoading(true);
    try {
      const data = await getHostNotifications();
      if (data && data.notifications) {
        setNotifications(data.notifications);
        if (onNotificationsUpdated) {
          onNotificationsUpdated(data.unread_count || 0);
        }
      }
    } catch (e) {
      console.warn('Failed to load host notifications:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchNotifs();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const filtered = filter === 'all' ? notifications : notifications.filter((n) => n.type === filter);

  const handleNotificationClick = (notif: HostNotification) => {
    // Mark as read locally
    setNotifications((prev) =>
      prev.map((n) => (n.id === notif.id ? { ...n, unread: false } : n))
    );
    onClose();
    if (notif.action_url) {
      navigate(notif.action_url);
    }
  };

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, unread: false })));
    if (onNotificationsUpdated) onNotificationsUpdated(0);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-slate-900 border-l border-slate-800 text-white shadow-2xl flex flex-col">
          {/* Header */}
          <div className="p-5 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 text-sm">
                <i className="fa-solid fa-bell" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Host Notifications</h3>
                <p className="text-[11px] text-slate-400">Operational alerts and physical access events</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={markAllRead}
                className="text-[11px] font-semibold text-slate-400 hover:text-amber-400 transition"
              >
                Mark all read
              </button>
              <button
                type="button"
                onClick={onClose}
                className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Filter Pills */}
          <div className="px-5 py-3 border-b border-slate-800/80 bg-slate-950/30 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
            {(['all', 'new_booking', 'check_in', 'active_session', 'verification'] as const).map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFilter(f)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-bold whitespace-nowrap transition ${
                  filter === f
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                {f === 'all'
                  ? 'All'
                  : f === 'new_booking'
                  ? 'Bookings'
                  : f === 'check_in'
                  ? 'Arrivals'
                  : f === 'active_session'
                  ? 'Live Sessions'
                  : 'Verification'}
              </button>
            ))}
          </div>

          {/* Notification List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
            {loading ? (
              <div className="py-12 text-center text-xs text-slate-500">Checking host notifications...</div>
            ) : filtered.length === 0 ? (
              <div className="py-16 text-center space-y-2">
                <div className="text-2xl text-slate-600">🔔</div>
                <div className="text-xs font-bold text-slate-300">No notifications in this filter</div>
                <p className="text-[11px] text-slate-500 max-w-xs mx-auto">
                  New reservations, geofenced check-in handshakes, and verification status changes will appear here.
                </p>
              </div>
            ) : (
              filtered.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleNotificationClick(item)}
                  className={`p-3.5 rounded-2xl border transition-all cursor-pointer ${
                    item.unread
                      ? 'bg-slate-950/90 border-amber-500/30 hover:border-amber-500/50 shadow-sm shadow-amber-500/5'
                      : 'bg-slate-950/40 border-slate-800/80 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full shrink-0 ${
                          item.unread ? 'bg-amber-400 animate-pulse' : 'bg-transparent'
                        }`}
                      />
                      <span className="text-xs font-bold text-white">{item.title}</span>
                    </div>
                    <span className="text-[10px] text-slate-500 whitespace-nowrap">
                      {item.timestamp ? new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Now'}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 pl-4 leading-relaxed">{item.message}</p>

                  <div className="pl-4 mt-2.5 flex items-center justify-between text-[11px]">
                    <span className="text-amber-400/90 font-semibold flex items-center gap-1 group">
                      <span>View details</span>
                      <i className="fa-solid fa-arrow-right text-[9px] group-hover:translate-x-0.5 transition-transform" />
                    </span>
                    <span className="text-[10px] uppercase font-mono text-slate-500 tracking-wider">
                      {item.type.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
