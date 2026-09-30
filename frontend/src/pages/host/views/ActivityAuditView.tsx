import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHostActivity, HostActivityEvent } from '../../../services/host';
import {
  HostPageHeader,
  HostCard,
  HostCardSkeleton,
  HostEmptyState,
} from '../components';

export const ActivityAuditView: React.FC = () => {
  const navigate = useNavigate();

  const [category, setCategory] = useState<string>('all');
  const [events, setEvents] = useState<HostActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadActivity();
  }, [category]);

  const loadActivity = async () => {
    try {
      setLoading(true);
      const res = await getHostActivity(category);
      if (res && res.events) {
        setEvents(res.events);
      }
    } catch (err) {
      console.error('Failed to load activity events:', err);
    } finally {
      setLoading(false);
    }
  };

  const categories = [
    { id: 'all', label: 'All Operations' },
    { id: 'booking', label: 'Bookings' },
    { id: 'access', label: 'Access & Geofence' },
    { id: 'verification', label: 'Verifications' },
    { id: 'settlement', label: 'Settlement & Escrow' },
    { id: 'space', label: 'Spaces' },
  ];

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <HostPageHeader
        category="Operational Audit Trail"
        title="System Activity & Audit Log"
        subtitle="Chronological record of every check-in handshake, escrow release, and property modification."
        badge={
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 uppercase tracking-wider">
            Immutable SQLite WAL Telemetry
          </span>
        }
      />

      {/* Category Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
        {categories.map(cat => {
          const active = category === cat.id;
          return (
            <button
              key={cat.id}
              onClick={() => setCategory(cat.id)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
                active
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
              }`}
            >
              {cat.label}
            </button>
          );
        })}
      </div>

      {/* Activity Timeline */}
      {loading ? (
        <HostCardSkeleton lines={6} />
      ) : events.length === 0 ? (
        <HostEmptyState
          icon="fa-solid fa-clock-rotate-left"
          title="No Activity Logged"
          description="No operations match your current filter category."
          secondaryAction={{
            label: 'View All Operations',
            onClick: () => setCategory('all'),
          }}
        />
      ) : (
        <HostCard
          title="Chronological Telemetry Stream"
          subtitle={`${events.length} system events recorded`}
          icon="fa-solid fa-clock-rotate-left"
        >
          <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
            {events.map((ev) => {
              const hasResource = Boolean(ev.resource_id);
              const isBooking = ev.resource_type === 'booking';
              const isSpace = ev.resource_type === 'space';

              return (
                <div key={ev.id} className="relative group">
                  {/* Timeline Node Icon */}
                  <div className="absolute -left-6 top-0 w-5 h-5 rounded-full bg-slate-900 border-2 border-amber-500/70 flex items-center justify-center text-[9px] text-amber-400 shadow-md">
                    <i className={ev.icon || 'fa-solid fa-circle'} />
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition space-y-1.5">
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-bold text-white text-xs">{ev.title}</span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {new Date(ev.timestamp).toLocaleString([], {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>

                    <p className="text-xs text-slate-400 leading-relaxed">
                      {ev.description}
                    </p>

                    {hasResource && (
                      <div className="pt-1 flex items-center gap-2">
                        {isBooking && (
                          <button
                            onClick={() => navigate(`/host/bookings/${ev.resource_id}`)}
                            className="text-[11px] text-amber-400 hover:text-amber-300 font-semibold"
                          >
                            View Booking #{ev.resource_id} →
                          </button>
                        )}
                        {isSpace && (
                          <button
                            onClick={() => navigate(`/host/spaces/${ev.resource_id}`)}
                            className="text-[11px] text-amber-400 hover:text-amber-300 font-semibold"
                          >
                            View Space #{ev.resource_id} →
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </HostCard>
      )}
    </div>
  );
};
