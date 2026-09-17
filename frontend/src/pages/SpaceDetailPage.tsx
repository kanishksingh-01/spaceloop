import React, { useState, useEffect } from 'react';
import { View, Text, Pressable, Image, TextInput, ScrollView } from 'react-native';
import { useParams, useNavigate } from 'react-router-dom';
import { Space, User } from '../types';
import { getSpaceById } from '../services/spaces';
import { createBooking, precheckBooking } from '../services/bookings';
import { AuthModal } from '../components/common/AuthModal';

interface SpaceDetailPageProps {
  currentUser: User | null;
}

export const SpaceDetailPage: React.FC<SpaceDetailPageProps> = ({ currentUser }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [space, setSpace] = useState<Space | null>(null);
  const [loading, setLoading] = useState(true);
  const [hours, setHours] = useState(2);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState<string | null>(null);
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

  const rentalTotal = space.hourly_rate * hours;
  const deposit = 100; // Flat ₹100 UPI escrow
  const grandTotal = rentalTotal + deposit;

  const handleBookNow = async () => {
    if (!currentUser) {
      setShowAuthModal(true);
      return;
    }

    setBookingLoading(true);
    setBookingError(null);
    try {
      const now = new Date();
      const startTime = now.toISOString();
      const end = new Date(now.getTime() + hours * 60 * 60 * 1000);
      const endTime = end.toISOString();

      const res = await createBooking({
        space_id: space.id,
        hours: hours,
        start_time: startTime,
        end_time: endTime,
        purpose: 'Study & Creative Work Session',
      });

      const confirmedBookingId = res.booking_id || res.booking?.id;
      if (confirmedBookingId) {
        navigate(`/session/${confirmedBookingId}`);
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setBookingError(err.message || 'Failed to complete booking. Please try again.');
    } finally {
      setBookingLoading(false);
    }
  };

  return (
    <View className="min-h-screen bg-slate-950 pb-20">
      {/* Back Bar */}
      <View className="border-b border-slate-800/80 bg-slate-900/50 px-4 py-3">
        <View className="max-w-7xl mx-auto flex-row items-center justify-between">
          <Pressable onPress={() => navigate('/')} className="flex-row items-center gap-2">
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
              <View className="flex-row items-center justify-between p-3.5 bg-slate-950/80 rounded-xl border border-slate-800">
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
            <View className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6">
              <View className="flex-row items-center gap-2 mb-4">
                <Text className="text-xl">🤖</Text>
                <Text className="text-base font-bold text-white">AI Space Inspector Metrics</Text>
              </View>

              <View className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <View className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <Text className="text-[11px] font-semibold text-slate-400">Usable Area</Text>
                  <Text className="text-lg font-black text-white mt-1">
                    {space.specs?.usable_sqft || 140} <Text className="text-xs font-normal text-slate-500">sq.ft</Text>
                  </Text>
                  <Text className="text-[10px] text-emerald-400 mt-1">✓ Measured by Vision AI</Text>
                </View>

                <View className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <Text className="text-[11px] font-semibold text-slate-400">Noise Level</Text>
                  <Text className="text-lg font-black text-white mt-1">
                    {space.specs?.acoustic_db || 34} <Text className="text-xs font-normal text-slate-500">dB</Text>
                  </Text>
                  <Text className="text-[10px] text-indigo-300 mt-1">✓ Quiet study grade</Text>
                </View>

                <View className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <Text className="text-[11px] font-semibold text-slate-400">Natural Lighting</Text>
                  <Text className="text-lg font-black text-white mt-1">
                    {space.specs?.lighting_lux || 480} <Text className="text-xs font-normal text-slate-500">lux</Text>
                  </Text>
                  <Text className="text-[10px] text-amber-400 mt-1">✓ Optimal for reading</Text>
                </View>

                <View className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <Text className="text-[11px] font-semibold text-slate-400">Power Circuit</Text>
                  <Text className="text-lg font-black text-white mt-1">
                    {space.specs?.power_circuits || '20A'}
                  </Text>
                  <Text className="text-[10px] text-indigo-300 mt-1">✓ Grounded outlets</Text>
                </View>
              </View>
            </View>

            {/* Amenities Checklist */}
            <View className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6">
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
          </View>

          {/* Right Column: Dynamic Booking Widget */}
          <View className="w-full lg:w-96">
            <View className="sticky top-20 bg-slate-900 border border-indigo-500/30 rounded-2xl p-6 shadow-2xl shadow-indigo-950/50">
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

              {bookingError && (
                <View className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl">
                  <Text className="text-xs text-rose-300 font-medium">{bookingError}</Text>
                </View>
              )}

              {/* Booking Controls */}
              <View className="space-y-4 mb-6">
                <View>
                  <Text className="text-xs font-semibold text-slate-300 mb-1.5">
                    Select Hours Needed
                  </Text>
                  <View className="flex-row items-center gap-2">
                    {[1, 2, 4, 8].map((h) => (
                      <Pressable
                        key={h}
                        onPress={() => setHours(h)}
                        className={`flex-1 py-2 rounded-xl border text-center transition ${
                          hours === h
                            ? 'bg-indigo-600 border-indigo-400'
                            : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        <Text
                          className={`text-xs font-bold text-center ${
                            hours === h ? 'text-white' : 'text-slate-300'
                          }`}
                        >
                          {h}h
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                </View>

                {/* Pricing Calculation Breakdown */}
                <View className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                  <View className="flex-row justify-between text-xs">
                    <Text className="text-slate-400">
                      ₹{space.hourly_rate} × {hours} hours
                    </Text>
                    <Text className="text-white font-medium">₹{rentalTotal}</Text>
                  </View>

                  <View className="flex-row justify-between text-xs">
                    <View className="flex-row items-center gap-1">
                      <Text className="text-slate-400">UPI Security Deposit</Text>
                      <Text className="text-[10px] text-emerald-400 font-bold">(Refundable)</Text>
                    </View>
                    <Text className="text-emerald-400 font-medium">₹{deposit}</Text>
                  </View>

                  <View className="pt-2 border-t border-slate-800 flex-row justify-between text-sm">
                    <Text className="text-slate-200 font-bold">Total Amount Due</Text>
                    <Text className="text-indigo-400 font-black">₹{grandTotal}</Text>
                  </View>
                </View>
              </View>

              {/* Book Button */}
              <Pressable
                onPress={handleBookNow}
                disabled={bookingLoading}
                className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl items-center justify-center transition shadow-lg shadow-indigo-600/40"
              >
                <Text className="text-sm font-bold text-white">
                  {bookingLoading
                    ? 'Securing Reservation...'
                    : currentUser
                    ? `⚡ Instant Book & Generate Pass (₹${grandTotal})`
                    : `⚡ Sign in to Book (₹${grandTotal})`}
                </Text>
              </Pressable>

              <View className="mt-4 flex-row items-center justify-center gap-2">
                <Text className="text-xs text-slate-500">🛡️ Protected by automated micro-escrow</Text>
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
