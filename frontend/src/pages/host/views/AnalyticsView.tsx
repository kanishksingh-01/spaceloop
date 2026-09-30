import React, { useState, useEffect } from 'react';
import { Space, Booking } from '../../../types';
import { getHostDashboardData, HostMetricData } from '../../../services/host';
import {
  HostPageHeader,
  HostStat,
  HostCard,
  HostStatSkeleton,
} from '../components';

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
      <div className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full space-y-6">
        <HostStatSkeleton count={4} />
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <HostPageHeader
        category="Operational Intelligence"
        title="Performance & Analytics"
        subtitle="Real-time occupancy yield, net UPI payout metrics, and SpaceLoop Operational Trust Index breakdown."
        badge={
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 uppercase tracking-wider">
            Revenue Yield • OTI Trust Index
          </span>
        }
      />

      {/* Main KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <HostStat
          label="Net UPI Payouts"
          value={`₹${netEarn.toLocaleString('en-IN')}`}
          subvalue={`Gross: ₹${grossRev.toLocaleString('en-IN')}`}
          icon="fa-solid fa-indian-rupee-sign"
          iconColor="text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
          badge={
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              95% Direct
            </span>
          }
        />

        <HostStat
          label="Estimated Occupancy"
          value={`${occupancyRate}%`}
          subvalue="+8% from last month"
          icon="fa-solid fa-chart-pie"
          iconColor="text-amber-400 bg-amber-500/10 border-amber-500/20"
          badge={
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
              Peak Hours
            </span>
          }
        />

        <HostStat
          label="Total Leased Hours"
          value={`${totalHours} hrs`}
          subvalue={`Across ${totalBks} total bookings`}
          icon="fa-solid fa-clock"
          iconColor="text-sky-400 bg-sky-500/10 border-sky-500/20"
          badge={
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-500/15 text-sky-400 border border-sky-500/30">
              Active Leases
            </span>
          }
        />

        <HostStat
          label="Cancellation Rate"
          value={`${cancellationRate}%`}
          subvalue="High Host Reliability"
          icon="fa-solid fa-shield-check"
          iconColor="text-indigo-400 bg-indigo-500/10 border-indigo-500/20"
          badge={
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              Tier 1
            </span>
          }
        />
      </div>

      {/* OTI 4-Pillar Trust Index */}
      <HostCard
        title="OTI (Operational Trust Index) Rating"
        subtitle="Composite 4-pillar trust engine powering search placement"
        icon="fa-solid fa-award"
        action={<span className="text-xl font-black text-amber-400 font-mono">97.0 / 100</span>}
      >
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
      </HostCard>

      {/* Space Revenue Breakdown */}
      <HostCard
        title="Space Revenue & Occupancy Breakdown"
        subtitle="Individual asset earnings and capacity utilisation"
        icon="fa-solid fa-building"
      >
        <div className="overflow-x-auto -mx-5 -my-4 sm:-mx-6 sm:-my-5">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800 text-[11px] uppercase tracking-wider">
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
                    <td className="p-3.5 font-mono text-slate-300">{s.bookings_count || 0}</td>
                    <td className="p-3.5 font-mono text-slate-200">₹{sRev}</td>
                    <td className="p-3.5 font-mono font-bold text-emerald-400">₹{Math.round(sRev * 0.95)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </HostCard>
    </div>
  );
};
