import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Booking, Space } from '../../../types';
import { getHostBookings, acceptBooking, rejectBooking, cancelBooking, getHostSpaces } from '../../../services/host';
import {
  HostPageHeader,
  HostCardSkeleton,
  HostEmptyState,
  StatusBadge,
} from '../components';

const PAGE_SIZE = 10;

export const BookingsView: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const currentStatusFilter = searchParams.get('status') || 'all';

  const [bookings, setBookings] = useState<Booking[]>([]);
  const [spaces, setSpaces] = useState<Space[]>([]);
  const [selectedSpaceId, setSelectedSpaceId] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const [loading, setLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);

  useEffect(() => {
    loadSpaces();
  }, []);

  useEffect(() => {
    loadBookings();
  }, [currentStatusFilter, selectedSpaceId]);

  const loadSpaces = async () => {
    try {
      const res = await getHostSpaces();
      if (res && res.spaces) {
        setSpaces(res.spaces);
      }
    } catch (err) {
      console.warn('Failed to load host spaces:', err);
    }
  };

  const loadBookings = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (currentStatusFilter !== 'all') {
        params.status = currentStatusFilter;
      }
      if (selectedSpaceId !== 'all') {
        params.space_id = Number(selectedSpaceId);
      }

      const res = await getHostBookings(params);
      if (res && res.bookings) {
        setBookings(res.bookings);
      }
    } catch (err) {
      console.error('Failed to load host bookings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusFilterChange = (status: string) => {
    setVisibleCount(PAGE_SIZE);
    if (status === 'all') {
      searchParams.delete('status');
      setSearchParams(searchParams);
    } else {
      setSearchParams({ status });
    }
  };

  const handleAccept = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    try {
      setActionLoadingId(id);
      await acceptBooking(id);
      setBookings(prev =>
        prev.map(b => (b.id === id ? { ...b, status: 'confirmed' } : b))
      );
    } catch (err) {
      console.error('Failed to accept booking:', err);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleReject = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    try {
      setActionLoadingId(id);
      await rejectBooking(id);
      setBookings(prev =>
        prev.map(b => (b.id === id ? { ...b, status: 'rejected' } : b))
      );
    } catch (err) {
      console.error('Failed to reject booking:', err);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleCancel = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!window.confirm(`Are you sure you want to cancel Booking #${id}? An instant refund will be issued to the seeker and the space slot released.`)) {
      return;
    }
    try {
      setActionLoadingId(id);
      await cancelBooking(id, 'Host requested cancellation from bookings list');
      setBookings(prev =>
        prev.map(b => (b.id === id ? { ...b, status: 'cancelled', session_state: 'cancelled', escrow_status: 'refunded' } : b))
      );
    } catch (err: any) {
      console.error('Failed to cancel booking:', err);
      alert(err?.message || 'Failed to cancel booking.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const filteredBookings = bookings.filter(b => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const matchId = String(b.id).includes(q);
    const matchUser = (b.renter?.name || b.user_name || '').toLowerCase().includes(q);
    const matchSpace = (b.space?.title || '').toLowerCase().includes(q);
    return matchId || matchUser || matchSpace;
  });

  const visibleBookings = filteredBookings.slice(0, visibleCount);

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <HostPageHeader
        category="Operational Workflow"
        title="Booking Management"
        subtitle="Operational queue for approvals, arrival tracking, live sessions, and escrow payouts."
        actions={
          <button
            onClick={() => navigate('/host/calendar')}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition flex items-center gap-2"
          >
            <i className="fa-regular fa-calendar-days text-amber-400 text-xs" />
            <span>View Calendar</span>
          </button>
        }
      />

      {/* Filter and Control Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800/80 p-3.5 rounded-2xl">
        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
          {[
            { id: 'all', label: 'All Bookings' },
            { id: 'pending', label: 'Pending Approval' },
            { id: 'confirmed', label: 'Confirmed' },
            { id: 'active', label: 'Active Now' },
            { id: 'completed', label: 'Completed' },
            { id: 'cancelled', label: 'Cancelled' },
          ].map(tab => {
            const active = currentStatusFilter === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => handleStatusFilterChange(tab.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition ${
                  active
                    ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Space Selector & Search */}
        <div className="flex items-center gap-2.5">
          <select
            value={selectedSpaceId}
            onChange={e => setSelectedSpaceId(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none transition"
          >
            <option value="all">All Spaces ({spaces.length})</option>
            {spaces.map(s => (
              <option key={s.id} value={s.id}>
                {s.title}
              </option>
            ))}
          </select>

          <div className="relative flex-1 sm:w-56">
            <i className="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search seeker, ID..."
              className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/50 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none transition"
            />
          </div>
        </div>
      </div>

      {/* Bookings Queue */}
      {loading ? (
        <div className="space-y-3">
          <HostCardSkeleton lines={3} />
          <HostCardSkeleton lines={3} />
          <HostCardSkeleton lines={3} />
        </div>
      ) : filteredBookings.length === 0 ? (
        <HostEmptyState
          icon="fa-regular fa-calendar-xmark"
          title="No Bookings Found"
          description={
            searchQuery
              ? 'No bookings match your current search query.'
              : 'There are no bookings matching this status category.'
          }
          primaryAction={{
            label: 'View Calendar',
            onClick: () => navigate('/host/calendar'),
            icon: 'fa-regular fa-calendar',
          }}
          secondaryAction={
            searchQuery
              ? {
                  label: 'Clear Search',
                  onClick: () => setSearchQuery(''),
                }
              : undefined
          }
        />
      ) : (
        <div className="space-y-3">
          {visibleBookings.map(b => {
            const isLive = b.status === 'active';
            const isPending = b.status === 'pending';

            return (
              <div
                key={b.id}
                onClick={() => navigate(`/host/bookings/${b.id}`)}
                className={`p-4 rounded-2xl border transition-all duration-150 cursor-pointer group ${
                  isLive
                    ? 'bg-slate-900/90 border-emerald-500/40 shadow-lg shadow-emerald-500/5'
                    : isPending
                    ? 'bg-slate-900/70 border-amber-500/30'
                    : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/90'
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  {/* Left: Space info & Seeker */}
                  <div className="flex items-start gap-3.5">
                    <img
                      src={b.space?.image_url || 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=150&q=80'}
                      alt="Space"
                      className="w-14 h-14 rounded-xl object-cover border border-slate-800 shrink-0"
                    />
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-white text-sm group-hover:text-amber-400 transition">
                          {b.space?.title || `Space #${b.space_id}`}
                        </span>
                        <StatusBadge status={b.status} type="booking" />
                        {isLive && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase animate-pulse">
                            Active Now
                          </span>
                        )}
                      </div>

                      <div className="text-xs text-slate-300">
                        Seeker: <strong className="text-white">{b.renter?.name || b.user_name || 'Guest'}</strong>
                        {b.renter?.is_verified && (
                          <i className="fa-solid fa-circle-check text-emerald-400 ml-1 text-[11px]" title="Aadhaar KYC Verified" />
                        )}
                        <span className="text-slate-500 mx-2">•</span>
                        <span>Booking #{b.id}</span>
                      </div>

                      <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-3 flex-wrap">
                        <span>
                          <i className="fa-regular fa-calendar mr-1 text-slate-500" />
                          {new Date(b.start_time).toLocaleDateString()}
                        </span>
                        <span>
                          <i className="fa-regular fa-clock mr-1 text-slate-500" />
                          {new Date(b.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -{' '}
                          {new Date(b.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({b.total_hours} hrs)
                        </span>
                        <span className="text-emerald-400 font-mono">
                          <i className="fa-solid fa-vault mr-1 text-[10px]" />
                          ₹100 Micro-Escrow Held
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Right: Price & Quick Action Buttons */}
                  <div className="flex items-center gap-4 self-end md:self-center shrink-0">
                    <div className="text-right">
                      <div className="text-base font-black text-white font-mono">
                        ₹{b.total_price}
                      </div>
                      <div className="text-[10px] text-emerald-400 font-semibold font-mono">
                        Host Payout: ₹{Math.round(b.total_price * 0.95)}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {isPending && (
                        <>
                          <button
                            onClick={(e) => handleReject(e, b.id)}
                            disabled={actionLoadingId === b.id}
                            className="px-3.5 py-1.5 rounded-xl border border-slate-700 hover:border-rose-500/40 text-slate-400 hover:text-rose-400 text-xs font-semibold transition"
                          >
                            Decline
                          </button>
                          <button
                            onClick={(e) => handleAccept(e, b.id)}
                            disabled={actionLoadingId === b.id}
                            className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md shadow-amber-500/20 transition"
                          >
                            {actionLoadingId === b.id ? 'Accepting...' : 'Accept'}
                          </button>
                        </>
                      )}

                      {b.status === 'confirmed' && (
                        <button
                          type="button"
                          onClick={(e) => handleCancel(e, b.id)}
                          disabled={actionLoadingId === b.id}
                          className="px-3 py-1.5 rounded-xl border border-rose-500/30 hover:border-rose-500/60 bg-rose-500/5 hover:bg-rose-500/10 text-rose-300 hover:text-rose-200 text-xs font-semibold transition disabled:opacity-50"
                        >
                          {actionLoadingId === b.id ? 'Cancelling...' : 'Cancel'}
                        </button>
                      )}

                      {isLive && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/host/live-sessions/${b.id}`);
                          }}
                          className="px-4 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition flex items-center gap-1.5"
                        >
                          <i className="fa-solid fa-satellite-dish text-xs" />
                          <span>Cockpit</span>
                        </button>
                      )}

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/host/bookings/${b.id}`);
                        }}
                        className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
                      >
                        Details →
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}

          {/* Load More Bookings Control */}
          {filteredBookings.length > visibleBookings.length && (
            <div className="pt-4 flex flex-col items-center justify-center gap-2">
              <div className="text-xs text-slate-400 font-medium">
                Showing <span className="text-white font-semibold">{visibleBookings.length}</span> of <span className="text-white font-semibold">{filteredBookings.length}</span> bookings
              </div>
              <button
                type="button"
                onClick={() => setVisibleCount(prev => prev + PAGE_SIZE)}
                className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 transition flex items-center gap-2 shadow-sm"
              >
                <i className="fa-solid fa-chevron-down text-xs text-amber-400" />
                <span>Load More Bookings</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
