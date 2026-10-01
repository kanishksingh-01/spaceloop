import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  HostNotification,
  getHostNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  deleteNotification,
} from '../../../services/host';
import {
  HostPageHeader,
  HostCardSkeleton,
  HostEmptyState,
} from '../components';

export const NotificationsView: React.FC = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<HostNotification[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [search, setSearch] = useState<string>('');
  const [loading, setLoading] = useState(true);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const data = await getHostNotifications();
      if (data && data.notifications) {
        setNotifications(data.notifications);
      }
    } catch (err) {
      console.warn('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleMarkRead = async (notif: HostNotification) => {
    const id = (notif as any).db_id || notif.id;
    setNotifications((prev) =>
      prev.map((n) => (n.id === notif.id ? { ...n, unread: false } : n))
    );
    if (typeof id === 'number' || (!isNaN(Number(id)) && !String(id).startsWith('dyn-'))) {
      try {
        await markNotificationRead(id);
      } catch (e) {
        console.warn('Error marking read:', e);
      }
    }
  };

  const handleMarkAllRead = async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, unread: false })));
    try {
      await markAllNotificationsRead();
    } catch (e) {
      console.warn('Error marking all read:', e);
    }
  };

  const handleDelete = async (notif: HostNotification, e: React.MouseEvent) => {
    e.stopPropagation();
    const id = (notif as any).db_id || notif.id;
    setNotifications((prev) => prev.filter((n) => n.id !== notif.id));
    if (typeof id === 'number' || (!isNaN(Number(id)) && !String(id).startsWith('dyn-'))) {
      try {
        await deleteNotification(id);
      } catch (err) {
        console.warn('Error deleting notification:', err);
      }
    }
  };

  const handleNotificationClick = async (notif: HostNotification) => {
    await handleMarkRead(notif);
    if (notif.action_url) {
      navigate(notif.action_url);
    }
  };

  const filtered = notifications.filter((n) => {
    const matchesFilter =
      filter === 'all'
        ? true
        : filter === 'unread'
        ? n.unread
        : filter === 'booking'
        ? n.type === 'new_booking' || n.type === 'booking'
        : filter === 'inquiry'
        ? n.type === 'inquiry' || n.type === 'new_inquiry'
        : filter === 'access'
        ? n.type === 'check_in' || n.type === 'checkin' || n.type === 'active_session'
        : filter === 'settlement'
        ? n.type === 'checkout' || n.type === 'inspection_alert' || (n.type as string).includes('dispute')
        : filter === 'verification'
        ? n.type === 'verification'
        : true;

    const matchesSearch =
      search.trim() === ''
        ? true
        : n.title.toLowerCase().includes(search.toLowerCase()) ||
          n.message.toLowerCase().includes(search.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  const unreadCount = notifications.filter((n) => n.unread).length;

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <HostPageHeader
        category="Operational Alerts"
        title="Notifications Hub"
        subtitle="Real-time operational alerts, in-room check-in telemetry, condition audits, and UPI micro-escrow releases."
        badge={
          unreadCount > 0 ? (
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500 text-slate-950 shadow-sm">
              {unreadCount} Unread
            </span>
          ) : undefined
        }
        actions={
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={fetchNotifications}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition flex items-center gap-1.5"
              title="Refresh notifications"
            >
              <i className={`fa-solid fa-arrows-rotate text-xs ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllRead}
                className="px-4 py-2 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300 text-xs font-bold transition flex items-center gap-1.5"
              >
                <i className="fa-solid fa-check-double text-xs" />
                <span>Mark all read</span>
              </button>
            )}
          </div>
        }
      />

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-slate-900/60 p-2.5 rounded-2xl border border-slate-800/80">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
          {[
            { id: 'all', label: 'All Alerts', icon: 'fa-solid fa-layer-group' },
            { id: 'unread', label: `Unread (${unreadCount})`, icon: 'fa-solid fa-envelope' },
            { id: 'inquiry', label: 'Inquiries', icon: 'fa-solid fa-comments' },
            { id: 'booking', label: 'Bookings', icon: 'fa-solid fa-calendar-check' },
            { id: 'access', label: 'Check-in & Sessions', icon: 'fa-solid fa-door-open' },
            { id: 'settlement', label: 'Settlement & Escrow', icon: 'fa-solid fa-vault' },
            { id: 'verification', label: 'Verification', icon: 'fa-solid fa-shield-halved' },
          ].map((tab) => {
            const active = filter === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setFilter(tab.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition flex items-center gap-1.5 ${
                  active
                    ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50 border border-transparent'
                }`}
              >
                <i className={`${tab.icon} text-[11px]`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        <div className="relative shrink-0 md:w-64">
          <i className="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search alerts..."
            className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 focus:border-amber-500/50 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none transition"
          />
        </div>
      </div>

      {/* Notifications List */}
      {loading ? (
        <div className="space-y-3">
          <HostCardSkeleton lines={3} />
          <HostCardSkeleton lines={3} />
          <HostCardSkeleton lines={3} />
        </div>
      ) : filtered.length === 0 ? (
        <HostEmptyState
          icon="fa-solid fa-bell-slash"
          title="No Notifications Found"
          description={
            search
              ? `No alerts match your search query "${search}".`
              : 'You are all caught up! New bookings, check-in handshakes, and settlements will appear here.'
          }
          secondaryAction={
            search
              ? {
                  label: 'Clear Search',
                  onClick: () => setSearch(''),
                }
              : undefined
          }
        />
      ) : (
        <div className="space-y-3">
          {filtered.map((item) => {
            const isUnread = item.unread;
            const priorityClass =
              item.priority === 'high'
                ? 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                : item.priority === 'medium'
                ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                : 'bg-slate-800 text-slate-400 border-slate-700';

            return (
              <div
                key={item.id}
                onClick={() => handleNotificationClick(item)}
                className={`group p-4 sm:p-5 rounded-2xl border transition cursor-pointer relative overflow-hidden flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
                  isUnread
                    ? 'bg-slate-900/90 border-amber-500/30 shadow-lg shadow-amber-500/5 hover:border-amber-500/50'
                    : 'bg-slate-950/40 border-slate-800/80 hover:bg-slate-900/40 hover:border-slate-700'
                }`}
              >
                {/* Left side indicator bar */}
                <div
                  className={`absolute left-0 top-0 bottom-0 w-1.5 transition-colors ${
                    isUnread ? 'bg-amber-500' : 'bg-transparent'
                  }`}
                />

                <div className="flex items-start gap-3.5 pl-2">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center text-base shrink-0 mt-0.5 ${
                      item.color === 'emerald'
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                        : item.color === 'sky'
                        ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
                        : item.color === 'purple'
                        ? 'bg-purple-500/15 text-purple-400 border border-purple-500/30'
                        : item.color === 'rose'
                        ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                        : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    <i className={`fa-solid ${item.icon || 'fa-bell'}`} />
                  </div>

                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h4 className="text-sm font-bold text-white group-hover:text-amber-400 transition-colors">
                        {item.title}
                      </h4>
                      {isUnread && (
                        <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse shrink-0" />
                      )}
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${priorityClass}`}>
                        {item.priority}
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed max-w-2xl">
                      {item.message}
                    </p>

                    <div className="flex items-center gap-3 text-[11px] text-slate-500 pt-1">
                      <span className="flex items-center gap-1 font-mono">
                        <i className="fa-regular fa-clock text-[10px]" />
                        <span>
                          {item.timestamp
                            ? new Date(item.timestamp).toLocaleString([], {
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                              })
                            : 'Just now'}
                        </span>
                      </span>
                      <span>•</span>
                      <span className="uppercase text-[10px] tracking-wider font-semibold">
                        {item.type.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex items-center gap-2 self-end sm:self-center shrink-0 pl-2">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleMarkRead(item);
                    }}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
                      isUnread
                        ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
                        : 'text-slate-500 hover:text-slate-300 border-transparent hover:bg-slate-800/40'
                    }`}
                    title={isUnread ? 'Mark as read' : 'Already read'}
                  >
                    {isUnread ? 'Mark Read' : 'Read'}
                  </button>

                  <button
                    type="button"
                    onClick={(e) => handleDelete(item, e)}
                    className="w-8 h-8 rounded-xl flex items-center justify-center text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition"
                    title="Dismiss alert"
                  >
                    <i className="fa-solid fa-trash-can text-xs" />
                  </button>

                  <button
                    type="button"
                    onClick={() => handleNotificationClick(item)}
                    className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md shadow-amber-500/15 transition flex items-center gap-1"
                  >
                    <span>View</span>
                    <i className="fa-solid fa-arrow-right text-[10px]" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
