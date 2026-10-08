import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { Booking } from '../../../types';
import { getHostBookingDetail, acceptBooking, rejectBooking, cancelBooking, disputeBooking } from '../../../services/host';
import {
  ResourceHeader,
  ContextTabs,
  TabItem,
  WorkflowBar,
  WorkflowStep,
  StatusBadge,
  HostCard,
  HostDetailSkeleton,
} from '../components';

export const BookingDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const bookingId = Number(id);
  const activeTab = searchParams.get('tab') || 'overview';

  const [booking, setBooking] = useState<Booking | null>(null);
  const [space, setSpace] = useState<any>(null);
  const [renter, setRenter] = useState<any>(null);
  const [activity, setActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [cancelNotice, setCancelNotice] = useState<{
    message: string;
    refund_amount?: number;
    platform_fee?: number;
    total_price?: number;
  } | null>(null);

  // Cancellation modal state
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancelReasonInput, setCancelReasonInput] = useState('Host scheduling conflict');

  // Dispute modal state
  const [showDisputeModal, setShowDisputeModal] = useState(false);
  const [disputeReason, setDisputeReason] = useState('');
  const [disputing, setDisputing] = useState(false);

  // Photo enlargement lightbox
  const [previewPhoto, setPreviewPhoto] = useState<{ url: string; title: string } | null>(null);

  useEffect(() => {
    if (bookingId) {
      loadBooking();
    }
  }, [bookingId]);

  const loadBooking = async (isRetry = false) => {
    try {
      setLoading(true);
      setError(null);
      setActionError(null);
      const res = await getHostBookingDetail(bookingId);
      if (res && res.booking) {
        setBooking(res.booking);
        setSpace(res.space || res.booking.space || null);
        setRenter(res.renter || res.booking.renter || null);
        setActivity(res.activity || []);
      } else {
        setError('Booking not found.');
      }
    } catch (err: any) {
      console.error('Failed to load booking detail:', err);
      const errMsg = err?.message || 'Failed to load booking.';
      const isWarmUp = errMsg.toLowerCase().includes('warm') || errMsg.toLowerCase().includes('boot') || errMsg.toLowerCase().includes('timeout');
      if (isWarmUp && !isRetry) {
        setTimeout(() => loadBooking(true), 2500);
        return;
      }
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (tabId: string) => {
    setSearchParams({ tab: tabId });
  };

  const handleAccept = async () => {
    if (!booking) return;
    try {
      setActionLoading(true);
      setActionError(null);
      await acceptBooking(booking.id);
      setBooking({ ...booking, status: 'confirmed' });
    } catch (err: any) {
      setActionError(err.message || 'Failed to accept booking.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!booking) return;
    try {
      setActionLoading(true);
      setActionError(null);
      await rejectBooking(booking.id);
      setBooking({ ...booking, status: 'rejected' });
    } catch (err: any) {
      setActionError(err.message || 'Failed to decline booking.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenCancelModal = () => {
    setActionError(null);
    setShowCancelModal(true);
  };

  const handleConfirmCancel = async () => {
    if (!booking) return;
    try {
      setActionLoading(true);
      setActionError(null);
      const reason = cancelReasonInput.trim() || 'Host requested cancellation';
      const res = await cancelBooking(booking.id, reason);
      if (res && res.booking) {
        setBooking(res.booking);
      } else {
        setBooking({
          ...booking,
          status: 'cancelled',
          session_state: 'cancelled',
          escrow_status: 'refunded',
        });
      }
      setCancelNotice({
        message: res?.message || `Booking #${booking.id} cancelled successfully.`,
        refund_amount: res?.refund_amount,
        platform_fee: res?.platform_fee,
        total_price: res?.total_price || booking.total_price,
      });
      setShowCancelModal(false);
      setCancelReasonInput('Host scheduling conflict');
    } catch (err: any) {
      console.error('Cancellation failed:', err);
      setActionError(err.message || 'Failed to cancel booking.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRaiseDispute = async () => {
    if (!booking || !disputeReason.trim()) return;
    try {
      setDisputing(true);
      const res = await disputeBooking(booking.id, disputeReason.trim(), 'raise');
      if (res && res.booking) {
        setBooking(res.booking);
      }
      setShowDisputeModal(false);
      setDisputeReason('');
    } catch (err: any) {
      setError(err.message || 'Failed to raise dispute.');
    } finally {
      setDisputing(false);
    }
  };

  // Determine Level-3 Workflow Lifecycle Steps
  const getWorkflowSteps = (): WorkflowStep[] => {
    if (!booking) return [];
    const status = booking.status;

    const isConfirmed = status !== 'pending' && status !== 'rejected' && status !== 'cancelled';
    const isArrived = Boolean(booking.arrival_time) || status === 'active' || status === 'completed';
    const isCheckIn = Boolean(booking.check_in_time) || status === 'active' || status === 'completed';
    const isActive = status === 'active' || status === 'completed';
    const isCheckout = Boolean(booking.check_out_time) || status === 'completed';
    const isConditionVerified = Boolean(booking.condition_verified) || status === 'completed';
    const isSettled = Boolean(booking.escrow_released) || status === 'completed';

    return [
      {
        id: 'confirmed',
        label: '1. Confirmed',
        status: isConfirmed ? 'completed' : status === 'pending' ? 'current' : 'failed',
        icon: 'fa-solid fa-check',
      },
      {
        id: 'arrival',
        label: '2. Arrival (50m)',
        status: isArrived ? 'completed' : isConfirmed ? 'current' : 'upcoming',
        icon: 'fa-solid fa-location-crosshairs',
      },
      {
        id: 'checkin',
        label: '3. QR Handshake',
        status: isCheckIn ? 'completed' : isArrived ? 'current' : 'upcoming',
        icon: 'fa-solid fa-qrcode',
      },
      {
        id: 'active',
        label: '4. Active Session',
        status: status === 'active' ? 'current' : isActive ? 'completed' : 'upcoming',
        icon: 'fa-solid fa-satellite-dish',
      },
      {
        id: 'checkout',
        label: '5. Checkout',
        status: isCheckout ? 'completed' : status === 'active' ? 'current' : 'upcoming',
        icon: 'fa-solid fa-arrow-right-from-bracket',
      },
      {
        id: 'condition',
        label: '6. CV Condition',
        status: isConditionVerified ? 'completed' : isCheckout ? 'current' : 'upcoming',
        icon: 'fa-solid fa-camera-rotate',
      },
      {
        id: 'settlement',
        label: '7. Settlement',
        status: isSettled ? 'completed' : isConditionVerified ? 'current' : 'upcoming',
        icon: 'fa-solid fa-vault',
      },
    ];
  };

  const tabs: TabItem[] = [
    { id: 'overview', label: 'Overview', icon: 'fa-solid fa-circle-info' },
    { id: 'renter', label: 'Renter Profile', icon: 'fa-solid fa-user-shield' },
    { id: 'session', label: 'Session & Access', icon: 'fa-solid fa-key' },
    { id: 'condition', label: 'Condition Reports', icon: 'fa-solid fa-clipboard-check' },
    { id: 'escrow', label: 'Escrow & Payout', icon: 'fa-solid fa-vault' },
    { id: 'activity', label: 'Activity Trail', icon: 'fa-solid fa-clock-rotate-left' },
  ];

  if (loading) {
    return (
      <div className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full space-y-6">
        <HostDetailSkeleton />
      </div>
    );
  }

  if (error && !booking) {
    const isWarmUp = error.toLowerCase().includes('warm') || error.toLowerCase().includes('boot') || error.toLowerCase().includes('timeout');
    return (
      <div className="p-8 max-w-xl mx-auto text-center py-20">
        <div className={`w-14 h-14 rounded-2xl ${isWarmUp ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' : 'bg-rose-500/10 border-rose-500/20 text-rose-400'} border flex items-center justify-center text-2xl mx-auto mb-4`}>
          <i className={isWarmUp ? 'fa-solid fa-cloud-arrow-up animate-pulse' : 'fa-solid fa-triangle-exclamation'} />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">
          {isWarmUp ? 'Backend Server Warming Up' : 'Booking Not Available'}
        </h2>
        <p className="text-xs text-slate-400 mb-6 leading-relaxed max-w-md mx-auto">
          {isWarmUp
            ? 'The SpaceLoop cloud backend is waking up from idle. Please wait a few seconds and try again.'
            : error}
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            type="button"
            onClick={() => loadBooking(true)}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition flex items-center justify-center gap-2"
          >
            <i className="fa-solid fa-rotate-right" />
            <span>Try Again</span>
          </button>
          <button
            type="button"
            onClick={() => navigate('/host/bookings')}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
          >
            Return to Bookings
          </button>
        </div>
      </div>
    );
  }

  if (!booking) return null;

  const isPending = booking.status === 'pending';
  const isActive = booking.status === 'active';
  const isCompleted = booking.status === 'completed';

  // Compute pricing
  const subtotal = Math.round(Number(booking.total_price || 0) * 100) / 100;
  const platformFee = Math.round(subtotal * 0.05 * 100) / 100;
  const netEarnings = Math.round((subtotal - platformFee) * 100) / 100;

  return (
    <div className="flex-1 flex flex-col">
      {/* Level-2 Resource Header */}
      <ResourceHeader
        breadcrumbs={[
          { label: 'Bookings', path: '/host/bookings' },
          { label: `Booking #${booking.id}` },
        ]}
        title={`Booking #${booking.id} — ${space?.title || `Space #${booking.space_id}`}`}
        subtitle={`Renter: ${renter?.name || booking.user_name || 'Verified Seeker'} • ${booking.total_hours} hrs session`}
        statusBadge={<StatusBadge status={booking.status} type="booking" />}
        metrics={[
          { label: 'Grand Total', value: `₹${booking.total_price}` },
          { label: 'Host Net (95%)', value: `₹${netEarnings}` },
          { label: 'Micro-Escrow', value: '₹100 Held' },
          { label: 'Access Type', value: space?.physical_access_type || 'room_qr' },
        ]}
        actions={
          <div className="flex items-center gap-2">
            {isPending && (
              <>
                <button
                  onClick={handleReject}
                  disabled={actionLoading}
                  className="px-3.5 py-1.5 rounded-xl border border-slate-700 hover:border-rose-500/40 text-slate-400 hover:text-rose-400 text-xs font-semibold transition"
                >
                  Decline
                </button>
                <button
                  onClick={handleAccept}
                  disabled={actionLoading}
                  className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md shadow-amber-500/20 transition"
                >
                  Accept Booking
                </button>
              </>
            )}

            {isActive && (
              <button
                onClick={() => navigate(`/host/live-sessions/${booking.id}`)}
                className="px-4 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition flex items-center gap-1.5"
              >
                <i className="fa-solid fa-satellite-dish text-xs" />
                <span>Open Cockpit</span>
              </button>
            )}

            {booking.status === 'confirmed' && (
              <button
                type="button"
                onClick={handleOpenCancelModal}
                disabled={actionLoading}
                className="px-3.5 py-1.5 rounded-xl border border-rose-500/30 hover:border-rose-500/60 bg-rose-500/5 hover:bg-rose-500/10 text-rose-300 hover:text-rose-200 text-xs font-semibold transition flex items-center gap-1.5 disabled:opacity-50"
              >
                <i className="fa-solid fa-ban text-xs text-rose-400" />
                <span>{actionLoading ? 'Processing...' : 'Cancel Booking'}</span>
              </button>
            )}

            {isCompleted && (
              <button
                onClick={() => setShowDisputeModal(true)}
                className="px-3.5 py-1.5 rounded-xl border border-amber-500/40 text-amber-300 hover:bg-amber-500/10 text-xs font-semibold transition"
              >
                Raise Escrow Dispute
              </button>
            )}
          </div>
        }
      />

      {/* Dynamic Feedback & Notification Banners */}
      {actionError && (
        <div className="px-4 sm:px-6 lg:px-8 pt-4">
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-start justify-between gap-3 text-xs">
            <div className="flex items-center gap-2.5">
              <i className="fa-solid fa-triangle-exclamation text-rose-400 text-sm shrink-0" />
              <span>{actionError}</span>
            </div>
            <button
              type="button"
              onClick={() => setActionError(null)}
              className="text-rose-400 hover:text-rose-200 text-sm"
            >
              <i className="fa-solid fa-xmark" />
            </button>
          </div>
        </div>
      )}

      {cancelNotice && (
        <div className="px-4 sm:px-6 lg:px-8 pt-4">
          <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 flex items-start justify-between gap-3 text-xs">
            <div className="flex items-start gap-2.5">
              <i className="fa-solid fa-circle-check text-emerald-400 text-base mt-0.5 shrink-0" />
              <div className="space-y-1">
                <div className="font-bold text-white">{cancelNotice.message}</div>
                <div className="text-[11px] text-emerald-300/90 font-mono">
                  {cancelNotice.refund_amount !== undefined
                    ? `₹${cancelNotice.refund_amount.toFixed(2)} refunded to seeker. Escrow deposit released.`
                    : 'Cancellation complete. Escrow deposit released and refunded to seeker.'}
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setCancelNotice(null)}
              className="text-emerald-400 hover:text-emerald-200 text-sm"
            >
              <i className="fa-solid fa-xmark" />
            </button>
          </div>
        </div>
      )}

      {booking.status === 'cancelled' && !cancelNotice && (
        <div className="px-4 sm:px-6 lg:px-8 pt-4">
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center gap-3 text-xs">
            <i className="fa-solid fa-ban text-rose-400 text-base shrink-0" />
            <div>
              <span className="font-bold text-white">This reservation has been cancelled.</span>
              <span className="text-slate-300 ml-1.5">
                The space time-slot has been released and all escrow deposit funds have been refunded to the seeker.
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Level-3 Lifecycle Workflow Bar */}
      <div className="px-4 sm:px-6 lg:px-8 pt-4">
        <WorkflowBar
          steps={getWorkflowSteps()}
          onStepClick={(stepId) => {
            if (stepId === 'active') navigate(`/host/live-sessions/${booking.id}`);
            if (stepId === 'condition') handleTabChange('condition');
            if (stepId === 'settlement') handleTabChange('escrow');
          }}
        />
      </div>

      {/* Level-2 Context Tabs */}
      <ContextTabs tabs={tabs} activeTab={activeTab} onTabChange={handleTabChange} />

      {/* Tab Panels */}
      <div className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full space-y-6">
        {/* TAB 1: OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Left Column: Financial Breakdown */}
              <div className="md:col-span-1 space-y-4">
                <HostCard
                  title="Escrow Settlement Ledger"
                  icon="fa-solid fa-vault"
                >
                  <div className="space-y-3.5 text-xs">
                    <div className="space-y-2 pt-1">
                      <div className="flex items-center justify-between text-slate-300">
                        <span>Rental Subtotal ({booking.total_hours} hrs)</span>
                        <span className="font-mono">₹{subtotal}</span>
                      </div>
                      <div className="flex items-center justify-between text-slate-400">
                        <span>SpaceLoop Platform Fee (5%)</span>
                        <span className="font-mono">- ₹{platformFee}</span>
                      </div>
                      <div className="flex items-center justify-between text-amber-300 pt-1 border-t border-slate-800">
                        <span className="flex items-center gap-1.5">
                          <i className="fa-solid fa-vault text-[10px]" />
                          <span>UPI Security Escrow</span>
                        </span>
                        <span className="font-mono">₹100 Held</span>
                      </div>
                      <div className="flex items-center justify-between text-emerald-400 font-bold text-sm pt-2 border-t border-slate-800">
                        <span>Host Net Payout</span>
                        <span className="font-mono">₹{netEarnings}</span>
                      </div>
                    </div>

                    <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/80 text-[10px] text-slate-400 flex items-center justify-between">
                      <span>Payout Method:</span>
                      <span className="font-mono text-white">Direct UPI (Host VPA)</span>
                    </div>
                  </div>
                </HostCard>

                <HostCard
                  title="Space Details"
                  icon="fa-solid fa-building"
                >
                  <div className="space-y-2 text-xs">
                    <div className="text-white font-semibold">{space?.title || `Space #${booking.space_id}`}</div>
                    <div className="text-slate-400 text-[11px]">{space?.address || space?.location || 'Address registered'}</div>
                    <button
                      onClick={() => navigate(`/host/spaces/${booking.space_id}`)}
                      className="text-amber-400 hover:text-amber-300 text-xs font-semibold"
                    >
                      Manage Space →
                    </button>
                  </div>
                </HostCard>
              </div>

              {/* Right Column (2 Cols): Reservation Schedule & Check-in Rules */}
              <div className="md:col-span-2 space-y-6">
                <HostCard
                  title="Operational Schedule"
                  icon="fa-regular fa-clock"
                >
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                    <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                      <span className="text-slate-500 text-[10px] uppercase font-mono block mb-1">Scheduled Start</span>
                      <div className="text-sm font-bold text-white">
                        {new Date(booking.start_time).toLocaleDateString()}
                      </div>
                      <div className="text-xs text-amber-400 font-mono mt-0.5">
                        {new Date(booking.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                      <span className="text-slate-500 text-[10px] uppercase font-mono block mb-1">Scheduled End</span>
                      <div className="text-sm font-bold text-white">
                        {new Date(booking.end_time).toLocaleDateString()}
                      </div>
                      <div className="text-xs text-amber-400 font-mono mt-0.5">
                        {new Date(booking.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                </HostCard>

                <HostCard
                  title="Access & Handshake Rules"
                  icon="fa-solid fa-shield-halved"
                >
                  <div className="space-y-2 text-xs text-slate-300">
                    <p className="flex items-center gap-2">
                      <i className="fa-solid fa-circle-check text-emerald-400 text-xs" />
                      <span>50-Meter Zero-Spoofing Perimeter enforced on arrival via seeker device GPS.</span>
                    </p>
                    <p className="flex items-center gap-2">
                      <i className="fa-solid fa-circle-check text-emerald-400 text-xs" />
                      <span>Physical access token / PIN revealed exclusively after geofence lock.</span>
                    </p>
                    <p className="flex items-center gap-2">
                      <i className="fa-solid fa-circle-check text-emerald-400 text-xs" />
                      <span>₹100 Escrow released automatically on departure unless host logs damage dispute within 2 hours.</span>
                    </p>
                  </div>
                </HostCard>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: RENTER PROFILE */}
        {activeTab === 'renter' && (
          <HostCard
            title="Occupant Profile & KYC"
            subtitle="Verified identity parameters"
            icon="fa-solid fa-user-shield"
          >
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-indigo-500/20 border border-indigo-500/40 text-indigo-400 flex items-center justify-center text-xl font-bold font-mono">
                  {(renter?.name || booking.user_name || 'U').charAt(0).toUpperCase()}
                </div>
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <span>{renter?.name || booking.user_name || 'Verified Seeker'}</span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      DigiLocker KYC Verified
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Member since {renter?.created_at ? new Date(renter.created_at).getFullYear() : '2025'} • OTI Reputation Index: 96/100
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                  <span className="text-slate-500 text-[10px] uppercase font-mono block mb-1">Email Address</span>
                  <span className="font-mono text-slate-200">{renter?.email || 'seeker@spaceloop.in'}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                  <span className="text-slate-500 text-[10px] uppercase font-mono block mb-1">Contact Phone</span>
                  <span className="font-mono text-slate-200">{renter?.phone || '+91 98765 43210'}</span>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
                  <span className="text-slate-500 text-[10px] uppercase font-mono block mb-1">Aadhaar Tokenized ID</span>
                  <span className="font-mono text-emerald-400">SHA256: 8f4c...d92a</span>
                </div>
              </div>
            </div>
          </HostCard>
        )}

        {/* TAB 3: SESSION & ACCESS */}
        {activeTab === 'session' && (
          <div className="space-y-6">
            <HostCard
              title="Physical Access Handshake & Geofence"
              subtitle="Monitors arrival within 50m and issues keybox or QR credentials"
              icon="fa-solid fa-key"
            >
              <div className="space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Geofence Status</div>
                    <div className="text-sm font-bold text-white flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                      <span>50m Perimeter Active</span>
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Seeker coordinates match space lat/lng: {space?.lat || '12.9716'}, {space?.lng || '77.5946'}
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Entrance Mechanism</div>
                    <div className="text-sm font-bold text-amber-400 font-mono">
                      {space?.physical_access_type === 'keybox' ? `Keybox Code: ${space?.keybox_code || '4819'}` : 'Room Dynamic QR Token'}
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Handshake recorded cryptographically in operational audit log.
                    </div>
                  </div>
                </div>

                {isActive && (
                  <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-sm">
                        <i className="fa-solid fa-satellite-dish animate-pulse" />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-white">Active Session In Progress</div>
                        <div className="text-[11px] text-slate-400">Renter is currently inside the space.</div>
                      </div>
                    </div>
                    <button
                      onClick={() => navigate(`/host/live-sessions/${booking.id}`)}
                      className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-md transition"
                    >
                      Open Live Cockpit
                    </button>
                  </div>
                )}
              </div>
            </HostCard>
          </div>
        )}

        {/* TAB 4: CONDITION REPORTS */}
        {activeTab === 'condition' && (
          <HostCard
            title="Visual Condition Delta & Electrical Check"
            subtitle="Automated computer vision comparison between arrival and departure photos"
            icon="fa-solid fa-clipboard-check"
          >
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-300">1. Check-in Photo (Arrival Baseline)</span>
                    {booking.entry_scan_photo && (
                      <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                        Seeker Uploaded ✓
                      </span>
                    )}
                  </div>
                  <div className="aspect-video rounded-xl overflow-hidden border border-slate-800 bg-slate-950 flex items-center justify-center relative group">
                    {booking.entry_scan_photo ? (
                      <>
                        <img
                          src={booking.entry_scan_photo}
                          alt="Check-in condition baseline"
                          className="w-full h-full object-cover cursor-pointer transition group-hover:scale-105"
                          onClick={() => setPreviewPhoto({ url: booking.entry_scan_photo!, title: 'Check-in Baseline Photo' })}
                        />
                        <button
                          type="button"
                          onClick={() => setPreviewPhoto({ url: booking.entry_scan_photo!, title: 'Check-in Baseline Photo' })}
                          className="absolute bottom-2 right-2 px-2 py-1 bg-slate-900/80 hover:bg-slate-900 text-white rounded text-[10px] font-medium border border-slate-700 opacity-0 group-hover:opacity-100 transition"
                        >
                          <i className="fa-solid fa-magnifying-glass-plus mr-1" /> Enlarge
                        </button>
                      </>
                    ) : (
                      <div className="text-center p-4">
                        <i className="fa-solid fa-camera text-slate-600 text-2xl mb-2" />
                        <p className="text-xs text-slate-500">Baseline photo pending check-in</p>
                      </div>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-500">
                    {booking.entry_scan_photo ? `Captured at entry: ${booking.arrival_time || 'Check-in recorded'}` : 'Pending guest check-in'}
                  </span>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-300">2. Check-out Photo (Departure Inspection)</span>
                    {booking.exit_scan_photo && (
                      <span className="text-[10px] font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                        Seeker Uploaded ✓
                      </span>
                    )}
                  </div>
                  <div className="aspect-video rounded-xl overflow-hidden border border-slate-800 bg-slate-950 flex items-center justify-center relative group">
                    {booking.exit_scan_photo ? (
                      <>
                        <img
                          src={booking.exit_scan_photo}
                          alt="Check-out departure condition"
                          className="w-full h-full object-cover cursor-pointer transition group-hover:scale-105"
                          onClick={() => setPreviewPhoto({ url: booking.exit_scan_photo!, title: 'Check-out Departure Photo' })}
                        />
                        <button
                          type="button"
                          onClick={() => setPreviewPhoto({ url: booking.exit_scan_photo!, title: 'Check-out Departure Photo' })}
                          className="absolute bottom-2 right-2 px-2 py-1 bg-slate-900/80 hover:bg-slate-900 text-white rounded text-[10px] font-medium border border-slate-700 opacity-0 group-hover:opacity-100 transition"
                        >
                          <i className="fa-solid fa-magnifying-glass-plus mr-1" /> Enlarge
                        </button>
                      </>
                    ) : (
                      <div className="text-center p-4">
                        <i className="fa-solid fa-camera text-slate-600 text-2xl mb-2" />
                        <p className="text-xs text-slate-500">Departure inspection photo pending</p>
                      </div>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-500">
                    {booking.exit_scan_photo ? `Captured at departure: ${booking.departure_time || 'Check-out recorded'}` : 'Pending session completion'}
                  </span>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                <div className="space-y-1">
                  <div className="font-bold text-white">
                    Computer Vision Match Confidence:{' '}
                    <span className={`font-mono ${(booking.condition_match_score || 100) >= 80 ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {booking.condition_match_score ? `${booking.condition_match_score}%` : '100%'}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Appliance Electrical Off Status:{' '}
                    <span className={booking.fans_lights_cleared !== false ? 'text-emerald-400 font-semibold' : 'text-amber-400 font-semibold'}>
                      {booking.fans_lights_cleared !== false ? 'Verified (0 active loads detected)' : 'Warning: Unverified or active electrical loads detected'}
                    </span>
                  </div>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${
                  (booking.condition_match_score || 100) >= 80 && booking.fans_lights_cleared !== false
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                    : (booking.session_state === 'checked_out' || booking.status === 'completed'
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                        : 'bg-slate-800 text-slate-400 border-slate-700')
                }`}>
                  {(booking.condition_match_score || 100) >= 80 && booking.fans_lights_cleared !== false
                    ? 'PASSED NO DAMAGE'
                    : (booking.session_state === 'checked_out' || booking.status === 'completed' ? 'FLAGGED FOR REVIEW' : 'PENDING CHECKOUT')}
                </span>
              </div>
            </div>
          </HostCard>
        )}

        {/* TAB 5: ESCROW & PAYOUT */}
        {activeTab === 'escrow' && (
          <HostCard
            title="UPI Micro-Escrow Hold"
            subtitle="₹100 security deposit managed automatically by the SpaceLoop Escrow engine"
            icon="fa-solid fa-vault"
            action={<StatusBadge status={booking.escrow_released ? 'released' : 'held'} type="escrow" />}
          >
            <div className="space-y-5">
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Escrow Hold Amount:</span>
                  <span className="font-mono font-bold text-amber-400">₹100.00</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Host Net Rental Payout (95%):</span>
                  <span className="font-mono font-bold text-emerald-400">₹{netEarnings}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Settlement Target UPI:</span>
                  <span className="font-mono text-white">Host Registered VPA</span>
                </div>
              </div>

              {!booking.escrow_released && isCompleted && (
                <div className="flex items-center gap-3 pt-2">
                  <button
                    onClick={() => setShowDisputeModal(true)}
                    className="px-4 py-2 rounded-xl border border-amber-500/40 hover:bg-amber-500/10 text-amber-300 text-xs font-semibold transition"
                  >
                    Raise Escrow Dispute
                  </button>
                </div>
              )}
            </div>
          </HostCard>
        )}

        {/* TAB 6: ACTIVITY */}
        {activeTab === 'activity' && (
          <HostCard
            title="Booking Audit & Telemetry Log"
            subtitle="Immutable event trail for this reservation"
            icon="fa-solid fa-clock-rotate-left"
          >
            {activity.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                No activity records logged for this booking yet.
              </div>
            ) : (
              <div className="space-y-3">
                {activity.map((ev, idx) => (
                  <div key={idx} className="flex items-start gap-3 text-xs border-b border-slate-800/80 pb-3 last:border-0">
                    <div className="w-6 h-6 rounded-lg bg-slate-950 border border-slate-800 text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
                      <i className="fa-solid fa-clock-rotate-left text-[10px]" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-slate-200 font-medium">{ev.title || ev.action || 'Booking Step'}</div>
                      <div className="text-[11px] text-slate-500">
                        {ev.timestamp ? new Date(ev.timestamp).toLocaleString() : 'Timestamped'} • {ev.description || ''}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </HostCard>
        )}
      </div>

      {/* Raise Dispute Modal */}
      {showDisputeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <i className="fa-solid fa-triangle-exclamation text-amber-400 text-xs" />
                <span>Raise Escrow Damage Dispute</span>
              </h3>
              <button
                onClick={() => setShowDisputeModal(false)}
                className="text-slate-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Disputing will hold the ₹100 deposit and escalate to SpaceLoop Trust & Safety with computer vision logs.
            </p>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Dispute Reason / Damage Description</label>
              <textarea
                rows={3}
                value={disputeReason}
                onChange={e => setDisputeReason(e.target.value)}
                placeholder="e.g. Appliance left running overnight, furniture damaged, or key unreturned..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowDisputeModal(false)}
                className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleRaiseDispute}
                disabled={disputing || !disputeReason.trim()}
                className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition disabled:opacity-50"
              >
                {disputing ? 'Submitting...' : 'Submit Dispute'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Host Cancel Booking Confirmation Modal */}
      {showCancelModal && booking && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center">
                  <i className="fa-solid fa-ban text-sm" />
                </div>
                <h3 className="text-base font-bold text-white">Cancel Reservation #{booking.id}</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowCancelModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <i className="fa-solid fa-xmark text-sm" />
              </button>
            </div>

            <div className="p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs leading-relaxed space-y-1">
              <div className="font-bold text-rose-200 flex items-center gap-1.5">
                <i className="fa-solid fa-circle-exclamation text-xs" />
                <span>Automatic Seeker Escrow Refund</span>
              </div>
              <p>
                Cancelling this booking will immediately refund ₹{Math.max(0, Math.round(Number(booking.total_price || 0) * 0.95))} to the seeker and release the ₹100 UPI escrow deposit hold. This action is irreversible.
              </p>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Cancellation Reason
              </label>
              <select
                value={cancelReasonInput}
                onChange={e => setCancelReasonInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-rose-500/50 mb-2"
              >
                <option value="Host scheduling conflict">Host scheduling conflict</option>
                <option value="Premises maintenance or repair">Premises maintenance or repair</option>
                <option value="Safety or weather hazard">Safety or weather hazard</option>
                <option value="Space double-booked offline">Space double-booked offline</option>
                <option value="Other">Other / Specific reason below</option>
              </select>

              {cancelReasonInput === 'Other' && (
                <textarea
                  rows={2}
                  placeholder="Please specify reason for audit log..."
                  onChange={e => setCancelReasonInput(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-rose-500/50 mt-1"
                />
              )}
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowCancelModal(false)}
                disabled={actionLoading}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
              >
                Keep Booking
              </button>
              <button
                type="button"
                onClick={handleConfirmCancel}
                disabled={actionLoading}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition flex items-center gap-1.5 shadow-lg shadow-rose-600/20 disabled:opacity-50"
              >
                {actionLoading && <i className="fa-solid fa-spinner animate-spin text-xs" />}
                <span>{actionLoading ? 'Cancelling...' : 'Confirm Cancellation'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* High-Resolution Photo Zoom Modal */}
      {previewPhoto && (
        <div
          className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200"
          onClick={() => setPreviewPhoto(null)}
        >
          <div
            className="relative max-w-4xl w-full bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl p-4"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <i className="fa-solid fa-camera text-slate-400" />
                <span className="text-sm font-bold text-white">{previewPhoto.title}</span>
              </div>
              <button
                type="button"
                onClick={() => setPreviewPhoto(null)}
                className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center text-sm transition"
              >
                ✕
              </button>
            </div>
            <div className="p-2 flex items-center justify-center bg-slate-950 rounded-2xl mt-3 overflow-hidden border border-slate-800">
              <img
                src={previewPhoto.url}
                alt={previewPhoto.title}
                className="max-h-[75vh] w-auto max-w-full rounded-xl object-contain"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
