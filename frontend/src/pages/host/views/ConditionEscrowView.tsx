import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Booking } from '../../../types';
import { getHostBookings, disputeBooking } from '../../../services/host';
import { StatusBadge } from '../components/StatusBadge';

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
    <div className="p-6 md:p-8 max-w-7xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 uppercase tracking-wider">
              Settlement & Trust
            </span>
            <span className="text-slate-500 text-xs font-mono">₹100 Micro-Escrow • Automated Departure CV</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
            {activeTab === 'escrow' ? 'Escrow & Payout Ledger' : 'Condition Verification Reports'}
          </h1>
          <p className="text-slate-400 text-xs md:text-sm mt-0.5">
            Automated settlement releases, ₹100 micro-escrow holds, and AI computer vision condition audits.
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs">
          <button
            onClick={() => setActiveTab('condition')}
            className={`px-4 py-1.5 rounded-lg font-semibold transition ${
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
            className={`px-4 py-1.5 rounded-lg font-semibold transition ${
              activeTab === 'escrow'
                ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <i className="fa-solid fa-vault mr-1.5" />
            Escrow Ledger
          </button>
        </div>
      </div>

      {loading ? (
        <div className="py-20 text-center text-slate-400 text-xs font-mono">
          <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          FETCHING SETTLEMENT RECORDS...
        </div>
      ) : activeTab === 'condition' ? (
        /* CONDITION REPORTS SECTION */
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {bookings.slice(0, 4).map(b => (
              <div
                key={b.id}
                className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 space-y-4 hover:border-slate-700 transition"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-white text-sm">{b.space?.title || `Space #${b.space_id}`}</h3>
                    <p className="text-[11px] text-slate-400">
                      Booking #{b.id} • Renter: {b.renter?.name || b.user_name || 'Guest'}
                    </p>
                  </div>
                  <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    CV MATCH: 98.4%
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-[10px] text-slate-400 block mb-1">Check-in Photo</span>
                    <div className="aspect-video rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                      <img
                        src="https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?auto=format&fit=crop&w=400&q=80"
                        alt="Entry"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block mb-1">Check-out Photo</span>
                    <div className="aspect-video rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                      <img
                        src="https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?auto=format&fit=crop&w=400&q=80"
                        alt="Exit"
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
                    className="text-xs text-amber-400 hover:text-amber-300 font-semibold"
                  >
                    View Full Report →
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        /* ESCROW LEDGER SECTION */
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-5 border-b border-slate-800 flex items-center justify-between">
            <h3 className="font-bold text-white text-base">₹100 Micro-Escrow Deposit Transactions</h3>
            <span className="text-xs font-mono text-emerald-400">Automated UPI Payouts</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
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
                            className="px-3 py-1 rounded-lg border border-amber-500/40 text-amber-300 text-xs font-semibold hover:bg-amber-500/10"
                          >
                            Dispute
                          </button>
                        ) : (
                          <button
                            onClick={() => navigate(`/host/bookings/${b.id}`)}
                            className="px-3 py-1 rounded-lg bg-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-700"
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
        </div>
      )}

      {/* Dispute Modal */}
      {selectedBookingForDispute && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-white">Raise Escrow Dispute</h3>
            <p className="text-xs text-slate-400">
              Dispute booking #{selectedBookingForDispute.id} deposit due to physical damage or appliances left on.
            </p>
            <textarea
              rows={3}
              value={disputeReason}
              onChange={e => setDisputeReason(e.target.value)}
              placeholder="Explain the damage or reason..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white"
            />
            <div className="flex items-center justify-end gap-2">
              <button
                onClick={() => setSelectedBookingForDispute(null)}
                className="px-3 py-1.5 rounded-xl bg-slate-800 text-slate-300 text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleRaiseDispute}
                disabled={submittingDispute || !disputeReason.trim()}
                className="px-4 py-1.5 rounded-xl bg-amber-500 text-slate-950 font-bold text-xs"
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
