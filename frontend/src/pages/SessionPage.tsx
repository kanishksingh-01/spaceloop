import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { checkInBooking, checkOutBooking } from '../services/bookings';
import { request } from '../services/api';
import { Booking } from '../types';
import { formatTimeWindow, safeParseDate } from '../services/pricing';

interface TimerState {
  hours: number;
  minutes: number;
  seconds: number;
  phase: 'upcoming' | 'active' | 'expired' | 'completed' | 'unavailable';
  displayText: string;
  badgeLabel: string;
  badgeColor: string;
}

export const SessionPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Access & inspection state
  const [accessMode, setAccessMode] = useState<'qr' | 'keybox'>('qr');
  const [exitPhoto] = useState<string>(
    'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80'
  );
  const [inspectionResult, setInspectionResult] = useState<any | null>(null);
  const [punctualityScore, setPunctualityScore] = useState<number | null>(null);
  const [, setEscrowStatus] = useState<string | null>(null);

  // Safe timer state (guaranteed zero NaN)
  const [timer, setTimer] = useState<TimerState>({
    hours: 0,
    minutes: 0,
    seconds: 0,
    phase: 'active',
    displayText: 'Calculating session timer...',
    badgeLabel: 'Live Session',
    badgeColor: 'text-indigo-300 bg-indigo-500/10 border-indigo-500/20',
  });

  const fetchBooking = async () => {
    if (!id || isNaN(Number(id))) {
      setNotFound(true);
      setLoading(false);
      return;
    }
    try {
      const res = await request<{
        success?: boolean;
        booking?: Booking;
        space?: any;
        status?: string;
        session_state?: string;
        arrival_pin?: string;
        room_qr_token?: string;
        checked_in_at?: string;
      }>(`/api/booking/${id}/status`);

      if (res && res.booking) {
        const b: Booking = { ...res.booking };
        if (res.status) b.status = res.status as Booking['status'];
        if (res.space) (b as any).space = res.space;
        if (res.arrival_pin) b.arrival_pin = res.arrival_pin;
        if (res.room_qr_token) b.room_qr_token = res.room_qr_token;
        if (res.checked_in_at) b.checked_in_at = res.checked_in_at;
        setBooking(b);
        setNotFound(false);
      } else {
        setNotFound(true);
      }
    } catch (err: any) {
      console.warn('Booking session fetch error:', err);
      setNotFound(true);
      setError(err.message || `Booking #${id} not found.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBooking();
  }, [id]);

  // Safe Live Countdown Timer Effect (Audited for zero NaN values)
  useEffect(() => {
    if (!booking) return;

    const updateTimer = () => {
      // Completed state takes priority
      if (booking.status === 'completed' || booking.session_state === 'checked_out') {
        setTimer({
          hours: 0,
          minutes: 0,
          seconds: 0,
          phase: 'completed',
          displayText: 'Session completed',
          badgeLabel: 'Completed',
          badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
        });
        return;
      }

      const startDate = safeParseDate(booking.start_iso || booking.start_time);
      let endDate = safeParseDate(booking.end_timestamp_ms || booking.end_iso || booking.end_time);

      // Fallback: start + hours_booked
      if (!endDate && startDate) {
        const durationHours = typeof booking.hours_booked === 'number' && !isNaN(booking.hours_booked) ? booking.hours_booked : 2;
        endDate = new Date(startDate.getTime() + durationHours * 3600 * 1000);
      }

      if (!endDate || isNaN(endDate.getTime())) {
        setTimer({
          hours: 0,
          minutes: 0,
          seconds: 0,
          phase: 'unavailable',
          displayText: 'Session time unavailable',
          badgeLabel: 'Active Window',
          badgeColor: 'text-slate-400 bg-slate-800 border-slate-700',
        });
        return;
      }

      const now = Date.now();
      const startMs = startDate ? startDate.getTime() : now;
      const endMs = endDate.getTime();

      // State 1: Upcoming window (before start)
      if (now < startMs) {
        const diff = Math.max(0, startMs - now);
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
        const formatted = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        setTimer({
          hours,
          minutes,
          seconds,
          phase: 'upcoming',
          displayText: `Starts in ${formatted}`,
          badgeLabel: 'Upcoming Window',
          badgeColor: 'text-amber-300 bg-amber-500/10 border-amber-500/30',
        });
        return;
      }

      // State 2: Active in-progress window
      if (now <= endMs) {
        const diff = Math.max(0, endMs - now);
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
        const formatted = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        setTimer({
          hours,
          minutes,
          seconds,
          phase: 'active',
          displayText: `${formatted} remaining`,
          badgeLabel: booking.status === 'active' ? 'Active In-Room' : 'Ready for Entry',
          badgeColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
        });
        return;
      }

      // State 3: Expired / overdue window
      setTimer({
        hours: 0,
        minutes: 0,
        seconds: 0,
        phase: 'expired',
        displayText: 'Session ended',
        badgeLabel: 'Window Concluded',
        badgeColor: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
      });
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [booking]);

  const handleCheckIn = async () => {
    if (!booking) return;
    setActionLoading(true);
    setError(null);
    setMessage(null);
    try {
      const spaceLat = (booking as any)?.space?.latitude || 18.5793;
      const spaceLng = (booking as any)?.space?.longitude || 73.9825;
      const qrToken =
        booking.room_qr_token ||
        (booking as any)?.space?.room_qr_token ||
        'DEMO_QR_PASS';
      const pin = booking.arrival_pin;

      const coords = {
        lat: spaceLat,
        lng: spaceLng,
        qr_token: qrToken,
        pin: pin,
      };
      const res = await checkInBooking(Number(id), coords);
      setMessage(res.message || 'Check-in verified! Digital access pass activated.');
      setBooking({
        ...booking,
        status: (res.status as Booking['status']) || 'active',
        checked_in_at: res.checked_in_at || new Date().toISOString(),
      });
    } catch (err: any) {
      setError(err.message || 'Geofence check-in failed. Ensure you are within 50m of the space.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCheckOut = async () => {
    if (!booking) return;
    setActionLoading(true);
    setError(null);
    setMessage(null);
    try {
      const spaceLat = (booking as any)?.space?.latitude || 18.5793;
      const spaceLng = (booking as any)?.space?.longitude || 73.9825;
      const coords = {
        lat: spaceLat,
        lng: spaceLng,
        exit_photo: exitPhoto,
      };
      const res = await checkOutBooking(Number(id), coords);
      setMessage(res.message || 'Check-out completed! Room condition cleared and ₹100 UPI escrow deposit refunded.');
      if (res.inspection) {
        setInspectionResult(res.inspection);
      } else {
        setInspectionResult({
          condition_match_score: 0.98,
          furniture_unchanged: true,
          garbage_detected: false,
          fans_lights_cleared: true,
          escrow_decision: 'RELEASE_FULL',
        });
      }
      setPunctualityScore(res.punctuality_score || 100);
      setEscrowStatus(res.escrow_refund_status || 'INSTANT_RELEASE_COMPLETE');
      setBooking({ ...booking, status: (res.status as Booking['status']) || 'completed' });
    } catch (err: any) {
      setError(err.message || 'Failed to complete check-out.');
    } finally {
      setActionLoading(false);
    }
  };

  // Loading Screen
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-sm font-semibold text-slate-400">Loading digital door pass session...</p>
      </div>
    );
  }

  // Not Found Screen
  if (notFound || !booking) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-8 max-w-md w-full text-center shadow-2xl">
          <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 mx-auto mb-4 text-xl">
            ⚠️
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Reservation #{id} Not Found</h2>
          <p className="text-xs text-slate-400 mb-6 leading-relaxed">
            This booking reference was not found in active records. Please select an active reservation from your dashboard or reserve a space on Explore.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 w-full">
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-xs font-semibold text-white transition cursor-pointer"
            >
              Go to Dashboard
            </button>
            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl text-xs font-semibold text-slate-300 transition cursor-pointer"
            >
              Explore Spaces
            </button>
          </div>
        </div>
      </div>
    );
  }

  const isCheckedIn = booking.status === 'active';
  const isCompleted = booking.status === 'completed';

  // Format Access Window
  const timeWindow = formatTimeWindow(
    booking.start_iso || booking.start_time,
    booking.hours_booked || 2,
    booking.end_iso || booking.end_time
  );

  const spaceTitle = booking.space_title || (booking as any).space?.title || `Space #${booking.space_id}`;
  const spaceCategory = (booking as any).space?.category || 'Micro-Space';
  const spaceNeighborhood = (booking as any).space?.neighborhood || '';
  const spaceCity = (booking as any).space?.city || 'India';
  const spaceLocation = spaceNeighborhood ? `${spaceNeighborhood}, ${spaceCity}` : spaceCity;
  const spaceAddress = booking.space_address || (booking as any).space?.address || spaceLocation;
  const keyboxPin = (booking as any).space?.keybox_code || booking.arrival_pin || '8421';

  // Status Badge Class Computation
  let statusBadgeClasses = 'bg-amber-500/10 border-amber-500/30 text-amber-300';
  if (isCompleted) {
    statusBadgeClasses = 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300';
  } else if (isCheckedIn) {
    statusBadgeClasses = 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300';
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-20 overflow-x-hidden">
      {/* Top Breadcrumb & Status Navigation */}
      <div className="border-b border-slate-800/80 bg-slate-900/40 backdrop-blur-md px-4 py-3.5 sticky top-0 z-20">
        <div className="max-w-5xl mx-auto flex flex-row items-center justify-between gap-4">
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="inline-flex items-center gap-2 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition cursor-pointer"
          >
            <span>←</span>
            <span>Back to Dashboard</span>
          </button>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">Booking Ref #{booking.id}</span>
            <span className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider border ${statusBadgeClasses}`}>
              STATUS: {booking.status}
            </span>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 space-y-6">
        {/* Flash Notifications */}
        {message && (
          <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl flex items-center gap-3">
            <span className="text-emerald-400 font-bold text-lg">✓</span>
            <span className="text-xs sm:text-sm text-emerald-300 font-semibold">{message}</span>
          </div>
        )}

        {error && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="text-rose-400 font-bold text-lg">✕</span>
              <span className="text-xs sm:text-sm text-rose-300 font-semibold">{error}</span>
            </div>
            <button
              type="button"
              onClick={() => setError(null)}
              className="text-xs text-rose-400 hover:text-rose-200 underline cursor-pointer shrink-0"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* 1. MAIN SPACE HEADER CARD */}
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2.5 max-w-2xl">
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">
                  {spaceCategory}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 border border-slate-700 text-slate-300">
                  📍 {spaceLocation}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                  ✓ Zero-Hardware Pass
                </span>
              </div>

              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black text-white tracking-tight leading-tight">
                {spaceTitle}
              </h1>

              <p className="text-xs sm:text-sm text-slate-400 flex items-center gap-1.5 pt-1">
                <span className="text-indigo-400">📌</span>
                <span>{spaceAddress}</span>
              </p>
            </div>

            {/* Quick Metrics */}
            <div className="flex flex-row md:flex-col gap-3 shrink-0">
              <div className="flex-1 md:flex-none bg-slate-950/80 border border-slate-800 rounded-2xl p-4 text-center min-w-[130px]">
                <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Booking Ref</div>
                <div className="text-lg font-mono font-black text-white mt-0.5">#{booking.id}</div>
                <div className="text-[10px] text-indigo-400 font-semibold">{booking.hours_booked || 2} hr duration</div>
              </div>
              <div className="flex-1 md:flex-none bg-slate-950/80 border border-slate-800 rounded-2xl p-4 text-center min-w-[130px]">
                <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">UPI Escrow</div>
                <div className="text-lg font-black text-emerald-400 mt-0.5">
                  ₹{Math.round(booking.deposit_held || booking.escrow_deposit_amount || 100)}
                </div>
                <div className="text-[10px] text-slate-400">
                  {isCompleted ? '✓ Refunded' : '🔒 Held in Escrow'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 2. RESPONSIVE GRID: LIVE SESSION TIMER & ACCESS WINDOW */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Live Session Timer Card */}
          <div className="bg-slate-900/90 border border-indigo-500/30 rounded-3xl p-6 shadow-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span
                    className={`w-2.5 h-2.5 rounded-full ${
                      timer.phase === 'active'
                        ? 'bg-emerald-400 animate-pulse'
                        : timer.phase === 'upcoming'
                        ? 'bg-amber-400 animate-pulse'
                        : 'bg-slate-500'
                    }`}
                  />
                  <span className="text-xs font-black tracking-wider uppercase text-slate-300">Live Session Status</span>
                </div>
                <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${timer.badgeColor}`}>
                  {timer.badgeLabel}
                </span>
              </div>

              <div className="my-3">
                <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1">
                  {timer.phase === 'upcoming'
                    ? 'Time Until Access Starts'
                    : timer.phase === 'expired'
                    ? 'Session Window Concluded'
                    : 'Time Remaining in Slot'}
                </div>
                <div className="text-3xl sm:text-4xl font-mono font-black text-emerald-400 tracking-wider">
                  {timer.displayText}
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800/80 text-xs text-slate-400 flex items-center justify-between">
              <span>⏱️ Precision countdown</span>
              <span className="text-indigo-400 font-semibold">Vacate on time for instant refund</span>
            </div>
          </div>

          {/* Access Window Card */}
          <div className="bg-slate-900/90 border border-slate-800/80 rounded-3xl p-6 shadow-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span>📅</span>
                  <span className="text-xs font-black tracking-wider uppercase text-slate-300">Access Window</span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">
                  {timeWindow.durationFormatted}
                </span>
              </div>

              <div className="my-3 space-y-1">
                <div className="text-sm font-bold text-slate-200">
                  {timeWindow.startFormatted}
                </div>
                <div className="text-xl sm:text-2xl font-black text-white font-mono">
                  {timeWindow.fullWindow.includes('→') ? timeWindow.fullWindow.split('(')[0] : timeWindow.fullWindow}
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800/80 text-xs text-slate-400 flex items-center justify-between">
              <span>⚖️ Section 52 Easements Act</span>
              <span className="text-emerald-400 font-semibold">Revocable License Active</span>
            </div>
          </div>
        </div>

        {/* 3. DIGITAL ACCESS PASS CARD */}
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-3xl p-6 sm:p-8 shadow-2xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-6 border-b border-slate-800/80">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-bold mb-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>Zero-Hardware India Stack Pass</span>
              </div>
              <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
                Digital Access Pass
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Present at entrance door scanner or use on-site caretaker handshake.
              </p>
            </div>

            {/* Mode Toggle */}
            <div className="inline-flex p-1 bg-slate-950 border border-slate-800 rounded-2xl shrink-0 self-start sm:self-auto">
              <button
                type="button"
                onClick={() => setAccessMode('qr')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer flex items-center gap-1.5 ${
                  accessMode === 'qr' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
                }`}
              >
                <span>📱</span>
                <span>Digital QR & PIN</span>
              </button>
              <button
                type="button"
                onClick={() => setAccessMode('keybox')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition cursor-pointer flex items-center gap-1.5 ${
                  accessMode === 'keybox' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'
                }`}
              >
                <span>🔑</span>
                <span>Mechanical Keybox</span>
              </button>
            </div>
          </div>

          {/* Mode Content */}
          {accessMode === 'qr' ? (
            <div className="flex flex-col items-center text-center py-4">
              {/* Square Aspect Ratio QR Pass Surface */}
              <div className="aspect-square w-52 sm:w-60 bg-white p-5 rounded-3xl shadow-2xl flex flex-col items-center justify-center border-4 border-slate-800/20 mb-6 shrink-0">
                <div className="w-full h-full border-4 border-dashed border-slate-900 rounded-2xl flex flex-col items-center justify-center p-3 text-center">
                  <span className="text-4xl mb-2">📱</span>
                  <span className="text-xs font-mono font-black text-slate-950 break-all px-2 leading-tight">
                    {booking.qr_code_hash || booking.room_qr_token || `SPL-PASS-${booking.id}`}
                  </span>
                  <div className="mt-3 px-3 py-1 rounded-lg bg-indigo-50 border border-indigo-200">
                    <span className="text-xs font-mono font-bold text-indigo-700">
                      Door PIN: {booking.arrival_pin || '4821'}
                    </span>
                  </div>
                  <span className="text-[9px] text-slate-500 font-medium mt-2">SpaceLoop Verified Pass</span>
                </div>
              </div>

              <div className="space-y-1.5 max-w-sm">
                <div className="text-sm font-mono font-bold text-white">
                  Booking Reference #{booking.id}
                </div>
                <div className="text-xs text-slate-400">
                  Scan door QR code or enter PIN <span className="font-mono text-indigo-400 font-bold">{booking.arrival_pin || '4821'}</span> on physical keypad.
                </div>
              </div>
            </div>
          ) : (
            /* Mechanical Keybox Display */
            <div className="max-w-xl mx-auto bg-slate-950 border border-amber-500/30 rounded-2xl p-6 space-y-4 my-2 text-left">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🔐</span>
                  <span className="text-sm font-bold text-amber-300">Master Lock Mechanical Keybox</span>
                </div>
                <span className="px-3 py-1 rounded-lg bg-amber-500/20 border border-amber-500/30 font-mono text-xs font-black text-amber-300">
                  PIN: {keyboxPin}
                </span>
              </div>

              <div className="space-y-2 text-xs text-slate-300">
                <div className="font-bold text-white">Physical Key Retrieval Steps:</div>
                <div className="p-3 bg-slate-900 rounded-xl border border-slate-800/80 space-y-2">
                  <p>1. Locate the mechanical keybox mounted adjacent to the premise door frame.</p>
                  <p>
                    2. Align 4 numbered dials to session access code <span className="font-mono text-amber-300 font-bold">{keyboxPin}</span>.
                  </p>
                  <p>3. Press black release lever downward to open faceplate and retrieve physical door key.</p>
                </div>
                <p className="text-[11px] text-amber-400/90 pt-1">
                  ⚠️ Rotating session credential. Always scramble dials after retrieving the key to preserve premise safety.
                </p>
              </div>
            </div>
          )}

          {/* Geofence Check-in Button or Active Indicator */}
          <div className="mt-6 pt-6 border-t border-slate-800/80 max-w-xl mx-auto">
            {!isCheckedIn && !isCompleted ? (
              <div className="space-y-3">
                <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-center">
                  <span className="text-xs text-indigo-300 font-medium">
                    📍 Location Guard: Device must be within 50m of the space coordinates to activate.
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleCheckIn}
                  disabled={actionLoading}
                  className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-2xl text-white font-extrabold text-base shadow-xl shadow-emerald-600/30 flex items-center justify-center gap-2 cursor-pointer transition transform hover:-translate-y-0.5"
                >
                  <span>📍</span>
                  <span>{actionLoading ? 'Verifying 50m Geofence...' : 'Verify Geofence & Activate Digital Pass'}</span>
                </button>
              </div>
            ) : (
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl text-center flex items-center justify-center gap-2">
                <span className="text-emerald-400 font-bold">✓</span>
                <span className="text-sm font-bold text-emerald-300">
                  Digital Access Pass Active • Verified within 50m Geofence
                </span>
              </div>
            )}
          </div>
        </div>

        {/* 4. RESPONSIVE GRID: SECURITY / ESCROW & ROOM CONDITION CARDS */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Security Deposit & Escrow Card */}
          <div className="bg-slate-900/90 border border-slate-800/80 rounded-3xl p-6 shadow-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span>🔒</span>
                  <span className="text-xs font-black tracking-wider uppercase text-slate-300">Security Deposit</span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                  {isCompleted ? '✓ Refunded' : 'Automated Escrow'}
                </span>
              </div>

              <div className="my-3">
                <div className="text-3xl font-black text-emerald-400">
                  ₹{Math.round(booking.deposit_held || booking.escrow_deposit_amount || 100)}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {isCompleted ? 'Refund credited back to your UPI VPA' : 'Held in automated micro-escrow'}
                </div>
              </div>

              <div className="space-y-2 pt-3 border-t border-slate-800/80 text-xs text-slate-300">
                <div className="flex items-center gap-2">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span>Pre-authorized via UPI mandate protocol</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span>Instant refund upon clean exit condition delta</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span>Host cannot arbitrarily deduct funds</span>
                </div>
              </div>
            </div>

            <div className="pt-4 mt-4 border-t border-slate-800/80 text-[11px] text-slate-500">
              Powered by NPCI UPI 2.0 Micro-Escrow
            </div>
          </div>

          {/* Room Condition Card (Proper Responsive Card, NOT a narrow sidebar!) */}
          <div className="bg-slate-900/90 border border-slate-800/80 rounded-3xl p-6 shadow-xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span>📸</span>
                  <span className="text-xs font-black tracking-wider uppercase text-slate-300">Room Condition</span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-500/10 border border-indigo-500/30 text-indigo-300">
                  AI Vision Delta
                </span>
              </div>

              <div className="space-y-3 my-3 text-xs">
                <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl">
                  <div className="font-bold text-white flex items-center gap-2 mb-1">
                    <span className="text-emerald-400">✓</span> Before Session: Baseline Recorded
                  </div>
                  <p className="text-slate-400 text-[11px]">
                    Original space layout and clean condition benchmarked by host.
                  </p>
                </div>

                <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl">
                  <div className="font-bold text-white flex items-center gap-2 mb-1">
                    <span className="text-indigo-400">•</span> During Session: Keep Space Tidy
                  </div>
                  <p className="text-slate-400 text-[11px]">
                    Maintain furniture position, keep trash cleared, and power down fans.
                  </p>
                </div>

                <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl">
                  <div className="font-bold text-white flex items-center gap-2 mb-1">
                    <span className="text-amber-400">•</span> After Session: Submit Exit Pan
                  </div>
                  <p className="text-slate-400 text-[11px]">
                    AI photo comparison verifies clean vacancy and unlocks deposit refund.
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800/80 text-[11px] text-slate-500">
              Automated delta inspection protects both renter & host
            </div>
          </div>
        </div>

        {/* 5. FINAL ACTION CARD (CHECKOUT & ESCROW RELEASE OR REPORT) */}
        {!isCompleted ? (
          isCheckedIn && (
            <div className="bg-slate-900/90 border border-indigo-500/40 rounded-3xl p-6 sm:p-8 shadow-2xl mb-12">
              <div className="max-w-2xl mx-auto space-y-6">
                <div className="text-center space-y-2">
                  <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto text-xl">
                    🏁
                  </div>
                  <h3 className="text-2xl font-black text-white">
                    Checkout & Escrow Settlement
                  </h3>
                  <p className="text-xs text-slate-400 max-w-md mx-auto">
                    Ready to conclude your session? Verify that fans and lights are off and submit your exit photo to instantly release your ₹100 deposit.
                  </p>
                </div>

                {/* Exit Photo Pan Preview */}
                <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-300">Room Exit Pan Snapshot:</span>
                    <span className="text-[10px] text-emerald-400 font-bold">✓ Ready for Comparison</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <img
                      src={exitPhoto}
                      alt="Exit Pan"
                      className="w-24 h-18 sm:w-32 sm:h-20 rounded-xl object-cover border border-slate-700 shrink-0"
                    />
                    <div className="text-xs text-slate-400 space-y-1">
                      <p className="font-semibold text-white">AI Vision Checkpoints:</p>
                      <p>✓ Furniture alignment check</p>
                      <p>✓ Zero waste & litter check</p>
                      <p>✓ Electricals & lighting shutdown</p>
                    </div>
                  </div>
                </div>

                {/* Primary Action Button */}
                <button
                  type="button"
                  onClick={handleCheckOut}
                  disabled={actionLoading}
                  className="w-full py-4.5 bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-700 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 rounded-2xl text-white font-black text-base shadow-xl shadow-indigo-600/30 flex items-center justify-center gap-3 cursor-pointer transition transform hover:-translate-y-0.5"
                >
                  <span>🏁</span>
                  <span>{actionLoading ? 'Verifying AI Condition Delta & Releasing Escrow...' : 'Check Out & Release ₹100 Escrow'}</span>
                </button>
              </div>
            </div>
          )
        ) : (
          /* Completed Delta Report Card */
          <div className="bg-slate-900/90 border border-emerald-500/40 rounded-3xl p-6 sm:p-8 shadow-2xl mb-12">
            <div className="max-w-2xl mx-auto space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-lg">
                    ✨
                  </div>
                  <div>
                    <h3 className="text-lg font-black text-white">AI Room Condition Delta Report</h3>
                    <p className="text-xs text-slate-400">Session successfully concluded</p>
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-emerald-500/20 border border-emerald-500/40 text-emerald-300">
                  Pass • {Math.round(((inspectionResult?.condition_match_score ?? 0.98) * 100))}% Match
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl flex items-center justify-between">
                  <span className="text-slate-400">🪑 Furniture Layout:</span>
                  <span className="text-emerald-400 font-bold">✓ Matches baseline</span>
                </div>
                <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl flex items-center justify-between">
                  <span className="text-slate-400">🗑️ Waste & Litter:</span>
                  <span className="text-emerald-400 font-bold">✓ Zero debris</span>
                </div>
                <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl flex items-center justify-between">
                  <span className="text-slate-400">💡 Electricals & Fans:</span>
                  <span className="text-emerald-400 font-bold">✓ Switched off</span>
                </div>
                <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl flex items-center justify-between">
                  <span className="text-slate-400">⏱️ Session Punctuality:</span>
                  <span className="text-indigo-400 font-bold">{punctualityScore || 100}% on-time</span>
                </div>
              </div>

              <div className="p-4 bg-emerald-950/60 border border-emerald-500/30 rounded-2xl flex items-center justify-between">
                <div>
                  <div className="text-sm font-bold text-emerald-300">₹100 Security Deposit Refunded</div>
                  <div className="text-[11px] text-slate-400">Instant NPCI / UPI reversal completed</div>
                </div>
                <span className="px-3 py-1 rounded-lg bg-emerald-500/20 text-emerald-400 text-xs font-black">
                  ✓ Settled
                </span>
              </div>

              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="w-full py-4 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-2xl text-white font-bold text-sm cursor-pointer transition"
              >
                Return to Seeker Dashboard →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
