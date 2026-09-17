import React, { useState, useEffect } from 'react';
import { View, Text, Pressable, Image, ScrollView } from 'react-native';
import { useNavigate } from 'react-router-dom';
import { User, Booking, Space } from '../types';
import { request } from '../services/api';
import { cancelBooking } from '../services/bookings';
import { toggleSpaceStatus } from '../services/spaces';

interface DashboardPageProps {
  currentUser: User | null;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ currentUser }) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'seeker' | 'host'>('seeker');
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [hostBookings, setHostBookings] = useState<Booking[]>([]);
  const [hostSpaces, setHostSpaces] = useState<Space[]>([]);
  const [loading, setLoading] = useState(true);
  const [seedingSpace, setSeedingSpace] = useState(false);
  const [cancelingId, setCancelingId] = useState<number | null>(null);
  const [metrics, setMetrics] = useState<{
    gross_revenue: number;
    platform_fee: number;
    net_earnings: number;
    total_hours: number;
    total_bookings: number;
    active_spaces_count: number;
    total_spaces_count: number;
    upcoming_count: number;
    completed_count: number;
    payout_vpa: string;
  } | null>(null);

  useEffect(() => {
    if (currentUser?.role === 'host') {
      setActiveTab('host');
    }
  }, [currentUser]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Load real seeker bookings, incoming host reservations, and host properties from backend
      const dashData = await request<{
        success: boolean;
        bookings?: Booking[];
        host_bookings?: Booking[];
        host_spaces?: Space[];
        host_metrics?: any;
      }>('/api/dashboard');

      if (dashData?.bookings) {
        setBookings(dashData.bookings);
      } else {
        setBookings([]);
      }

      if (dashData?.host_bookings) {
        setHostBookings(dashData.host_bookings);
      } else {
        setHostBookings([]);
      }

      if (dashData?.host_spaces && dashData.host_spaces.length > 0) {
        setHostSpaces(dashData.host_spaces);
      } else {
        const spacesData = await request<{ spaces?: Space[] } | Space[]>('/api/spaces');
        const allSpaces = Array.isArray(spacesData) ? spacesData : spacesData.spaces || [];
        setHostSpaces(allSpaces.filter(s => currentUser ? s.owner_id === currentUser.id : true));
      }

      if (dashData?.host_metrics) {
        setMetrics(dashData.host_metrics);
      }
    } catch (err) {
      console.warn('Dashboard API call failed or user unauthenticated:', err);
      try {
        const spacesData = await request<{ spaces?: Space[] } | Space[]>('/api/spaces');
        const allSpaces = Array.isArray(spacesData) ? spacesData : spacesData.spaces || [];
        setHostSpaces(allSpaces);
      } catch (e) {
        // ignore
      }
      setBookings([]);
      setHostBookings([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [currentUser]);

  const handleCancelBooking = async (bookingId: number) => {
    setCancelingId(bookingId);
    try {
      await cancelBooking(bookingId);
      setBookings(bookings.map((b) => (b.id === bookingId ? { ...b, status: 'cancelled' } : b)));
    } catch (err) {
      console.error('Cancellation failed:', err);
    } finally {
      setCancelingId(null);
    }
  };

  const handleToggleStatus = async (spaceId: number) => {
    try {
      const res = await toggleSpaceStatus(spaceId);
      setHostSpaces(
        hostSpaces.map((s) => (s.id === spaceId ? { ...s, is_active: res.is_active } : s))
      );
    } catch (err) {
      console.error('Failed to toggle status:', err);
    }
  };

  const handleSeedSampleSpace = async () => {
    setSeedingSpace(true);
    try {
      const res = await request<{ success: boolean; space: Space }>('/api/host/seed-sample-space', {
        method: 'POST',
      });
      if (res.success && res.space) {
        setHostSpaces(prev => [res.space, ...prev]);
      }
    } catch (err) {
      console.error('Failed to seed sample space:', err);
    } finally {
      setSeedingSpace(false);
    }
  };

  return (
    <View className="min-h-screen bg-slate-950 pb-20">
      {/* Header Profile Summary */}
      <View className="bg-slate-900 border-b border-slate-800 px-4 py-8">
        <View className="max-w-7xl mx-auto flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <View className="flex-row items-center gap-4">
            <Image
              source={{
                uri:
                  currentUser?.avatar_url ||
                  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80',
              }}
              className="w-16 h-16 rounded-2xl object-cover border-2 border-indigo-500/40"
            />
            <View>
              <View className="flex-row items-center gap-2">
                <Text className="text-xl font-bold text-white">
                  {currentUser?.name || 'Aarav Sharma'}
                </Text>
                <View className="px-2 py-0.5 rounded-md bg-indigo-500/20 border border-indigo-500/30">
                  <Text className="text-[10px] font-bold text-indigo-300 uppercase">
                    {currentUser?.role || 'Seeker'}
                  </Text>
                </View>
              </View>
              <Text className="text-xs text-slate-400 mt-0.5">
                {currentUser?.email || 'aarav@iitd.ac.in'}
              </Text>
              <Text className="text-[11px] text-emerald-400 font-medium mt-1">
                ✓ DigiLocker Verified • Trust Score 840 / 1000
              </Text>
            </View>
          </View>

          {/* Quick Metrics */}
          <View className="flex-row items-center gap-3">
            {activeTab === 'seeker' ? (
              <>
                <View className="p-3 bg-slate-950 rounded-xl border border-slate-800 items-center min-w-[90px]">
                  <Text className="text-[10px] text-slate-400 font-semibold">Active Passes</Text>
                  <Text className="text-base font-black text-emerald-400">
                    {bookings.filter(b => b.status === 'confirmed').length} Active
                  </Text>
                </View>
                <View className="p-3 bg-slate-950 rounded-xl border border-slate-800 items-center min-w-[90px]">
                  <Text className="text-[10px] text-slate-400 font-semibold">Micro-Escrow</Text>
                  <Text className="text-base font-black text-indigo-400">
                    ₹{bookings.filter(b => b.status === 'confirmed').reduce((acc, b) => acc + (b.deposit_held || 100), 0)} Held
                  </Text>
                </View>
              </>
            ) : (
              <>
                <View className="p-3 bg-slate-950 rounded-xl border border-slate-800 items-center min-w-[90px]">
                  <Text className="text-[10px] text-slate-400 font-semibold">Net Earnings</Text>
                  <Text className="text-base font-black text-emerald-400">
                    ₹{metrics?.net_earnings ?? 0}
                  </Text>
                </View>
                <View className="p-3 bg-slate-950 rounded-xl border border-slate-800 items-center min-w-[90px]">
                  <Text className="text-[10px] text-slate-400 font-semibold">Active Spaces</Text>
                  <Text className="text-base font-black text-indigo-400">
                    {hostSpaces.filter(s => s.is_active).length} Listed
                  </Text>
                </View>
              </>
            )}
          </View>
        </View>
      </View>

      {/* Tabs */}
      <View className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <View className="flex-row items-center gap-3 border-b border-slate-800 pb-4 mb-6">
          <Pressable
            onPress={() => setActiveTab('seeker')}
            className={`px-4 py-2 rounded-xl border text-xs font-bold transition ${
              activeTab === 'seeker'
                ? 'bg-indigo-600 border-indigo-400 text-white'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            <Text
              className={`text-xs font-bold ${
                activeTab === 'seeker' ? 'text-white' : 'text-slate-400'
              }`}
            >
              🎟️ My Bookings (Seeker)
            </Text>
          </Pressable>

          <Pressable
            onPress={() => navigate('/host/dashboard')}
            className="px-4 py-2 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20 transition flex-row items-center gap-1.5 ml-auto"
          >
            <Text className="text-xs font-bold text-amber-300">
              🏡 Switch to Host Portal & Dashboard →
            </Text>
          </Pressable>
        </View>

        {/* Tab 1: Seeker Bookings */}
        {activeTab === 'seeker' && (
          <View className="space-y-4">
            <View className="flex-row items-center justify-between mb-2">
              <Text className="text-base font-bold text-white">Your Reserved Spaces</Text>
              <Pressable
                onPress={() => navigate('/')}
                className="text-xs text-indigo-400 hover:underline"
              >
                <Text className="text-xs font-medium text-indigo-400">+ Find New Space</Text>
              </Pressable>
            </View>

            {bookings.length === 0 ? (
              <View className="p-8 bg-slate-900 rounded-2xl border border-slate-800 text-center items-center">
                <Text className="text-3xl mb-2">🎟️</Text>
                <Text className="text-sm font-bold text-white mb-1">No active bookings</Text>
                <Text className="text-xs text-slate-400 mb-4">
                  You haven't reserved any temporary spaces yet.
                </Text>
                <Pressable
                  onPress={() => navigate('/')}
                  className="px-4 py-2 bg-indigo-600 rounded-xl"
                >
                  <Text className="text-xs font-semibold text-white">Explore Spaces</Text>
                </Pressable>
              </View>
            ) : (
              bookings.map((b) => (
                <View
                  key={b.id}
                  className="p-5 bg-slate-900 border border-slate-800 rounded-2xl flex-col md:flex-row items-start md:items-center justify-between gap-4"
                >
                  <View className="flex-row items-center gap-4 flex-1">
                    <Image
                      source={{
                        uri:
                          b.space_photo ||
                          'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=400&q=80',
                      }}
                      className="w-20 h-20 rounded-xl object-cover"
                    />
                    <View>
                      <View className="flex-row items-center gap-2 mb-1">
                        <Text className="text-base font-bold text-white">{b.space_title}</Text>
                        <View className="px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/40">
                          <Text className="text-[10px] font-bold text-emerald-300 uppercase">
                            {b.status}
                          </Text>
                        </View>
                      </View>
                      <Text className="text-xs text-slate-400 mb-1">{b.space_address}</Text>
                      <Text className="text-xs font-semibold text-indigo-300">
                        Total: ₹{b.total_price} (₹{b.deposit_held} Deposit Escrow Held)
                      </Text>
                    </View>
                  </View>

                  <View className="flex-row items-center gap-2 self-stretch md:self-auto justify-end">
                    <Pressable
                      onPress={() => navigate(`/session/${b.id}`)}
                      className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl transition"
                    >
                      <Text className="text-xs font-bold text-white">📱 Digital Door Pass →</Text>
                    </Pressable>

                    {b.status !== 'cancelled' && b.status !== 'completed' && (
                      <Pressable
                        onPress={() => handleCancelBooking(b.id)}
                        disabled={cancelingId === b.id}
                        className="px-3 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl transition"
                      >
                        <Text className="text-xs font-medium text-rose-300">
                          {cancelingId === b.id ? 'Canceling...' : 'Cancel'}
                        </Text>
                      </Pressable>
                    )}
                  </View>
                </View>
              ))
            )}
          </View>
        )}

        {/* Tab 2: Host Workspace & Listings */}
        {activeTab === 'host' && (
          <View className="space-y-6">
            {/* Host IoT Mesh & Connectivity Telemetry Banner */}
            <View className="p-4 bg-emerald-950/40 border border-emerald-500/30 rounded-2xl flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <View className="flex-row items-center gap-3">
                <View className="w-3 h-3 rounded-full bg-emerald-400" />
                <View>
                  <Text className="text-xs font-bold text-emerald-300">
                    Host Access & IoT Connectivity Mesh: ONLINE (14ms Latency)
                  </Text>
                  <Text className="text-[11px] text-slate-400">
                    ESP32 Bluetooth Mesh Synced • Door Relay Online • Geofence armed (25m) • Micro-Escrow UPI Active
                  </Text>
                </View>
              </View>
              <View className="flex-row items-center gap-2">
                <View className="px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/30">
                  <Text className="text-[10px] font-bold text-emerald-300 uppercase">Hardware 99.9%</Text>
                </View>
              </View>
            </View>

            {/* Section A: Incoming Guest Reservations */}
            <View>
              <View className="flex-row items-center justify-between mb-3">
                <View>
                  <Text className="text-base font-bold text-white">Incoming Guest Reservations</Text>
                  <Text className="text-xs text-slate-400">Bookings placed on your spaces with held escrow deposits</Text>
                </View>
                <View className="px-2.5 py-1 rounded-lg bg-indigo-500/20 border border-indigo-500/30">
                  <Text className="text-xs font-bold text-indigo-300">
                    {hostBookings.length} {hostBookings.length === 1 ? 'Booking' : 'Bookings'}
                  </Text>
                </View>
              </View>

              {hostBookings.length === 0 ? (
                <View className="p-6 bg-slate-900 border border-slate-800 rounded-2xl items-center text-center">
                  <Text className="text-2xl mb-1">📅</Text>
                  <Text className="text-sm font-bold text-white mb-0.5">No Guest Reservations Yet</Text>
                  <Text className="text-xs text-slate-400 max-w-md">
                    When seekers book your active spaces, their reservation details, access codes, and automated payout escrow will appear here.
                  </Text>
                </View>
              ) : (
                <View className="space-y-3">
                  {hostBookings.map((hb) => (
                    <View
                      key={hb.id}
                      className="p-4 bg-slate-900 border border-slate-800 rounded-2xl flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
                    >
                      <View className="flex-row items-center gap-3">
                        <View className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 items-center justify-center">
                          <Text className="text-base">🎟️</Text>
                        </View>
                        <View>
                          <View className="flex-row items-center gap-2">
                            <Text className="text-sm font-bold text-white">
                              {hb.seeker_name || 'Verified Seeker'}
                            </Text>
                            <View className="px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/30">
                              <Text className="text-[10px] font-bold text-emerald-300 uppercase">
                                {hb.status}
                              </Text>
                            </View>
                          </View>
                          <Text className="text-xs text-slate-400">
                            {hb.space_title || 'Space Listing'} • {hb.hours_booked || 1} hrs
                          </Text>
                        </View>
                      </View>

                      <View className="flex-row items-center gap-4 self-stretch sm:self-auto justify-between sm:justify-end">
                        <View className="text-right">
                          <Text className="text-sm font-bold text-emerald-400">₹{hb.total_price}</Text>
                          <Text className="text-[10px] text-slate-400">
                            Deposit: ₹{hb.deposit_held || 100} Held
                          </Text>
                        </View>
                        <Pressable
                          onPress={() => navigate(`/session/${hb.id}`)}
                          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl transition"
                        >
                          <Text className="text-xs font-semibold text-indigo-300">View Pass →</Text>
                        </Pressable>
                      </View>
                    </View>
                  ))}
                </View>
              )}
            </View>

            {/* Section B: Listed Spaces Portfolio */}
            <View>
              <View className="flex-row items-center justify-between mb-3">
                <View>
                  <Text className="text-base font-bold text-white">Your Listed Properties</Text>
                  <Text className="text-xs text-slate-400">Manage active spaces, pricing, and availability</Text>
                </View>
                <View className="flex-row items-center gap-2">
                  <Pressable
                    onPress={handleSeedSampleSpace}
                    disabled={seedingSpace}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl transition"
                  >
                    <Text className="text-xs font-bold text-indigo-300">
                      {seedingSpace ? 'Provisioning...' : '⚡ Seed Turnkey Pod'}
                    </Text>
                  </Pressable>
                  <Pressable
                    onPress={() => navigate('/list-space')}
                    className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl shadow-md transition"
                  >
                    <Text className="text-xs font-bold text-white">+ List New Space</Text>
                  </Pressable>
                </View>
              </View>

              {hostSpaces.length === 0 ? (
                <View className="p-8 bg-slate-900 border border-slate-800 rounded-2xl items-center text-center">
                  <Text className="text-3xl mb-2">🏠</Text>
                  <Text className="text-sm font-bold text-white mb-1">No Listed Spaces Found</Text>
                  <Text className="text-xs text-slate-400 mb-4 max-w-sm">
                    Monetize your unused square footage. List a room, study desk, or studio in under 2 minutes.
                  </Text>
                  <View className="flex-row items-center gap-3">
                    <Pressable
                      onPress={handleSeedSampleSpace}
                      disabled={seedingSpace}
                      className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl"
                    >
                      <Text className="text-xs font-bold text-indigo-300">
                        {seedingSpace ? 'Generating Pod...' : '⚡ Seed Turnkey Pod'}
                      </Text>
                    </Pressable>
                    <Pressable
                      onPress={() => navigate('/list-space')}
                      className="px-4 py-2 bg-indigo-600 rounded-xl"
                    >
                      <Text className="text-xs font-bold text-white">List Your First Space</Text>
                    </Pressable>
                  </View>
                </View>
              ) : (
                <View className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {hostSpaces.map((space) => (
                    <View
                      key={space.id}
                      className="p-4 bg-slate-900 border border-slate-800 rounded-2xl flex-row items-center justify-between gap-4"
                    >
                      <View className="flex-row items-center gap-3 flex-1">
                        <Image
                          source={{
                            uri:
                              space.photos && space.photos.length > 0
                                ? space.photos[0]
                                : 'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=400&q=80',
                          }}
                          className="w-16 h-16 rounded-xl object-cover"
                        />
                        <View className="flex-1">
                          <Text className="text-sm font-bold text-white" numberOfLines={1}>
                            {space.title}
                          </Text>
                          <Text className="text-xs text-slate-400 mb-1">
                            ₹{space.hourly_rate || space.price_hourly}/hr • {space.location || space.city}
                          </Text>
                          <View className="flex-row items-center gap-1.5">
                            <View
                              className={`w-2 h-2 rounded-full ${
                                space.is_active ? 'bg-emerald-400' : 'bg-slate-600'
                              }`}
                            />
                            <Text className="text-[10px] text-slate-400">
                              {space.is_active ? 'Active & Accepting Bookings' : 'Paused / Offline'}
                            </Text>
                          </View>
                        </View>
                      </View>

                      <Pressable
                        onPress={() => handleToggleStatus(space.id)}
                        className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl"
                      >
                        <Text className="text-xs font-medium text-slate-300">
                          {space.is_active ? 'Pause' : 'Activate'}
                        </Text>
                      </Pressable>
                    </View>
                  ))}
                </View>
              )}
            </View>
          </View>
        )}
      </View>
    </View>
  );
};
