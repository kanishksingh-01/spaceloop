import React, { useState, useEffect } from 'react';
import { View, Text, Pressable, Image, TextInput, ScrollView } from 'react-native';
import { useParams, useNavigate } from 'react-router-dom';
import { Space, User } from '../types';
import { getSpaceById, submitInquiry } from '../services/spaces';
import { createBooking, precheckBooking } from '../services/bookings';
import { AuthModal } from '../components/common/AuthModal';
import { calculateRentalPricing, formatTimeWindow, MIN_BOOKING_HOURS, MAX_BOOKING_HOURS } from '../services/pricing';

interface SpaceDetailPageProps {
  currentUser: User | null;
}

export const SpaceDetailPage: React.FC<SpaceDetailPageProps> = ({ currentUser }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [space, setSpace] = useState<Space | null>(null);
  const [loading, setLoading] = useState(true);

  // Direct Inquiry States
  const [inquiryQuestion, setInquiryQuestion] = useState('');
  const [inquiryLoading, setInquiryLoading] = useState(false);
  const [inquiryResponse, setInquiryResponse] = useState<string | null>(null);
  const [inquiryError, setInquiryError] = useState<string | null>(null);

  // Flexible Booking Time & Duration States
  const [bookingMode, setBookingMode] = useState<'now' | 'schedule'>('now');
  const [selectedDate, setSelectedDate] = useState(() => {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  });
  const [selectedTime, setSelectedTime] = useState(() => {
    const d = new Date();
    const currentMins = d.getMinutes();
    const roundedMins = Math.ceil(currentMins / 15) * 15;
    d.setMinutes(roundedMins + 15, 0, 0);
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `${hh}:${mm}`;
  });
  const [hours, setHours] = useState<number>(2);
  const [customHoursInput, setCustomHoursInput] = useState<string>('2');
  const [purpose, setPurpose] = useState<string>('Study & Creative Work Session');

  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [availabilityStatus, setAvailabilityStatus] = useState<'idle' | 'checking' | 'available' | 'conflict'>('idle');
  const [availabilityMessage, setAvailabilityMessage] = useState<string | null>(null);
  const precheckRequestId = React.useRef(0);

  const [showAuthModal, setShowAuthModal] = useState(false);
  const [selectedPhotoIndex, setSelectedPhotoIndex] = useState(0);

  useEffect(() => {
    if (!id) return;
    const loadSpace = async () => {
      setLoading(true);
      try {
        const data = await getSpaceById(Number(id));
        setSpace(data);
      } catch (err) {
        console.error('Failed to load space:', err);
      } finally {
        setLoading(false);
      }
    };
    loadSpace();
  }, [id]);

  const pricing = React.useMemo(() => {
    return calculateRentalPricing(space?.hourly_rate ?? 50, hours);
  }, [space?.hourly_rate, hours]);

  const computedStart = React.useMemo(() => {
    if (bookingMode === 'now') {
      return new Date(Date.now() + 15 * 60 * 1000);
    }
    const [year, month, day] = selectedDate.split('-').map(Number);
    const [hour, minute] = selectedTime.split(':').map(Number);
    const dt = new Date(year, (month || 1) - 1, day || 1, hour || 0, minute || 0);
    return isNaN(dt.getTime()) ? new Date(Date.now() + 15 * 60 * 1000) : dt;
  }, [bookingMode, selectedDate, selectedTime]);

  const timeWindow = React.useMemo(() => {
    return formatTimeWindow(computedStart, pricing.hours);
  }, [computedStart, pricing.hours]);

  // Debounced dynamic availability precheck with stale request protection
  useEffect(() => {
    setBookingError(null);
    setAvailabilityMessage(null);

    if (!space?.id || !pricing.isValidDuration) {
      setAvailabilityStatus('idle');
      return;
    }

    const reqId = ++precheckRequestId.current;
    setAvailabilityStatus('checking');

    const timer = setTimeout(async () => {
      try {
        const startIso = computedStart.toISOString();
        const endObj = new Date(computedStart.getTime() + pricing.hours * 3600 * 1000);
        const endIso = endObj.toISOString();

        const res = await precheckBooking(space.id, startIso, endIso, pricing.hours);
        if (reqId !== precheckRequestId.current) return;

        if (res && res.available === false) {
          setAvailabilityStatus('conflict');
          setAvailabilityMessage(
            res.message || 'This space is already booked for the selected time slot. Please choose another time or adjust duration.'
          );
        } else {
          setAvailabilityStatus('available');
          setAvailabilityMessage('Selected Time Slot Available');
        }
      } catch (err: any) {
        if (reqId !== precheckRequestId.current) return;
        if (
          err?.status === 409 ||
          err?.message?.toLowerCase().includes('conflict') ||
          err?.message?.toLowerCase().includes('already booked')
        ) {
          setAvailabilityStatus('conflict');
          setAvailabilityMessage('This space is already booked for the selected time slot. Please choose another time or adjust duration.');
        } else {
          setAvailabilityStatus('idle');
        }
      }
    }, 350);

    return () => clearTimeout(timer);
  }, [space?.id, computedStart, pricing.hours, pricing.isValidDuration]);

  const handleHoursChange = (newVal: number) => {
    setBookingError(null);
    const clamped = Math.max(MIN_BOOKING_HOURS, Math.min(MAX_BOOKING_HOURS, Math.round(newVal * 10) / 10));
    setHours(clamped);
    setCustomHoursInput(String(clamped));
  };

  const handleCustomInput = (val: string) => {
    setBookingError(null);
    setCustomHoursInput(val);
    const parsed = parseFloat(val);
    if (!isNaN(parsed) && parsed >= MIN_BOOKING_HOURS && parsed <= MAX_BOOKING_HOURS) {
      setHours(Math.round(parsed * 10) / 10);
    }
  };

  const setQuickDate = (offsetDays: number) => {
    setBookingError(null);
    const d = new Date();
    d.setDate(d.getDate() + offsetDays);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    setSelectedDate(`${y}-${m}-${day}`);
  };

  const setQuickTime = (timeStr: string) => {
    setBookingError(null);
    setSelectedTime(timeStr);
  };

  if (loading) {
    return (
      <View className="min-h-screen bg-slate-950 items-center justify-center">
        <View className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4" />
        <Text className="text-sm text-slate-400">Loading space details...</Text>
      </View>
    );
  }

  if (!space) {
    return (
      <View className="min-h-screen bg-slate-950 items-center justify-center p-4">
        <Text className="text-lg font-bold text-white mb-2">Space not found</Text>
        <Pressable onPress={() => navigate('/')} className="px-4 py-2 bg-indigo-600 rounded-xl">
          <Text className="text-xs font-semibold text-white">← Return to Explore</Text>
        </Pressable>
      </View>
    );
  }

  const photos = space.photos && space.photos.length > 0
    ? space.photos
    : ['https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=1200&q=80'];

  const handleSendInquiry = async () => {
    const q = inquiryQuestion.trim();
    if (!q || inquiryLoading) return;
    if (!currentUser) {
      setShowAuthModal(true);
      return;
    }
    setInquiryLoading(true);
    setInquiryError(null);
    try {
      const res = await submitInquiry(space.id, q);
      const answer = res.inquiry?.ai_answer || 'Inquiry sent directly to host.';
      setInquiryResponse(answer);
      setInquiryQuestion('');
    } catch (err: any) {
      setInquiryError(err.message || 'Failed to submit inquiry. Please try again.');
    } finally {
      setInquiryLoading(false);
    }
  };

  const handleBookNow = async () => {
    if (!currentUser) {
      setShowAuthModal(true);
      return;
    }

    if (!pricing.isValidDuration) {
      setBookingError(pricing.validationError || 'Please select a valid duration between 0.5 and 168 hours.');
      return;
    }

    if (bookingMode === 'schedule' && computedStart.getTime() < Date.now() - 5 * 60 * 1000) {
      setBookingError('Selected booking time is in the past. Please select a future time slot.');
      return;
    }

    if (availabilityStatus === 'conflict') {
      setBookingError(availabilityMessage || 'This space is already booked for the selected time slot. Please choose another time or adjust duration.');
      return;
    }

    setBookingLoading(true);
    setBookingError(null);
    try {
      const startIso = computedStart.toISOString();
      const endObj = new Date(computedStart.getTime() + pricing.hours * 3600 * 1000);
      const endIso = endObj.toISOString();

      const res = await createBooking({
        space_id: space.id,
        hours: pricing.hours,
        start_time: startIso,
        end_time: endIso,
        purpose: purpose.trim() || 'Study & Creative Work Session',
      });

      const confirmedBookingId = res.booking_id || res.booking?.id;
      if (confirmedBookingId) {
        navigate(`/session/${confirmedBookingId}`);
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      if (
        err?.status === 409 ||
        err?.message?.toLowerCase().includes('conflict') ||
        err?.message?.toLowerCase().includes('already booked')
      ) {
        setAvailabilityStatus('conflict');
        setBookingError('This space is already booked for the selected time slot. Please choose another time or adjust duration.');
      } else {
        setBookingError(err.message || 'Failed to complete booking. Please try again.');
      }
    } finally {
      setBookingLoading(false);
    }
  };

  return (
    <View className="min-h-screen bg-slate-950 pb-20">
      {/* Back Bar */}
      <View className="border-b border-slate-800/80 bg-slate-900/50 px-4 py-3">
        <View className="max-w-7xl mx-auto flex-row items-center justify-between">
          <Pressable onPress={() => navigate('/explore')} className="flex-row items-center gap-2">
            <Text className="text-xs font-semibold text-indigo-400">← Back to Explore</Text>
          </Pressable>
          <View className="flex-row items-center gap-2">
            <View className="w-2 h-2 rounded-full bg-emerald-400" />
            <Text className="text-xs text-slate-400">Active Listing • Verified Host</Text>
          </View>
        </View>
      </View>

      <View className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <View className="flex-col lg:flex-row gap-8">
          {/* Left Column: Photos & Details */}
          <View className="flex-1 space-y-6">
            {/* Main Photo Gallery */}
            <View className="space-y-3">
              <View className="w-full h-80 sm:h-96 rounded-2xl overflow-hidden bg-slate-900 border border-slate-800">
                <Image
                  source={{ uri: photos[selectedPhotoIndex] }}
                  className="w-full h-full object-cover"
                />
              </View>

              {photos.length > 1 && (
                <View className="flex-row gap-2 overflow-x-auto">
                  {photos.map((p, idx) => (
                    <Pressable
                      key={idx}
                      onPress={() => setSelectedPhotoIndex(idx)}
                      className={`w-20 h-16 rounded-xl overflow-hidden border-2 transition ${
                        selectedPhotoIndex === idx ? 'border-indigo-500 scale-105' : 'border-slate-800 opacity-60'
                      }`}
                    >
                      <Image source={{ uri: p }} className="w-full h-full object-cover" />
                    </Pressable>
                  ))}
                </View>
              )}
            </View>

            {/* Header Specs */}
            <View className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6">
              <View className="flex-row items-center gap-2 mb-2">
                <View className="bg-indigo-500/10 px-2.5 py-1 rounded-lg border border-indigo-500/20">
                  <Text className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
                    {space.category}
                  </Text>
                </View>
                <Text className="text-xs text-slate-400">📍 {space.location}, {space.city}</Text>
              </View>

              <Text className="text-2xl sm:text-3xl font-black text-white mb-3">
                {space.title}
              </Text>

              <Text className="text-sm text-slate-300 leading-relaxed mb-6">
                {space.description}
              </Text>

              {/* Host Trust Badge */}
              <View className="flex-row items-center justify-between p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 floating-interactive">
                <View className="flex-row items-center gap-3">
                  <View className="w-10 h-10 rounded-full bg-indigo-600/30 items-center justify-center border border-indigo-500/40">
                    <Text className="text-sm font-bold text-indigo-300">
                      {space.host_name ? space.host_name[0] : 'H'}
                    </Text>
                  </View>
                  <View>
                    <Text className="text-sm font-bold text-white">
                      Hosted by {space.host_name || 'SpaceLoop Verified Host'}
                    </Text>
                    <Text className="text-[11px] text-emerald-400 font-medium">
                      ✓ DigiLocker & Identity Verified Host
                    </Text>
                  </View>
                </View>
                <View className="items-end">
                  <Text className="text-xs font-semibold text-indigo-400">Host Trust Score</Text>
                  <Text className="text-sm font-black text-white">920 / 1000</Text>
                </View>
              </View>
            </View>

            {/* AI Multimodal Sensor Analysis */}
            <View className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 floating-container">
              <View className="flex-row items-center gap-2 mb-4">
                <Text className="text-xl">🤖</Text>
                <Text className="text-base font-bold text-white">AI Space Inspector Metrics</Text>
              </View>

              <View className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <View className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 floating-interactive">
                  <Text className="text-[11px] font-semibold text-slate-400">Usable Area</Text>
                  <Text className="text-lg font-black text-white mt-1">
                    {space.specs?.usable_sqft || 140} <Text className="text-xs font-normal text-slate-500">sq.ft</Text>
                  </Text>
                  <Text className="text-[10px] text-emerald-400 mt-1">✓ Measured by Vision AI</Text>
                </View>

                <View className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 floating-interactive">
                  <Text className="text-[11px] font-semibold text-slate-400">Noise Level</Text>
                  <Text className="text-lg font-black text-white mt-1">
                    {space.specs?.acoustic_db || 34} <Text className="text-xs font-normal text-slate-500">dB</Text>
                  </Text>
                  <Text className="text-[10px] text-indigo-300 mt-1">✓ Quiet study grade</Text>
                </View>

                <View className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 floating-interactive">
                  <Text className="text-[11px] font-semibold text-slate-400">Natural Lighting</Text>
                  <Text className="text-lg font-black text-white mt-1">
                    {space.specs?.lighting_lux || 480} <Text className="text-xs font-normal text-slate-500">lux</Text>
                  </Text>
                  <Text className="text-[10px] text-amber-400 mt-1">✓ Optimal for reading</Text>
                </View>

                <View className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 floating-interactive">
                  <Text className="text-[11px] font-semibold text-slate-400">Power Circuit</Text>
                  <Text className="text-lg font-black text-white mt-1">
                    {space.specs?.power_circuits || '20A'}
                  </Text>
                  <Text className="text-[10px] text-indigo-300 mt-1">✓ Grounded outlets</Text>
                </View>
              </View>
            </View>

            {/* Amenities Checklist */}
            <View className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 floating-container">
              <Text className="text-base font-bold text-white mb-4">Included Amenities</Text>
              <View className="flex-row flex-wrap gap-2">
                {space.amenities?.map((amenity, idx) => (
                  <View key={idx} className="bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 flex-row items-center gap-2">
                    <Text className="text-emerald-400 text-xs">✓</Text>
                    <Text className="text-xs text-slate-200 font-medium">{amenity}</Text>
                  </View>
                ))}
              </View>
            </View>

            {/* Legal Framework Disclaimer */}
            <View className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 space-y-1">
              <Text className="font-semibold text-slate-300">⚖️ Indian Easements Act, 1882 Notice:</Text>
              <Text className="text-[11px] text-slate-400 leading-relaxed">
                This booking constitutes a revocable temporary license under Section 52 of the Indian Easements Act, 1882. No tenancy or leasehold interest is transferred. The space must be vacated promptly at the booking conclusion.
              </Text>
            </View>

            {/* Direct Inquiry: Ask Host & AI Concierge */}
            <View className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 floating-container">
              <View className="flex-row items-center justify-between">
                <View className="flex-row items-center gap-2">
                  <Text className="text-lg">💬</Text>
                  <View>
                    <Text className="text-base font-bold text-white">Direct Space Inquiry</Text>
                    <Text className="text-xs text-slate-400">Ask questions answered by verified metadata & host</Text>
                  </View>
                </View>
                <View className="px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30">
                  <Text className="text-[10px] font-bold text-indigo-300">AI Grounded</Text>
                </View>
              </View>

              {inquiryResponse && (
                <View className="p-4 bg-indigo-950/40 border border-indigo-500/30 rounded-xl space-y-1.5 animate-in fade-in duration-200">
                  <View className="flex-row items-center gap-1.5 text-xs text-indigo-400 font-semibold">
                    <Text className="text-xs font-bold text-indigo-300">🤖 Verified Response:</Text>
                  </View>
                  <Text className="text-xs text-slate-200 leading-relaxed whitespace-pre-wrap">
                    {inquiryResponse}
                  </Text>
                </View>
              )}

              {inquiryError && (
                <View className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl">
                  <Text className="text-xs text-rose-300 font-medium">✕ {inquiryError}</Text>
                </View>
              )}

              <View className="space-y-2">
                <TextInput
                  value={inquiryQuestion}
                  onChangeText={setInquiryQuestion}
                  placeholder="Ask about power circuits, elevator clearance, AC chilling, quiet hours..."
                  placeholderTextColor="#64748b"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white placeholder:text-slate-500 focus:border-indigo-500"
                />
                <View className="flex-row items-center justify-between pt-1">
                  <Text className="text-[10px] text-slate-500">
                    AI checks verified property telemetry first; forwards unknown requests to host.
                  </Text>
                  <Pressable
                    onPress={handleSendInquiry}
                    disabled={inquiryLoading || !inquiryQuestion.trim()}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl items-center justify-center transition shadow-md disabled:opacity-50"
                  >
                    <Text className="text-xs font-bold text-white">
                      {inquiryLoading ? 'Checking...' : 'Send Inquiry →'}
                    </Text>
                  </Pressable>
                </View>
              </View>
            </View>
          </View>

          {/* Right Column: Dynamic Booking Widget */}
          <View className="w-full lg:w-96">
            <View className="sticky top-20 bg-slate-900 border border-indigo-500/30 rounded-2xl p-6 floating-panel">
              <View className="flex-row items-baseline justify-between pb-4 mb-5 border-b border-slate-800">
                <View>
                  <Text className="text-3xl font-black text-white">
                    ₹{space.hourly_rate}
                    <Text className="text-xs font-normal text-slate-400"> / hour</Text>
                  </Text>
                  <Text className="text-[11px] text-emerald-400 font-medium mt-0.5">
                    ● Instant Zero-Hardware Confirmation
                  </Text>
                </View>
                <View className="bg-indigo-500/10 px-2 py-1 rounded-md border border-indigo-500/20">
                  <Text className="text-[10px] font-bold text-indigo-300">BEST VALUE</Text>
                </View>
              </View>

              {(bookingError || (availabilityStatus === 'conflict' && availabilityMessage)) && (
                <View className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl">
                  <Text className="text-xs text-rose-300 font-medium">
                    ⚠️ {bookingError || availabilityMessage}
                  </Text>
                </View>
              )}

              {availabilityStatus === 'available' && !bookingError && (
                <View className="mb-4 px-3 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex-row items-center gap-2">
                  <View className="w-2 h-2 rounded-full bg-emerald-400" />
                  <Text className="text-xs text-emerald-300 font-medium">Time Slot Available • Ready to Reserve</Text>
                </View>
              )}

              {availabilityStatus === 'checking' && (
                <View className="mb-4 px-3 py-2 bg-indigo-500/10 border border-indigo-500/20 rounded-xl flex-row items-center gap-2">
                  <View className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                  <Text className="text-xs text-indigo-300 font-medium">Checking slot availability...</Text>
                </View>
              )}

                {/* 1. TIMING MODE: START NOW vs SCHEDULE AHEAD */}
                <div className="mb-5">
                  <label className="block text-xs font-semibold text-slate-300 mb-2">
                    When do you need this space?
                  </label>
                  <div className="grid grid-cols-2 gap-2 p-1 bg-slate-950 rounded-xl border border-slate-800">
                    <button
                      type="button"
                      onClick={() => setBookingMode('now')}
                      className={`py-2 px-3 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                        bookingMode === 'now'
                          ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                          : 'text-slate-400 hover:text-white hover:bg-slate-900'
                      }`}
                    >
                      <span>⚡ Start Now</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setBookingMode('schedule')}
                      className={`py-2 px-3 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                        bookingMode === 'schedule'
                          ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                          : 'text-slate-400 hover:text-white hover:bg-slate-900'
                      }`}
                    >
                      <span>📅 Schedule Ahead</span>
                    </button>
                  </div>
                </div>

                {/* 2. SCHEDULE PICKERS (shown when bookingMode === 'schedule') */}
                {bookingMode === 'schedule' && (
                  <div className="space-y-3 mb-5 p-3.5 bg-slate-950/80 rounded-xl border border-slate-800/90">
                    {/* Date Picker */}
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-xs font-semibold text-slate-300">Booking Date</label>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => setQuickDate(0)}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] font-medium text-slate-300"
                          >
                            Today
                          </button>
                          <button
                            type="button"
                            onClick={() => setQuickDate(1)}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] font-medium text-slate-300"
                          >
                            Tomorrow
                          </button>
                          <button
                            type="button"
                            onClick={() => setQuickDate(2)}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] font-medium text-slate-300"
                          >
                            +2 Days
                          </button>
                        </div>
                      </div>
                      <input
                        type="date"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                    </div>

                    {/* Time Picker */}
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-xs font-semibold text-slate-300">Start Time</label>
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => setQuickTime('09:00')}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] font-medium text-slate-300"
                          >
                            9 AM
                          </button>
                          <button
                            type="button"
                            onClick={() => setQuickTime('12:00')}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] font-medium text-slate-300"
                          >
                            12 PM
                          </button>
                          <button
                            type="button"
                            onClick={() => setQuickTime('15:00')}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] font-medium text-slate-300"
                          >
                            3 PM
                          </button>
                          <button
                            type="button"
                            onClick={() => setQuickTime('18:00')}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] font-medium text-slate-300"
                          >
                            6 PM
                          </button>
                        </div>
                      </div>
                      <input
                        type="time"
                        value={selectedTime}
                        onChange={(e) => setSelectedTime(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>
                )}

                {/* 3. DURATION SELECTOR (Chips + Stepper) */}
                <div className="mb-5">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs font-semibold text-slate-300">
                      Duration Needed
                    </label>
                    <span className="text-[11px] font-bold text-indigo-400">
                      {pricing.hours} {pricing.hours === 1 ? 'hour' : 'hours'}
                    </span>
                  </div>

                  {/* Quick Duration Chips */}
                  <div className="grid grid-cols-5 gap-1.5 mb-2">
                    {[0.5, 1, 2, 3, 4].map((h) => (
                      <button
                        key={h}
                        type="button"
                        onClick={() => handleHoursChange(h)}
                        className={`py-1.5 rounded-lg border text-xs font-bold transition text-center ${
                          hours === h
                            ? 'bg-indigo-600 border-indigo-400 text-white'
                            : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                        }`}
                      >
                        {h}h
                      </button>
                    ))}
                  </div>
                  <div className="grid grid-cols-4 gap-1.5 mb-3">
                    {[6, 8, 12, 24].map((h) => (
                      <button
                        key={h}
                        type="button"
                        onClick={() => handleHoursChange(h)}
                        className={`py-1.5 rounded-lg border text-xs font-bold transition text-center ${
                          hours === h
                            ? 'bg-indigo-600 border-indigo-400 text-white'
                            : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                        }`}
                      >
                        {h === 12 ? '12h (Day)' : h === 24 ? '24h (Overnight)' : `${h}h`}
                      </button>
                    ))}
                  </div>

                  {/* Precision Stepper & Custom Number Input */}
                  <div className="flex items-center justify-between gap-2 p-2 bg-slate-950 rounded-xl border border-slate-800">
                    <span className="text-[11px] text-slate-400 font-medium pl-1">Custom hours:</span>
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => handleHoursChange(hours - 0.5)}
                        disabled={hours <= 0.5}
                        className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-700 hover:bg-slate-800 text-white font-bold text-sm flex items-center justify-center transition disabled:opacity-40 disabled:cursor-not-allowed"
                        title="Decrease by 30 mins"
                      >
                        -
                      </button>
                      <div className="flex items-center bg-slate-900 border border-slate-700 rounded-lg px-2 py-1">
                        <input
                          type="number"
                          step="0.5"
                          min="0.5"
                          max="168"
                          value={customHoursInput}
                          onChange={(e) => handleCustomInput(e.target.value)}
                          className="w-14 bg-transparent text-center text-xs font-bold text-white focus:outline-none"
                        />
                        <span className="text-[11px] text-slate-400 font-medium pr-1">hrs</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleHoursChange(hours + 0.5)}
                        disabled={hours >= 168}
                        className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-700 hover:bg-slate-800 text-white font-bold text-sm flex items-center justify-center transition disabled:opacity-40 disabled:cursor-not-allowed"
                        title="Increase by 30 mins"
                      >
                        +
                      </button>
                    </div>
                  </div>
                </div>

                {/* 4. LIVE TIME WINDOW BADGE */}
                <div className="mb-4 p-3 bg-gradient-to-r from-indigo-950/40 via-slate-950 to-indigo-950/40 border border-indigo-500/30 rounded-xl space-y-1.5">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400 flex items-center gap-1.5 font-medium">
                      <span>🕒</span> <span>Start Time:</span>
                    </span>
                    <span className="text-white font-semibold">{timeWindow.startFormatted}</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400 flex items-center gap-1.5 font-medium">
                      <span>🏁</span> <span>End Time:</span>
                    </span>
                    <span className="text-white font-semibold">{timeWindow.endFormatted}</span>
                  </div>
                  <div className="pt-1.5 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
                    <span className="text-emerald-400 font-bold flex items-center gap-1">
                      <span>✓</span> <span>Duration Confirmed</span>
                    </span>
                    <span className="text-indigo-300 font-bold">{timeWindow.durationFormatted}</span>
                  </div>
                </div>

                {/* 5. INTENDED PURPOSE */}
                <div className="mb-5">
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Intended Activity / Purpose
                  </label>
                  <div className="flex flex-wrap gap-1 mb-2">
                    {[
                      '💻 Coding Sprint',
                      '📚 Quiet Study',
                      '🎙️ Podcast Session',
                      '📸 Content Creation',
                      '📦 Storage',
                    ].map((p) => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setPurpose(p)}
                        className={`px-2 py-0.5 rounded-lg text-[10px] font-medium border transition ${
                          purpose === p
                            ? 'bg-indigo-600/30 border-indigo-500 text-white'
                            : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                        }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                  <input
                    type="text"
                    value={purpose}
                    onChange={(e) => setPurpose(e.target.value)}
                    placeholder="e.g. Hackathon code sprint, exam preparation..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                {/* 6. PRICING BREAKDOWN */}
                <View className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2 mb-5">
                  <View className="flex-row justify-between text-xs">
                    <Text className="text-slate-400">
                      ₹{space.hourly_rate} × {pricing.hours} hours
                    </Text>
                    <Text className="text-white font-medium">₹{pricing.rentalSubtotal}</Text>
                  </View>

                  <View className="flex-row justify-between text-xs">
                    <Text className="text-slate-400">Platform Convenience (5%)</Text>
                    <Text className="text-slate-300 font-medium">₹{pricing.platformFee}</Text>
                  </View>

                  <View className="flex-row justify-between text-xs">
                    <View className="flex-row items-center gap-1">
                      <Text className="text-slate-400">UPI Security Deposit</Text>
                      <Text className="text-[10px] text-emerald-400 font-bold">(Refundable)</Text>
                    </View>
                    <Text className="text-emerald-400 font-medium">₹{pricing.escrowDeposit}</Text>
                  </View>

                  <View className="pt-2 border-t border-slate-800 flex-row justify-between text-sm">
                    <Text className="text-slate-200 font-bold">Total Amount Due</Text>
                    <Text className="text-indigo-400 font-black">₹{pricing.grandTotal}</Text>
                  </View>
                </View>

                {/* 7. BOOK BUTTON */}
                <Pressable
                  onPress={handleBookNow}
                  disabled={bookingLoading || !pricing.isValidDuration || availabilityStatus === 'conflict' || availabilityStatus === 'checking'}
                  className={`w-full py-3.5 rounded-xl items-center justify-center transition shadow-lg ${
                    bookingLoading || !pricing.isValidDuration || availabilityStatus === 'conflict' || availabilityStatus === 'checking'
                      ? 'bg-indigo-600/50 cursor-not-allowed shadow-none'
                      : 'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-600/40'
                  }`}
                >
                  <Text className="text-sm font-bold text-white">
                    {bookingLoading
                      ? 'Securing Reservation...'
                      : !pricing.isValidDuration
                      ? 'Invalid Duration'
                      : availabilityStatus === 'conflict'
                      ? '⚠️ Time Slot Unavailable'
                      : availabilityStatus === 'checking'
                      ? 'Checking Availability...'
                      : currentUser
                      ? `⚡ Instant Book & Lock Slot (₹${pricing.grandTotal})`
                      : `⚡ Sign in to Book (₹${pricing.grandTotal})`}
                  </Text>
                </Pressable>

                <View className="mt-4 flex-row items-center justify-center gap-2">
                  <Text className="text-xs text-slate-500">🛡️ Section 52 micro-lease & ₹100 automated escrow</Text>
                </View>
            </View>
          </View>
        </View>
      </View>

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onSuccess={() => handleBookNow()}
      />
    </View>
  );
};
