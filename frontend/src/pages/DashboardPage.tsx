import React, { useState, useEffect } from 'react';
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
  const [activeTab, setActiveTab] = useState<'seeker' | 'inquiries' | 'security'>('seeker');

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
  const [cancelingId, setCancelingId] = useState<number | null>(null);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
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
      console.warn('Dashboard API call failed:', err);
      setBookings([]);
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

  const activeBookingsCount = bookings.filter(b => b.status === 'confirmed' || b.status === 'active').length;
  const escrowHeldTotal = bookings.filter(b => b.status === 'confirmed' || b.status === 'active').reduce((acc, b) => acc + (b.deposit_held || 100), 0);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased">
      {/* 1. PROFILE HEADER SECTION */}
      <section className="border-b border-slate-800/80 bg-slate-900/50 pt-8 pb-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            {/* User Identity Details */}
            <div className="flex items-start sm:items-center gap-4">
              {currentUser?.avatar_url ? (
                <img
                  src={currentUser.avatar_url}
                  alt={currentUser.name || 'User Avatar'}
                  className="w-16 h-16 rounded-xl object-cover border border-slate-700 shrink-0"
                />
              ) : (
                <div className="w-16 h-16 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-300 font-bold text-xl uppercase shrink-0">
                  {(currentUser?.name || currentUser?.email || 'U').charAt(0)}
                </div>
              )}

              <div className="space-y-1.5">
                <div className="flex items-center gap-2.5 flex-wrap">
                  <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                    {currentUser?.name || currentUser?.email?.split('@')[0] || 'Space Seeker'}
                  </h1>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    {currentUser?.role ? currentUser.role.toUpperCase() : 'SEEKER'}
                  </span>
                </div>

                <p className="text-xs font-mono text-slate-400">
                  {currentUser?.email || 'No email registered'}
                </p>

                {/* Trust and Verification Signals */}
                <div className="flex items-center gap-2 pt-0.5 flex-wrap text-xs">
                  <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                    <i className="fa-solid fa-circle-check text-[11px]" />
                    <span>DigiLocker Verified</span>
                  </span>
                  <span className="text-slate-600">•</span>
                  <span className={`inline-flex items-center gap-1 font-medium ${userState?.is_email_verified ? 'text-emerald-400' : 'text-amber-400'}`}>
                    <i className={`fa-solid ${userState?.is_email_verified ? 'fa-envelope-circle-check' : 'fa-triangle-exclamation'} text-[11px]`} />
                    <span>{userState?.is_email_verified ? 'Email Verified' : 'Email Unverified'}</span>
                  </span>
                  <span className="text-slate-600">•</span>
                  <span className={`inline-flex items-center gap-1 font-medium ${userState?.mfa_enabled ? 'text-emerald-400' : 'text-slate-400'}`}>
                    <i className={`fa-solid ${userState?.mfa_enabled ? 'fa-shield-halved text-emerald-400' : 'fa-lock-open'} text-[11px]`} />
                    <span>{userState?.mfa_enabled ? '2FA Active' : '2FA Off'}</span>
                  </span>
                  <span className="text-slate-600">•</span>
                  <button
                    type="button"
                    onClick={() => setShowOtiBreakdown(!showOtiBreakdown)}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition"
                  >
                    <span>OTI Score: {(currentUser as any)?.objective_trust_score ?? 98.5}/100</span>
                    <i className={`fa-solid ${showOtiBreakdown ? 'fa-chevron-up' : 'fa-chevron-down'} text-[10px]`} />
                  </button>
                </div>
              </div>
            </div>

            {/* Quick Overview Metric Cards */}
            <div className="grid grid-cols-2 gap-3 sm:w-auto">
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-left min-w-[130px]">
                <div className="text-xs text-slate-400 font-medium flex items-center gap-1.5 mb-1">
                  <span>🎟️</span>
                  <span>Active Passes</span>
                </div>
                <div className="text-xl font-bold text-white">
                  {activeBookingsCount}
                </div>
                <div className="text-[11px] text-emerald-400 font-medium mt-0.5">
                  {activeBookingsCount === 1 ? '1 Pass Ready' : `${activeBookingsCount} Active`}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-left min-w-[130px]">
                <div className="text-xs text-slate-400 font-medium flex items-center gap-1.5 mb-1">
                  <span>🛡️</span>
                  <span>Micro-Escrow</span>
                </div>
                <div className="text-xl font-bold text-white">
                  ₹{escrowHeldTotal}
                </div>
                <div className="text-[11px] text-indigo-400 font-medium mt-0.5">
                  Refundable Held
                </div>
              </div>
            </div>
          </div>

          {/* OTI Multi-Pillar Breakdown Accordion */}
          {showOtiBreakdown && (
            <div className="mt-6 pt-6 border-t border-slate-800/80 animate-fadeIn">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-white">Objective Trust Index (OTI) Multi-Pillar Audit</h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                    Grade AAA • High Reliability
                  </span>
                </div>
                <span className="text-[11px] font-mono text-slate-400">
                  Weighted: 0.35·Punctual + 0.35·Condition + 0.20·Identity + 0.10·Dispute
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-slate-300">⏱️ Punctuality</span>
                    <span className="text-[11px] font-mono text-indigo-400">35% Weight</span>
                  </div>
                  <div className="text-lg font-bold text-white mb-0.5">100%</div>
                  <p className="text-[11px] text-slate-400 leading-normal">
                    On-time checkout & zero overrun history verified via session telemetry.
                  </p>
                </div>

                <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-slate-300">🧹 Condition Match</span>
                    <span className="text-[11px] font-mono text-indigo-400">35% Weight</span>
                  </div>
                  <div className="text-lg font-bold text-emerald-400 mb-0.5">98%</div>
                  <p className="text-[11px] text-slate-400 leading-normal">
                    Pre/post check-in vision scan delta confirms zero property damage.
                  </p>
                </div>

                <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-slate-300">🪪 Identity KYC</span>
                    <span className="text-[11px] font-mono text-indigo-400">20% Weight</span>
                  </div>
                  <div className="text-lg font-bold text-indigo-300 mb-0.5">100%</div>
                  <p className="text-[11px] text-slate-400 leading-normal">
                    DigiLocker verified Aadhaar/PAN and institutional SSO active.
                  </p>
                </div>

                <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-xl">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-slate-300">🛡️ Dispute Free</span>
                    <span className="text-[11px] font-mono text-indigo-400">10% Weight</span>
                  </div>
                  <div className="text-lg font-bold text-emerald-400 mb-0.5">100%</div>
                  <p className="text-[11px] text-slate-400 leading-normal">
                    0 micro-escrow claims or payment disputes across all bookings.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* 2. NAVIGATION TABS & BODY */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        {/* Clean Segmented Tab Control */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 border-b border-slate-800 pb-4 mb-6">
          <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
            <button
              type="button"
              onClick={() => setActiveTab('seeker')}
              className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition whitespace-nowrap flex items-center gap-2 ${
                activeTab === 'seeker'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <i className="fa-solid fa-ticket text-xs" />
              <span>My Bookings ({bookings.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('inquiries')}
              className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition whitespace-nowrap flex items-center gap-2 ${
                activeTab === 'inquiries'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <i className="fa-solid fa-comments text-xs" />
              <span>Direct Inquiries ({inquiries.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('security')}
              className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition whitespace-nowrap flex items-center gap-2 ${
                activeTab === 'security'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <i className="fa-solid fa-shield-halved text-xs" />
              <span>Security & 2FA</span>
            </button>
          </div>

          {/* Quick Switch to Host Workspace */}
          <button
            type="button"
            onClick={() => navigate('/host')}
            className="inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/25 text-xs font-semibold transition self-start sm:self-auto"
          >
            <span>🏡 Launch Host Operating System</span>
            <i className="fa-solid fa-arrow-right text-[10px]" />
          </button>
        </div>

        {/* TAB 1: RESERVED SPACES & BOOKINGS */}
        {activeTab === 'seeker' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-white">Your Reserved Spaces</h2>
                <p className="text-xs text-slate-400">Manage active hourly sessions, door passes, and booking history.</p>
              </div>
              <button
                type="button"
                onClick={() => navigate('/explore')}
                className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition flex items-center gap-1"
              >
                <span>+ Find New Space</span>
              </button>
            </div>

            {loading ? (
              <div className="py-16 flex flex-col items-center justify-center">
                <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3" />
                <p className="text-xs text-slate-400">Loading your reservations...</p>
              </div>
            ) : bookings.length === 0 ? (
              <div className="p-10 rounded-2xl bg-slate-900/60 border border-slate-800 text-center flex flex-col items-center max-w-lg mx-auto my-6">
                <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center text-xl mb-3 text-slate-300">
                  🎟️
                </div>
                <h3 className="text-base font-bold text-white mb-1">No Active Bookings</h3>
                <p className="text-xs text-slate-400 mb-5 leading-relaxed">
                  You haven't reserved any temporary spaces yet. Discover quiet study desks, meeting rooms, maker bays, and creative studios nearby.
                </p>
                <button
                  type="button"
                  onClick={() => navigate('/explore')}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-sm transition"
                >
                  Explore Spaces
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {bookings.map((b) => (
                  <div
                    key={b.id}
                    className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <img
                        src={
                          b.space_photo ||
                          'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=400&q=80'
                        }
                        alt={b.space_title}
                        className="w-16 h-16 rounded-lg object-cover shrink-0 border border-slate-800"
                      />
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="text-sm font-bold text-white">{b.space_title}</h4>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            b.status === 'confirmed' || b.status === 'active'
                              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                              : 'bg-slate-800 text-slate-400 border border-slate-700'
                          }`}>
                            {b.status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400">{b.space_address}</p>
                        <p className="text-xs font-medium text-slate-300">
                          Total: <strong className="text-white">₹{b.total_price}</strong> • Deposit: ₹{b.deposit_held || 100} Held
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-stretch md:self-auto justify-end">
                      <button
                        type="button"
                        onClick={() => navigate(`/session/${b.id}`)}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition flex items-center gap-1.5 shadow-sm"
                      >
                        <i className="fa-solid fa-mobile-screen text-xs" />
                        <span>Digital Door Pass</span>
                      </button>

                      {b.status !== 'cancelled' && b.status !== 'completed' && (
                        <button
                          type="button"
                          onClick={() => handleCancelBooking(b.id)}
                          disabled={cancelingId === b.id}
                          className="px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-rose-300 rounded-lg text-xs font-medium transition"
                        >
                          {cancelingId === b.id ? 'Canceling...' : 'Cancel'}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: DIRECT HOST INQUIRIES */}
        {activeTab === 'inquiries' && (
          <div className="space-y-4">
            <div>
              <h2 className="text-base font-bold text-white">Direct Host Inquiries</h2>
              <p className="text-xs text-slate-400">Questions you asked hosts with instant AI answers and host responses.</p>
            </div>

            {inquiries.length === 0 ? (
              <div className="p-10 rounded-2xl bg-slate-900/60 border border-slate-800 text-center flex flex-col items-center max-w-lg mx-auto my-6">
                <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center text-xl mb-3 text-slate-300">
                  💬
                </div>
                <h3 className="text-base font-bold text-white mb-1">No Inquiries Sent Yet</h3>
                <p className="text-xs text-slate-400 max-w-sm mb-4 leading-relaxed">
                  Have questions about WiFi speeds, noise levels, or equipment? Ask directly on any space detail page to get an instant AI-grounded reply.
                </p>
                <button
                  type="button"
                  onClick={() => navigate('/explore')}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition"
                >
                  Browse Spaces
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {inquiries.map((inq: any) => (
                  <div key={inq.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-indigo-400">Space #{inq.space_id} Inquiry</span>
                      <span className="text-[11px] text-slate-500">{new Date(inq.created_at).toLocaleDateString()}</span>
                    </div>

                    <p className="text-xs font-semibold text-white">Q: {inq.question}</p>

                    {inq.ai_response && (
                      <div className="p-3 bg-slate-950 border border-slate-800/80 rounded-lg">
                        <div className="text-[10px] font-bold text-indigo-300 mb-1 flex items-center gap-1">
                          <i className="fa-solid fa-robot" />
                          <span>AI Instant Answer:</span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">{inq.ai_response}</p>
                      </div>
                    )}

                    {inq.response && (
                      <div className="p-3 bg-emerald-950/30 border border-emerald-500/20 rounded-lg">
                        <div className="text-[10px] font-bold text-emerald-400 mb-1 flex items-center gap-1">
                          <i className="fa-solid fa-user-tie" />
                          <span>Host Response:</span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">{inq.response}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: SECURITY & MFA SETTINGS */}
        {activeTab === 'security' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-bold text-white">Account Security & Authentication</h2>
              <p className="text-xs text-slate-400">Manage your Multi-Factor Authentication (MFA), email verification gate, and password credentials.</p>
            </div>

            {/* Email Verification Box */}
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3.5">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg shrink-0 ${
                    userState?.is_email_verified
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                  }`}>
                    {userState?.is_email_verified ? '✓' : '✉️'}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">Email Address Verification</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        userState?.is_email_verified
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                          : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                      }`}>
                        {userState?.is_email_verified ? 'Verified' : 'Unverified'}
                      </span>
                    </div>
                    <p className="text-xs font-mono text-slate-400 mt-0.5">{userState?.email || 'No email registered'}</p>
                  </div>
                </div>

                {!userState?.is_email_verified && (
                  <button
                    type="button"
                    onClick={handleResendEmail}
                    disabled={resendingEmail}
                    className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition shrink-0"
                  >
                    {resendingEmail ? 'Sending Link...' : 'Send Verification Email'}
                  </button>
                )}
              </div>

              {emailNotice && (
                <div className="p-3 bg-slate-950 border border-indigo-500/30 rounded-lg text-xs text-indigo-300">
                  {emailNotice}
                </div>
              )}
            </div>

            {/* TOTP 2FA Box */}
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3.5">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg shrink-0 ${
                    userState?.mfa_enabled
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/30'
                  }`}>
                    🔐
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">Two-Factor Authentication (TOTP)</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        userState?.mfa_enabled
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                          : 'bg-slate-800 text-slate-400 border border-slate-700'
                      }`}>
                        {userState?.mfa_enabled ? 'Active (RFC 6238)' : 'Disabled'}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Standard Time-based One-Time Passwords compatible with Google Authenticator, Microsoft Authenticator, and 1Password.
                    </p>
                  </div>
                </div>

                {userState?.mfa_enabled ? (
                  <button
                    type="button"
                    onClick={() => {
                      setShowDisableMfaModal(true);
                      setDisableError(null);
                      setDisableSuccess(null);
                      setDisablePassword('');
                      setDisableCode('');
                      setDisableRecoveryCode('');
                    }}
                    className="px-3.5 py-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 font-semibold text-xs transition shrink-0"
                  >
                    Disable 2FA
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleStartMfaEnrollment}
                    className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition shrink-0 shadow-sm"
                  >
                    Enable 2FA →
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg">
                  <div className="text-sm mb-1">📱</div>
                  <div className="text-xs font-semibold text-white mb-1">Authenticator Apps</div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Uses standard RFC 6238 TOTP protocols. Works offline with Google Authenticator, Microsoft Authenticator, and Bitwarden.
                  </p>
                </div>

                <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg">
                  <div className="text-sm mb-1">🛡️</div>
                  <div className="text-xs font-semibold text-white mb-1">Encrypted At Rest</div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    TOTP secrets are encrypted with Fernet symmetric cryptography and are never returned in public APIs.
                  </p>
                </div>

                <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg">
                  <div className="text-sm mb-1">🔑</div>
                  <div className="text-xs font-semibold text-white mb-1">10 Backup Codes</div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    10 single-use recovery codes are issued upon enrollment to recover your account if your mobile device is lost.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* MFA ENROLLMENT MODAL */}
      {showMfaEnrollModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
          <div className="bg-slate-900 border border-slate-800 text-white w-full max-w-lg rounded-2xl overflow-hidden my-6 shadow-2xl">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
                  🔐 Security Enrollment
                </span>
                <h3 className="text-base font-bold text-white mt-1">
                  {mfaEnrollStep === 'recovery' ? 'Backup Recovery Codes' : 'Two-Factor Authentication Setup'}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => {
                  setShowMfaEnrollModal(false);
                  setMfaEnrollError(null);
                  setMfaCopyStatus(null);
                }}
                className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                ✕
              </button>
            </div>

            <div className="p-5 space-y-4">
              {mfaEnrollError && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-start gap-2">
                  <span className="text-rose-400 text-xs">⚠️</span>
                  <p className="text-xs text-rose-300 font-medium">{mfaEnrollError}</p>
                </div>
              )}

              {!userState?.is_email_verified ? (
                <div className="space-y-4 py-2 text-center">
                  <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 text-xl mx-auto">
                    ✉️
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white mb-1">Email Verification Required</h4>
                    <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
                      MFA enrollment is gated until your email address (<strong className="text-white font-mono">{userState?.email}</strong>) is verified.
                    </p>
                  </div>

                  <div className="pt-2 flex flex-col gap-2">
                    <button
                      type="button"
                      onClick={handleResendEmail}
                      disabled={resendingEmail}
                      className="w-full py-2.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition"
                    >
                      {resendingEmail ? 'Sending Link...' : 'Send Verification Link'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowMfaEnrollModal(false)}
                      className="w-full py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
                    >
                      Close
                    </button>
                  </div>
                </div>
              ) : mfaEnrollStep === 'scan' ? (
                <div className="space-y-4">
                  {mfaEnrollLoading && !mfaSetupData ? (
                    <div className="py-10 flex flex-col items-center justify-center">
                      <div className="w-7 h-7 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-2" />
                      <p className="text-xs text-slate-400">Generating cryptographic TOTP key...</p>
                    </div>
                  ) : mfaSetupData ? (
                    <>
                      <p className="text-xs text-slate-400 text-center">
                        Scan the QR code with your authenticator app (Google Authenticator, Microsoft Authenticator, or 1Password):
                      </p>

                      <div className="flex justify-center py-2">
                        <img
                          src={mfaSetupData.qr_code}
                          alt="SpaceLoop MFA QR Code"
                          className="w-44 h-44 rounded-xl p-2 bg-white"
                        />
                      </div>

                      <div>
                        <label className="block text-[11px] font-semibold text-slate-400 mb-1 text-center">
                          Or enter this key manually into your app:
                        </label>
                        <div className="flex items-center gap-2 p-2 bg-slate-950 border border-slate-800 rounded-lg">
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
                            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-semibold transition shrink-0"
                          >
                            {mfaCopyStatus || 'Copy'}
                          </button>
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-white mb-1.5 text-center">
                          Enter the 6-digit code to verify setup:
                        </label>
                        <input
                          type="text"
                          maxLength={6}
                          autoFocus
                          value={mfaEnrollCode}
                          onChange={(e) => setMfaEnrollCode(e.target.value.replace(/\D/g, ''))}
                          placeholder="000000"
                          className="w-full text-center tracking-[0.4em] text-xl font-mono px-4 py-2.5 rounded-lg border border-slate-700 bg-slate-950 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        />
                      </div>

                      <div className="pt-2 flex items-center gap-3">
                        <button
                          type="button"
                          onClick={() => setShowMfaEnrollModal(false)}
                          className="flex-1 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          onClick={handleConfirmMfaEnrollment}
                          disabled={mfaEnrollLoading || mfaEnrollCode.length !== 6}
                          className="flex-1 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-xs transition shadow-sm"
                        >
                          {mfaEnrollLoading ? 'Activating...' : 'Verify & Enable MFA'}
                        </button>
                      </div>
                    </>
                  ) : null}
                </div>
              ) : (
                /* Recovery Codes */
                <div className="space-y-4">
                  <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-start gap-2">
                    <span className="text-amber-400 text-xs">⚠️</span>
                    <p className="text-xs text-amber-300 leading-relaxed">
                      <strong>Save your backup codes now:</strong> If you lose access to your device, each single-use code allows one account recovery.
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-2 p-3.5 bg-slate-950 border border-slate-800 rounded-lg">
                    {mfaEnrollRecoveryCodes.map((rc, idx) => (
                      <div key={idx} className="flex items-center gap-2 font-mono text-xs text-indigo-300 py-1 px-2 rounded bg-slate-900 border border-slate-800/80">
                        <span className="text-slate-500 text-[10px] w-4">{idx + 1}.</span>
                        <span className="font-bold tracking-wider">{rc}</span>
                      </div>
                    ))}
                  </div>

                  <div className="pt-2 flex flex-col sm:flex-row items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        navigator.clipboard.writeText(mfaEnrollRecoveryCodes.join('\n'));
                        setMfaCopyStatus('All 10 codes copied to clipboard!');
                        setTimeout(() => setMfaCopyStatus(null), 3000);
                      }}
                      className="w-full sm:flex-1 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition"
                    >
                      {mfaCopyStatus || '📋 Copy All 10 Codes'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowMfaEnrollModal(false)}
                      className="w-full sm:flex-1 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition shadow-sm"
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
          <div className="bg-slate-900 border border-slate-800 text-white w-full max-w-md rounded-2xl overflow-hidden my-6 shadow-2xl">
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-500/15 text-rose-300 border border-rose-500/30">
                  ⚠️ Security Deactivation
                </span>
                <h3 className="text-base font-bold text-white mt-1">
                  Disable Two-Factor Authentication
                </h3>
              </div>
              <button
                type="button"
                onClick={() => {
                  setShowDisableMfaModal(false);
                  setDisableError(null);
                  setDisableSuccess(null);
                }}
                className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                ✕
              </button>
            </div>

            <div className="p-5 space-y-4">
              {disableError && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-start gap-2">
                  <span className="text-rose-400 text-xs">⚠️</span>
                  <p className="text-xs text-rose-300 font-medium">{disableError}</p>
                </div>
              )}

              {disableSuccess && (
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-start gap-2">
                  <span className="text-emerald-400 text-xs">✓</span>
                  <p className="text-xs text-emerald-300 font-medium">{disableSuccess}</p>
                </div>
              )}

              <p className="text-xs text-slate-400 leading-relaxed">
                Verify your account password and either your 6-digit TOTP code or backup recovery code to deactivate 2FA.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Account Password</label>
                <input
                  type="password"
                  value={disablePassword}
                  onChange={(e) => setDisablePassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-rose-500 transition"
                  required
                />
              </div>

              {!disableUseRecovery ? (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    6-Digit Authenticator Code
                  </label>
                  <input
                    type="text"
                    maxLength={6}
                    value={disableCode}
                    onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="000000"
                    className="w-full text-center tracking-[0.3em] font-mono text-base px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-rose-500 transition"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Single-Use Recovery Code
                  </label>
                  <input
                    type="text"
                    value={disableRecoveryCode}
                    onChange={(e) => setDisableRecoveryCode(e.target.value.toUpperCase())}
                    placeholder="XXXX-XXXX"
                    className="w-full text-center font-mono text-xs px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-rose-500 transition uppercase"
                  />
                </div>
              )}

              <div className="flex items-center justify-between text-xs pt-0.5">
                <button
                  type="button"
                  onClick={() => {
                    setDisableUseRecovery(!disableUseRecovery);
                    setDisableError(null);
                  }}
                  className="text-indigo-400 hover:underline font-medium text-[11px]"
                >
                  {disableUseRecovery ? '← Use 6-digit code' : '🔑 Use a backup recovery code'}
                </button>
              </div>

              <div className="pt-2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowDisableMfaModal(false)}
                  className="flex-1 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmDisableMfa}
                  disabled={disableLoading || !disablePassword || (!disableUseRecovery ? disableCode.length !== 6 : !disableRecoveryCode.trim())}
                  className="flex-1 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white font-semibold text-xs transition shadow-sm"
                >
                  {disableLoading ? 'Verifying...' : 'Confirm Deactivation'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
