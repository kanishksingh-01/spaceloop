import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHostActivity, HostActivityEvent } from '../../../services/host';

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
    <div className="p-6 md:p-8 max-w-7xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 uppercase tracking-wider">
            Operational Audit Trail
          </span>
          <span className="text-slate-500 text-xs font-mono">Immutable SQLite WAL Telemetry</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          System Activity & Audit Log
        </h1>
        <p className="text-slate-400 text-xs md:text-sm mt-0.5">
          Chronological record of every check-in handshake, escrow release, and property modification.
        </p>
      </div>

      {/* Category Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => setCategory(cat.id)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
              category === cat.id
                ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Activity Timeline */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-xs font-mono">
          <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          FETCHING AUDIT TRAIL...
        </div>
      ) : events.length === 0 ? (
        <div className="p-12 text-center bg-slate-900/40 border border-slate-800/80 rounded-2xl">
          <i className="fa-solid fa-clock-rotate-left text-3xl text-slate-600 mb-3 block" />
          <h3 className="text-base font-bold text-white mb-1">No Activity Logged</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            No events match your current filter category.
          </p>
        </div>
      ) : (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
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
        </div>
      )}
    </div>
  );
};
