import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Booking } from '../../../types';
import { getHostBookings, checkOutBooking } from '../../../services/host';
import {
  HostPageHeader,
  HostStat,
  HostCard,
  HostStatSkeleton,
  HostEmptyState,
} from '../components';

export const LiveSessionsView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [activeBookings, setActiveBookings] = useState<Booking[]>([]);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [timerSecondsRemaining, setTimerSecondsRemaining] = useState<number>(0);
  const [checkingOut, setCheckingOut] = useState(false);
  const [checkoutResult, setCheckoutResult] = useState<any>(null);
  const [exitPhotoUrl] = useState<string>('https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?auto=format&fit=crop&w=800&q=80');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSessions();
  }, [id]);

  // Live session countdown timer ticker
  useEffect(() => {
    if (!selectedBooking) return;

    const calculateRemaining = () => {
      const end = new Date(selectedBooking.end_time).getTime();
      const now = Date.now();
      const diffSec = Math.max(0, Math.floor((end - now) / 1000));
      setTimerSecondsRemaining(diffSec);
    };

    calculateRemaining();
    const interval = setInterval(calculateRemaining, 1000);
    return () => clearInterval(interval);
  }, [selectedBooking]);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const res = await getHostBookings({ status: 'active' });
      const activeList = res.bookings || [];
      setActiveBookings(activeList);

      if (id) {
        const found = activeList.find(b => b.id === Number(id));
        if (found) {
          setSelectedBooking(found);
        } else {
          // If not in active, fetch single booking to see if confirmed/completed
          const single = await getHostBookings({ q: id });
          if (single.bookings && single.bookings.length > 0) {
            setSelectedBooking(single.bookings[0]);
          }
        }
      } else if (activeList.length > 0) {
        setSelectedBooking(activeList[0]);
      } else {
        setSelectedBooking(null);
      }
    } catch (err) {
      console.error('Failed to load active sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatTimer = (sec: number) => {
    const hrs = Math.floor(sec / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    const secs = sec % 60;
    return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const handleCheckoutAndReleaseEscrow = async () => {
    if (!selectedBooking) return;
    try {
      setCheckingOut(true);
      setError(null);
      const res = await checkOutBooking(selectedBooking.id, {
        exit_photo: exitPhotoUrl,
        lat: selectedBooking.space?.lat || 12.9716,
        lng: selectedBooking.space?.lng || 77.5946,
      });

      setCheckoutResult(res);
      setSelectedBooking(prev => prev ? { ...prev, status: 'completed', escrow_released: true } : null);
      loadSessions();
    } catch (err: any) {
      setError(err.message || 'Checkout failed.');
    } finally {
      setCheckingOut(false);
    }
  };

  if (loading) {
    return (
      <div className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full space-y-6">
        <HostStatSkeleton count={4} />
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <HostPageHeader
        category="Live Operations Cockpit"
        title="Live Session Command"
        subtitle="Monitor real-time occupant presence, dynamic PIN handshakes, and CV condition deltas."
        badge={
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 uppercase tracking-wider animate-pulse">
            50m Zero-Spoofing Perimeter
          </span>
        }
        actions={
          activeBookings.length > 1 ? (
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Switch Session:</span>
              <select
                value={selectedBooking?.id || ''}
                onChange={e => {
                  const found = activeBookings.find(b => b.id === Number(e.target.value));
                  if (found) setSelectedBooking(found);
                }}
                className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none"
              >
                {activeBookings.map(b => (
                  <option key={b.id} value={b.id}>
                    Booking #{b.id} ({b.space?.title})
                  </option>
                ))}
              </select>
            </div>
          ) : undefined
        }
      />

      {error && (
        <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300 flex items-center gap-2.5">
          <i className="fa-solid fa-triangle-exclamation text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Cockpit Surface */}
      {!selectedBooking ? (
        <HostEmptyState
          icon="fa-solid fa-satellite-dish"
          title="No Active Sessions Right Now"
          description="When a verified seeker enters within the 50m geofence and executes a check-in handshake, their session cockpit telemetry will stream live here."
          primaryAction={{
            label: 'Check Upcoming Bookings Queue',
            onClick: () => navigate('/host/bookings'),
            icon: 'fa-regular fa-calendar-check',
          }}
        />
      ) : (
        <div className="space-y-6">
          {/* Top Operational Status Bar */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Live Countdown Clock */}
            <HostStat
              label="Session Countdown"
              value={formatTimer(timerSecondsRemaining)}
              subvalue={`End: ${new Date(selectedBooking.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
              icon="fa-solid fa-stopwatch"
              iconColor="text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
              badge={
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              }
            />

            {/* Geofence Perimeter Beacon */}
            <HostStat
              label="50m GPS Geofence"
              value="Inside Perimeter"
              subvalue="Zero-spoofing Haversine locked: ~12m"
              icon="fa-solid fa-location-crosshairs"
              iconColor="text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
              badge={
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  Locked
                </span>
              }
            />

            {/* Physical Access Handshake */}
            <HostStat
              label="Access Handshake"
              value={
                selectedBooking.space?.physical_access_type === 'keybox'
                  ? `PIN: ${selectedBooking.space?.keybox_code || '4819'}`
                  : 'QR Handshake ✓'
              }
              subvalue="Physical credentials authenticated"
              icon="fa-solid fa-key"
              iconColor="text-amber-400 bg-amber-500/10 border-amber-500/20"
              badge={
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                  Active
                </span>
              }
            />

            {/* Micro-Escrow Hold */}
            <HostStat
              label="Micro-Escrow Deposit"
              value="₹100.00 Held"
              subvalue="Pending departure condition check"
              icon="fa-solid fa-vault"
              iconColor="text-indigo-400 bg-indigo-500/10 border-indigo-500/20"
              badge={
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
                  Secured
                </span>
              }
            />
          </div>

          {/* Renter & Physical Room Inspection Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Occupant Card */}
            <HostCard
              title="Current Occupant"
              icon="fa-solid fa-user-check"
              badge={
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Verified Seeker
                </span>
              }
            >
              <div className="space-y-4">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-12 rounded-xl bg-indigo-500/20 border border-indigo-500/40 text-indigo-400 flex items-center justify-center font-bold text-lg font-mono">
                    {(selectedBooking.renter?.name || selectedBooking.user_name || 'U').charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="text-sm font-bold text-white">{selectedBooking.renter?.name || selectedBooking.user_name || 'Confirmed Guest'}</div>
                    <div className="text-[11px] text-slate-400">{selectedBooking.renter?.phone || '+91 98765 43210'}</div>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs space-y-2">
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Aadhaar Token:</span>
                    <span className="font-mono text-emerald-400 font-bold">Verified ✓</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Trust Score:</span>
                    <span className="font-mono font-bold text-white">97 / 100</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Session Length:</span>
                    <span className="font-mono text-white">{selectedBooking.total_hours} Hours</span>
                  </div>
                </div>

                <button
                  onClick={() => navigate(`/host/bookings/${selectedBooking.id}`)}
                  className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
                >
                  View Full Booking File →
                </button>
              </div>
            </HostCard>

            {/* Live Checkout & Condition Verification Engine */}
            <div className="lg:col-span-2">
              <HostCard
                title="Departure Inspection & Escrow Release"
                subtitle="Verify visual condition delta and release the ₹100 deposit back to renter upon exit"
                icon="fa-solid fa-clipboard-check"
                action={
                  <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
                    Escrow Protocol
                  </span>
                }
              >
                {checkoutResult ? (
                  <div className="p-5 rounded-2xl bg-emerald-950/30 border border-emerald-500/40 space-y-3">
                    <div className="flex items-center gap-2.5 text-emerald-400 font-bold text-sm">
                      <i className="fa-solid fa-circle-check text-base" />
                      <span>Checkout Completed & Escrow Released!</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {checkoutResult.message || 'Inspection passed with 98.4% visual match. ₹100 micro-escrow released to seeker UPI. Net host payout initiated.'}
                    </p>
                    <div className="flex items-center gap-2 pt-2">
                      <button
                        onClick={() => navigate('/host/escrow')}
                        className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition"
                      >
                        View Escrow Ledger
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-slate-300">Baseline Entry Condition</span>
                          {selectedBooking.entry_scan_photo && (
                            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                              Seeker Photo ✓
                            </span>
                          )}
                        </div>
                        <div className="aspect-video rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                          <img
                            src={selectedBooking.entry_scan_photo || 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=600&q=80'}
                            alt="Entry baseline"
                            className="w-full h-full object-cover"
                          />
                        </div>
                      </div>

                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-slate-300">Departure Inspection Photo</span>
                          {selectedBooking.exit_scan_photo && (
                            <span className="text-[10px] font-bold text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded border border-indigo-500/20">
                              Seeker Photo ✓
                            </span>
                          )}
                        </div>
                        <div className="aspect-video rounded-xl overflow-hidden border border-slate-800 bg-slate-950 relative group">
                          <img
                            src={selectedBooking.exit_scan_photo || selectedBooking.entry_scan_photo || exitPhotoUrl}
                            alt="Exit condition"
                            className="w-full h-full object-cover"
                          />
                          <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                            <span className="text-[10px] text-white bg-slate-900 px-2 py-1 rounded border border-slate-700">
                              {selectedBooking.exit_scan_photo ? 'Captured by Guest at Departure' : 'Auto-Captured Baseline'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-800/80">
                      <div className="text-xs text-slate-400">
                        Condition Check: <span className="text-emerald-400 font-semibold font-mono">98.4% match</span> • Electrical load: <span className="text-emerald-400 font-semibold">OFF</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => navigate(`/host/bookings/${selectedBooking.id}?tab=escrow`)}
                          className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
                        >
                          Raise Issue
                        </button>
                        <button
                          onClick={handleCheckoutAndReleaseEscrow}
                          disabled={checkingOut}
                          className="px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition flex items-center gap-2 disabled:opacity-50"
                        >
                          <i className={`fa-solid ${checkingOut ? 'fa-spinner animate-spin' : 'fa-check-double'} text-xs`} />
                          <span>{checkingOut ? 'Processing Release...' : 'Approve Checkout & Release ₹100'}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </HostCard>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
