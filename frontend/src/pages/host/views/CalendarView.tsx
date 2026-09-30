import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Booking, Space } from '../../../types';
import { getHostBookings, getHostSpaces } from '../../../services/host';
import { StatusBadge } from '../components/StatusBadge';

export const CalendarView: React.FC = () => {
  const navigate = useNavigate();

  const [spaces, setSpaces] = useState<Space[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [selectedSpaceId, setSelectedSpaceId] = useState<string>('all');
  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [viewMode, setViewMode] = useState<'day' | 'week' | 'month'>('month');
  const [loading, setLoading] = useState(true);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sRes, bRes] = await Promise.all([
        getHostSpaces(),
        getHostBookings(),
      ]);
      if (sRes && sRes.spaces) setSpaces(sRes.spaces);
      if (bRes && bRes.bookings) setBookings(bRes.bookings);
    } catch (err) {
      console.error('Failed to load calendar data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePrev = () => {
    const d = new Date(currentDate);
    if (viewMode === 'day') d.setDate(d.getDate() - 1);
    else if (viewMode === 'week') d.setDate(d.getDate() - 7);
    else d.setMonth(d.getMonth() - 1);
    setCurrentDate(d);
  };

  const handleNext = () => {
    const d = new Date(currentDate);
    if (viewMode === 'day') d.setDate(d.getDate() + 1);
    else if (viewMode === 'week') d.setDate(d.getDate() + 7);
    else d.setMonth(d.getMonth() + 1);
    setCurrentDate(d);
  };

  const handleToday = () => {
    setCurrentDate(new Date());
  };

  const filteredBookings = bookings.filter(b => {
    if (selectedSpaceId !== 'all' && b.space_id !== Number(selectedSpaceId)) return false;
    return true;
  });

  // Month grid helpers
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const firstDayOfMonth = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const daysArray = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  const blanksArray = Array.from({ length: firstDayOfMonth }, (_, i) => i);

  const getBookingsForDay = (day: number) => {
    return filteredBookings.filter(b => {
      const bDate = new Date(b.start_time);
      return (
        bDate.getDate() === day &&
        bDate.getMonth() === month &&
        bDate.getFullYear() === year
      );
    });
  };

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Calendar Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Operational Schedule</h1>
          <p className="text-slate-400 text-xs md:text-sm mt-0.5">
            Cross-space reservation timeline, session overlaps, and buffer windows.
          </p>
        </div>

        {/* View Mode & Space Filter */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <select
            value={selectedSpaceId}
            onChange={e => setSelectedSpaceId(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none"
          >
            <option value="all">All Spaces ({spaces.length})</option>
            {spaces.map(s => (
              <option key={s.id} value={s.id}>
                {s.title}
              </option>
            ))}
          </select>

          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-0.5 text-xs">
            {(['day', 'week', 'month'] as const).map(mode => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={`px-3 py-1 rounded-lg capitalize font-semibold transition ${
                  viewMode === mode
                    ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Date Navigation Bar */}
      <div className="flex items-center justify-between bg-slate-900/60 border border-slate-800 p-3.5 rounded-2xl">
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrev}
            className="w-8 h-8 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center transition"
          >
            <i className="fa-solid fa-chevron-left text-xs" />
          </button>
          <button
            onClick={handleToday}
            className="px-3 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
          >
            Today
          </button>
          <button
            onClick={handleNext}
            className="w-8 h-8 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center transition"
          >
            <i className="fa-solid fa-chevron-right text-xs" />
          </button>
        </div>

        <h2 className="text-base font-bold text-white">
          {currentDate.toLocaleDateString('en-US', {
            month: 'long',
            year: 'numeric',
            ...(viewMode === 'day' ? { day: 'numeric', weekday: 'short' } : {}),
          })}
        </h2>

        {/* Legend */}
        <div className="hidden sm:flex items-center gap-3 text-[11px] text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" /> Active
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-indigo-400" /> Confirmed
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400" /> Pending
          </span>
        </div>
      </div>

      {/* Calendar Grid */}
      {loading ? (
        <div className="py-24 text-center text-slate-400 text-xs font-mono">
          <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          SYNCHRONIZING CALENDAR...
        </div>
      ) : viewMode === 'month' ? (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
          {/* Weekday headers */}
          <div className="grid grid-cols-7 border-b border-slate-800 bg-slate-950/60 text-slate-400 text-xs font-semibold py-2.5 text-center">
            <span>Sun</span>
            <span>Mon</span>
            <span>Tue</span>
            <span>Wed</span>
            <span>Thu</span>
            <span>Fri</span>
            <span>Sat</span>
          </div>

          {/* Month Cells */}
          <div className="grid grid-cols-7 divide-x divide-y divide-slate-800/80">
            {blanksArray.map(b => (
              <div key={`blank-${b}`} className="min-h-[100px] p-2 bg-slate-950/20" />
            ))}

            {daysArray.map(day => {
              const dayBookings = getBookingsForDay(day);
              const isToday =
                new Date().getDate() === day &&
                new Date().getMonth() === month &&
                new Date().getFullYear() === year;

              return (
                <div
                  key={day}
                  className={`min-h-[110px] p-2 transition ${
                    isToday ? 'bg-amber-500/5 ring-1 ring-inset ring-amber-500/30' : 'bg-slate-900/30 hover:bg-slate-800/20'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span
                      className={`text-xs font-mono font-bold w-6 h-6 rounded-full flex items-center justify-center ${
                        isToday ? 'bg-amber-500 text-slate-950' : 'text-slate-300'
                      }`}
                    >
                      {day}
                    </span>
                    {dayBookings.length > 0 && (
                      <span className="text-[10px] text-slate-500 font-mono">
                        {dayBookings.length} {dayBookings.length === 1 ? 'slot' : 'slots'}
                      </span>
                    )}
                  </div>

                  <div className="space-y-1">
                    {dayBookings.slice(0, 3).map(b => {
                      const isActive = b.status === 'active';
                      const isPending = b.status === 'pending';
                      return (
                        <div
                          key={b.id}
                          onClick={() => setSelectedBooking(b)}
                          className={`px-2 py-1 rounded-lg text-[10px] font-semibold truncate cursor-pointer transition border ${
                            isActive
                              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                              : isPending
                              ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                              : 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'
                          }`}
                        >
                          <span className="font-mono">
                            {new Date(b.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>{' '}
                          {b.space?.title || 'Session'}
                        </div>
                      );
                    })}
                    {dayBookings.length > 3 && (
                      <div className="text-[9px] text-slate-500 text-center font-mono">
                        +{dayBookings.length - 3} more
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* Day / Week Agenda Mode */
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-sm font-bold text-white">Daily Operational Schedule View</h3>
          {filteredBookings.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              No sessions scheduled for this period.
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {filteredBookings.map(b => (
                <div
                  key={b.id}
                  onClick={() => navigate(`/host/bookings/${b.id}`)}
                  className="py-3.5 flex items-center justify-between cursor-pointer hover:bg-slate-800/30 px-3 rounded-xl transition"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-slate-800 text-amber-400 flex items-center justify-center font-mono text-xs font-bold">
                      {new Date(b.start_time).getDate()}
                    </div>
                    <div>
                      <div className="text-xs font-bold text-white flex items-center gap-2">
                        <span>{b.space?.title || `Space #${b.space_id}`}</span>
                        <StatusBadge status={b.status} type="booking" />
                      </div>
                      <div className="text-[11px] text-slate-400">
                        Seeker: {b.renter?.name || b.user_name || 'Guest'} •{' '}
                        {new Date(b.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -{' '}
                        {new Date(b.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-xs font-bold text-emerald-400">₹{b.total_price}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Booking Quick Detail Modal */}
      {selectedBooking && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-sm w-full p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-white text-sm">Booking #{selectedBooking.id}</h3>
              <button
                onClick={() => setSelectedBooking(null)}
                className="text-slate-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <div className="text-amber-400 font-semibold">{selectedBooking.space?.title}</div>
              <div className="text-slate-300">Renter: {selectedBooking.renter?.name || selectedBooking.user_name || 'Guest'}</div>
              <div className="text-slate-400">
                {new Date(selectedBooking.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -{' '}
                {new Date(selectedBooking.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
              <div className="font-mono font-bold text-emerald-400">Total: ₹{selectedBooking.total_price} (₹100 Escrow)</div>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={() => {
                  setSelectedBooking(null);
                  navigate(`/host/bookings/${selectedBooking.id}`);
                }}
                className="w-full py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition"
              >
                Open Booking Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
