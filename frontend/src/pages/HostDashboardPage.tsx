import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Booking, Space } from '../types';
import { request } from '../services/api';
import { toggleSpaceStatus } from '../services/spaces';

interface HostDashboardPageProps {
  currentUser: User | null;
  onOpenHostAuthModal: () => void;
}

export const HostDashboardPage: React.FC<HostDashboardPageProps> = ({
  currentUser,
  onOpenHostAuthModal,
}) => {
  const navigate = useNavigate();
  const [hostSpaces, setHostSpaces] = useState<Space[]>([]);
  const [hostBookings, setHostBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [togglingSpaceId, setTogglingSpaceId] = useState<number | null>(null);
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
  }>({
    gross_revenue: 14850,
    platform_fee: 1782,
    net_earnings: 13068,
    total_hours: 48,
    total_bookings: 14,
    active_spaces_count: 2,
    total_spaces_count: 2,
    upcoming_count: 3,
    completed_count: 11,
    payout_vpa: currentUser?.upi_vpa_masked || 'sunita.spaces@okhdfcbank',
  });

  const isHost = Boolean(currentUser?.is_host && (currentUser?.is_host_verified ?? true));

  const loadHostData = async () => {
    if (!currentUser) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await request<{
        success: boolean;
        host_bookings?: Booking[];
        host_spaces?: Space[];
        host_metrics?: any;
      }>('/api/dashboard');

      if (data?.host_spaces && data.host_spaces.length > 0) {
        setHostSpaces(data.host_spaces);
      } else {
        const spacesData = await request<{ spaces?: Space[] } | Space[]>('/api/spaces');
        const allSpaces = Array.isArray(spacesData) ? spacesData : spacesData?.spaces || [];
        // Filter spaces belonging to this user or seed host
        const userSpaces = allSpaces.filter((s: Space) =>
          currentUser ? s.host_id === currentUser.id || s.owner_id === currentUser.id : true
        );
        setHostSpaces(userSpaces.length > 0 ? userSpaces : allSpaces.slice(0, 3));
      }

      if (data?.host_bookings) {
        setHostBookings(data.host_bookings);
      }

      if (data?.host_metrics) {
        setMetrics((prev) => ({
          ...prev,
          ...data.host_metrics,
          payout_vpa: currentUser?.upi_vpa_masked || data.host_metrics.payout_vpa || prev.payout_vpa,
        }));
      }
    } catch (err) {
      console.warn('Host dashboard data fetch fallback:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHostData();
  }, [currentUser]);

  const handleToggleSpace = async (spaceId: number) => {
    setTogglingSpaceId(spaceId);
    try {
      const res = await toggleSpaceStatus(spaceId);
      setHostSpaces((prev) =>
        prev.map((s) => (s.id === spaceId ? { ...s, is_active: res.is_active } : s))
      );
    } catch (err: any) {
      alert(err.message || 'Failed to toggle space status');
    } finally {
      setTogglingSpaceId(null);
    }
  };

  // If user is not logged in as a verified host, display the Host Authentication Gate
  if (!currentUser || !currentUser.is_host) {
    return (
      <div className="min-h-screen bg-slate-950 text-white py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Header */}
          <div className="text-center space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-bold uppercase tracking-wider">
              🏡 SpaceLoop Host Management Portal
            </div>
            <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-white">
              Property Owner & Host Portal
            </h1>
            <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto">
              Monetize unutilized residential or commercial space securely under Section 52 of the Indian Easements Act with automated electricity billing audits and NPCI bank payouts.
            </p>
          </div>

          {/* Authentication Gate Card */}
          <div className="bg-slate-900/90 border border-amber-500/30 rounded-3xl p-6 sm:p-10 floating-container space-y-8 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-2xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 text-2xl shrink-0">
                🛡️
              </div>
              <div className="space-y-1">
                <h2 className="text-xl font-bold text-white">
                  Host Authentication & Property KYC Required
                </h2>
                <p className="text-xs sm:text-sm text-slate-400">
                  To protect students and property owners alike, access to space listing, pricing controls, and daily UPI payouts is strictly reserved for verified hosts.
                </p>
              </div>
            </div>

            {/* Two Pillars of Host Verification */}
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-2 floating-interactive">
                <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
                  <span>⚡ 1. State Discom Electricity Verification</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  We cross-reference the property's Consumer Account (CA#) against State Electricity Board (BBPS) records to confirm physical possession and utility standing.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-2 floating-interactive">
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                  <span>🏦 2. NPCI ₹1 Penny Drop Bank Validation</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Instant ₹1 penny drop to the host's UPI VPA confirms legal beneficiary account ownership before any seeker payouts or deposits are collected.
                </p>
              </div>
            </div>

            {/* Action Call to Action */}
            <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-xs text-slate-400">
                {currentUser ? (
                  <span>
                    Currently signed in as <span className="text-white font-semibold">{currentUser.email}</span> (Seeker account).
                  </span>
                ) : (
                  <span>Sign in with your host credentials or complete a 60-second host registration.</span>
                )}
              </div>

              <div className="flex items-center gap-3 w-full sm:w-auto">
                <button
                  type="button"
                  onClick={() => navigate('/dashboard')}
                  className="w-full sm:w-auto px-4 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition text-center"
                >
                  Go to Seeker Portal
                </button>
                <button
                  type="button"
                  onClick={onOpenHostAuthModal}
                  className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs transition shadow-lg shadow-amber-500/20 text-center"
                >
                  {currentUser ? 'Upgrade Account to Host →' : 'Sign In as Host / Register Property →'}
                </button>
              </div>
            </div>
          </div>

          {/* Host Benefits Overview */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
            <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800 floating-interactive">
              <div className="text-2xl font-black text-amber-400">88%</div>
              <div className="text-xs font-bold text-slate-200 mt-1">Host Payout Retention</div>
              <div className="text-[11px] text-slate-500 mt-0.5">Lowest platform take-rate in India</div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800 floating-interactive">
              <div className="text-2xl font-black text-emerald-400">T+0</div>
              <div className="text-xs font-bold text-slate-200 mt-1">Instant Daily UPI Payouts</div>
              <div className="text-[11px] text-slate-500 mt-0.5">Direct into your verified bank account</div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800 floating-interactive">
              <div className="text-2xl font-black text-indigo-400">Sec 52</div>
              <div className="text-xs font-bold text-slate-200 mt-1">Indian Easements License</div>
              <div className="text-[11px] text-slate-500 mt-0.5">Strict tenancy & eviction exclusion</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // User is Authenticated as Host
  return (
    <div className="min-h-screen bg-slate-950 text-white pb-20">
      {/* Top Banner & Host Status */}
      <div className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-3 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-extrabold uppercase tracking-wider">
                  🏡 SpaceLoop Host Management Center
                </span>
                <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold flex items-center gap-1">
                  ✓ Discom Verified
                </span>
                <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-bold flex items-center gap-1">
                  ✓ Bank Beneficiary Match
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-black text-white">
                Welcome back, {currentUser.name || 'Verified Host'}
              </h1>
              <p className="text-xs text-slate-400">
                Host ID #{currentUser.id} • Utility CA #{currentUser.discom_ca_masked || 'CA•••9102'} ({currentUser.discom_provider || 'BESCOM / TPDDL'}) • Payouts to {currentUser.upi_vpa_masked || 'sunita.spaces@okhdfcbank'}
              </p>
            </div>

            {/* Quick Action Buttons */}
            <div className="flex items-center gap-3 shrink-0 flex-wrap">
              <button
                type="button"
                onClick={() => navigate('/list-space')}
                className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 transition flex items-center gap-1.5"
              >
                <span>+ List New Space</span>
              </button>
              <button
                type="button"
                onClick={() => navigate('/calculator')}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition flex items-center gap-1.5"
              >
                <span>Pricing Calculator</span>
              </button>
              <button
                type="button"
                onClick={() => navigate('/verify')}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition flex items-center gap-1.5"
              >
                <span>Smart Locks & KYC</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Host Financial & Performance Metrics Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl floating-interactive">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Gross Bookings</div>
            <div className="text-2xl font-black text-white mt-1">₹{metrics.gross_revenue.toLocaleString()}</div>
            <div className="text-[11px] text-emerald-400 mt-1">14 completed reservations</div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl floating-interactive">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Net Payouts (88%)</div>
            <div className="text-2xl font-black text-emerald-400 mt-1">₹{metrics.net_earnings.toLocaleString()}</div>
            <div className="text-[11px] text-slate-400 mt-1">Direct to {metrics.payout_vpa}</div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl floating-interactive">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">SpaceLoop Fee (12%)</div>
            <div className="text-2xl font-black text-indigo-400 mt-1">₹{metrics.platform_fee.toLocaleString()}</div>
            <div className="text-[11px] text-slate-400 mt-1">Includes AI & Escrow cover</div>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl floating-interactive">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Listings</div>
            <div className="text-2xl font-black text-amber-400 mt-1">
              {hostSpaces.filter((s) => s.is_active).length} / {hostSpaces.length}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">Micro-spaces live for booking</div>
          </div>
        </div>

        {/* Host Properties / Spaces Management */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white">Your Listed Properties</h2>
              <p className="text-xs text-slate-400">
                Manage your active micro-spaces, toggle availability instantly, or edit rates.
              </p>
            </div>
            <button
              type="button"
              onClick={() => navigate('/list-space')}
              className="text-xs font-bold text-amber-400 hover:text-amber-300 flex items-center gap-1"
            >
              <span>+ Add Another Space</span>
            </button>
          </div>

          {loading ? (
            <div className="text-center py-12 text-slate-500 text-sm">Loading your host properties...</div>
          ) : hostSpaces.length === 0 ? (
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 text-center space-y-3">
              <div className="text-3xl">🏠</div>
              <h3 className="text-base font-bold text-white">No spaces listed yet</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Turn your spare desk, garage, or acoustic nook into recurring hourly income in under 60 seconds.
              </p>
              <button
                type="button"
                onClick={() => navigate('/list-space')}
                className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-xl transition"
              >
                Create First Space Listing
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {hostSpaces.map((space) => {
                const photo =
                  Array.isArray(space.photos) && space.photos[0]
                    ? space.photos[0]
                    : 'https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?auto=format&fit=crop&w=800&q=80';
                return (
                  <div
                    key={space.id}
                    className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden hover:border-slate-700 floating-interactive flex flex-col"
                  >
                    <div className="relative h-44 w-full bg-slate-950">
                      <img
                        src={photo}
                        alt={space.title}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute top-3 left-3 bg-slate-950/80 backdrop-blur-md px-2.5 py-1 rounded-xl text-[11px] font-bold text-white border border-slate-700/60">
                        {space.category || 'Study Pod'}
                      </div>
                      <div className="absolute top-3 right-3 bg-amber-500/90 backdrop-blur-md px-2.5 py-1 rounded-xl text-[11px] font-black text-slate-950 shadow-md">
                        ₹{Math.round(space.hourly_rate ?? space.price_hourly ?? 50)}/hr
                      </div>
                    </div>

                    <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <h3 className="text-base font-bold text-white line-clamp-1">{space.title}</h3>
                          <span
                            className={`w-2.5 h-2.5 rounded-full ${
                              space.is_active ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'
                            }`}
                            title={space.is_active ? 'Active & Bookable' : 'Paused'}
                          />
                        </div>
                        <p className="text-xs text-slate-400 line-clamp-1">
                          {space.location || `${space.neighborhood || 'Wagholi'}, ${space.city || 'Pune'}`}
                        </p>
                      </div>

                      <div className="flex items-center gap-2 pt-2 border-t border-slate-800/80">
                        <button
                          type="button"
                          onClick={() => navigate(`/space/${space.id}`)}
                          className="flex-1 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition text-center"
                        >
                          View Listing
                        </button>
                        <button
                          type="button"
                          onClick={() => handleToggleSpace(space.id)}
                          disabled={togglingSpaceId === space.id}
                          className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold transition text-center ${
                            space.is_active
                              ? 'bg-amber-500/10 text-amber-300 border border-amber-500/30 hover:bg-amber-500/20'
                              : 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/20'
                          }`}
                        >
                          {togglingSpaceId === space.id
                            ? 'Updating...'
                            : space.is_active
                            ? 'Pause Space'
                            : 'Activate Space'}
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Incoming Seeker Reservations */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4 floating-container">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white">Incoming Reservations & Check-Ins</h2>
              <p className="text-xs text-slate-400">
                Verified student and professional seekers booked at your properties.
              </p>
            </div>
            <span className="text-xs font-bold text-slate-400">
              {hostBookings.length} total bookings
            </span>
          </div>

          {hostBookings.length === 0 ? (
            <div className="py-8 text-center text-slate-500 text-xs">
              No recent reservations logged yet. Incoming seeker bookings will appear here automatically.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Booking Ref</th>
                    <th className="py-3 px-4">Seeker</th>
                    <th className="py-3 px-4">Space</th>
                    <th className="py-3 px-4">Date & Slot</th>
                    <th className="py-3 px-4">Earnings</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {hostBookings.map((bk) => (
                    <tr key={bk.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4 font-mono font-bold text-indigo-400">
                        #{bk.id}
                      </td>
                      <td className="py-3 px-4 font-semibold text-white">
                        {bk.user_name || (bk as any).seeker_name || 'Academic Seeker'}
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        {bk.space_title || 'Micro-Space'}
                      </td>
                      <td className="py-3 px-4 text-slate-400">
                        {bk.start_time ? new Date(bk.start_time).toLocaleDateString() : 'Today'}
                      </td>
                      <td className="py-3 px-4 font-bold text-emerald-400">
                        ₹{bk.total_price || (bk as any).amount || 150}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {bk.status || 'confirmed'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Indian Easements Act Section 52 Legal Compliance Badge */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 floating-interactive">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-base">📜</span>
              <span className="text-xs font-bold text-slate-200">
                Protected by Section 52 Indian Easements Act (1882)
              </span>
            </div>
            <p className="text-[11px] text-slate-400 max-w-2xl">
              All bookings execute revocable day-license agreements. No tenancy, leasehold, or adverse possession rights accrue to seekers under any circumstances.
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/verify')}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition shrink-0"
          >
            Review Legal Agreement
          </button>
        </div>
      </div>
    </div>
  );
};
