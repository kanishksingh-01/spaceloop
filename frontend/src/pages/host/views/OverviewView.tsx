import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Booking, Space, User } from '../../../types';
import { getHostDashboardData, getHostActivity, HostMetricData, HostActivityEvent } from '../../../services/host';
import {
  HostPageHeader,
  HostStat,
  HostCard,
  HostStatSkeleton,
  HostCardSkeleton,
  StatusBadge,
} from '../components';
import { useTranslation } from '../../../i18n';

interface OverviewViewProps {
  currentUser?: User | null;
}

export const OverviewView: React.FC<OverviewViewProps> = () => {
  const navigate = useNavigate();
  const { t, formatCurrency } = useTranslation();

  const [loading, setLoading] = useState(true);
  const [spaces, setSpaces] = useState<Space[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [metrics, setMetrics] = useState<HostMetricData | null>(null);
  const [recentActivity, setRecentActivity] = useState<HostActivityEvent[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [dashRes, actRes] = await Promise.all([
        getHostDashboardData(),
        getHostActivity(),
      ]);

      if (dashRes && dashRes.success) {
        setSpaces(dashRes.host_spaces || []);
        setBookings(dashRes.host_bookings || []);
        setMetrics(dashRes.host_metrics || null);
      }

      if (actRes && actRes.success) {
        setRecentActivity(actRes.events ? actRes.events.slice(0, 6) : []);
      }
    } catch (err) {
      console.error('Failed to load host overview data:', err);
    } finally {
      setLoading(false);
    }
  };

  const activeSession = bookings.find(b => b.status === 'active');
  const pendingBookings = bookings.filter(b => b.status === 'pending');
  const upcomingBookings = bookings.filter(b => b.status === 'confirmed');

  // Space stats
  const publishedSpaces = spaces.filter(s => s.is_active);
  const draftSpaces = spaces.filter(s => !s.is_active);
  const unverifiedSpaces = spaces.filter(s => !s.is_verified);

  if (loading) {
    return (
      <div className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full space-y-6">
        <div className="h-16 w-1/3 bg-slate-900/60 rounded-2xl animate-pulse" />
        <HostStatSkeleton count={4} />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <HostCardSkeleton lines={4} />
            <HostCardSkeleton lines={5} />
          </div>
          <div className="space-y-6">
            <HostCardSkeleton lines={3} />
            <HostCardSkeleton lines={4} />
          </div>
        </div>
      </div>
    );
  }

  const grossRev = metrics?.gross_revenue || 0;
  const netEarn = metrics?.net_earnings || Math.round(grossRev * 0.95);

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-6 max-w-7xl mx-auto w-full space-y-6">
      {/* Top Banner / Welcome & Quick Actions */}
      <HostPageHeader
        category={t('host.hostConsoleCategory')}
        title={t('host.overviewTitle')}
        subtitle={t('host.overviewSubtitle')}
        actions={
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => navigate('/host/spaces/create')}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md shadow-amber-500/20 transition flex items-center gap-1.5"
            >
              <i className="fa-solid fa-plus text-xs" />
              <span>{t('host.addNewSpaceBtn')}</span>
            </button>
            <button
              onClick={() => navigate('/host/calendar')}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition flex items-center gap-1.5"
            >
              <i className="fa-regular fa-calendar text-xs text-amber-400" />
              <span>{t('host.calendar')}</span>
            </button>
            <button
              onClick={() => navigate('/host/activity')}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition flex items-center gap-1.5"
            >
              <i className="fa-solid fa-clock-rotate-left text-xs text-slate-400" />
              <span>{t('host.activityAudit')}</span>
            </button>
          </div>
        }
      />

      {/* KPI Stats Strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <HostStat
          label="Net Earnings"
          value={`₹${netEarn.toLocaleString('en-IN')}`}
          subvalue={`95% direct payout • Gross ₹${grossRev.toLocaleString('en-IN')}`}
          icon="fa-solid fa-indian-rupee-sign"
          iconColor="text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
          badge={
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              Automated UPI
            </span>
          }
        />

        <HostStat
          label="Space Fleet"
          value={spaces.length}
          subvalue={`${publishedSpaces.length} published • ${draftSpaces.length} inactive`}
          icon="fa-solid fa-building"
          iconColor="text-amber-400 bg-amber-500/10 border-amber-500/20"
          badge={
            <span
              className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                unverifiedSpaces.length > 0
                  ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                  : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
              }`}
            >
              {unverifiedSpaces.length > 0 ? `${unverifiedSpaces.length} unverified` : 'All verified'}
            </span>
          }
        />

        <HostStat
          label="Leased Hours"
          value={`${metrics?.total_hours || 0} hrs`}
          subvalue={`${metrics?.total_bookings || bookings.length} bookings completed`}
          icon="fa-solid fa-clock"
          iconColor="text-sky-400 bg-sky-500/10 border-sky-500/20"
          badge={
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-500/15 text-sky-400 border border-sky-500/30">
              Capacity 84%
            </span>
          }
        />

        <HostStat
          label="Action Queue"
          value={pendingBookings.length}
          subvalue={`${upcomingBookings.length} confirmed arrivals scheduled`}
          icon="fa-solid fa-bell"
          iconColor={pendingBookings.length > 0 ? 'text-amber-400 bg-amber-500/10 border-amber-500/20' : 'text-slate-400 bg-slate-800 border-slate-700'}
          badge={
            <span
              className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                pendingBookings.length > 0
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 animate-pulse'
                  : 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
              }`}
            >
              {pendingBookings.length > 0 ? 'Action Needed' : 'All Clear'}
            </span>
          }
        />
      </div>

      {/* Live Session Alert Banner (if active) */}
      {activeSession && (
        <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-950/70 via-slate-900 to-emerald-950/40 border border-emerald-500/40 shadow-xl relative overflow-hidden">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shrink-0 animate-pulse">
                <i className="fa-solid fa-satellite-dish text-base" />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 uppercase tracking-wider animate-pulse">
                    Live Session in Progress
                  </span>
                  <span className="text-xs text-slate-400 font-mono">
                    Booking #{activeSession.id}
                  </span>
                </div>
                <h3 className="text-base font-bold text-white">
                  {activeSession.space?.title || `Space #${activeSession.space_id}`}
                </h3>
                <p className="text-xs text-slate-300 mt-0.5">
                  Occupant: <strong className="text-white">{activeSession.renter?.name || activeSession.user_name || 'Verified Seeker'}</strong> •{' '}
                  ₹100 Micro-Escrow Active • Check-in: {activeSession.arrival_time ? new Date(activeSession.arrival_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Verified'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate(`/host/live-sessions/${activeSession.id}`)}
                className="px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition flex items-center gap-2"
              >
                <i className="fa-solid fa-display text-xs" />
                <span>Open Live Cockpit</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Grid: Pending Action Items & Today's Schedule */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): Pending Approval & Today's Schedule */}
        <div className="lg:col-span-2 space-y-6">
          {/* Pending Approval Section */}
          <HostCard
            title={
              <div className="flex items-center gap-2.5">
                <span>Attention Required</span>
                {pendingBookings.length > 0 && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                    {pendingBookings.length} Pending
                  </span>
                )}
              </div>
            }
            subtitle="Booking requests awaiting host confirmation"
            icon="fa-solid fa-bell"
            iconColor="text-amber-400 bg-amber-500/10 border-amber-500/20"
            action={
              <button
                onClick={() => navigate('/host/bookings?status=pending')}
                className="text-xs text-amber-400 hover:text-amber-300 font-semibold"
              >
                View all pending →
              </button>
            }
          >
            {pendingBookings.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                <i className="fa-solid fa-circle-check text-emerald-400 text-xl mb-2 block" />
                No pending booking requests. All spaces operate automatically!
              </div>
            ) : (
              <div className="space-y-3">
                {pendingBookings.map((b) => (
                  <div
                    key={b.id}
                    className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-amber-500/40 transition"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-white text-xs">
                          {b.space?.title || `Space #${b.space_id}`}
                        </span>
                        <StatusBadge status={b.status} type="booking" />
                      </div>
                      <p className="text-[11px] text-slate-400">
                        Seeker: <strong className="text-slate-300">{b.renter?.name || b.user_name || 'Guest'}</strong> •{' '}
                        {new Date(b.start_time).toLocaleDateString()} at{' '}
                        {new Date(b.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} •{' '}
                        {b.total_hours} hrs (₹{b.total_price})
                      </p>
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-center">
                      <button
                        onClick={() => navigate(`/host/bookings/${b.id}`)}
                        className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs transition"
                      >
                        Review Request
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </HostCard>

          {/* Today's / Upcoming Schedule */}
          <HostCard
            title="Upcoming Operational Schedule"
            subtitle="Confirmed arrivals and booked sessions"
            icon="fa-regular fa-calendar-check"
            iconColor="text-sky-400 bg-sky-500/10 border-sky-500/20"
            action={
              <button
                onClick={() => navigate('/host/calendar')}
                className="text-xs text-sky-400 hover:text-sky-300 font-semibold"
              >
                Calendar view →
              </button>
            }
          >
            {upcomingBookings.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                <i className="fa-regular fa-calendar-xmark text-slate-600 text-xl mb-2 block" />
                No upcoming confirmed sessions for today.
              </div>
            ) : (
              <div className="divide-y divide-slate-800/80">
                {upcomingBookings.slice(0, 5).map((b) => (
                  <div
                    key={b.id}
                    onClick={() => navigate(`/host/bookings/${b.id}`)}
                    className="py-3 flex items-center justify-between gap-3 cursor-pointer group hover:bg-slate-800/40 px-2.5 rounded-xl transition"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-slate-950 border border-slate-800 flex flex-col items-center justify-center text-slate-300 text-[10px] font-mono leading-none">
                        <span className="font-bold text-white text-xs">
                          {new Date(b.start_time).getDate()}
                        </span>
                        <span>{new Date(b.start_time).toLocaleString('en', { month: 'short' })}</span>
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-white group-hover:text-amber-400 transition">
                          {b.space?.title || `Space #${b.space_id}`}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {new Date(b.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -{' '}
                          {new Date(b.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} •{' '}
                          Seeker: {b.renter?.name || b.user_name || 'Confirmed Guest'}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2.5">
                      <span className="text-xs font-mono font-bold text-emerald-400">
                        ₹{b.total_price}
                      </span>
                      <i className="fa-solid fa-chevron-right text-slate-600 text-xs group-hover:text-slate-400 transition" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </HostCard>
        </div>

        {/* Right Column (1 Col): Space Status & Recent Operational Activity */}
        <div className="space-y-6">
          {/* Space Status Overview */}
          <HostCard
            title="Space Fleet Status"
            icon="fa-solid fa-building"
            iconColor="text-amber-400 bg-amber-500/10 border-amber-500/20"
            action={
              <button
                onClick={() => navigate('/host/spaces')}
                className="text-xs text-amber-400 hover:text-amber-300 font-semibold"
              >
                Manage →
              </button>
            }
          >
            <div className="space-y-2.5">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-xs text-slate-300 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
                  Published & Active
                </span>
                <span className="text-xs font-bold text-white font-mono">{publishedSpaces.length}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-xs text-slate-300 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-amber-400 shadow-sm shadow-amber-400/50" />
                  Verification Pending
                </span>
                <span className="text-xs font-bold text-amber-400 font-mono">{unverifiedSpaces.length}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-xs text-slate-300 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-slate-500" />
                  Inactive / Draft
                </span>
                <span className="text-xs font-bold text-slate-400 font-mono">{draftSpaces.length}</span>
              </div>
            </div>

            {unverifiedSpaces.length > 0 && (
              <button
                onClick={() => navigate('/host/verification')}
                className="w-full mt-3 py-2 px-3 rounded-xl bg-amber-500/10 hover:bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs font-semibold transition flex items-center justify-center gap-2"
              >
                <i className="fa-solid fa-shield-halved text-xs" />
                <span>Verify {unverifiedSpaces.length} Spaces via Discom</span>
              </button>
            )}
          </HostCard>

          {/* Recent Operational Activity */}
          <HostCard
            title="Recent Activity"
            icon="fa-solid fa-clock-rotate-left"
            iconColor="text-slate-400 bg-slate-800 border-slate-700"
            action={
              <button
                onClick={() => navigate('/host/activity')}
                className="text-xs text-slate-400 hover:text-slate-200"
              >
                Full log →
              </button>
            }
          >
            {recentActivity.length === 0 ? (
              <div className="py-6 text-center text-slate-500 text-xs">
                No recent activity logged.
              </div>
            ) : (
              <div className="space-y-3">
                {recentActivity.map((ev) => (
                  <div key={ev.id} className="flex items-start gap-2.5 text-xs">
                    <div className="w-6 h-6 rounded-lg bg-slate-950 border border-slate-800 text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
                      <i className={ev.icon || 'fa-solid fa-clock'} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-slate-200 font-medium truncate">{ev.title}</div>
                      <div className="text-[11px] text-slate-500 leading-tight">
                        {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {ev.description}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </HostCard>
        </div>
      </div>
    </div>
  );
};
