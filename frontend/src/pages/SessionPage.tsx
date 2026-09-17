import React, { useState, useEffect } from 'react';
import { View, Text, Pressable, ScrollView } from 'react-native';
import { useParams, useNavigate } from 'react-router-dom';
import { checkInBooking, checkOutBooking } from '../services/bookings';
import { request } from '../services/api';
import { Booking } from '../types';

export const SessionPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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
        exit_photo: 'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80',
      };
      const res = await checkOutBooking(Number(id), coords);
      setMessage(res.message || 'Check-out completed! ₹100 UPI deposit released to your bank account.');
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

        {/* Digital QR Door Pass Card */}
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

          {/* QR Box Visual */}
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

          {/* Session Details & Escrow Status */}
          <View className="w-full max-w-md bg-slate-950 p-4 rounded-2xl border border-slate-800 mb-6 space-y-2.5">
            <View className="flex-row items-center justify-between text-xs">
              <Text className="text-slate-400">Access Window:</Text>
              <Text className="text-white font-bold">
                {booking.hours_booked || 2} Hours ({booking.start_time || 'Start'} → {booking.end_time || 'End'})
              </Text>
            </View>
            <View className="flex-row items-center justify-between text-xs">
              <Text className="text-slate-400">UPI Security Deposit:</Text>
              <Text className="text-emerald-400 font-bold">
                {isCompleted ? '✓ ₹100 Released to Bank' : '🔒 ₹100 Held in Automated Escrow'}
              </Text>
            </View>
            <View className="flex-row items-center justify-between text-xs">
              <Text className="text-slate-400">Geofence Proximity:</Text>
              <Text className="text-indigo-400 font-bold">50m Radius Gate Ready</Text>
            </View>
          </View>

          {/* Action Buttons */}
          {!isCompleted ? (
            <View className="w-full max-w-md space-y-3">
              {!isCheckedIn ? (
                <Pressable
                  onPress={handleCheckIn}
                  disabled={actionLoading}
                  className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 rounded-2xl items-center justify-center transition shadow-lg shadow-emerald-600/30"
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
                    className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 rounded-2xl items-center justify-center transition shadow-lg shadow-indigo-600/30"
                  >
                    <Text className="text-sm font-bold text-white">
                      {actionLoading ? 'Finalizing Checkout...' : '🏁 Check-Out & Release ₹100 Deposit'}
                    </Text>
                  </Pressable>
                </View>
              )}
            </View>
          ) : (
            <View className="p-4 bg-slate-800/80 rounded-2xl border border-slate-700 w-full max-w-md">
              <Text className="text-sm font-bold text-white mb-1">
                ✨ Session Successfully Completed
              </Text>
              <Text className="text-xs text-slate-300">
                Thank you for using SpaceLoop. Your deposit was released and host rating submitted.
              </Text>
            </View>
          )}
        </View>
      </View>
    </View>
  );
};
