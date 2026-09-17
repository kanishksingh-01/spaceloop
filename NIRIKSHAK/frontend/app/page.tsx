"use client";

import { useEffect, useState } from "react";
import {
  Shield,
  Database,
  Activity,
  CheckCircle,
  AlertTriangle,
  Users,
  Server,
  Lock,
  Play,
  Eye,
  Check,
  X,
  Clock,
  ArrowUpRight,
  FileText,
  History,
  Radio,
  RefreshCw,
  AlertOctagon,
  ChevronRight,
  Zap,
  Globe,
  KeyRound,
  Crosshair,
} from "lucide-react";
import {
  checkHealth,
  loginWithSeededCredentials,
  fetchEvents,
  fetchEventExplanation,
  fetchCases,
  fetchCaseDetail,
  reviewCase,
  triggerScenario,
  fetchAuditLogs,
  fetchPraharakSignals,
  fetchCircuitBreakerStates,
  resetCircuitBreaker,
  fetchCrossDomainIncidents,
  triggerPraharakScenario,
} from "@/lib/api";
import { CommandConsole } from "@/components/terminal/CommandConsole";
import { RiskTrendChart } from "@/components/analytics/RiskTrendChart";

interface EventItem {
  id: string;
  event_id: string;
  timestamp: string;
  user_identifier: string;
  department: string;
  device_identifier: string;
  resource_name: string;
  action: string;
  result: string;
  data_volume: number;
  risk_score: number;
  risk_level: string;
  case_id?: string | null;
}

interface FactorItem {
  factor: string;
  subscore: number;
  weight: number;
  contribution: number;
  explanation: string;
  details: Record<string, any>;
}

interface CaseItem {
  id: string;
  case_identifier: string;
  status: string;
  severity: string;
  opened_at: string;
  primary_user_identifier: string;
  department: string;
  event_id?: string;
  resource_name?: string;
  risk_score?: number;
}

interface AuditItem {
  id: string;
  timestamp: string;
  actor_username: string;
  action: string;
  target_id?: string;
  justification: string;
  details: Record<string, any>;
}

interface ExternalSignalItem {
  id: string;
  signal_identifier: string;
  timestamp: string;
  source_ip: string;
  source_asn?: string | null;
  target_service: string;
  command_type: string;
  raw_envelope: Record<string, any>;
  signature_valid: boolean;
  signature_algorithm: string;
  risk_score: number;
  risk_tier: string;
  disposition: string;
  factors: FactorItem[];
  audit_hash: string;
}

interface CircuitBreakerItem {
  id: string;
  source_identifier: string;
  state: string;
  request_count: number;
  window_start: string;
  trip_expires_at?: string | null;
  is_quarantined: boolean;
}

interface CrossDomainIncidentItem {
  id: string;
  incident_identifier: string;
  external_signal_id: string;
  internal_event_id?: string | null;
  case_id?: string | null;
  unified_risk_score: number;
  attack_pattern: string;
  summary: string;
  detected_at: string;
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<"events" | "cases" | "audit" | "praharak">("events");
  const [health, setHealth] = useState<{ status: string; database: string } | null>(null);
  const [authStatus, setAuthStatus] = useState<string>("Not Authenticated");
  const [currentUser, setCurrentUser] = useState<string | null>(null);

  // Data states
  const [events, setEvents] = useState<EventItem[]>([]);
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditItem[]>([]);
  const [praharakSignals, setPraharakSignals] = useState<ExternalSignalItem[]>([]);
  const [circuitBreakers, setCircuitBreakers] = useState<CircuitBreakerItem[]>([]);
  const [crossDomainIncidents, setCrossDomainIncidents] = useState<CrossDomainIncidentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [triggeringScenario, setTriggeringScenario] = useState<string | null>(null);
  const [scenarioBanner, setScenarioBanner] = useState<{ scenario: string; summary: string; level: string } | null>(null);

  // PRAHARAK UI states
  const [triggeringPraharak, setTriggeringPraharak] = useState<string | null>(null);
  const [selectedSignal, setSelectedSignal] = useState<ExternalSignalItem | null>(null);
  const [praharakBanner, setPraharakBanner] = useState<{
    scenario: string;
    summary: string;
    level: string;
    disposition: string;
    tripped: boolean;
    incidentId?: string | null;
  } | null>(null);

  // Inspector Modal states
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [explanationData, setExplanationData] = useState<{ event_id: string; total_score: number; risk_level: string; factors: FactorItem[] } | null>(null);
  const [inspecting, setInspecting] = useState(false);

