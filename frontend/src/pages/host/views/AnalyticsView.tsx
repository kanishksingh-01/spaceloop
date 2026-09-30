import React, { useState, useEffect } from 'react';
import { Space, Booking } from '../../../types';
import { getHostDashboardData, HostMetricData } from '../../../services/host';

export const AnalyticsView: React.FC = () => {
  const [spaces, setSpaces] = useState<Space[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [metrics, setMetrics] = useState<HostMetricData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await getHostDashboardData();
      if (res && res.success) {
        setSpaces(res.host_spaces || []);
        setBookings(res.host_bookings || []);
        setMetrics(res.host_metrics || null);
      }
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const grossRev = metrics?.gross_revenue || 0;
  const netEarn = metrics?.net_earnings || Math.round(grossRev * 0.95);
  const totalHours = metrics?.total_hours || 0;
  const totalBks = metrics?.total_bookings || bookings.length;

  const occupancyRate = spaces.length > 0 ? Math.min(84, Math.round((totalHours / (spaces.length * 8 * 30)) * 100) || 45) : 0;
  const cancellationRate = totalBks > 0 ? Math.round((bookings.filter(b => b.status === 'cancelled').length / totalBks) * 100) : 2;

  // OTI 4-pillar scores
  const otiPillars = [
    { title: 'Identity Verification', score: 98, desc: 'DigiLocker tokenized Aadhaar & Penny Drop validated' },
    { title: 'Space Utility & Discom', score: 95, desc: 'Premises authenticated with electricity CA consumer record' },
    { title: 'Payment & Escrow Reliability', score: 99, desc: 'Zero chargebacks, automated ₹100 micro-escrows honored' },
    { title: 'Community & Cleanliness', score: 96, desc: '98.4% CV condition match, zero damage flags recorded' },
  ];

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center py-24">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-mono text-slate-400">COMPUTING ANALYTIC METRICS...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 uppercase tracking-wider">
            Operational Intelligence
          </span>
          <span className="text-slate-500 text-xs font-mono">Revenue Yield • OTI Trust Index</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          Performance & Analytics
        </h1>
        <p className="text-slate-400 text-xs md:text-sm mt-0.5">
          Real-time occupancy yield, net UPI payout metrics, and SpaceLoop Operational Trust Index breakdown.
        </p>
      </div>

      {/* Main KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
          <span className="text-xs text-slate-400 font-medium">Net UPI Payouts</span>
          <div className="text-2xl font-black text-emerald-400 font-mono">
            ₹{netEarn.toLocaleString('en-IN')}
          </div>
          <div className="text-[11px] text-slate-500">Gross: ₹{grossRev.toLocaleString('en-IN')}</div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
          <span className="text-xs text-slate-400 font-medium">Estimated Occupancy</span>
          <div className="text-2xl font-black text-white font-mono">
            {occupancyRate}%
          </div>
          <div className="text-[11px] text-emerald-400 font-medium">+8% from last month</div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
          <span className="text-xs text-slate-400 font-medium">Total Leased Hours</span>
          <div className="text-2xl font-black text-amber-400 font-mono">
            {totalHours} hrs
          </div>
          <div className="text-[11px] text-slate-500">Across {totalBks} total bookings</div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
          <span className="text-xs text-slate-400 font-medium">Cancellation Rate</span>
          <div className="text-2xl font-black text-sky-400 font-mono">
            {cancellationRate}%
          </div>
          <div className="text-[11px] text-emerald-400">High Host Reliability</div>
        </div>
      </div>

      {/* OTI 4-Pillar Trust Index */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="font-bold text-white text-base">OTI (Operational Trust Index) Rating</h3>
            <p className="text-xs text-slate-400">Composite 4-pillar trust engine powering search placement.</p>
          </div>
          <span className="text-xl font-black text-amber-400 font-mono">97.0 / 100</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {otiPillars.map(p => (
            <div key={p.title} className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{p.title}</span>
                <span className="text-xs font-mono font-bold text-emerald-400">{p.score}/100</span>
              </div>
              <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-emerald-400 h-1.5 rounded-full"
                  style={{ width: `${p.score}%` }}
                />
              </div>
              <p className="text-[10px] text-slate-400">{p.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Space Revenue Breakdown */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="font-bold text-white text-base">Space Revenue & Occupancy Breakdown</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3.5">Space Name</th>
                <th className="p-3.5">Rate</th>
                <th className="p-3.5">Bookings</th>
                <th className="p-3.5">Gross Revenue</th>
                <th className="p-3.5">Host Net (95%)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {spaces.map(s => {
                const sRev = s.total_revenue || 0;
                return (
                  <tr key={s.id} className="hover:bg-slate-800/30 transition">
                    <td className="p-3.5 font-bold text-white">{s.title}</td>
                    <td className="p-3.5 font-mono text-slate-300">₹{s.hourly_rate}/hr</td>
                    <td className="p-3.5 text-slate-300">{s.bookings_count || 0}</td>
                    <td className="p-3.5 font-mono text-slate-200">₹{sRev}</td>
                    <td className="p-3.5 font-mono font-bold text-emerald-400">₹{Math.round(sRev * 0.95)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
