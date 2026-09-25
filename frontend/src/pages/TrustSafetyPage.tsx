import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getAssessments,
  getTrustSafetyStats,
  takeAssessmentAction,
  getEntityGraph,
} from '../services/trustSafety';
import {
  RiskAssessment,
  TrustSafetyStats,
  EntityGraphData,
  RiskLevel,
  ActionTaken,
} from '../types';

export const TrustSafetyPage: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<TrustSafetyStats | null>(null);
  const [assessments, setAssessments] = useState<RiskAssessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedRiskLevel, setSelectedRiskLevel] = useState<string>('all');
  const [selectedEntityType, setSelectedEntityType] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');

  // Modal / Drawer state for detailed investigation
  const [activeAssessment, setActiveAssessment] = useState<RiskAssessment | null>(null);
  const [graphData, setGraphData] = useState<EntityGraphData | null>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [actionNotes, setActionNotes] = useState('');
  const [actionSubmitting, setActionSubmitting] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [statsRes, assessRes] = await Promise.all([
        getTrustSafetyStats().catch(() => ({ success: false, stats: null })),
        getAssessments({
          risk_level: selectedRiskLevel !== 'all' ? selectedRiskLevel : undefined,
          entity_type: selectedEntityType !== 'all' ? selectedEntityType : undefined,
          status: selectedStatus !== 'all' ? selectedStatus : undefined,
          limit: 50,
        }),
      ]);

      if (statsRes.stats) {
        setStats(statsRes.stats);
      }
      if (assessRes.assessments) {
        setAssessments(assessRes.assessments);
      }
    } catch (err: any) {
      console.error('Failed to load Trust & Safety assessments:', err);
      setError(err?.message || 'Failed to load Trust & Safety data.');
    } finally {
      setLoading(false);
    }
  }, [selectedRiskLevel, selectedEntityType, selectedStatus]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSelectAssessment = async (assessment: RiskAssessment) => {
    setActiveAssessment(assessment);
    setActionNotes(assessment.reviewer_notes || '');
    setGraphData(null);

    // Fetch entity graph
    try {
      setGraphLoading(true);
      const res = await getEntityGraph(assessment.entity_type, assessment.entity_id);
      if (res.success && res.graph) {
        setGraphData(res.graph);
      }
    } catch (e) {
      console.warn('Could not fetch entity graph:', e);
    } finally {
      setGraphLoading(false);
    }
  };

  const handleTriageAction = async (action: ActionTaken) => {
    if (!activeAssessment) return;
    try {
      setActionSubmitting(true);
      const res = await takeAssessmentAction(activeAssessment.id, action, actionNotes);
      if (res.success) {
        showToast(`Action '${action}' applied to ${activeAssessment.entity_type} #${activeAssessment.entity_id}.`);
        setActiveAssessment(res.assessment);
        // Refresh list
        loadData();
      }
    } catch (err: any) {
      alert(`Action failed: ${err.message || err}`);
    } finally {
      setActionSubmitting(false);
    }
  };

  const getRiskBadge = (level: RiskLevel) => {
    switch (level) {
      case 'high_risk':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
            HIGH RISK
          </span>
        );
      case 'suspicious':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            SUSPICIOUS
          </span>
        );
      case 'unusual':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-yellow-500/10 text-yellow-300 border border-yellow-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-yellow-400" />
            UNUSUAL
          </span>
        );
      case 'normal':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            NORMAL
          </span>
        );
    }
  };

  const getActionBadge = (action: ActionTaken) => {
    switch (action) {
      case 'escrow_held':
        return <span className="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-medium">Escrow Held</span>;
      case 'account_restricted':
        return <span className="text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 font-medium">Restricted</span>;
      case 'verification_requested':
        return <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 font-medium">KYC Requested</span>;
      case 'mfa_enforced':
        return <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-medium">MFA Required</span>;
      case 'dismissed':
        return <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-medium">Dismissed / Allowed</span>;
      case 'pending':
      default:
        return <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-medium">Pending Review</span>;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-20">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 border border-indigo-500/40 text-white px-5 py-3 rounded-2xl shadow-2xl flex items-center gap-3 backdrop-blur-md animate-fade-in">
          <i className="fa-solid fa-circle-check text-emerald-400 text-lg" />
          <span className="text-sm font-medium">{toastMessage}</span>
        </div>
      )}

      {/* Top Header Banner */}
      <div className="bg-slate-900/90 border-b border-slate-800 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-bold tracking-wide uppercase">
                Trust & Safety Intelligence
              </span>
              <span className="text-slate-500 text-xs">•</span>
              <span className="text-slate-400 text-xs font-mono">DPDP Act 2023 Compliant</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
              <i className="fa-solid fa-shield-halved text-indigo-400" />
              Risk & Abuse Operations Console
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              Real-time multi-tier forensic inspection across seeker bookings, host listings, reviews, shared devices, and circular transaction collusion.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={loadData}
              disabled={loading}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-sm font-semibold text-slate-200 transition flex items-center gap-2"
            >
              <i className={`fa-solid fa-rotate-right ${loading ? 'animate-spin' : ''}`} />
              Refresh Signals
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-4 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 text-sm font-semibold text-indigo-300 transition"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {/* Statistics Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 shadow-sm">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Total Monitored</div>
            <div className="text-2xl font-black text-white">{stats?.total_assessments ?? assessments.length}</div>
            <div className="text-[11px] text-slate-500 mt-1">Events & Entities</div>
          </div>

          <div className="bg-rose-950/20 border border-rose-900/40 rounded-2xl p-4 shadow-sm">
            <div className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-1">High Risk Critical</div>
            <div className="text-2xl font-black text-rose-400">{stats?.high_risk_count ?? 0}</div>
            <div className="text-[11px] text-rose-400/70 mt-1">Immediate Action Gate</div>
          </div>

          <div className="bg-amber-950/20 border border-amber-900/40 rounded-2xl p-4 shadow-sm">
            <div className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-1">Suspicious Activity</div>
            <div className="text-2xl font-black text-amber-400">{stats?.suspicious_count ?? 0}</div>
            <div className="text-[11px] text-amber-400/70 mt-1">Manual Escrow Hold</div>
          </div>

          <div className="bg-yellow-950/20 border border-yellow-900/40 rounded-2xl p-4 shadow-sm">
            <div className="text-xs font-bold text-yellow-300 uppercase tracking-wider mb-1">Unusual Anomalies</div>
            <div className="text-2xl font-black text-yellow-300">{stats?.unusual_count ?? 0}</div>
            <div className="text-[11px] text-yellow-300/70 mt-1">Velocity & Deviations</div>
          </div>

          <div className="bg-indigo-950/20 border border-indigo-900/40 rounded-2xl p-4 shadow-sm col-span-2 lg:col-span-1">
            <div className="text-xs font-bold text-indigo-300 uppercase tracking-wider mb-1">Pending Triage</div>
            <div className="text-2xl font-black text-indigo-400">{stats?.pending_action_count ?? 0}</div>
            <div className="text-[11px] text-indigo-300/70 mt-1">Awaiting Analyst</div>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 mb-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            {/* Risk Level Filter */}
            <div>
              <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">Risk Severity</label>
              <select
                value={selectedRiskLevel}
                onChange={(e) => setSelectedRiskLevel(e.target.value)}
                className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs font-medium text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All Severities</option>
                <option value="high_risk">High Risk Only</option>
                <option value="suspicious">Suspicious</option>
                <option value="unusual">Unusual</option>
                <option value="normal">Normal</option>
              </select>
            </div>

            {/* Entity Type Filter */}
            <div>
              <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">Entity Domain</label>
              <select
                value={selectedEntityType}
                onChange={(e) => setSelectedEntityType(e.target.value)}
                className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs font-medium text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All Entities</option>
                <option value="booking">Bookings</option>
                <option value="listing">Listings / Spaces</option>
                <option value="review">Reviews</option>
                <option value="checkout">Checkouts</option>
                <option value="user">Users</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-[11px] font-bold text-slate-400 uppercase mb-1">Triage Status</label>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs font-medium text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="all">All Statuses</option>
                <option value="pending">Pending Triage</option>
                <option value="escrow_held">Escrow Held</option>
                <option value="account_restricted">Restricted</option>
                <option value="dismissed">Dismissed / Allowed</option>
              </select>
            </div>
          </div>

          <div className="text-xs text-slate-400">
            Showing <span className="font-bold text-white">{assessments.length}</span> assessments
          </div>
        </div>

        {/* Assessment Queue Table / List */}
        {loading ? (
          <div className="py-24 text-center">
            <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-slate-400 text-sm">Evaluating entity graph & risk vectors...</p>
          </div>
        ) : error ? (
          <div className="bg-rose-950/20 border border-rose-900/40 rounded-2xl p-6 text-center text-rose-300 text-sm">
            <i className="fa-solid fa-triangle-exclamation text-xl mb-2 text-rose-400 block" />
            {error}
          </div>
        ) : assessments.length === 0 ? (
          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center">
            <i className="fa-solid fa-shield-check text-4xl text-emerald-400 mb-3 block" />
            <h3 className="text-lg font-bold text-white mb-1">No Flagged Assessments Found</h3>
            <p className="text-sm text-slate-400 max-w-md mx-auto">
              All marketplace bookings, listings, and checkout sessions are currently operating within normal risk parameters.
            </p>
          </div>
        ) : (
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="py-3 px-4">Entity</th>
                    <th className="py-3 px-4">Risk Level</th>
                    <th className="py-3 px-4">Risk Score</th>
                    <th className="py-3 px-4">Triggered Signals</th>
                    <th className="py-3 px-4">Recommended Policy</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {assessments.map((a) => {
                    const pct = Math.round(a.risk_score * 100);
                    return (
                      <tr
                        key={a.id}
                        className={`hover:bg-slate-800/40 transition cursor-pointer ${
                          activeAssessment?.id === a.id ? 'bg-indigo-950/20' : ''
                        }`}
                        onClick={() => handleSelectAssessment(a)}
                      >
                        <td className="py-3.5 px-4 font-mono font-medium text-slate-200">
                          <span className="uppercase text-[11px] font-bold text-indigo-400 mr-1.5">
                            {a.entity_type}
                          </span>
                          #{a.entity_id}
                          {a.created_at && (
                            <div className="text-[10px] text-slate-500 font-sans mt-0.5">
                              {new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </div>
                          )}
                        </td>
                        <td className="py-3.5 px-4">{getRiskBadge(a.risk_level)}</td>
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  pct >= 75
                                    ? 'bg-rose-500'
                                    : pct >= 50
                                    ? 'bg-amber-500'
                                    : pct >= 25
                                    ? 'bg-yellow-400'
                                    : 'bg-emerald-500'
                                }`}
                                style={{ width: `${Math.max(5, pct)}%` }}
                              />
                            </div>
                            <span className="font-mono font-bold text-slate-200">{pct}%</span>
                          </div>
                          <div className="text-[10px] text-slate-500">conf: {Math.round(a.confidence * 100)}%</div>
                        </td>
                        <td className="py-3.5 px-4 max-w-xs">
                          <div className="flex flex-wrap gap-1">
                            {a.signals && a.signals.length > 0 ? (
                              a.signals.slice(0, 2).map((s, idx) => (
                                <span
                                  key={idx}
                                  className="px-2 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300 font-medium truncate max-w-[140px]"
                                  title={s.description}
                                >
                                  {s.name}
                                </span>
                              ))
                            ) : (
                              <span className="text-slate-500 text-[11px]">No active signals</span>
                            )}
                            {a.signals && a.signals.length > 2 && (
                              <span className="text-[10px] text-indigo-400 font-medium">
                                +{a.signals.length - 2} more
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-3.5 px-4 font-medium text-slate-300">
                          <code className="text-[11px] bg-slate-950 px-2 py-0.5 rounded text-indigo-300">
                            {a.recommended_action}
                          </code>
                        </td>
                        <td className="py-3.5 px-4">{getActionBadge(a.action_taken)}</td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSelectAssessment(a);
                            }}
                            className="px-3 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 font-semibold transition"
                          >
                            Investigate
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Investigation Drawer / Modal */}
      {activeAssessment && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex justify-end animate-fade-in">
          <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto flex flex-col shadow-2xl">
            {/* Drawer Header */}
            <div className="sticky top-0 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 p-5 flex items-center justify-between z-10">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 text-lg">
                  <i className="fa-solid fa-magnifying-glass-chart" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-white capitalize">
                      {activeAssessment.entity_type} #{activeAssessment.entity_id}
                    </h2>
                    {getRiskBadge(activeAssessment.risk_level)}
                  </div>
                  <div className="text-xs text-slate-400">
                    Assessment ID: #{activeAssessment.id} • {activeAssessment.created_at ? new Date(activeAssessment.created_at).toLocaleString() : ''}
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setActiveAssessment(null)}
                className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition"
              >
                <i className="fa-solid fa-xmark" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="p-6 space-y-6 flex-1">
              {/* Risk Summary Card */}
              <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-[11px] font-bold text-slate-400 uppercase">Composite Score</div>
                    <div className="text-xl font-black text-white mt-1">
                      {Math.round(activeAssessment.risk_score * 100)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] font-bold text-slate-400 uppercase">Confidence</div>
                    <div className="text-xl font-black text-indigo-300 mt-1">
                      {Math.round(activeAssessment.confidence * 100)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] font-bold text-slate-400 uppercase">Action Protocol</div>
                    <div className="text-xs font-mono font-bold text-amber-400 mt-2 truncate">
                      {activeAssessment.recommended_action}
                    </div>
                  </div>
                </div>
              </div>

              {/* Explainable AI Forensic Narrative */}
              <div>
                <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <i className="fa-solid fa-robot" /> Multi-Tier AI Forensic Rationale
                </h3>
                <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4 text-xs text-slate-300 leading-relaxed font-sans">
                  {activeAssessment.evidence_text || 'No detailed forensic notes logged for this assessment.'}
                </div>
              </div>

              {/* Triggered Signals Breakdown */}
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <i className="fa-solid fa-bolt" /> Triggered Trust Signals ({activeAssessment.signals?.length || 0})
                </h3>
                {activeAssessment.signals && activeAssessment.signals.length > 0 ? (
                  <div className="space-y-2">
                    {activeAssessment.signals.map((sig, idx) => (
                      <div
                        key={idx}
                        className="bg-slate-950 border border-slate-800/80 rounded-xl p-3 flex flex-col gap-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-xs text-white flex items-center gap-1.5">
                            <span
                              className={`w-2 h-2 rounded-full ${
                                sig.severity === 'critical'
                                  ? 'bg-rose-500'
                                  : sig.severity === 'high'
                                  ? 'bg-amber-500'
                                  : 'bg-yellow-400'
                              }`}
                            />
                            {sig.name}
                          </span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                            weight: {sig.weight}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400">{sig.description}</p>
                        {sig.evidence && (
                          <div className="text-[11px] font-mono text-indigo-300 bg-indigo-950/20 px-2 py-1 rounded border border-indigo-900/30 mt-1">
                            {sig.evidence}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">No anomaly signals active.</p>
                )}
              </div>

              {/* Entity Knowledge Graph Context */}
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <i className="fa-solid fa-diagram-project" /> Entity Relationship Subgraph
                </h3>
                <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4">
                  {graphLoading ? (
                    <div className="py-6 text-center text-xs text-slate-500">
                      <div className="w-5 h-5 border border-indigo-400 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                      Loading 2-hop topological subgraph...
                    </div>
                  ) : graphData && graphData.nodes?.length > 0 ? (
                    <div>
                      <div className="flex items-center justify-between text-[11px] text-slate-400 mb-3 pb-2 border-b border-slate-800">
                        <span>Connected Nodes: <b className="text-white">{graphData.subgraph_size.nodes}</b></span>
                        <span>Correlated Edges: <b className="text-white">{graphData.subgraph_size.edges}</b></span>
                      </div>
                      <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto">
                        {graphData.nodes.map((n) => (
                          <span
                            key={n.id}
                            className={`px-2 py-1 rounded text-[11px] border font-mono ${
                              n.type === 'Device'
                                ? 'bg-amber-950/30 border-amber-800/40 text-amber-300'
                                : n.type === 'IP'
                                ? 'bg-blue-950/30 border-blue-800/40 text-blue-300'
                                : n.type === 'User'
                                ? 'bg-purple-950/30 border-purple-800/40 text-purple-300'
                                : 'bg-slate-900 border-slate-800 text-slate-300'
                            }`}
                          >
                            <b>{n.type}:</b> {n.label}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-slate-500 italic py-2 text-center">
                      No multi-entity links or shared hardware clusters detected for this item.
                    </div>
                  )}
                </div>
              </div>

              {/* Analyst Triage Decision Box */}
              <div className="border-t border-slate-800 pt-4">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <i className="fa-solid fa-gavel text-amber-400" /> Analyst Triage Decision
                </h3>

                <div className="mb-3">
                  <label className="block text-[11px] text-slate-400 mb-1">Investigation Notes & Rationale</label>
                  <textarea
                    rows={2}
                    value={actionNotes}
                    onChange={(e) => setActionNotes(e.target.value)}
                    placeholder="Enter compliance or audit justification for your decision..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  <button
                    type="button"
                    disabled={actionSubmitting}
                    onClick={() => handleTriageAction('dismissed')}
                    className="px-3 py-2 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/30 text-emerald-300 text-xs font-bold transition flex items-center justify-center gap-1.5"
                  >
                    <i className="fa-solid fa-check" /> Allow / Dismiss
                  </button>

                  <button
                    type="button"
                    disabled={actionSubmitting}
                    onClick={() => handleTriageAction('escrow_held')}
                    className="px-3 py-2 rounded-xl bg-amber-600/20 hover:bg-amber-600/30 border border-amber-500/30 text-amber-300 text-xs font-bold transition flex items-center justify-center gap-1.5"
                  >
                    <i className="fa-solid fa-lock" /> Hold Escrow
                  </button>

                  <button
                    type="button"
                    disabled={actionSubmitting}
                    onClick={() => handleTriageAction('verification_requested')}
                    className="px-3 py-2 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 text-blue-300 text-xs font-bold transition flex items-center justify-center gap-1.5"
                  >
                    <i className="fa-solid fa-id-card" /> Request KYC
                  </button>

                  <button
                    type="button"
                    disabled={actionSubmitting}
                    onClick={() => handleTriageAction('mfa_enforced')}
                    className="px-3 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 text-indigo-300 text-xs font-bold transition flex items-center justify-center gap-1.5"
                  >
                    <i className="fa-solid fa-key" /> Require MFA
                  </button>

                  <button
                    type="button"
                    disabled={actionSubmitting}
                    onClick={() => handleTriageAction('account_restricted')}
                    className="col-span-2 px-3 py-2 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/40 text-rose-300 text-xs font-bold transition flex items-center justify-center gap-1.5"
                  >
                    <i className="fa-solid fa-ban" /> Restrict / Freeze Action
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