  // Case Review Modal states
  const [reviewCaseObj, setReviewCaseObj] = useState<CaseItem | null>(null);
  const [reviewAction, setReviewAction] = useState<"DISMISS" | "ESCALATE">("ESCALATE");
  const [reviewJustification, setReviewJustification] = useState<string>("");
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);

  // Load Initial Data & Health
  const refreshAllData = async () => {
    try {
      const [h, evs, cs, aud, sigs, cbs, incs] = await Promise.all([
        checkHealth(),
        fetchEvents(50),
        fetchCases(),
        fetchAuditLogs(50),
        fetchPraharakSignals(50).catch(() => []),
        fetchCircuitBreakerStates().catch(() => []),
        fetchCrossDomainIncidents(20).catch(() => []),
      ]);
      setHealth(h);
      setEvents(evs);
      setCases(cs);
      setAuditLogs(aud);
      setPraharakSignals(sigs || []);
      setCircuitBreakers(cbs || []);
      setCrossDomainIncidents(incs || []);
    } catch (err) {
      console.error("Error refreshing dashboard data:", err);
    }
  };

  useEffect(() => {
    refreshAllData();
    const interval = setInterval(refreshAllData, 5000);
    return () => clearInterval(interval);
  }, []);

  // Quick Seeded Login
  const handleQuickLogin = async () => {
    try {
      const res = await loginWithSeededCredentials("analyst_sarah", "analyst123");
      setAuthStatus(`Authenticated as ${res.user.username}`);
      setCurrentUser(res.user.username);
    } catch (err) {
      alert("Failed to login with seeded credentials.");
    }
  };

  // Trigger On-Demand Demo Scenario (NIRIKSHAK)
  const handleTriggerScenario = async (name: "normal" | "off_hours" | "exfiltration" | "kill_chain") => {
    try {
      setTriggeringScenario(name);
      const res = await triggerScenario(name);
      setScenarioBanner({
        scenario: res.scenario.toUpperCase(),
        summary: res.summary,
        level: res.risk_level,
      });
      await refreshAllData();
      if (res.internal_id) {
        handleInspectEvent(res.internal_id);
      }
    } catch (err: any) {
      alert(`Failed to trigger scenario: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setTriggeringScenario(null);
    }
  };

  // Trigger On-Demand Demo Scenario (PRAHARAK)
  const handleTriggerPraharak = async (
    name: "normal_telemetry" | "spoofed_command" | "ddos_flood" | "hybrid_coordinated_attack"
  ) => {
    try {
      setTriggeringPraharak(name);
      const res = await triggerPraharakScenario(name);
      setPraharakBanner({
        scenario: res.scenario.toUpperCase(),
        summary: res.summary,
        level: res.risk_tier,
        disposition: res.disposition,
        tripped: res.circuit_breaker_tripped,
        incidentId: res.cross_domain_incident_id,
      });
      setActiveTab("praharak");
      await refreshAllData();
    } catch (err: any) {
      alert(`Failed to trigger PRAHARAK scenario: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setTriggeringPraharak(null);
    }
  };

  // Reset Circuit Breaker
  const handleResetCircuitBreaker = async (sourceIdentifier: string) => {
    try {
      await resetCircuitBreaker(sourceIdentifier);
      await refreshAllData();
    } catch (err: any) {
      alert(`Failed to reset circuit breaker: ${err?.response?.data?.detail || err.message}`);
    }
  };

  // Inspect Event Explanation
  const handleInspectEvent = async (eventId: string) => {
    try {
      setSelectedEventId(eventId);
      setInspecting(true);
      const exp = await fetchEventExplanation(eventId);
      setExplanationData(exp);
    } catch (err) {
      console.error("Failed to load explanation:", err);
    }
  };

  // Submit Case Review
  const handleSubmitCaseReview = async () => {
    if (!reviewCaseObj) return;
    if (reviewJustification.trim().length < 5) {
      setReviewError("Please provide a justification of at least 5 characters.");
      return;
    }

    try {
      setSubmittingReview(true);
      setReviewError(null);
      await reviewCase(reviewCaseObj.id, reviewAction, reviewJustification);
      setReviewCaseObj(null);
      setReviewJustification("");
      await refreshAllData();
    } catch (err: any) {
      setReviewError(err?.response?.data?.detail || "Failed to submit case review.");
    } finally {
      setSubmittingReview(false);
    }
  };

  // Helper badge formatters
  const getRiskBadge = (level: string) => {
    switch (level.toUpperCase()) {
      case "CRITICAL":
        return "bg-rose-950/80 text-rose-300 border-rose-800";
      case "HIGH":
        return "bg-amber-950/80 text-amber-300 border-amber-800";
      case "MODERATE":
        return "bg-blue-950/80 text-blue-300 border-blue-800";
      default:
        return "bg-emerald-950/80 text-emerald-300 border-emerald-800";
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(2) + " GB";
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + " MB";
    if (bytes >= 1024) return (bytes / 1024).toFixed(0) + " KB";
    return bytes + " B";
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-4 flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white">
                NIRIKSHAK <span className="text-slate-400 font-normal">&amp;</span> PRAHARAK
              </h1>
              <span className="text-xs px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono">
                निरीक्षक &amp; प्रहारक
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                Dual-Twin Cyber Defense
              </span>
            </div>
            <p className="text-xs text-slate-400">Continuous Contextual Insider Risk &amp; External Perimeter Protection</p>
          </div>
        </div>

        {/* Global Controls & Auth */}
        <div className="flex items-center gap-4">
          {/* Framework Toggle Pill in Header */}
          <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setActiveTab("events")}
              className={`px-3 py-1.5 rounded text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab !== "praharak"
                  ? "bg-indigo-600 text-white shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>NIRIKSHAK</span>
            </button>
            <button
              onClick={() => setActiveTab("praharak")}
              className={`px-3 py-1.5 rounded text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeTab === "praharak"
                  ? "bg-amber-600 text-white shadow"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Shield className="w-3.5 h-3.5" />
              <span>PRAHARAK</span>
              {crossDomainIncidents.length > 0 && (
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
              )}
            </button>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                health?.status === "healthy" ? "bg-emerald-500 animate-pulse" : "bg-amber-500"
              }`}
            />
            <span className="font-medium text-slate-300">
              Postgres: {health?.database === "connected" ? "Online" : "Connecting"}
            </span>
          </div>

          <button
            onClick={handleQuickLogin}
            className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
          >
            <Lock className="w-3.5 h-3.5" />
            {currentUser ? `Analyst: ${currentUser}` : "Login as analyst_sarah"}
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Prominent Primary Framework Switcher Banner */}
        <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xl">
          <div className="flex items-center gap-2.5 w-full sm:w-auto">
            <button
              onClick={() => setActiveTab("events")}
              className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                activeTab !== "praharak"
                  ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 ring-1 ring-indigo-400"
                  : "bg-slate-950/60 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800"
              }`}
            >
              <Eye className="w-4 h-4 text-indigo-300" />
              <span>NIRIKSHAK (Insider Risk)</span>
              <span className="text-xs px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono">
                {events.length} Events
              </span>
            </button>

            <button
              onClick={() => setActiveTab("praharak")}
              className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                activeTab === "praharak"
                  ? "bg-amber-600 text-white shadow-lg shadow-amber-600/30 ring-1 ring-amber-400"
                  : "bg-slate-950/60 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800"
              }`}
            >
              <Shield className="w-4 h-4 text-amber-300" />
              <span>PRAHARAK (Perimeter Defense)</span>
              <span className="text-xs px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 font-mono">
                {praharakSignals.length} Signals
              </span>
              {crossDomainIncidents.length > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800 text-[10px] font-mono animate-pulse">
                  {crossDomainIncidents.length} HYBRID
                </span>
              )}
            </button>
          </div>

          <div className="text-xs text-slate-400 font-mono hidden md:block">
            {activeTab === "praharak"
              ? "🛡️ OUTWARD PERIMETER: Cryptographic Verification • Circuit Breakers • MITRE ATT&CK Recon"
              : "👁️ INWARD CONTEXT: Behavioral Baselines • Isolation Forest Anomaly • Human Triage"}
          </div>
        </div>

        {/* On-Demand Scenario Trigger Panel (Dynamic based on selected twin) */}
        <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Play className={`w-4 h-4 ${activeTab === "praharak" ? "text-amber-400" : "text-indigo-400"}`} />
              <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
                {activeTab === "praharak"
                  ? "PRAHARAK Perimeter Scenario Controller"
                  : "NIRIKSHAK Live Scenario Demo Controller"}
              </h2>
            </div>
            <span className="text-xs text-slate-400">
              {activeTab === "praharak"
                ? "Trigger external ingress threat vectors directly into perimeter pipeline"
                : "Trigger on-demand demo events directly into the pipeline"}
            </span>
          </div>

          {activeTab === "praharak" ? (
            /* PRAHARAK Scenario Buttons */
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <button
                onClick={() => handleTriggerPraharak("normal_telemetry")}
                disabled={triggeringPraharak !== null}
                className="text-left p-4 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-emerald-500/50 transition-all hover:bg-emerald-950/10 group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-emerald-400 group-hover:translate-x-0.5 transition-transform">
                    SCENARIO 1: NORMAL BEACON
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono">
                    ALLOWED
                  </span>
                </div>
                <div className="text-sm font-medium text-white">Signed Telemetry</div>
                <div className="text-xs text-slate-400 mt-1">Legitimate gateway payload with valid HMAC-SHA256 signature and fresh nonce.</div>
              </button>

              <button
                onClick={() => handleTriggerPraharak("spoofed_command")}
                disabled={triggeringPraharak !== null}
                className="text-left p-4 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-rose-500/50 transition-all hover:bg-rose-950/10 group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-rose-400 group-hover:translate-x-0.5 transition-transform">
                    SCENARIO 2: SPOOFED COMMAND
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 font-mono">
                    BLOCKED
                  </span>
                </div>
                <div className="text-sm font-medium text-white">Forged Drone Reroute</div>
                <div className="text-xs text-slate-400 mt-1">High-risk command with forged Ed25519 signature. Zero-trust rejection.</div>
              </button>

              <button
                onClick={() => handleTriggerPraharak("ddos_flood")}
                disabled={triggeringPraharak !== null}
                className="text-left p-4 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-amber-500/50 transition-all hover:bg-amber-950/10 group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-amber-400 group-hover:translate-x-0.5 transition-transform">
                    SCENARIO 3: DDOS FLOOD
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 font-mono">
                    QUARANTINE
                  </span>
                </div>
                <div className="text-sm font-medium text-white">High-Rate Burst Flood</div>
                <div className="text-xs text-slate-400 mt-1">17 requests in 3s trip token-bucket circuit breaker to OPEN with 15m quarantine.</div>
              </button>

              <button
                onClick={() => handleTriggerPraharak("hybrid_coordinated_attack")}
                disabled={triggeringPraharak !== null}
                className="text-left p-4 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-purple-500/50 transition-all hover:bg-purple-950/10 group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-purple-400 group-hover:translate-x-0.5 transition-transform">
                    SCENARIO 4: HYBRID ATTACK
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800 font-mono">
                    NEXUS FUSION
                  </span>
                </div>
                <div className="text-sm font-medium text-white">External Probe + Insider Exfil</div>
                <div className="text-xs text-slate-400 mt-1">Correlates external brute-force IP with internal credential exfiltration.</div>
              </button>
            </div>
          ) : (
            /* NIRIKSHAK Scenario Buttons */
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <button
                onClick={() => handleTriggerScenario("normal")}
                disabled={triggeringScenario !== null}
                className="text-left p-4 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-emerald-500/50 transition-all hover:bg-emerald-950/10 group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-emerald-400 group-hover:translate-x-0.5 transition-transform">
                    SCENARIO 1: NORMAL
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono">
                    LOW RISK
                  </span>
                </div>
                <div className="text-sm font-medium text-white">Standard Daytime Access</div>
                <div className="text-xs text-slate-400 mt-1">USER-001 reads Operational Repo A with MFA during working hours.</div>
              </button>

              <button
                onClick={() => handleTriggerScenario("off_hours")}
                disabled={triggeringScenario !== null}
                className="text-left p-4 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-amber-500/50 transition-all hover:bg-amber-950/10 group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-amber-400 group-hover:translate-x-0.5 transition-transform">
                    SCENARIO 2: OFF-HOURS
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 font-mono">
                    HIGH RISK
                  </span>
                </div>
                <div className="text-sm font-medium text-white">Cross-Department Read</div>
                <div className="text-xs text-slate-400 mt-1">USER-002 reads Operational Repo A at 02:30 AM without MFA.</div>
              </button>

              <button
                onClick={() => handleTriggerScenario("exfiltration")}
                disabled={triggeringScenario !== null}
                className="text-left p-4 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-rose-500/50 transition-all hover:bg-rose-950/10 group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-rose-400 group-hover:translate-x-0.5 transition-transform">
                    SCENARIO 3: EXFILTRATION
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 font-mono">
                    CRITICAL RISK
                  </span>
                </div>
                <div className="text-sm font-medium text-white">Bulk Data Exfiltration</div>
                <div className="text-xs text-slate-400 mt-1">USER-003 downloads 2.5 GB from unregistered DEV-999 at 03:15 AM.</div>
              </button>

              <button
                onClick={() => handleTriggerScenario("kill_chain")}
                disabled={triggeringScenario !== null}
                className="text-left p-4 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-purple-500/50 transition-all hover:bg-purple-950/10 group"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-purple-400 group-hover:translate-x-0.5 transition-transform">
                    SCENARIO 4: KILL CHAIN
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800 font-mono">
                    APT SEQUENCE
                  </span>
                </div>
                <div className="text-sm font-medium text-white">Multi-Stage Lateral Attack</div>
                <div className="text-xs text-slate-400 mt-1">Recon → Lateral crawl → Privilege bypass → 1.8 GB Exfil.</div>
              </button>
            </div>
          )}

          {/* Scenario Execution Result Banner (NIRIKSHAK) */}
          {scenarioBanner && (
            <div className={`p-4 rounded-lg border flex items-start gap-3 mt-3 animate-in fade-in ${getRiskBadge(scenarioBanner.level)}`}>
              <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm">INJECTED: {scenarioBanner.scenario}</span>
                  <span className="text-xs px-2 py-0.2 rounded border font-mono">{scenarioBanner.level}</span>
                </div>
                <p className="text-xs mt-1 text-slate-200">{scenarioBanner.summary}</p>
              </div>
              <button onClick={() => setScenarioBanner(null)} className="text-xs opacity-60 hover:opacity-100">
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Scenario Execution Result Banner (PRAHARAK) */}
          {praharakBanner && (
            <div className="p-4 rounded-lg border border-amber-700 bg-amber-950/40 text-amber-200 flex items-start gap-3 mt-3 animate-in fade-in">
              <Shield className="w-5 h-5 flex-shrink-0 mt-0.5 text-amber-400" />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm">PRAHARAK INGRESS: {praharakBanner.scenario}</span>
                  <span className="text-xs px-2 py-0.5 rounded border border-amber-600 bg-amber-900 font-mono">
                    {praharakBanner.disposition}
                  </span>
                  {praharakBanner.tripped && (
                    <span className="text-xs px-2 py-0.5 rounded border border-rose-600 bg-rose-900 text-rose-200 font-mono animate-pulse">
                      CIRCUIT OPEN
                    </span>
                  )}
                  {praharakBanner.incidentId && (
                    <span className="text-xs px-2 py-0.5 rounded border border-purple-600 bg-purple-900 text-purple-200 font-mono animate-pulse">
                      NEXUS FUSION: {praharakBanner.incidentId}
                    </span>
                  )}
                </div>
                <p className="text-xs mt-1 text-slate-200">{praharakBanner.summary}</p>
              </div>
              <button onClick={() => setPraharakBanner(null)} className="text-xs opacity-60 hover:opacity-100">
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center justify-between border-b border-slate-800">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab("events")}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === "events"
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Activity className="w-4 h-4" />
              Live Access Telemetry ({events.length})
            </button>

            <button
              onClick={() => setActiveTab("cases")}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === "cases"
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <AlertOctagon className="w-4 h-4" />
              Security Cases & Triage ({cases.length})
            </button>

            <button
              onClick={() => setActiveTab("audit")}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === "audit"
                  ? "border-indigo-500 text-indigo-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <History className="w-4 h-4" />
              Immutable Audit Trail ({auditLogs.length})
            </button>

            <button
              onClick={() => setActiveTab("praharak")}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === "praharak"
                  ? "border-amber-500 text-amber-400"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Shield className="w-4 h-4 text-amber-400" />
              PRAHARAK Perimeter & Outsider Risk ({praharakSignals.length})
              {crossDomainIncidents.length > 0 && (
                <span className="px-1.5 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800 text-[10px] font-mono animate-pulse">
                  {crossDomainIncidents.length} HYBRID
                </span>
              )}
              {circuitBreakers.some((cb) => cb.state === "OPEN" || cb.is_quarantined) && (
                <span className="px-1.5 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-800 text-[10px] font-mono">
                  CIRCUIT TRIPPED
                </span>
              )}
            </button>
          </div>

          <button
            onClick={refreshAllData}
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 px-3 py-1.5 rounded hover:bg-slate-900 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>

        {/* TAB 1: ACCESS TELEMETRY STREAM */}
        {activeTab === "events" && (
          <div className="space-y-4">
            {/* Longitudinal Risk Velocity Chart */}
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-amber-400" />
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                    Longitudinal Risk Score Velocity & Decision Thresholds
                  </span>
                </div>
                <span className="text-[10px] font-mono text-slate-500">
                  Sliding-window temporal telemetry trend
                </span>
              </div>
              <RiskTrendChart
                events={events.map((e) => ({
                  id: e.id,
                  event_id: e.event_id,
                  timestamp: e.timestamp,
                  total_score: e.risk_score,
                  risk_level: e.risk_level,
                  user_identifier: e.user_identifier,
                  action: e.action,
                }))}
                onSelectEvent={(eid) => {
                  const ev = events.find((x) => x.event_id === eid || x.id === eid);
                  if (ev) handleInspectEvent(ev.id);
                }}
              />
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden">
              <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-5 py-3.5">Time (UTC)</th>
                  <th className="px-5 py-3.5">User / Dept</th>
                  <th className="px-5 py-3.5">Device</th>
                  <th className="px-5 py-3.5">Resource</th>
                  <th className="px-5 py-3.5">Action</th>
                  <th className="px-5 py-3.5">Volume</th>
                  <th className="px-5 py-3.5">Risk Score</th>
                  <th className="px-5 py-3.5 text-right">Inspection</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {events.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-5 py-8 text-center text-slate-500">
                      No telemetry ingested yet. Use the buttons above to inject demo scenarios.
                    </td>
                  </tr>
                ) : (
                  events.map((ev) => (
                    <tr key={ev.id} className="hover:bg-slate-900/60 transition-colors">
                      <td className="px-5 py-3.5 font-mono text-xs text-slate-400">
                        {new Date(ev.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="font-semibold text-white">{ev.user_identifier}</div>
                        <div className="text-xs text-slate-400">{ev.department}</div>
                      </td>
                      <td className="px-5 py-3.5 font-mono text-xs text-slate-300">
                        {ev.device_identifier}
                      </td>
                      <td className="px-5 py-3.5 text-slate-200">
                        {ev.resource_name}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                          {ev.action}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 font-mono text-xs text-slate-400">
                        {formatBytes(ev.data_volume)}
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2.5 py-1 rounded-full border font-mono font-bold ${getRiskBadge(ev.risk_level)}`}>
                            {ev.risk_score} — {ev.risk_level}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button
                          onClick={() => handleInspectEvent(ev.id)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Inspect Why
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

        {/* TAB 2: SECURITY CASES & HUMAN TRIAGE */}
        {activeTab === "cases" && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-5 py-3.5">Case ID</th>
                  <th className="px-5 py-3.5">Severity</th>
                  <th className="px-5 py-3.5">Status</th>
                  <th className="px-5 py-3.5">Subject User</th>
                  <th className="px-5 py-3.5">Target Resource</th>
                  <th className="px-5 py-3.5">Score</th>
                  <th className="px-5 py-3.5">Opened At</th>
                  <th className="px-5 py-3.5 text-right">Human Triage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {cases.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-5 py-8 text-center text-slate-500">
                      No security cases generated yet. Elevated risk events ($\ge 61.0$) automatically appear here.
                    </td>
                  </tr>
                ) : (
                  cases.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-900/60 transition-colors">
                      <td className="px-5 py-3.5 font-mono font-bold text-white">
                        {c.case_identifier}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`text-xs px-2 py-0.5 rounded border font-mono font-semibold ${getRiskBadge(c.severity)}`}>
                          {c.severity}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                            c.status === "OPEN"
                              ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                              : c.status === "ESCALATED"
                              ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {c.status}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="font-semibold text-white">{c.primary_user_identifier}</div>
                        <div className="text-xs text-slate-400">{c.department}</div>
                      </td>
                      <td className="px-5 py-3.5 text-slate-200">
                        {c.resource_name || "N/A"}
                      </td>
                      <td className="px-5 py-3.5 font-mono text-xs font-bold text-white">
                        {c.risk_score || "N/A"}
                      </td>
                      <td className="px-5 py-3.5 font-mono text-xs text-slate-400">
                        {new Date(c.opened_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <button
                          onClick={() => {
                            setReviewCaseObj(c);
                            setReviewAction("ESCALATE");
                            setReviewJustification("");
                            setReviewError(null);
                          }}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors"
                        >
                          Triage Action
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* TAB 3: IMMUTABLE AUDIT TRAIL */}
        {activeTab === "audit" && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-5 py-3.5">Timestamp (UTC)</th>
                  <th className="px-5 py-3.5">Analyst / Actor</th>
                  <th className="px-5 py-3.5">Action</th>
                  <th className="px-5 py-3.5">Target Case</th>
                  <th className="px-5 py-3.5">Documented Human Justification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-5 py-8 text-center text-slate-500">
                      No audit entries recorded yet. Perform a case review to verify audit recording.
                    </td>
                  </tr>
                ) : (
                  auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-900/60 transition-colors">
                      <td className="px-5 py-3.5 font-mono text-xs text-slate-400 whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="px-5 py-3.5 font-semibold text-white">
                        {log.actor_username}
                      </td>
                      <td className="px-5 py-3.5">
                        <span
                          className={`text-xs px-2.5 py-0.5 rounded font-mono font-semibold ${
                            log.action.includes("escalate")
                              ? "bg-rose-950 text-rose-300 border border-rose-800"
                              : "bg-emerald-950 text-emerald-300 border border-emerald-800"
                          }`}
                        >
                          {log.action}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 font-mono text-xs text-slate-300">
                        {log.details?.case_identifier || log.target_id || "N/A"}
                      </td>
                      <td className="px-5 py-3.5 text-xs text-slate-300 max-w-md">
                        {log.justification}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* TAB 4: PRAHARAK OUTSIDER RISK & COMMAND VERIFICATION */}
        {activeTab === "praharak" && (
          <div className="space-y-6">
            {/* Top Metric Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
                <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
                  <span>External Ingress Signals</span>
                  <Globe className="w-4 h-4 text-sky-400" />
                </div>
                <div className="text-2xl font-bold text-white mt-2 font-mono">
                  {praharakSignals.length}
                </div>
                <div className="text-[11px] text-slate-500 mt-1">Perimeter API & Command Gateway</div>
              </div>

              <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
                <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
                  <span>Cryptographic Verification</span>
                  <KeyRound className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-2xl font-bold text-emerald-400 mt-2 font-mono">
                  {praharakSignals.filter((s) => s.signature_valid).length} / {praharakSignals.length}
                </div>
                <div className="text-[11px] text-slate-500 mt-1">
                  {praharakSignals.filter((s) => !s.signature_valid && s.raw_envelope?.signature).length} Spoofed / Tampered
                </div>
              </div>

              <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
                <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
                  <span>Circuit Breaker Status</span>
                  <Zap className="w-4 h-4 text-amber-400" />
                </div>
                <div className="flex items-center gap-2 mt-2">
                  {circuitBreakers.some((cb) => cb.state === "OPEN" || cb.is_quarantined) ? (
                    <span className="text-sm px-2.5 py-1 rounded bg-amber-950 text-amber-300 border border-amber-800 font-mono font-bold flex items-center gap-1.5 animate-pulse">
                      <AlertTriangle className="w-3.5 h-3.5" /> OPEN (QUARANTINE)
                    </span>
                  ) : (
                    <span className="text-sm px-2.5 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono font-bold flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5" /> CLOSED (NORMAL)
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-slate-500 mt-1">
                  {circuitBreakers.length} Source subnets monitored
                </div>
              </div>

              <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
                <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase">
                  <span>Cross-Domain Incidents</span>
                  <Crosshair className="w-4 h-4 text-rose-400" />
                </div>
                <div className="text-2xl font-bold text-rose-400 mt-2 font-mono">
                  {crossDomainIncidents.length}
                </div>
                <div className="text-[11px] text-slate-500 mt-1">Unified Outsider + Insider Breaches</div>
              </div>
            </div>

            {/* Cross-Domain Nexus Alert Banner (If Active) */}
            {crossDomainIncidents.length > 0 && (
              <div className="p-4 rounded-xl border border-rose-800 bg-rose-950/30 space-y-3 animate-in fade-in">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-2.5 w-2.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
                    </span>
                    <span className="text-sm font-bold text-rose-300 tracking-wide">
                      PRAHARAK & NIRIKSHAK CROSS-DOMAIN NEXUS CORRELATION ACTIVE
                    </span>
                  </div>
                  <span className="text-xs px-2.5 py-0.5 rounded bg-rose-900 text-rose-200 border border-rose-700 font-mono font-bold">
                    HYBRID KILL-CHAIN DETECTED
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {crossDomainIncidents.slice(0, 2).map((inc) => (
                    <div key={inc.id} className="p-3 rounded-lg bg-slate-900/80 border border-rose-900/60 text-xs space-y-1.5">
                      <div className="flex items-center justify-between font-mono">
                        <span className="font-bold text-rose-400">{inc.incident_identifier}</span>
                        <span className="text-slate-400">Score: <strong className="text-rose-300">{inc.unified_risk_score} (CRITICAL)</strong></span>
                      </div>
                      <p className="text-slate-300 leading-relaxed">{inc.summary}</p>
                      <div className="text-[10px] text-slate-500 font-mono">
                        Pattern: {inc.attack_pattern} • Detected: {new Date(inc.detected_at).toLocaleTimeString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* PRAHARAK Scenario Injection Controls */}
            <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/50 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Shield className="w-4 h-4 text-amber-400" />
                    PRAHARAK On-Demand Perimeter Threat Scenarios
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Inject cryptographic spoofing, flood surges, and cross-domain hybrid attacks into the PRAHARAK pipeline.
                  </p>
                </div>
                {triggeringPraharak && (
                  <span className="text-xs font-mono text-amber-400 animate-pulse flex items-center gap-1.5">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Ingesting & Verifying...
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-1">
                {/* Scenario P1 */}
                <button
                  onClick={() => handleTriggerPraharak("normal_telemetry")}
                  disabled={triggeringPraharak !== null}
                  className="text-left p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-emerald-500/50 transition-all hover:bg-emerald-950/10 group"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-emerald-400">SCENARIO P1</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono">
                      ALLOWED
                    </span>
                  </div>
                  <div className="text-sm font-medium text-white">Valid Telemetry Beacon</div>
                  <div className="text-[11px] text-slate-400 mt-1">Enrolled gateway, authentic HMAC-SHA256 signature.</div>
                </button>

                {/* Scenario P2 */}
                <button
                  onClick={() => handleTriggerPraharak("spoofed_command")}
                  disabled={triggeringPraharak !== null}
                  className="text-left p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-rose-500/50 transition-all hover:bg-rose-950/10 group"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-rose-400">SCENARIO P2 ⭐</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-950 text-rose-300 border border-rose-800 font-mono">
                      BLOCKED
                    </span>
                  </div>
                  <div className="text-sm font-medium text-white">Spoofed Drone Reroute</div>
                  <div className="text-[11px] text-slate-400 mt-1">Hostile ASN, forged Ed25519 signature rejected before execution.</div>
                </button>

                {/* Scenario P3 */}
                <button
                  onClick={() => handleTriggerPraharak("ddos_flood")}
                  disabled={triggeringPraharak !== null}
                  className="text-left p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-amber-500/50 transition-all hover:bg-amber-950/10 group"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-amber-400">SCENARIO P3 ⭐</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-950 text-amber-300 border border-amber-800 font-mono">
                      CIRCUIT TRIP
                    </span>
                  </div>
                  <div className="text-sm font-medium text-white">Mass Command Surge</div>
                  <div className="text-[11px] text-slate-400 mt-1">17 rapid bursts trip circuit breaker to OPEN quarantine.</div>
                </button>

                {/* Scenario P4 */}
                <button
                  onClick={() => handleTriggerPraharak("hybrid_coordinated_attack")}
                  disabled={triggeringPraharak !== null}
                  className="text-left p-3.5 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-purple-500/50 transition-all hover:bg-purple-950/10 group"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-purple-400">SCENARIO P4 🌟</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-950 text-purple-300 border border-purple-800 font-mono">
                      NEXUS FUSION
                    </span>
                  </div>
                  <div className="text-sm font-medium text-white">Hybrid Attack Kill-Chain</div>
                  <div className="text-[11px] text-slate-400 mt-1">External recon probe fused with internal stolen credential exfiltration.</div>
                </button>
              </div>

              {praharakBanner && (
                <div className={`p-4 rounded-lg border flex items-start gap-3 mt-3 animate-in fade-in ${getRiskBadge(praharakBanner.level)}`}>
                  <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm">PRAHARAK INJECTED: {praharakBanner.scenario}</span>
                      <span className="text-xs px-2 py-0.2 rounded border font-mono">{praharakBanner.level}</span>
                      <span className="text-xs px-2 py-0.2 rounded bg-slate-900 border font-mono">
                        ACTION: {praharakBanner.disposition}
                      </span>
                    </div>
                    <p className="text-xs mt-1 text-slate-200">{praharakBanner.summary}</p>
                  </div>
                  <button onClick={() => setPraharakBanner(null)} className="text-xs opacity-60 hover:opacity-100">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            {/* Ingress Signals Table */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-white">Real-Time External Signal & Command Stream</h4>
                  <p className="text-xs text-slate-400">Inspecting external packets, cryptographic anti-spoofing, and edge dispositions</p>
                </div>
                <span className="text-xs text-slate-500 font-mono">Append-only SHA-256 hash-chained</span>
              </div>
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-900/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-5 py-3.5">Time</th>
                    <th className="px-5 py-3.5">Signal ID</th>
                    <th className="px-5 py-3.5">Origin IP / ASN</th>
                    <th className="px-5 py-3.5">Target Service</th>
                    <th className="px-5 py-3.5">Command Type</th>
                    <th className="px-5 py-3.5">Signature Integrity</th>
                    <th className="px-5 py-3.5">Threat Score</th>
                    <th className="px-5 py-3.5">Disposition</th>
                    <th className="px-5 py-3.5 text-right">Inspection</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {praharakSignals.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="px-5 py-8 text-center text-slate-500">
                        No external signals ingested yet. Use the scenario buttons above to inject sample external traffic.
                      </td>
                    </tr>
                  ) : (
                    praharakSignals.map((sig) => (
                      <tr key={sig.id} className="hover:bg-slate-900/60 transition-colors">
                        <td className="px-5 py-3.5 font-mono text-xs text-slate-400">
                          {new Date(sig.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                        </td>
                        <td className="px-5 py-3.5 font-mono text-xs font-semibold text-amber-400">
                          {sig.signal_identifier}
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="font-mono text-xs text-white">{sig.source_ip}</div>
                          <div className="text-[10px] text-slate-400">{sig.source_asn || "UNKNOWN ASN"}</div>
                        </td>
                        <td className="px-5 py-3.5 text-slate-200 font-mono text-xs">
                          {sig.target_service}
                        </td>
                        <td className="px-5 py-3.5">
                          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                            {sig.command_type}
                          </span>
                        </td>
                        <td className="px-5 py-3.5">
                          {sig.signature_valid ? (
                            <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono font-medium flex items-center gap-1 w-max">
                              <Check className="w-3 h-3" /> VERIFIED [{sig.signature_algorithm}]
                            </span>
                          ) : sig.raw_envelope?.signature ? (
                            <span className="text-xs px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 font-mono font-bold flex items-center gap-1 w-max">
                              <X className="w-3 h-3" /> SPOOFED / FORGED
                            </span>
                          ) : (
                            <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono w-max">
                              UNSIGNED
                            </span>
                          )}
                        </td>
                        <td className="px-5 py-3.5">
                          <span className={`text-xs px-2.5 py-0.5 rounded font-mono font-semibold ${getRiskBadge(sig.risk_tier)}`}>
                            {sig.risk_score} ({sig.risk_tier})
                          </span>
                        </td>
                        <td className="px-5 py-3.5">
                          <span
                            className={`text-xs px-2.5 py-0.5 rounded font-mono font-bold ${
                              sig.disposition === "BLOCKED"
                                ? "bg-rose-950 text-rose-300 border border-rose-800"
                                : sig.disposition === "THROTTLED"
                                ? "bg-amber-950 text-amber-300 border border-amber-800"
                                : sig.disposition === "CHALLENGED"
                                ? "bg-yellow-950 text-yellow-300 border border-yellow-800"
                                : "bg-emerald-950 text-emerald-300 border border-emerald-800"
                            }`}
                          >
                            {sig.disposition}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-right">
                          <button
                            onClick={() => setSelectedSignal(sig)}
                            className="text-xs text-amber-400 hover:text-amber-300 font-semibold inline-flex items-center gap-1 px-2.5 py-1 rounded hover:bg-slate-800 transition-colors"
                          >
                            <Eye className="w-3.5 h-3.5" /> Details
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Circuit Breaker Management */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                    <Zap className="w-4 h-4 text-amber-400" />
                    Graduated Token-Bucket Circuit Breakers
                  </h4>
                  <p className="text-xs text-slate-400">Monitored sliding-window velocity per external traffic source with automated 15-minute quarantine</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {circuitBreakers.length === 0 ? (
                  <div className="text-xs text-slate-500 py-3 col-span-3">No active circuit breaker entries recorded yet.</div>
                ) : (
                  circuitBreakers.map((cb) => (
                    <div key={cb.id} className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between font-mono">
                        <span className="text-xs font-bold text-white">{cb.source_identifier}</span>
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                            cb.state === "OPEN"
                              ? "bg-rose-950 text-rose-300 border border-rose-800"
                              : cb.state === "HALF-OPEN"
                              ? "bg-amber-950 text-amber-300 border border-amber-800"
                              : "bg-emerald-950 text-emerald-300 border border-emerald-800"
                          }`}
                        >
                          {cb.state}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 flex items-center justify-between">
                        <span>Window Requests: <strong className="text-slate-200">{cb.request_count}</strong></span>
                        {cb.is_quarantined && <span className="text-rose-400 font-semibold">QUARANTINED</span>}
                      </div>
                      {(cb.state === "OPEN" || cb.is_quarantined) && (
                        <button
                          onClick={() => handleResetCircuitBreaker(cb.source_identifier)}
                          className="w-full text-xs py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold transition-colors mt-1"
                        >
                          Manual Reset / De-quarantine
                        </button>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* MODAL 1: EXPLAINABLE FACTOR BREAKDOWN INSPECTOR */}
      {inspecting && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl animate-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-white">Explainable Risk Decomposition</h3>
                  {explanationData && (
                    <span className={`text-xs px-2.5 py-0.5 rounded-full border font-mono font-bold ${getRiskBadge(explanationData.risk_level)}`}>
                      {explanationData.risk_level} ({explanationData.total_score} / 100)
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Transparent factor attribution: Why was this access event flagged?
                </p>
              </div>
              <button
                onClick={() => setInspecting(false)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body: Factor Breakdown List */}
            <div className="p-6 overflow-y-auto space-y-4 flex-1">
              {!explanationData ? (
                <div className="py-8 text-center text-slate-400">Loading factor attribution...</div>
              ) : explanationData.factors.length === 0 ? (
                <div className="py-8 text-center text-emerald-400">
                  <CheckCircle className="w-8 h-8 mx-auto mb-2 opacity-80" />
                  Activity conforms to all historical and contextual security baselines.
                </div>
              ) : (
                explanationData.factors.map((f, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold text-indigo-400">
                        {f.factor}
                      </span>
                      <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800">
                        +{f.contribution} pts (wt: {f.weight})
                      </span>
                    </div>
                    <p className="text-sm text-slate-200">{f.explanation}</p>
                  </div>
                ))
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950 flex justify-end">
              <button
                onClick={() => setInspecting(false)}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition-colors"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: HUMAN CASE TRIAGE MODAL */}
      {reviewCaseObj && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full flex flex-col shadow-2xl animate-in zoom-in-95 duration-150">
            {/* Header */}
            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white">
                  Human Security Review: {reviewCaseObj.case_identifier}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Subject: {reviewCaseObj.primary_user_identifier} ({reviewCaseObj.department})
                </p>
              </div>
              <button
                onClick={() => setReviewCaseObj(null)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Body */}
            <div className="p-6 space-y-4">
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-2">
                  Proportional Action
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setReviewAction("ESCALATE")}
                    className={`p-3 rounded-lg border text-left flex items-center justify-between transition-all ${
                      reviewAction === "ESCALATE"
                        ? "bg-rose-950/60 border-rose-500 text-white"
                        : "bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <div>
                      <div className="font-bold text-xs">ESCALATE</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">Flag for identity verification</div>
                    </div>
                    {reviewAction === "ESCALATE" && <Check className="w-4 h-4 text-rose-400" />}
                  </button>

                  <button
                    type="button"
                    onClick={() => setReviewAction("DISMISS")}
                    className={`p-3 rounded-lg border text-left flex items-center justify-between transition-all ${
                      reviewAction === "DISMISS"
                        ? "bg-emerald-950/60 border-emerald-500 text-white"
                        : "bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <div>
                      <div className="font-bold text-xs">DISMISS</div>
                      <div className="text-[11px] text-slate-400 mt-0.5">Benign contextual variance</div>
                    </div>
                    {reviewAction === "DISMISS" && <Check className="w-4 h-4 text-emerald-400" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
                  Mandatory Human Justification (Immutable Audit Record)
                </label>
                <textarea
                  rows={3}
                  value={reviewJustification}
                  onChange={(e) => setReviewJustification(e.target.value)}
                  placeholder="State the investigative rationale for this decision..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors resize-none"
                />
                {reviewError && <p className="text-xs text-rose-400 mt-1">{reviewError}</p>}
              </div>

              {/* Quick Prompt Suggestions */}
              <div className="space-y-1.5">
                <span className="text-[11px] text-slate-400 font-medium">Quick Demo Prompts:</span>
                <div className="flex flex-wrap gap-1.5">
                  <button
                    type="button"
                    onClick={() => setReviewJustification("Confirmed critical exfiltration pattern from unregistered personal device outside shift hours.")}
                    className="text-[10px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                  >
                    + Exfiltration Justification
                  </button>
                  <button
                    type="button"
                    onClick={() => setReviewJustification("Verified with team lead: scheduled off-hours emergency operational maintenance.")}
                    className="text-[10px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                  >
                    + Scheduled Maintenance
                  </button>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center justify-between">
              <span className="text-[11px] text-slate-500 font-mono">Actor: analyst_sarah</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setReviewCaseObj(null)}
                  className="px-3 py-1.5 text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSubmitCaseReview}
                  disabled={submittingReview}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors flex items-center gap-1.5"
                >
                  {submittingReview ? "Submitting..." : "Record Determination"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 3: PRAHARAK EXTERNAL SIGNAL INSPECTOR */}
      {selectedSignal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-white">External Signal Inspection</h3>
                  <span className={`text-xs px-2.5 py-0.5 rounded-full border font-mono font-bold ${getRiskBadge(selectedSignal.risk_tier)}`}>
                    {selectedSignal.risk_tier} ({selectedSignal.risk_score} / 100)
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1 font-mono">
                  {selectedSignal.signal_identifier} • Disposition: {selectedSignal.disposition}
                </p>
              </div>
              <button
                onClick={() => setSelectedSignal(null)}
                className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 flex-1">
              {/* Envelope details */}
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2 text-xs">
                <div className="text-slate-400 font-semibold uppercase text-[10px]">Cryptographic Envelope & Transport</div>
                <div className="grid grid-cols-2 gap-2 font-mono">
                  <div>Origin IP: <span className="text-white">{selectedSignal.source_ip}</span></div>
                  <div>Origin ASN: <span className="text-white">{selectedSignal.source_asn || "N/A"}</span></div>
                  <div>Target Service: <span className="text-white">{selectedSignal.target_service}</span></div>
                  <div>Command Type: <span className="text-white">{selectedSignal.command_type}</span></div>
                  <div>Signature Algo: <span className="text-amber-400">{selectedSignal.signature_algorithm}</span></div>
                  <div>Signature Status: <span className={selectedSignal.signature_valid ? "text-emerald-400" : "text-rose-400"}>{selectedSignal.signature_valid ? "VALID" : "INVALID / SPOOFED"}</span></div>
                </div>
                <div className="mt-2 pt-2 border-t border-slate-800 text-[11px] font-mono break-all text-slate-400">
                  <span className="text-slate-500">SHA-256 Audit Chain Hash:</span> {selectedSignal.audit_hash}
                </div>
              </div>

              {/* Factors */}
              <div className="space-y-3">
                <div className="text-xs font-semibold uppercase text-slate-400 tracking-wider">
                  Attribution Factor Decomposition ({selectedSignal.factors?.length || 0} Factors)
                </div>
                {selectedSignal.factors?.map((f, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-slate-950/50 border border-slate-800/80 space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-white font-mono">{f.factor}</span>
                      <span className="text-amber-400 font-mono font-bold">+{f.contribution} pts</span>
                    </div>
                    <p className="text-slate-300">{f.explanation}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedSignal(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hybrid Analyst Command Console */}
      <CommandConsole
        onSelectCase={(caseId) => {
          const c = cases.find((item) => item.id === caseId || item.case_identifier === caseId);
          if (c) {
            setReviewCaseObj(c);
          }
        }}
        onSelectEvent={(eventId) => {
          const e = events.find((item) => item.id === eventId || item.event_id === eventId);
          if (e) {
            handleInspectEvent(e.id);
          }
        }}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800 px-6 py-4 text-xs text-slate-500 flex justify-between items-center bg-slate-950 pb-16">
        <div>NIRIKSHAK Prototype — Defensive Decision Support System</div>
        <div className="font-mono">Unusual Activity ≠ Confirmed Malicious Activity</div>
      </footer>
    </div>
  );
}
