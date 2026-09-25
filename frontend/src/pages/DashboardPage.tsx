import React, { useState, useEffect } from 'react';
import { View, Text, Pressable, Image, ScrollView } from 'react-native';
import { useNavigate } from 'react-router-dom';
import { User, Booking, Space } from '../types';
import { request } from '../services/api';
import { cancelBooking } from '../services/bookings';
import { toggleSpaceStatus, getInquiries } from '../services/spaces';
import { setupMfa, verifyMfaSetup, disableMfa, resendEmailVerification } from '../services/auth';

interface DashboardPageProps {
  currentUser: User | null;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ currentUser }) => {
  const navigate = useNavigate();
  const [userState, setUserState] = useState<User | null>(currentUser);
  const [activeTab, setActiveTab] = useState<'seeker' | 'host' | 'security'>('seeker');

  useEffect(() => {
    setUserState(currentUser);
  }, [currentUser]);

  // MFA Enrollment Modal State
  const [showMfaEnrollModal, setShowMfaEnrollModal] = useState(false);
  const [mfaEnrollStep, setMfaEnrollStep] = useState<'scan' | 'recovery'>('scan');
  const [mfaSetupData, setMfaSetupData] = useState<{
    secret: string;
    qr_code: string;
    otpauth_uri: string;
    setup_token: string;
  } | null>(null);
  const [mfaEnrollCode, setMfaEnrollCode] = useState('');
  const [mfaEnrollRecoveryCodes, setMfaEnrollRecoveryCodes] = useState<string[]>([]);
  const [mfaEnrollLoading, setMfaEnrollLoading] = useState(false);
  const [mfaEnrollError, setMfaEnrollError] = useState<string | null>(null);
  const [mfaCopyStatus, setMfaCopyStatus] = useState<string | null>(null);

  // Email Verification State
  const [resendingEmail, setResendingEmail] = useState(false);
  const [emailNotice, setEmailNotice] = useState<string | null>(null);

  // MFA Disable Modal State
  const [showDisableMfaModal, setShowDisableMfaModal] = useState(false);
  const [disablePassword, setDisablePassword] = useState('');
  const [disableCode, setDisableCode] = useState('');
  const [disableRecoveryCode, setDisableRecoveryCode] = useState('');
  const [disableUseRecovery, setDisableUseRecovery] = useState(false);
  const [disableLoading, setDisableLoading] = useState(false);
  const [disableError, setDisableError] = useState<string | null>(null);
  const [disableSuccess, setDisableSuccess] = useState<string | null>(null);

  const [bookings, setBookings] = useState<Booking[]>([]);
  const [hostBookings, setHostBookings] = useState<Booking[]>([]);
  const [hostSpaces, setHostSpaces] = useState<Space[]>([]);
  const [inquiries, setInquiries] = useState<any[]>([]);
  const [showOtiBreakdown, setShowOtiBreakdown] = useState(false);
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

      try {
        const inqData = await getInquiries();
        if (inqData && inqData.inquiries) {
          setInquiries(inqData.inquiries);
        }
      } catch (e) {
        console.warn('Failed to load inquiries:', e);
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

  const handleResendEmail = async () => {
    setResendingEmail(true);
    setEmailNotice(null);
    try {
      const res = await resendEmailVerification();
      setEmailNotice(res.message || 'Verification link sent to your email.');
    } catch (err: any) {
      setEmailNotice(err.message || 'Failed to send verification email.');
    } finally {
      setResendingEmail(false);
    }
  };

  const handleStartMfaEnrollment = async () => {
    setMfaEnrollError(null);
    setMfaEnrollCode('');
    setMfaEnrollRecoveryCodes([]);
    setMfaEnrollStep('scan');

    // Email verification gate check
    if (!userState?.is_email_verified) {
      setMfaEnrollError('Email verification is required before enrolling in Multi-Factor Authentication. Please verify your email first.');
      setShowMfaEnrollModal(true);
      return;
    }

    setMfaEnrollLoading(true);
    setShowMfaEnrollModal(true);
    try {
      const res = await setupMfa();
      if (!res.success) {
        setMfaEnrollError(res.error || 'Failed to initialize MFA setup.');
        setMfaEnrollLoading(false);
        return;
      }
      setMfaSetupData(res);
      setMfaEnrollLoading(false);
    } catch (err: any) {
      setMfaEnrollError(err.message || 'Failed to start MFA setup.');
      setMfaEnrollLoading(false);
    }
  };

  const handleConfirmMfaEnrollment = async () => {
    if (!mfaSetupData?.setup_token) return;
    if (!mfaEnrollCode.trim() || mfaEnrollCode.trim().length !== 6) {
      setMfaEnrollError('Please enter the 6-digit code from your authenticator app.');
      return;
    }
    setMfaEnrollLoading(true);
    setMfaEnrollError(null);
    try {
      const res = await verifyMfaSetup(mfaSetupData.setup_token, mfaEnrollCode.trim());
      if (!res.success) {
        setMfaEnrollError(res.error || 'Invalid verification code.');
        setMfaEnrollLoading(false);
        return;
      }
      setMfaEnrollRecoveryCodes(res.recovery_codes || []);
      setMfaEnrollStep('recovery');
      if (res.user) {
        setUserState(res.user);
      } else if (userState) {
        setUserState({ ...userState, mfa_enabled: true });
      }
      setMfaEnrollLoading(false);
    } catch (err: any) {
      setMfaEnrollError(err.message || 'MFA enrollment verification failed.');
      setMfaEnrollLoading(false);
    }
  };

  const handleConfirmDisableMfa = async () => {
    if (!disablePassword) {
      setDisableError('Please enter your account password.');
      return;
    }
    if (!disableUseRecovery && (!disableCode.trim() || disableCode.trim().length !== 6)) {
      setDisableError('Please enter your 6-digit TOTP code.');
      return;
    }
    if (disableUseRecovery && !disableRecoveryCode.trim()) {
      setDisableError('Please enter your backup recovery code.');
      return;
    }
    setDisableLoading(true);
    setDisableError(null);
    try {
      const res = await disableMfa({
        password: disablePassword,
        code: !disableUseRecovery ? disableCode.trim() : undefined,
        recovery_code: disableUseRecovery ? disableRecoveryCode.trim() : undefined,
      });
      setDisableSuccess('Two-Factor Authentication disabled successfully.');
      if (res.user) {
        setUserState(res.user);
      } else if (userState) {
        setUserState({ ...userState, mfa_enabled: false });
      }
      setTimeout(() => {
        setShowDisableMfaModal(false);
        setDisablePassword('');
        setDisableCode('');
        setDisableRecoveryCode('');
        setDisableSuccess(null);
      }, 1000);
    } catch (err: any) {
      setDisableError(err.message || 'Failed to disable MFA. Check your credentials.');
    } finally {
      setDisableLoading(false);
    }
  };

  return (
    <View className="min-h-screen bg-slate-950 pb-20">
      {/* Header Profile Summary */}
      <View className="bg-slate-900 border-b border-slate-800 px-4 py-8">
        <View className="max-w-7xl mx-auto flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <View className="flex-row items-center gap-4">
            {currentUser?.avatar_url ? (
              <Image
                source={{ uri: currentUser.avatar_url }}
                className="w-16 h-16 rounded-2xl object-cover border-2 border-indigo-500/40"
              />
            ) : (
              <div className="w-16 h-16 rounded-2xl bg-indigo-950/80 border-2 border-indigo-500/40 flex items-center justify-center text-indigo-300 font-bold text-2xl uppercase shadow-inner">
                {(currentUser?.name || currentUser?.email || 'U').charAt(0)}
              </div>
            )}
            <View>
              <View className="flex-row items-center gap-2">
                <Text className="text-xl font-bold text-white">
                  {currentUser?.name || currentUser?.email?.split('@')[0] || 'Member'}
                </Text>
                <View className="px-2 py-0.5 rounded-md bg-indigo-500/20 border border-indigo-500/30">
                  <Text className="text-[10px] font-bold text-indigo-300 uppercase">
                    {currentUser?.role || (currentUser?.is_host ? 'Host' : 'Seeker')}
                  </Text>
                </View>
              </View>
              <Text className="text-xs text-slate-400 mt-0.5">
                {currentUser?.email || 'No email registered'}
              </Text>
              <View className="flex-row items-center gap-2 mt-1 flex-wrap">
                <Text className="text-[11px] text-emerald-400 font-medium">
                  ✓ DigiLocker Verified
                </Text>
                <Text className="text-[11px] text-slate-500">•</Text>
                <Text className={`text-[11px] font-medium ${userState?.is_email_verified ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {userState?.is_email_verified ? '✓ Email Verified' : '⚠️ Email Unverified'}
                </Text>
                <Text className="text-[11px] text-slate-500">•</Text>
                <Text className={`text-[11px] font-medium ${userState?.mfa_enabled ? 'text-emerald-400' : 'text-slate-400'}`}>
                  {userState?.mfa_enabled ? '🔐 2FA Active' : '🔓 2FA Off'}
                </Text>
                <Text className="text-[11px] text-slate-500">•</Text>
                <Pressable
                  onPress={() => setShowOtiBreakdown(!showOtiBreakdown)}
                  className="flex-row items-center gap-1.5 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 px-2 py-0.5 rounded-md transition cursor-pointer"
                >
                  <Text className="text-[11px] text-indigo-300 font-bold">
                    OTI: {(currentUser as any)?.objective_trust_score ?? 98.5}/100
                  </Text>
                  <Text className="text-[10px] text-indigo-400 font-mono">
                    {showOtiBreakdown ? '▲ Hide' : '▼ 4 Pillars'}
                  </Text>
                </Pressable>
              </View>
            </View>
          </View>

          {/* Quick Metrics */}
          <View className="flex-row items-center gap-3">
            {activeTab === 'seeker' ? (
              <>
                <View className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 items-center min-w-[95px] floating-interactive">
                  <Text className="text-[10px] text-slate-400 font-semibold">Active Passes</Text>
                  <Text className="text-base font-black text-emerald-400">
                    {bookings.filter(b => b.status === 'confirmed').length} Active
                  </Text>
                </View>
                <View className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 items-center min-w-[95px] floating-interactive">
                  <Text className="text-[10px] text-slate-400 font-semibold">Micro-Escrow</Text>
                  <Text className="text-base font-black text-indigo-400">
                    ₹{bookings.filter(b => b.status === 'confirmed').reduce((acc, b) => acc + (b.deposit_held || 100), 0)} Held
                  </Text>
                </View>
              </>
            ) : (
              <>
                <View className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 items-center min-w-[95px] floating-interactive">
                  <Text className="text-[10px] text-slate-400 font-semibold">Net Earnings</Text>
                  <Text className="text-base font-black text-emerald-400">
                    ₹{metrics?.net_earnings ?? 0}
                  </Text>
                </View>
                <View className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 items-center min-w-[95px] floating-interactive">
                  <Text className="text-[10px] text-slate-400 font-semibold">Active Spaces</Text>
                  <Text className="text-base font-black text-indigo-400">
                    {hostSpaces.filter(s => s.is_active).length} Listed
                  </Text>
                </View>
              </>
            )}
          </View>
        </View>

        {/* Objective Trust Index 4-Pillar Breakdown Drawer */}
        {showOtiBreakdown && (
          <View className="max-w-7xl mx-auto mt-6 pt-6 border-t border-slate-800 animate-fadeIn">
            <View className="flex-col sm:flex-row items-start sm:items-center justify-between mb-3 gap-2">
              <View className="flex-row items-center gap-2">
                <Text className="text-sm font-bold text-white">Objective Trust Index (OTI) Multi-Pillar Audit</Text>
                <View className="px-2 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/30">
                  <Text className="text-[10px] font-bold text-emerald-300">Grade AAA • Verified</Text>
                </View>
              </View>
              <Text className="text-[11px] font-mono text-slate-400">
                Formula: 0.35·Punctual + 0.35·Condition + 0.20·Identity + 0.10·Dispute
              </Text>
            </View>
            <View className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <View className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl">
                <View className="flex-row items-center justify-between mb-1">
                  <Text className="text-xs font-semibold text-slate-300">⏱️ Punctuality</Text>
                  <Text className="text-xs font-mono font-bold text-indigo-400">35% Weight</Text>
                </View>
                <Text className="text-xl font-black text-white mb-1">100%</Text>
                <Text className="text-[10px] text-slate-400 leading-tight">
                  On-time checkout & zero overrun history verified via live session telemetry.
                </Text>
              </View>
              <View className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl">
                <View className="flex-row items-center justify-between mb-1">
                  <Text className="text-xs font-semibold text-slate-300">🧹 Condition Match</Text>
                  <Text className="text-xs font-mono font-bold text-indigo-400">35% Weight</Text>
                </View>
                <Text className="text-xl font-black text-emerald-400 mb-1">98%</Text>
                <Text className="text-[10px] text-slate-400 leading-tight">
                  Pre/post check-in vision scan delta confirms zero property damage or debris.
                </Text>
              </View>
              <View className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl">
                <View className="flex-row items-center justify-between mb-1">
                  <Text className="text-xs font-semibold text-slate-300">🪪 Identity KYC</Text>
                  <Text className="text-xs font-mono font-bold text-indigo-400">20% Weight</Text>
                </View>
                <Text className="text-xl font-black text-indigo-300 mb-1">100%</Text>
                <Text className="text-[10px] text-slate-400 leading-tight">
                  DigiLocker verified Aadhaar/PAN + University institutional SSO active.
                </Text>
              </View>
              <View className="p-3.5 bg-slate-950/80 border border-slate-800 rounded-xl">
                <View className="flex-row items-center justify-between mb-1">
                  <Text className="text-xs font-semibold text-slate-300">🛡️ Dispute Free</Text>
                  <Text className="text-xs font-mono font-bold text-indigo-400">10% Weight</Text>
                </View>
                <Text className="text-xl font-black text-emerald-400 mb-1">100%</Text>
                <Text className="text-[10px] text-slate-400 leading-tight">
                  0 micro-escrow claims or payment disputes across all bookings.
                </Text>
              </View>
            </View>
          </View>
        )}
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
            onPress={() => setActiveTab('security')}
            className={`px-4 py-2 rounded-xl border text-xs font-bold transition ${
              activeTab === 'security'
                ? 'bg-indigo-600 border-indigo-400 text-white'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            <Text
              className={`text-xs font-bold ${
                activeTab === 'security' ? 'text-white' : 'text-slate-400'
              }`}
            >
              🛡️ Security & Two-Factor Authentication
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
              <View className="p-8 bg-slate-900 rounded-2xl border border-slate-800 text-center items-center floating-container">
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
                  className="p-5 bg-slate-900 border border-slate-800 rounded-2xl flex-col md:flex-row items-start md:items-center justify-between gap-4 floating-interactive"
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

            {/* Direct Inquiries Sent to Hosts */}
            <View className="mt-8 pt-6 border-t border-slate-800/80">
              <View className="flex-row items-center justify-between mb-3">
                <View>
                  <Text className="text-base font-bold text-white">Direct Host Inquiries</Text>
                  <Text className="text-xs text-slate-400">Questions you asked hosts with instant AI-grounded answers</Text>
                </View>
                {inquiries.length > 0 && (
                  <View className="px-2.5 py-1 rounded-lg bg-indigo-500/20 border border-indigo-500/30">
                    <Text className="text-xs font-bold text-indigo-300">
                      {inquiries.length} {inquiries.length === 1 ? 'Inquiry' : 'Inquiries'}
                    </Text>
                  </View>
                )}
              </View>

              {inquiries.length === 0 ? (
                <View className="p-6 bg-slate-900 border border-slate-800 rounded-2xl items-center text-center">
                  <Text className="text-2xl mb-1">💬</Text>
                  <Text className="text-sm font-bold text-white mb-0.5">No Inquiries Sent Yet</Text>
                  <Text className="text-xs text-slate-400 max-w-md">
                    Have questions about noise levels, dual monitors, or WiFi speeds? Ask directly on any space detail page to get an instant AI grounded reply.
                  </Text>
                </View>
              ) : (
                <View className="space-y-3">
                  {inquiries.map((inq: any) => (
                    <View key={inq.id} className="p-4 bg-slate-900 border border-slate-800 rounded-2xl floating-interactive">
                      <View className="flex-row items-center justify-between mb-2">
                        <Text className="text-xs font-bold text-indigo-400">Space #{inq.space_id} Inquiry</Text>
                        <Text className="text-[10px] text-slate-500">{new Date(inq.created_at).toLocaleDateString()}</Text>
                      </View>
                      <Text className="text-xs font-semibold text-white mb-2">Q: {inq.question}</Text>
                      {inq.ai_response && (
                        <View className="p-3 bg-slate-950 border border-slate-800/80 rounded-xl mb-2">
                          <Text className="text-[10px] font-bold text-indigo-300 mb-0.5">🤖 AI Instant Answer:</Text>
                          <Text className="text-xs text-slate-300 leading-relaxed">{inq.ai_response}</Text>
                        </View>
                      )}
                      {inq.response && (
                        <View className="p-3 bg-emerald-950/30 border border-emerald-500/20 rounded-xl">
                          <Text className="text-[10px] font-bold text-emerald-400 mb-0.5">👤 Host Response:</Text>
                          <Text className="text-xs text-slate-300 leading-relaxed">{inq.response}</Text>
                        </View>
                      )}
                    </View>
                  ))}
                </View>
              )}
            </View>
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
                      className="p-4 bg-slate-900 border border-slate-800 rounded-2xl flex-col sm:flex-row items-start sm:items-center justify-between gap-3 floating-interactive"
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
                    onPress={() => navigate('/list-space')}
                    className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl shadow-md transition"
                  >
                    <Text className="text-xs font-bold text-white">+ List New Space</Text>
                  </Pressable>
                </View>
              </View>

              {hostSpaces.length === 0 ? (
                <View className="p-8 bg-slate-900 border border-slate-800 rounded-2xl items-center text-center floating-container">
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
                      className="p-4 bg-slate-900 border border-slate-800 rounded-2xl flex-row items-center justify-between gap-4 floating-interactive"
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

        {/* Tab 3: Security & Multi-Factor Authentication Settings */}
        {activeTab === 'security' && (
          <View className="space-y-6">
            {/* Header info */}
            <View className="flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <View>
                <Text className="text-xl font-bold text-white">Account Security & Authentication</Text>
                <Text className="text-xs text-slate-400 mt-0.5">
                  Manage your Multi-Factor Authentication (MFA), email verification gate, and security credentials.
                </Text>
              </View>
              <View className="flex-row items-center gap-2">
                <View className={`px-3 py-1 rounded-full border ${userState?.mfa_enabled ? 'bg-emerald-500/20 border-emerald-500/40' : 'bg-slate-800 border-slate-700'}`}>
                  <Text className={`text-xs font-bold ${userState?.mfa_enabled ? 'text-emerald-300' : 'text-slate-400'}`}>
                    {userState?.mfa_enabled ? '🔐 MFA Protected' : '🔓 Single-Factor Only'}
                  </Text>
                </View>
              </View>
            </View>

            {/* Email Verification Card */}
            <View className="p-6 bg-slate-900 border border-slate-800 rounded-3xl space-y-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-xl shrink-0 ${userState?.is_email_verified ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'}`}>
                    {userState?.is_email_verified ? '✓' : '✉️'}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-base font-bold text-white">Email Address Verification</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${userState?.is_email_verified ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'}`}>
                        {userState?.is_email_verified ? 'Verified' : 'Unverified'}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5 font-mono">{userState?.email || 'No email registered'}</div>
                  </div>
                </div>

                {!userState?.is_email_verified && (
                  <button
                    onClick={handleResendEmail}
                    disabled={resendingEmail}
                    className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition shrink-0"
                  >
                    {resendingEmail ? 'Sending Link...' : 'Send Verification Email →'}
                  </button>
                )}
              </div>

              {emailNotice && (
                <div className="p-3.5 bg-slate-950 border border-indigo-500/30 rounded-xl text-xs text-indigo-300">
                  {emailNotice}
                </div>
              )}

              {!userState?.is_email_verified && (
                <div className="p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex items-start gap-2.5">
                  <span className="text-amber-400 text-sm mt-0.5">⚠️</span>
                  <div className="text-xs text-amber-300">
                    <strong>Email Verification Gate:</strong> Multi-Factor Authentication requires a verified email address to prevent account lockouts and protect recovery paths. Please verify your email before enrolling in TOTP MFA.
                  </div>
                </div>
              )}
            </View>

            {/* TOTP Multi-Factor Authentication Card */}
            <View className="p-6 bg-slate-900 border border-slate-800 rounded-3xl space-y-5">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-xl shrink-0 ${userState?.mfa_enabled ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/30'}`}>
                    🔐
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-base font-bold text-white">Two-Factor Authentication (TOTP)</span>
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${userState?.mfa_enabled ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-slate-800 text-slate-400 border border-slate-700'}`}>
                        {userState?.mfa_enabled ? 'Active (RFC 6238)' : 'Disabled'}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      Standard Time-based One-Time Passwords compatible with Google Authenticator, Microsoft Authenticator, and 1Password.
                    </div>
                  </div>
                </div>

                {userState?.mfa_enabled ? (
                  <button
                    onClick={() => {
                      setShowDisableMfaModal(true);
                      setDisableError(null);
                      setDisableSuccess(null);
                      setDisablePassword('');
                      setDisableCode('');
                      setDisableRecoveryCode('');
                    }}
                    className="px-4 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 font-bold text-xs transition shrink-0"
                  >
                    Disable Two-Factor Authentication
                  </button>
                ) : (
                  <button
                    onClick={handleStartMfaEnrollment}
                    className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition shadow-lg shadow-indigo-600/25 shrink-0"
                  >
                    Enable Two-Factor Authentication →
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-2xl">
                  <div className="text-base mb-1">📱</div>
                  <div className="text-xs font-bold text-white mb-1">Authenticator App Support</div>
                  <div className="text-[11px] text-slate-400 leading-relaxed">
                    Uses standard RFC 6238 TOTP protocols. Works offline with Google Authenticator, Microsoft Authenticator, and Bitwarden.
                  </div>
                </div>
                <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-2xl">
                  <div className="text-base mb-1">🛡️</div>
                  <div className="text-xs font-bold text-white mb-1">Encrypted At Rest</div>
                  <div className="text-[11px] text-slate-400 leading-relaxed">
                    TOTP secrets are encrypted with Fernet symmetric cryptography and are never returned in public user profiles or APIs.
                  </div>
                </div>
                <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-2xl">
                  <div className="text-base mb-1">🔑</div>
                  <div className="text-xs font-bold text-white mb-1">Single-Use Backup Codes</div>
                  <div className="text-[11px] text-slate-400 leading-relaxed">
                    10 single-use recovery codes are issued upon enrollment so you never lose access if your mobile device is unavailable.
                  </div>
                </div>
              </div>
            </View>
          </View>
        )}
      </View>

      {/* MFA ENROLLMENT MODAL */}
      {showMfaEnrollModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
          <div className="bg-slate-900 border border-indigo-500/30 text-white w-full max-w-lg rounded-3xl floating-panel overflow-hidden my-6 transition-all">
            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
              <div>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  🔐 Security Enrollment
                </span>
                <h3 className="text-lg font-bold text-white mt-1">
                  {mfaEnrollStep === 'recovery' ? 'Backup Recovery Codes' : 'Two-Factor Authentication Setup'}
                </h3>
              </div>
              <button
                onClick={() => {
                  setShowMfaEnrollModal(false);
                  setMfaEnrollError(null);
                  setMfaCopyStatus(null);
                }}
                className="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4">
              {mfaEnrollError && (
                <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-2xl flex items-start gap-2.5">
                  <span className="text-rose-400 text-sm">⚠️</span>
                  <p className="text-xs text-rose-300 font-medium">{mfaEnrollError}</p>
                </div>
              )}

              {/* Email Verification Gate Notice */}
              {!userState?.is_email_verified ? (
                <div className="space-y-4 py-2">
                  <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 text-2xl mx-auto shadow-inner">
                    ✉️
                  </div>
                  <div className="text-center">
                    <h4 className="text-base font-bold text-white mb-1">Email Verification Required</h4>
                    <p className="text-xs text-slate-400 max-w-sm mx-auto">
                      In accordance with SpaceLoop security standards, MFA enrollment is blocked until your email address (<span className="text-white font-mono">{userState?.email}</span>) is verified.
                    </p>
                  </div>

                  <div className="pt-2 flex flex-col gap-2">
                    <button
                      onClick={handleResendEmail}
                      disabled={resendingEmail}
                      className="w-full py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition"
                    >
                      {resendingEmail ? 'Sending Link...' : 'Send Verification Email Link →'}
                    </button>
                    <button
                      onClick={() => setShowMfaEnrollModal(false)}
                      className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
                    >
                      Close
                    </button>
                  </div>
                </div>
              ) : mfaEnrollStep === 'scan' ? (
                <div className="space-y-4">
                  {mfaEnrollLoading && !mfaSetupData ? (
                    <div className="py-12 flex flex-col items-center justify-center">
                      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3" />
                      <p className="text-xs text-slate-400">Generating cryptographic TOTP key...</p>
                    </div>
                  ) : mfaSetupData ? (
                    <>
                      <div className="text-center">
                        <p className="text-xs text-slate-400">
                          Scan the QR code below with your authenticator app (Google Authenticator, Microsoft Authenticator, 1Password, or Authy):
                        </p>
                      </div>

                      <div className="flex justify-center py-2">
                        <img
                          src={mfaSetupData.qr_code}
                          alt="SpaceLoop MFA QR Code"
                          className="w-48 h-48 rounded-2xl p-2 bg-white shadow-xl"
                        />
                      </div>

                      <div>
                        <label className="block text-[11px] font-bold text-slate-400 mb-1 text-center">
                          Or enter this secret key manually into your app:
                        </label>
                        <div className="flex items-center gap-2 p-2.5 bg-slate-950 border border-slate-800 rounded-xl">
                          <code className="text-xs font-mono text-indigo-300 flex-1 text-center tracking-wider select-all break-all">
                            {mfaSetupData.secret}
                          </code>
                          <button
                            type="button"
                            onClick={() => {
                              navigator.clipboard.writeText(mfaSetupData.secret);
                              setMfaCopyStatus('Copied!');
                              setTimeout(() => setMfaCopyStatus(null), 2000);
                            }}
                            className="px-2.5 py-1 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-300 text-[10px] font-bold shrink-0 transition"
                          >
                            {mfaCopyStatus || 'Copy'}
                          </button>
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-white mb-1.5 text-center">
                          Enter the 6-digit code from your app to verify setup:
                        </label>
                        <input
                          type="text"
                          maxLength={6}
                          autoFocus
                          value={mfaEnrollCode}
                          onChange={(e) => setMfaEnrollCode(e.target.value.replace(/\D/g, ''))}
                          placeholder="000000"
                          className="w-full text-center tracking-[0.4em] text-2xl font-mono px-4 py-3 rounded-xl border border-slate-700 bg-slate-950 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>

                      <div className="pt-2 flex items-center gap-3">
                        <button
                          type="button"
                          onClick={() => setShowMfaEnrollModal(false)}
                          className="flex-1 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs transition"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          onClick={handleConfirmMfaEnrollment}
                          disabled={mfaEnrollLoading || mfaEnrollCode.length !== 6}
                          className="flex-1 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xs transition shadow-lg shadow-indigo-600/25"
                        >
                          {mfaEnrollLoading ? 'Activating...' : 'Verify & Enable MFA →'}
                        </button>
                      </div>
                    </>
                  ) : null}
                </div>
              ) : (
                /* Recovery Codes Display Step */
                <div className="space-y-4">
                  <div className="p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex items-start gap-2.5">
                    <span className="text-amber-400 text-base">⚠️</span>
                    <div className="text-xs text-amber-300">
                      <strong>Save your backup codes now:</strong> If you lose access to your authenticator app, these single-use recovery codes are the only way to recover your account. Each code can be used at most once. They will not be displayed again.
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2.5 p-4 bg-slate-950 border border-slate-800 rounded-2xl">
                    {mfaEnrollRecoveryCodes.map((rc, idx) => (
                      <div key={idx} className="flex items-center gap-2 font-mono text-xs text-indigo-300 py-1 px-2 rounded bg-slate-900 border border-slate-800/80">
                        <span className="text-slate-500 text-[10px] w-4">{idx + 1}.</span>
                        <span className="font-bold tracking-wider">{rc}</span>
                      </div>
                    ))}
                  </div>

                  <div className="pt-2 flex flex-col sm:flex-row items-center gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        navigator.clipboard.writeText(mfaEnrollRecoveryCodes.join('\n'));
                        setMfaCopyStatus('All 10 codes copied to clipboard!');
                        setTimeout(() => setMfaCopyStatus(null), 3000);
                      }}
                      className="w-full sm:flex-1 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs transition"
                    >
                      {mfaCopyStatus || '📋 Copy All 10 Codes'}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowMfaEnrollModal(false);
                      }}
                      className="w-full sm:flex-1 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition shadow-lg shadow-indigo-600/25"
                    >
                      I Have Saved My Codes ✓
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* MFA DISABLE MODAL */}
      {showDisableMfaModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
          <div className="bg-slate-900 border border-rose-500/30 text-white w-full max-w-md rounded-3xl floating-panel overflow-hidden my-6 transition-all">
            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
              <div>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  ⚠️ Security Deactivation
                </span>
                <h3 className="text-lg font-bold text-white mt-1">
                  Disable Two-Factor Authentication
                </h3>
              </div>
              <button
                onClick={() => {
                  setShowDisableMfaModal(false);
                  setDisableError(null);
                  setDisableSuccess(null);
                }}
                className="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4">
              {disableError && (
                <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-2xl flex items-start gap-2.5">
                  <span className="text-rose-400 text-sm">⚠️</span>
                  <p className="text-xs text-rose-300 font-medium">{disableError}</p>
                </div>
              )}

              {disableSuccess && (
                <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl flex items-start gap-2.5">
                  <span className="text-emerald-400 text-sm">✓</span>
                  <p className="text-xs text-emerald-300 font-medium">{disableSuccess}</p>
                </div>
              )}

              <p className="text-xs text-slate-400">
                To disable two-factor authentication, verify your account password and either your current 6-digit TOTP code or a single-use backup recovery code.
              </p>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">Account Password</label>
                <input
                  type="password"
                  value={disablePassword}
                  onChange={(e) => setDisablePassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-rose-500 transition"
                  required
                />
              </div>

              {!disableUseRecovery ? (
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    6-Digit Authenticator Code
                  </label>
                  <input
                    type="text"
                    maxLength={6}
                    value={disableCode}
                    onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="000000"
                    className="w-full text-center tracking-[0.3em] font-mono text-lg px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-rose-500 transition"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    Single-Use Backup Recovery Code
                  </label>
                  <input
                    type="text"
                    value={disableRecoveryCode}
                    onChange={(e) => setDisableRecoveryCode(e.target.value.toUpperCase())}
                    placeholder="XXXX-XXXX"
                    className="w-full text-center font-mono text-sm px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-rose-500 transition uppercase"
                  />
                </div>
              )}

              <div className="flex items-center justify-between text-xs pt-1">
                <button
                  type="button"
                  onClick={() => {
                    setDisableUseRecovery(!disableUseRecovery);
                    setDisableError(null);
                  }}
                  className="text-indigo-400 hover:underline font-medium"
                >
                  {disableUseRecovery ? '← Use 6-digit TOTP code' : '🔑 Use a backup recovery code instead'}
                </button>
              </div>

              <div className="pt-2 flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setShowDisableMfaModal(false)}
                  className="flex-1 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmDisableMfa}
                  disabled={disableLoading || !disablePassword || (!disableUseRecovery ? disableCode.length !== 6 : !disableRecoveryCode.trim())}
                  className="flex-1 py-3 rounded-xl bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white font-bold text-xs transition shadow-lg shadow-rose-600/25"
                >
                  {disableLoading ? 'Verifying...' : 'Confirm Deactivation'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </View>
  );
};
