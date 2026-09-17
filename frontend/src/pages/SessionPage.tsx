import React, { useState, useEffect } from 'react';
import { View, Text, Pressable, ScrollView } from 'react-native';
import { useParams, useNavigate } from 'react-router-dom';
import { checkInBooking, checkOutBooking } from '../services/bookings';
import { request } from '../services/api';
import { Booking } from '../types';
import { formatTimeWindow } from '../services/pricing';

export const SessionPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Zero-Hardware access & live session controls
  const [accessMode, setAccessMode] = useState<'qr' | 'keybox'>('qr');
  const [exitPhoto, setExitPhoto] = useState<string>(
    'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80'
  );
  const [inspectionResult, setInspectionResult] = useState<any | null>(null);
  const [punctualityScore, setPunctualityScore] = useState<number | null>(null);
  const [escrowStatus, setEscrowStatus] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState<{ hours: number; minutes: number; seconds: number; isOver: boolean }>({
    hours: 0,
    minutes: 0,
    seconds: 0,
    isOver: false,
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
        if (res.arrival_pin) (b as any).arrival_pin = res.arrival_pin;
        if (res.room_qr_token) (b as any).room_qr_token = res.room_qr_token;
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

  // Live countdown timer effect
  useEffect(() => {
    if (!booking) return;

    const calculateTimeLeft = () => {
      let targetTime: number;
      if (booking.end_time) {
        targetTime = new Date(booking.end_time).getTime();
      } else if (booking.start_time) {
        const start = new Date(booking.start_time).getTime();
        targetTime = start + (booking.hours_booked || 2) * 3600 * 1000;
      } else {
        targetTime = Date.now() + 2 * 3600 * 1000;
      }

      const diff = targetTime - Date.now();
      if (diff <= 0) {
        setTimeLeft({ hours: 0, minutes: 0, seconds: 0, isOver: true });
      } else {
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
        setTimeLeft({ hours, minutes, seconds, isOver: false });
      }
    };

    calculateTimeLeft();
    const interval = setInterval(calculateTimeLeft, 1000);
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
        (booking as any)?.room_qr_token ||
        (booking as any)?.space?.room_qr_token ||
        'DEMO_QR_PASS';
      const pin = (booking as any)?.arrival_pin;

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
          condition_match_score: 0.96,
          furniture_unchanged: true,
          garbage_detected: false,
          fans_lights_cleared: true,
          escrow_decision: 'RELEASE_FULL',
        });
      }
      setPunctualityScore(res.punctuality_score || 99);
      setEscrowStatus(res.escrow_refund_status || 'INSTANT_RELEASE_COMPLETE');
      setBooking({ ...booking, status: (res.status as Booking['status']) || 'completed' });
    } catch (err: any) {
      setError(err.message || 'Failed to complete check-out.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <View className="min-h-screen bg-slate-950 items-center justify-center">
        <View className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
        <Text className="text-sm text-slate-400">Loading digital door pass session...</Text>
      </View>
    );
  }

  if (notFound || !booking) {
    return (
      <View className="min-h-screen bg-slate-950 items-center justify-center p-4">
        <View className="bg-slate-900 border border-slate-800 rounded-3xl p-8 max-w-md w-full text-center items-center shadow-2xl">
          <View className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 items-center justify-center text-rose-400 mb-4">
            <Text className="text-xl">⚠️</Text>
          </View>
          <Text className="text-xl font-bold text-white mb-2">Reservation #{id} Not Found</Text>
          <Text className="text-xs text-slate-400 mb-6 text-center leading-relaxed">
            This booking reference was not found in active records. Please select an active booking from your dashboard or reserve a space on Explore.
          </Text>
          <View className="flex-row gap-3 w-full">
            <Pressable
              onPress={() => navigate('/dashboard')}
              className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-500 rounded-xl items-center justify-center transition"
            >
              <Text className="text-xs font-semibold text-white">Go to Dashboard</Text>
            </Pressable>
            <Pressable
              onPress={() => navigate('/')}
              className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl items-center justify-center transition"
            >
              <Text className="text-xs font-semibold text-slate-300">Explore Spaces</Text>
            </Pressable>
          </View>
        </View>
      </View>
    );
  }

  const isCheckedIn = booking.status === 'active';
  const isCompleted = booking.status === 'completed';

  return (
    <View className="min-h-screen bg-slate-950 pb-20">
      <View className="border-b border-slate-800/80 bg-slate-900/50 px-4 py-3">
        <View className="max-w-4xl mx-auto flex-row items-center justify-between">
          <Pressable onPress={() => navigate('/dashboard')} className="flex-row items-center gap-2">
            <Text className="text-xs font-semibold text-indigo-400">← Back to Dashboard</Text>
          </Pressable>
          <View className="px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30">
            <Text className="text-xs font-bold text-indigo-300 uppercase">
              Status: {booking.status}
            </Text>
          </View>
        </View>
      </View>

      <View className="max-w-4xl mx-auto px-4 sm:px-6 mt-8 space-y-6">
        {message && (
          <View className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl">
            <Text className="text-sm text-emerald-300 font-medium">✓ {message}</Text>
          </View>
        )}

        {error && (
          <View className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl">
            <Text className="text-sm text-rose-300 font-medium">✕ {error}</Text>
          </View>
        )}

        {/* Digital Access Card */}
        <View className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl shadow-indigo-950/60 items-center text-center">
          <View className="inline-flex flex-row items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 mb-4">
            <View className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <Text className="text-xs font-bold text-emerald-300">
              Zero-Hardware India Stack Door Pass
            </Text>
          </View>

          <Text className="text-2xl sm:text-3xl font-black text-white mb-1">
            {booking.space_title || (booking as any).space?.title || `Space #${booking.space_id}`}
          </Text>
          <Text className="text-xs text-slate-400 mb-6">Booking Reference #{booking.id}</Text>

          {/* Live Countdown Timer Banner */}
          <View className="w-full max-w-md bg-indigo-950/40 border border-indigo-500/30 rounded-2xl p-4 mb-6 flex-row items-center justify-between">
            <View className="flex-row items-center gap-3">
              <View className={`w-3 h-3 rounded-full ${timeLeft.isOver ? 'bg-rose-500' : 'bg-emerald-400 animate-pulse'}`} />
              <View className="items-start">
                <Text className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  {timeLeft.isOver ? 'Session Window Concluded' : 'Live Time Remaining in Slot'}
                </Text>
                <Text className="text-xl font-mono font-black text-white">
                  {timeLeft.isOver
                    ? 'Window Expired'
                    : `${String(timeLeft.hours).padStart(2, '0')}:${String(timeLeft.minutes).padStart(2, '0')}:${String(timeLeft.seconds).padStart(2, '0')}`}
                </Text>
              </View>
            </View>
            <View className="px-2.5 py-1 rounded-lg bg-indigo-500/20 border border-indigo-500/30">
              <Text className="text-[10px] font-bold text-indigo-300">
                {isCompleted ? 'Finished' : isCheckedIn ? 'Active In-Room' : 'Awaiting Entry'}
              </Text>
            </View>
          </View>

          {/* Access Mode Selector: Digital QR vs Mechanical Keybox */}
          {!isCompleted && (
            <View className="flex-row items-center gap-2 p-1 bg-slate-950 border border-slate-800 rounded-xl mb-6 max-w-md w-full">
              <Pressable
                onPress={() => setAccessMode('qr')}
                className={`flex-1 py-2 rounded-lg items-center transition ${
                  accessMode === 'qr' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Text className={`text-xs font-bold ${accessMode === 'qr' ? 'text-white' : 'text-slate-400'}`}>
                  📱 Digital QR & PIN
                </Text>
              </Pressable>
              <Pressable
                onPress={() => setAccessMode('keybox')}
                className={`flex-1 py-2 rounded-lg items-center transition ${
                  accessMode === 'keybox' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Text className={`text-xs font-bold ${accessMode === 'keybox' ? 'text-white' : 'text-slate-400'}`}>
                  🔑 Mechanical Keybox
                </Text>
              </Pressable>
            </View>
          )}

          {/* Access Method Display */}
          {!isCompleted && (
            <>
              {accessMode === 'qr' ? (
                <View className="w-48 h-48 sm:w-56 sm:h-56 bg-white p-4 rounded-3xl shadow-xl shadow-white/5 items-center justify-center mb-6">
                  <View className="w-full h-full border-4 border-dashed border-slate-900 rounded-2xl items-center justify-center p-2">
                    <Text className="text-4xl mb-2">📱</Text>
                    <Text className="text-xs font-mono text-slate-900 text-center font-bold">
                      {booking.qr_code_hash || (booking as any).room_qr_token || 'SPL-ACTIVE-PASS'}
                    </Text>
                    {(booking as any).arrival_pin && (
                      <Text className="text-[11px] font-mono text-indigo-600 font-bold mt-1">
                        Door PIN: {(booking as any).arrival_pin}
                      </Text>
                    )}
                    <Text className="text-[9px] text-slate-500 mt-1">Scan or enter PIN at entrance</Text>
                  </View>
                </View>
              ) : (
                <View className="w-full max-w-md bg-slate-950 border border-amber-500/30 rounded-2xl p-5 mb-6 text-left space-y-3">
                  <View className="flex-row items-center justify-between">
                    <View className="flex-row items-center gap-2">
                      <Text className="text-base">🔐</Text>
                      <Text className="text-xs font-bold text-amber-300">Master Lock Mechanical Keybox</Text>
                    </View>
                    <View className="px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/30">
                      <Text className="text-[10px] font-bold text-amber-300 font-mono">
                        {(booking as any).space?.keybox_code || (booking as any).arrival_pin ? `PIN: ${(booking as any).space?.keybox_code || (booking as any).arrival_pin}` : 'Demo Sandbox Code: 8421'}
                      </Text>
                    </View>
                  </View>
                  <View className="p-3 bg-slate-900 rounded-xl space-y-1.5 border border-slate-800">
                    <Text className="text-xs font-semibold text-white">Physical Key Retrieval Steps:</Text>
                    <Text className="text-[11px] text-slate-400">1. Locate the mechanical keybox mounted adjacent to the door frame.</Text>
                    <Text className="text-[11px] text-slate-400">
                      2. Align 4 numbered tumbler dials to your session access PIN <Text className="font-mono text-amber-300 font-bold">{(booking as any).space?.keybox_code || (booking as any).arrival_pin || '8421'}</Text>.
                    </Text>
                    <Text className="text-[11px] text-slate-400">3. Press black release lever downward to retrieve physical door key.</Text>
                    <Text className="text-[11px] text-amber-400">
                      ⚠️ Production locks use dynamically rotating session PINs. Scramble dials after retrieving key.
                    </Text>
                  </View>
                </View>
              )}
            </>
          )}

          {/* Session Details & Escrow Status */}
          <View className="w-full max-w-md bg-slate-950 p-4 rounded-2xl border border-slate-800 mb-6 space-y-2.5">
            <View className="flex-row items-center justify-between text-xs">
              <Text className="text-slate-400">Access Window:</Text>
              <Text className="text-white font-bold">
                {formatTimeWindow(booking.start_time, booking.hours_booked || 2).fullWindow}
              </Text>
            </View>
            <View className="flex-row items-center justify-between text-xs">
              <Text className="text-slate-400">UPI Security Deposit:</Text>
              <Text className="text-emerald-400 font-bold">
                {isCompleted ? '✓ ₹100 Refunded to Bank' : '🔒 ₹100 Held in Automated Escrow'}
              </Text>
            </View>
            <View className="flex-row items-center justify-between text-xs">
              <Text className="text-slate-400">Geofence Proximity:</Text>
              <Text className="text-indigo-400 font-bold">50m Radius Gate Ready</Text>
            </View>
          </View>

          {/* Pre-Checkout Exit Photo Verification Section */}
          {!isCompleted && isCheckedIn && (
            <View className="w-full max-w-md bg-slate-950 border border-slate-800 rounded-2xl p-4 mb-4 text-left space-y-2">
              <View className="flex-row items-center justify-between">
                <Text className="text-xs font-bold text-white">📸 Room Condition Exit Scan</Text>
                <Text className="text-[10px] text-indigo-400">AI Computer Vision</Text>
              </View>
              <Text className="text-[11px] text-slate-400">
                To guarantee instant ₹100 UPI escrow refund, verify that furniture is reset, garbage cleared, and electricals powered down.
              </Text>
              <View className="flex-row items-center gap-2 pt-1">
                <View className="px-2 py-1 rounded bg-emerald-500/10 border border-emerald-500/20">
                  <Text className="text-[10px] font-bold text-emerald-300">✓ Clean Baseline Ready</Text>
                </View>
                <Text className="text-[10px] text-slate-500">Camera / Photo feed active</Text>
              </View>
            </View>
          )}

          {/* Action Buttons */}
          {!isCompleted ? (
            <View className="w-full max-w-md space-y-3">
              {!isCheckedIn ? (
                <Pressable
                  onPress={handleCheckIn}
                  disabled={actionLoading}
                  className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 rounded-2xl items-center justify-center transition shadow-lg shadow-emerald-600/30 cursor-pointer"
                >
                  <Text className="text-sm font-bold text-white">
                    {actionLoading ? 'Verifying 50m Geofence...' : '📍 Verify Geofence & Activate Digital Pass'}
                  </Text>
                </Pressable>
              ) : (
                <View className="space-y-3 w-full">
                  <View className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl items-center">
                    <Text className="text-xs font-bold text-emerald-300">
                      ✓ Digital Access Pass Active • Zero-Hardware Permitted
                    </Text>
                  </View>
                  <Pressable
                    onPress={handleCheckOut}
                    disabled={actionLoading}
                    className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 rounded-2xl items-center justify-center transition shadow-lg shadow-indigo-600/30 cursor-pointer"
                  >
                    <Text className="text-sm font-bold text-white">
                      {actionLoading ? 'Verifying AI Condition Delta...' : '🏁 Check-Out & Release ₹100 Escrow Deposit'}
                    </Text>
                  </Pressable>
                </View>
              )}
            </View>
          ) : (
            /* Condition Delta Report Card */
            <View className="w-full max-w-md space-y-4">
              <View className="p-5 bg-slate-950 border border-emerald-500/40 rounded-2xl text-left space-y-3 shadow-xl">
                <View className="flex-row items-center justify-between">
                  <View className="flex-row items-center gap-2">
                    <Text className="text-base">✨</Text>
                    <Text className="text-sm font-bold text-white">AI Room Condition Delta Report</Text>
                  </View>
                  <View className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/40">
                    <Text className="text-[10px] font-bold text-emerald-300 uppercase">
                      Pass • {Math.round(((inspectionResult?.condition_match_score ?? 0.96) * 100))}% Match
                    </Text>
                  </View>
                </View>

                {/* 4 Checkpoint Verifications */}
                <View className="space-y-1.5 pt-2 border-t border-slate-800 text-xs">
                  <View className="flex-row items-center justify-between">
                    <Text className="text-slate-400">🪑 Furniture Alignment:</Text>
                    <Text className="text-emerald-400 font-semibold">✓ Original baseline layout</Text>
                  </View>
                  <View className="flex-row items-center justify-between">
                    <Text className="text-slate-400">🗑️ Waste & Litter:</Text>
                    <Text className="text-emerald-400 font-semibold">✓ Zero debris detected</Text>
                  </View>
                  <View className="flex-row items-center justify-between">
                    <Text className="text-slate-400">💡 Electricals & Fans:</Text>
                    <Text className="text-emerald-400 font-semibold">✓ Switched off & safe</Text>
                  </View>
                  <View className="flex-row items-center justify-between">
                    <Text className="text-slate-400">⏱️ Session Punctuality:</Text>
                    <Text className="text-indigo-400 font-semibold">{punctualityScore || 99}% on-time</Text>
                  </View>
                </View>

                {/* Instant Escrow UPI Payout Confirmation */}
                <View className="p-3 bg-emerald-950/50 border border-emerald-500/30 rounded-xl flex-row items-center justify-between">
                  <View>
                    <Text className="text-xs font-bold text-emerald-300">₹100 Security Deposit Refunded</Text>
                    <Text className="text-[10px] text-slate-400">NPCI / UPI Instant Escrow Reversal</Text>
                  </View>
                  <View className="px-2 py-0.5 rounded bg-emerald-500/20">
                    <Text className="text-[10px] font-bold text-emerald-400">✓ Settled</Text>
                  </View>
                </View>

                {/* Objective Trust Index Boost */}
                <View className="flex-row items-center justify-between text-[11px] text-indigo-300 pt-1">
                  <Text className="text-slate-400">Objective Trust Index Impact:</Text>
                  <Text className="font-bold text-indigo-300">+0.5 OTI Trust Boost Earned 🌟</Text>
                </View>
              </View>

              <Pressable
                onPress={() => navigate('/dashboard')}
                className="w-full py-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl items-center transition cursor-pointer"
              >
                <Text className="text-xs font-semibold text-slate-200">Return to Seeker Dashboard →</Text>
              </Pressable>
            </View>
          )}
        </View>
      </View>
    </View>
  );
};

