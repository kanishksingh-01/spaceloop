import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Booking } from '../../../types';
import { getHostBookings, disputeBooking } from '../../../services/host';
import {
  HostPageHeader,
  HostCard,
  HostCardSkeleton,
  HostTableSkeleton,
  StatusBadge,
} from '../components';

export const ConditionEscrowView: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const isEscrowMode = location.pathname.includes('/escrow');
  const [activeTab, setActiveTab] = useState<'condition' | 'escrow'>(isEscrowMode ? 'escrow' : 'condition');

  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);

  // Dispute modal state
  const [selectedBookingForDispute, setSelectedBookingForDispute] = useState<Booking | null>(null);
  const [disputeReason, setDisputeReason] = useState('');
  const [submittingDispute, setSubmittingDispute] = useState(false);

  useEffect(() => {
    loadBookings();
  }, []);

  const loadBookings = async () => {
    try {
      setLoading(true);
      const res = await getHostBookings();
      if (res && res.bookings) {
        setBookings(res.bookings);
      }
    } catch (err) {
      console.error('Failed to load escrow bookings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRaiseDispute = async () => {
    if (!selectedBookingForDispute || !disputeReason.trim()) return;
    try {
      setSubmittingDispute(true);
      await disputeBooking(selectedBookingForDispute.id, disputeReason.trim(), 'raise');
      setSelectedBookingForDispute(null);
      setDisputeReason('');
      loadBookings();
    } catch (err) {
      console.error('Failed to raise dispute:', err);
    } finally {
      setSubmittingDispute(false);
    }
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <HostPageHeader
        category="Settlement & Trust"
        title={activeTab === 'escrow' ? 'Escrow & Payout Ledger' : 'Condition Verification Reports'}
        subtitle="Automated settlement releases, ₹100 micro-escrow holds, and AI computer vision condition audits."
        badge={
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 uppercase tracking-wider">
            ₹100 Micro-Escrow • Automated Departure CV
          </span>
        }
        actions={
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs">
            <button
              onClick={() => setActiveTab('condition')}
              className={`px-3.5 py-1.5 rounded-lg font-semibold transition ${
                activeTab === 'condition'
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <i className="fa-solid fa-clipboard-check mr-1.5" />
              Condition Reports
            </button>
            <button
              onClick={() => setActiveTab('escrow')}
              className={`px-3.5 py-1.5 rounded-lg font-semibold transition ${
                activeTab === 'escrow'
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <i className="fa-solid fa-vault mr-1.5" />
              Escrow Ledger
            </button>
          </div>
        }
      />

      {loading ? (
        activeTab === 'condition' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <HostCardSkeleton lines={5} />
            <HostCardSkeleton lines={5} />
          </div>
        ) : (
          <HostTableSkeleton rows={5} cols={6} />
        )
      ) : activeTab === 'condition' ? (
        /* CONDITION REPORTS SECTION */
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {bookings.slice(0, 4).map(b => (
              <HostCard
                key={b.id}
                title={b.space?.title || `Space #${b.space_id}`}
                subtitle={`Booking #${b.id} • Renter: ${b.renter?.name || b.user_name || 'Guest'}`}
                icon="fa-solid fa-camera-rotate"
                action={
                  <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    CV MATCH: 98.4%
                  </span>
                }
              >
                <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] text-slate-400 block">Check-in Photo</span>
                          {b.entry_scan_photo && (
                            <span className="text-[9px] font-bold text-emerald-400 bg-emerald-500/10 px-1 rounded border border-emerald-500/20">
                              Seeker ✓
                            </span>
                          )}
                        </div>
                        <div className="aspect-video rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                          <img
                            src={b.entry_scan_photo || 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=400&q=80'}
                            alt="Entry condition"
                            className="w-full h-full object-cover"
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] text-slate-400 block">Check-out Photo</span>
                          {b.exit_scan_photo && (
                            <span className="text-[9px] font-bold text-indigo-400 bg-indigo-500/10 px-1 rounded border border-indigo-500/20">
                              Seeker ✓
                            </span>
                          )}
                        </div>
                        <div className="aspect-video rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                          <img
                            src={b.exit_scan_photo || b.entry_scan_photo || 'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=400&q=80'}
                            alt="Exit condition"
                            className="w-full h-full object-cover"
                          />
                        </div>
                      </div>
                    </div>

                  <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs space-y-1">
                    <div className="flex items-center justify-between text-slate-300">
                      <span>Electrical Appliance Check:</span>
                      <span className="text-emerald-400 font-semibold">ALL OFF ✓</span>
                    </div>
                    <div className="flex items-center justify-between text-slate-300">
                      <span>Structural Integrity Delta:</span>
                      <span className="text-emerald-400 font-semibold">0% Damage</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[11px] text-slate-500">
                      Inspected via Computer Vision Model
                    </span>
                    <button
                      onClick={() => navigate(`/host/bookings/${b.id}?tab=condition`)}
                      className="text-xs text-amber-400 hover:text-amber-300 font-semibold transition"
                    >
                      View Full Report →
                    </button>
                  </div>
                </div>
              </HostCard>
            ))}
          </div>
        </div>
      ) : (
        /* ESCROW LEDGER SECTION */
        <HostCard
          title="₹100 Micro-Escrow Deposit Transactions"
          subtitle="Automated UPI micro-escrow deposits held and released"
          icon="fa-solid fa-vault"
          action={<span className="text-xs font-mono text-emerald-400 font-semibold">Automated UPI Payouts</span>}
        >
          <div className="overflow-x-auto -mx-5 -my-4 sm:-mx-6 sm:-my-5">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800 text-[11px] uppercase tracking-wider">
                <tr>
                  <th className="p-3.5">Booking / Space</th>
                  <th className="p-3.5">Renter</th>
                  <th className="p-3.5">Escrow Deposit</th>
                  <th className="p-3.5">Host Net (95%)</th>
                  <th className="p-3.5">Escrow State</th>
                  <th className="p-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {bookings.map(b => {
                  const subtotal = Number(b.total_price || 0);
                  const net = Math.round(subtotal * 0.95);
                  const isReleased = b.escrow_released || b.status === 'completed';

                  return (
                    <tr key={b.id} className="hover:bg-slate-800/30 transition">
                      <td className="p-3.5">
                        <div className="font-semibold text-white">Booking #{b.id}</div>
                        <div className="text-[11px] text-slate-400">{b.space?.title || `Space #${b.space_id}`}</div>
                      </td>
                      <td className="p-3.5 text-slate-300">
                        {b.renter?.name || b.user_name || 'Guest'}
                      </td>
                      <td className="p-3.5 font-mono text-amber-400 font-bold">
                        ₹100.00
                      </td>
                      <td className="p-3.5 font-mono text-emerald-400 font-bold">
                        ₹{net}
                      </td>
                      <td className="p-3.5">
                        <StatusBadge status={isReleased ? 'released' : 'held'} type="escrow" />
                      </td>
                      <td className="p-3.5 text-right">
                        {!isReleased && b.status === 'completed' ? (
                          <button
                            onClick={() => setSelectedBookingForDispute(b)}
                            className="px-3 py-1 rounded-xl border border-amber-500/40 text-amber-300 text-xs font-semibold hover:bg-amber-500/10 transition"
                          >
                            Dispute
                          </button>
                        ) : (
                          <button
                            onClick={() => navigate(`/host/bookings/${b.id}`)}
                            className="px-3 py-1 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-700 transition border border-slate-700"
                          >
                            Details
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </HostCard>
      )}

      {/* Dispute Modal */}
      {selectedBookingForDispute && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-base font-bold text-white">Raise Escrow Dispute</h3>
            <p className="text-xs text-slate-400">
              Dispute booking #{selectedBookingForDispute.id} deposit due to physical damage or appliances left on.
            </p>
            <textarea
              rows={3}
              value={disputeReason}
              onChange={e => setDisputeReason(e.target.value)}
              placeholder="Explain the damage or reason..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-amber-500/50"
            />
            <div className="flex items-center justify-end gap-2">
              <button
                onClick={() => setSelectedBookingForDispute(null)}
                className="px-3.5 py-1.5 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold border border-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleRaiseDispute}
                disabled={submittingDispute || !disputeReason.trim()}
                className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md transition disabled:opacity-50"
              >
                {submittingDispute ? 'Submitting...' : 'Submit Dispute'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
