"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Terminal as TerminalIcon,
  ChevronDown,
  ChevronUp,
  Maximize2,
  Minimize2,
  Trash2,
  ShieldCheck,
  Zap,
} from "lucide-react";
import {
  checkHealth,
  fetchEvents,
  fetchCases,
  fetchCaseDetail,
  fetchEventExplanation,
  fetchPolicies,
  fetchDevices,
  fetchPraharakSignals,
  fetchCircuitBreakerStates,
  resetCircuitBreaker,
  fetchCrossDomainIncidents,
  triggerPraharakScenario,
} from "@/lib/api";

interface CommandConsoleProps {
  onSelectCase?: (caseId: string) => void;
  onSelectEvent?: (eventId: string) => void;
}

interface ConsoleLine {
  id: string;
  type: "input" | "output" | "error" | "info";
  content: string | React.ReactNode;
}

const ALLOWED_COMMANDS = [
  "help",
  "status",
  "events",
  "cases",
  "investigate",
  "explain",
  "devices",
  "policy",
  "praharak",
  "clear",
];

export const CommandConsole: React.FC<CommandConsoleProps> = ({
  onSelectCase,
  onSelectEvent,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [inputVal, setInputVal] = useState("");
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number>(-1);
  const [lines, setLines] = useState<ConsoleLine[]>([
    {
      id: "welcome",
      type: "info",
      content:
        "NIRIKSHAK Analyst Command Console v1.0.0 [Active Mode: AST Allowlist / REST]\nType 'help' to inspect available analytical commands.",
    },
  ]);

  const outputEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    outputEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  // Global hotkey Ctrl + ~
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && (e.key === "~" || e.key === "`")) {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const addLine = (type: "input" | "output" | "error" | "info", content: string | React.ReactNode) => {
    setLines((prev) => [...prev, { id: `${Date.now()}-${Math.random()}`, type, content }]);
  };

  const handleCommandExecution = async (rawCmd: string) => {
    const trimmed = rawCmd.trim();
    if (!trimmed) return;

    // Add to command history
    setHistory((prev) => [...prev, trimmed]);
    setHistoryIndex(-1);

    // Echo input
    addLine("input", `nirikshak:analyst_sarah> ${trimmed}`);

    const parts = trimmed.split(/\s+/);
    const command = parts[0].toLowerCase();
    const args = parts.slice(1);

    // AST / Security Allowlist Check (Zero OS Shell Breakout)
    if (!ALLOWED_COMMANDS.includes(command)) {
      addLine(
        "error",
        `Access Prohibited / Unknown command: '${command}'. Browser shell access is strictly forbidden by NIRIKSHAK policy. Type 'help' for allowlisted commands.`
      );
      return;
    }

    try {
      switch (command) {
        case "clear":
          setLines([]);
          break;

        case "help":
          addLine(
            "output",
            `AVAILABLE SOC ANALYST COMMANDS:
  status                     - Verify backend services, DB connectivity & active policy weights
  events [limit]             - List recent access events (default limit: 10)
  cases                      - List open security cases requiring human review
  investigate <id>           - Display deep-dive case dossier and audit history
  explain <event_id>         - Output multi-factor mathematical risk attribution breakdown
  devices                    - List enrolled corporate devices and current trust levels
  policy                     - View active dimensional scoring weights and threshold tiers
  praharak <subcommand>      - PRAHARAK Perimeter & Outsider Risk Command Subsystem:
    • praharak status        - View perimeter defense health & circuit breaker counts
    • praharak signals [n]   - List recent external ingress signals & dispositions
    • praharak circuit       - Inspect tracked source IPs and active quarantines
    • praharak reset <ip>    - Manually reset a tripped circuit breaker
    • praharak incidents     - List cross-domain NIRIKSHAK-PRAHARAK hybrid incidents
    • praharak trigger <scn> - Inject scenario (normal_telemetry | spoofed_command | ddos_flood | hybrid_coordinated_attack)
  clear                      - Clear console output window`
          );
          break;

        case "status": {
          addLine("info", "Querying analytical subsystem health...");
          const [health, policyData] = await Promise.all([checkHealth(), fetchPolicies()]);
          const weights = policyData.active_weights || {};
          addLine(
            "output",
            `[SYSTEM HEALTH & SUBSYSTEM STATUS]
Status:          ${health.status?.toUpperCase() || "OPERATIONAL"}
Database:        ${health.database?.toUpperCase() || "CONNECTED"} (PostgreSQL 16)
IsolationForest: ACTIVE (Loaded v1.0.0, 6D Feature Vector)
Correlation:     ACTIVE (15m Temporal Sliding Window)

[ACTIVE RISK WEIGHTS (Sum: ${policyData.weight_sum})]
• Identity:     ${weights.WEIGHT_IDENTITY}
• Device:       ${weights.WEIGHT_DEVICE}
• Sensitivity:  ${weights.WEIGHT_SENSITIVITY}
• Behavior:     ${weights.WEIGHT_BEHAVIOR}
• ML Anomaly:   ${weights.WEIGHT_ANOMALY}
• Correlation:  ${weights.WEIGHT_CORRELATION}`
          );
          break;
        }

        case "events": {
          const limit = args[0] ? parseInt(args[0], 10) : 10;
          addLine("info", `Fetching latest ${limit} events from telemetry store...`);
          const evts = await fetchEvents(limit);
          if (!evts || evts.length === 0) {
            addLine("output", "No access events recorded in current database session.");
            return;
          }

          const header = "EVENT ID        | USER     | ACTION | DATA VOL | RISK | LEVEL";
          const divider = "----------------+----------+--------+----------+------+----------";
          const rows = evts.map((e: any) => {
            const eid = (e.event_id || "").padEnd(15);
            const usr = (e.user_identifier || "").padEnd(8);
            const act = (e.action || "").padEnd(6);
            const vol = `${Math.round((e.data_volume || 0) / 1024)} KB`.padEnd(8);
            const rsk = `${e.total_score ?? "N/A"}`.padEnd(4);
            const lvl = e.risk_level || "LOW";
            return `${eid} | ${usr} | ${act} | ${vol} | ${rsk} | ${lvl}`;
          });

          addLine("output", [header, divider, ...rows].join("\n"));
          break;
        }

        case "cases": {
          addLine("info", "Querying open security cases...");
          const cases = await fetchCases();
          if (!cases || cases.length === 0) {
            addLine("output", "All security cases resolved. No open cases pending review.");
            return;
          }

          const header = "CASE IDENTIFIER  | SEVERITY | STATUS | USER     | OPENED AT";
          const divider = "-----------------+----------+--------+----------+--------------------";
          const rows = cases.map((c: any) => {
            const cid = (c.case_identifier || "").padEnd(16);
            const sev = (c.severity || "").padEnd(8);
            const st = (c.status || "").padEnd(6);
            const usr = (c.primary_user_identifier || "").padEnd(8);
            const dt = (c.opened_at || "").slice(0, 19).replace("T", " ");
            return `${cid} | ${sev} | ${st} | ${usr} | ${dt}`;
          });

          addLine("output", [header, divider, ...rows].join("\n"));
          break;
        }

        case "investigate": {
          if (!args[0]) {
            addLine("error", "Usage: investigate <CASE_IDENTIFIER_OR_ID>");
            return;
          }
          const caseId = args[0];
          addLine("info", `Fetching case details for ${caseId}...`);
          const detail = await fetchCaseDetail(caseId);
          if (onSelectCase) onSelectCase(detail.id);

          const factorSummary = (detail.factors || [])
            .map(
              (f: any) =>
                `  • [${f.factor}] +${f.contribution} pts (Subscore: ${f.subscore})\n    ${f.explanation}`
            )
            .join("\n");

          addLine(
            "output",
            `==================== CASE DOSSIER: ${detail.case_identifier} ====================
Status:       ${detail.status}
Severity:     ${detail.severity} (Score: ${detail.total_score}/100)
Subject:      ${detail.primary_user_identifier} (${detail.department})
Resource:     ${detail.resource_name || "N/A"}
Endpoint:     ${detail.device_identifier || "N/A"}
Opened At:    ${detail.opened_at}

KEY RISK FACTORS ATTRIBUTED:
${factorSummary || "  No factors recorded."}
================================================================================`
          );
          break;
        }

        case "explain": {
          if (!args[0]) {
            addLine("error", "Usage: explain <EVENT_ID>");
            return;
          }
          const eventId = args[0];
          addLine("info", `Decomposing factor attribution for event ${eventId}...`);
          const expl = await fetchEventExplanation(eventId);
          if (onSelectEvent) onSelectEvent(expl.event_id);

          const header = "FACTOR                             | SUBSCORE | WEIGHT | CONTRIBUTION";
          const divider = "-----------------------------------+----------+--------+-------------";
          const rows = (expl.factors || []).map((f: any) => {
            const name = (f.factor || "").padEnd(34);
            const sub = `${f.subscore}`.padEnd(8);
            const wt = `${f.weight}`.padEnd(6);
            const cont = `+${f.contribution} pts`;
            return `${name} | ${sub} | ${wt} | ${cont}`;
          });

          addLine(
            "output",
            `EVENT ${expl.event_id} RISK ATTRIBUTION MATRIX (Score: ${expl.total_score} [${expl.risk_level}])\n${[
              header,
              divider,
              ...rows,
            ].join("\n")}`
          );
          break;
        }

        case "devices": {
          addLine("info", "Listing registered endpoints...");
          const devs = await fetchDevices();
          const header = "DEVICE ID   | TYPE               | REGISTERED | TRUST LEVEL | STATUS";
          const divider = "------------+--------------------+------------+-------------+---------";
          const rows = devs.map((d: any) => {
            const id = (d.device_identifier || "").padEnd(11);
            const type = (d.device_type || "").padEnd(18);
            const reg = (d.registered ? "YES" : "NO").padEnd(10);
            const tr = (d.trust_level || "").padEnd(11);
            const st = d.status || "ACTIVE";
            return `${id} | ${type} | ${reg} | ${tr} | ${st}`;
          });
          addLine("output", [header, divider, ...rows].join("\n"));
          break;
        }

        case "policy": {
          addLine("info", "Querying risk calculation policies...");
          const pol = await fetchPolicies();
          const w = pol.active_weights || {};
          const t = pol.active_thresholds || {};
          addLine(
            "output",
            `NIRIKSHAK ACTIVE RISK SCORING WEIGHTS:
  Identity Signal (w_I):     ${w.WEIGHT_IDENTITY}
  Device Trust (w_D):        ${w.WEIGHT_DEVICE}
  Sensitivity (w_S):         ${w.WEIGHT_SENSITIVITY}
  Behavior Baseline (w_B):   ${w.WEIGHT_BEHAVIOR}
  ML Anomaly Signal (w_A):   ${w.WEIGHT_ANOMALY}
  Correlation Signal (w_C):  ${w.WEIGHT_CORRELATION}
  -----------------------------------------------
  Total Weight Sum:          ${pol.weight_sum} (Valid: ${pol.is_weight_sum_valid})

DECISION THRESHOLDS:
  LOW:       0.0 - ${t.THRESHOLD_LOW}
  MODERATE:  ${t.THRESHOLD_MODERATE} - ${t.THRESHOLD_HIGH - 1}
  HIGH:      ${t.THRESHOLD_HIGH} - ${t.THRESHOLD_CRITICAL - 1}
  CRITICAL:  ${t.THRESHOLD_CRITICAL} - 100.0`
          );
          break;
        }

        case "praharak": {
          const sub = (args[0] || "help").toLowerCase();
          const subArgs = args.slice(1);

          switch (sub) {
            case "help": {
              addLine(
                "output",
                `PRAHARAK PERIMETER DEFENSE SUBCOMMANDS:
  praharak status          - Summary of perimeter telemetry, circuit breakers & incidents
  praharak signals [limit] - Stream recent external signals (default limit: 10)
  praharak circuit         - Inspect token-bucket velocity counters & quarantine states
  praharak reset <ip>      - Clear quarantine and reset circuit breaker for source IP
  praharak incidents       - List cross-domain correlation incidents (NIRIKSHAK + PRAHARAK)
  praharak trigger <scn>   - Trigger synthetic threat scenario:
                             • normal_telemetry
                             • spoofed_command
                             • ddos_flood
                             • hybrid_coordinated_attack`
              );
              break;
            }

            case "status": {
              addLine("info", "Querying PRAHARAK perimeter subsystems...");
              const [signals, breakers, incidents] = await Promise.all([
                fetchPraharakSignals(50),
                fetchCircuitBreakerStates(),
                fetchCrossDomainIncidents(10),
              ]);

              const quarantinedCount = (breakers || []).filter((b: any) => b.is_quarantined || b.state === "OPEN").length;
              const blockedSignals = (signals || []).filter((s: any) => s.disposition === "BLOCKED").length;
              const throttledSignals = (signals || []).filter((s: any) => s.disposition === "THROTTLED").length;

              addLine(
                "output",
                `[PRAHARAK PERIMETER DEFENSE STATUS]
Subsystem:           ACTIVE & SYNCHRONIZED
Ingress Protection:  ZERO-TRUST CRYPTOGRAPHIC ENGINE (Ed25519, HMAC-SHA256, PQC Dilithium-3)
Rate Limiting:       SLIDING TOKEN-BUCKET (10s Burst / 60s Sustained)
Correlation Nexus:   SHARED 30-MIN TEMPORAL SLIDING WINDOW

[PERIMETER METRICS]
• Total Tracked Ingress Signals: ${signals?.length || 0}
• Blocked Signals:               ${blockedSignals}
• Throttled Signals:             ${throttledSignals}
• Active Circuit Breakers:       ${breakers?.length || 0} (Quarantined: ${quarantinedCount})
• Cross-Domain Incidents:        ${incidents?.length || 0}`
              );
              break;
            }

            case "signals": {
              const limit = subArgs[0] ? parseInt(subArgs[0], 10) : 10;
              addLine("info", `Fetching latest ${limit} external signals...`);
              const sigs = await fetchPraharakSignals(limit);
              if (!sigs || sigs.length === 0) {
                addLine("output", "No external signals recorded. Run 'praharak trigger <scenario>' to simulate.");
                return;
              }

              const header = "SIGNAL ID       | PROTOCOL | SOURCE IP       | RECON TACTIC | SCORE | DISPOSITION";
              const divider = "----------------+----------+-----------------+--------------+-------+------------";
              const rows = sigs.map((s: any) => {
                const sid = (s.signal_id || "").padEnd(15);
                const proto = (s.protocol || "").padEnd(8);
                const ip = (s.source_ip || "").padEnd(15);
                const recon = (s.recon_tactics?.[0] || "NONE").padEnd(12);
                const score = `${Math.round(s.final_risk_score ?? 0)}`.padEnd(5);
                const disp = s.disposition || "ALLOWED";
                return `${sid} | ${proto} | ${ip} | ${recon} | ${score} | ${disp}`;
              });

              addLine("output", [header, divider, ...rows].join("\n"));
              break;
            }

            case "circuit": {
              addLine("info", "Querying circuit breaker registry...");
              const breakers = await fetchCircuitBreakerStates();
              if (!breakers || breakers.length === 0) {
                addLine("output", "No circuit breakers currently tracking external sources.");
                return;
              }

              const header = "SOURCE IDENTIFIER | STATE     | BURST | SUSTAINED | QUARANTINED UNTIL";
              const divider = "------------------+-----------+-------+-----------+-----------------------";
              const rows = breakers.map((b: any) => {
                const src = (b.source_identifier || "").padEnd(17);
                const st = (b.state || "CLOSED").padEnd(9);
                const burst = `${b.fast_counter || 0}/15`.padEnd(5);
                const sust = `${b.slow_counter || 0}/60`.padEnd(9);
                const quar = b.quarantined_until ? new Date(b.quarantined_until).toLocaleTimeString() : "NONE";
                return `${src} | ${st} | ${burst} | ${sust} | ${quar}`;
              });

              addLine("output", [header, divider, ...rows].join("\n"));
              break;
            }

            case "reset": {
              if (!subArgs[0]) {
                addLine("error", "Usage: praharak reset <SOURCE_IP_OR_IDENTIFIER>");
                return;
              }
              const ip = subArgs[0];
              addLine("info", `Resetting circuit breaker for ${ip}...`);
              const res = await resetCircuitBreaker(ip);
              addLine(
                "output",
                `Circuit breaker for '${res.source_identifier}' has been reset to state: ${res.state} (Counters zeroed, quarantine lifted).`
              );
              break;
            }

            case "incidents": {
              addLine("info", "Querying cross-domain correlation incidents...");
              const incs = await fetchCrossDomainIncidents(10);
              if (!incs || incs.length === 0) {
                addLine("output", "No cross-domain incidents detected. Trigger 'hybrid_coordinated_attack' to simulate.");
                return;
              }

              const header = "INCIDENT ID          | SEVERITY | SCORE | EXTERNAL IP     | INTERNAL USER | CORRELATED AT";
              const divider = "---------------------+----------+-------+-----------------+---------------+--------------------";
              const rows = incs.map((i: any) => {
                const iid = (i.incident_id || "").padEnd(20);
                const sev = (i.severity || "").padEnd(8);
                const sc = `${Math.round(i.unified_score || 0)}`.padEnd(5);
                const extIp = (i.external_source_ip || "").padEnd(15);
                const usr = (i.compromised_user_id || "").padEnd(13);
                const dt = (i.correlated_at || "").slice(0, 19).replace("T", " ");
                return `${iid} | ${sev} | ${sc} | ${extIp} | ${usr} | ${dt}`;
              });

              addLine("output", [header, divider, ...rows].join("\n"));
              break;
            }

            case "trigger": {
              const scn = subArgs[0];
              const validScenarios = [
                "normal_telemetry",
                "spoofed_command",
                "ddos_flood",
                "hybrid_coordinated_attack",
              ];
              if (!scn || !validScenarios.includes(scn)) {
                addLine(
                  "error",
                  `Invalid scenario '${scn}'. Valid options:\n  • normal_telemetry\n  • spoofed_command\n  • ddos_flood\n  • hybrid_coordinated_attack`
                );
                return;
              }

              addLine("info", `Injecting synthetic scenario '${scn}' into PRAHARAK pipeline...`);
              const res = await triggerPraharakScenario(scn as any);
              addLine(
                "output",
                `[SCENARIO EXECUTED: ${res.scenario}]
Status:      ${res.status.toUpperCase()}
Message:     ${res.message}
Target IP:   ${res.source_ip || "N/A"}
Result Summary:
  • Signals Processed: ${res.signals_created || (res.signal ? 1 : 0)}
  • Disposition:       ${res.signal?.disposition || res.circuit_breaker?.state || "PROCESSED"}
  • Risk Score:        ${res.signal?.final_risk_score ?? "N/A"}`
              );
              break;
            }

            default:
              addLine("error", `Unknown PRAHARAK subcommand: '${sub}'. Run 'praharak help' for usage.`);
              break;
          }
          break;
        }
      }
    } catch (err: any) {
      addLine("error", `Execution error: ${err?.response?.data?.detail || err?.message || String(err)}`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleCommandExecution(inputVal);
      setInputVal("");
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (history.length > 0) {
        const nextIdx = historyIndex === -1 ? history.length - 1 : Math.max(0, historyIndex - 1);
        setHistoryIndex(nextIdx);
        setInputVal(history[nextIdx]);
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (historyIndex !== -1) {
        const nextIdx = historyIndex + 1;
        if (nextIdx >= history.length) {
          setHistoryIndex(-1);
          setInputVal("");
        } else {
          setHistoryIndex(nextIdx);
          setInputVal(history[nextIdx]);
        }
      }
    } else if (e.key === "Tab") {
      e.preventDefault();
      const current = inputVal.trim();
      if (current) {
        const match = ALLOWED_COMMANDS.find((cmd) => cmd.startsWith(current.toLowerCase()));
        if (match) setInputVal(match);
      }
    }
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-3 right-4 z-50">
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-700 hover:border-emerald-500 rounded text-xs font-mono text-emerald-400 shadow-xl transition-all"
        >
          <TerminalIcon className="w-3.5 h-3.5 text-emerald-400" />
          <span>NIRIKSHAK CONSOLE</span>
          <span className="text-slate-500 text-[10px]">[Ctrl+~]</span>
        </button>
      </div>
    );
  }

  return (
    <aside
      aria-label="NIRIKSHAK Analyst Command Console"
      className={`fixed bottom-0 left-0 right-0 z-40 bg-slate-950/95 border-t border-slate-800 backdrop-blur-md transition-all duration-200 flex flex-col font-mono shadow-2xl ${
        isExpanded ? "h-[500px]" : "h-72"
      }`}
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800 text-xs">
        <div className="flex items-center gap-2">
          <TerminalIcon className="w-4 h-4 text-emerald-400" />
          <span className="font-semibold text-slate-200">NIRIKSHAK ANALYST CONSOLE</span>
          <span className="text-[10px] text-slate-500 hidden sm:inline">| AST ALLOWLIST REST PARSER</span>
          <div className="flex items-center gap-1.5 ml-2 px-2 py-0.5 rounded bg-emerald-950/50 border border-emerald-800/60 text-emerald-400 text-[10px]">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>CONNECTED</span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-slate-400">
          <span className="text-[10px] text-slate-500 hidden md:inline">Ctrl + ~ to toggle</span>
          <button
            onClick={() => setLines([])}
            title="Clear Console"
            className="p-1 hover:text-slate-200 hover:bg-slate-800 rounded transition"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? "Collapse" : "Expand"}
            className="p-1 hover:text-slate-200 hover:bg-slate-800 rounded transition"
          >
            {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            title="Minimize"
            className="p-1 hover:text-slate-200 hover:bg-slate-800 rounded transition"
          >
            <ChevronDown className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Output Stream */}
      <div
        tabIndex={0}
        aria-label="Console Output Feed"
        className="flex-1 overflow-y-auto p-3 text-xs space-y-1.5 text-slate-300 selection:bg-emerald-900/50"
      >
        {lines.map((l) => {
          if (l.type === "input") {
            return (
              <div key={l.id} className="text-emerald-400 font-semibold">
                {l.content}
              </div>
            );
          }
          if (l.type === "error") {
            return (
              <div key={l.id} className="text-rose-400 bg-rose-950/30 border border-rose-900/50 p-2 rounded whitespace-pre-wrap">
                {l.content}
              </div>
            );
          }
          if (l.type === "info") {
            return (
              <div key={l.id} className="text-cyan-400/90 whitespace-pre-wrap">
                {l.content}
              </div>
            );
          }
          return (
            <pre key={l.id} className="text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">
              {l.content}
            </pre>
          );
        })}
        <div ref={outputEndRef} />
      </div>

      {/* Command Input Bar */}
      <div className="flex items-center px-3 py-2 bg-slate-900/90 border-t border-slate-800/80">
        <span className="text-emerald-400 font-semibold mr-2 select-none text-xs">
          nirikshak:analyst_sarah&gt;
        </span>
        <input
          ref={inputRef}
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter command (e.g. 'status', 'events 5', 'cases', 'explain evt_...')..."
          className="flex-1 bg-transparent text-slate-100 text-xs font-mono focus:outline-none placeholder:text-slate-600"
          autoFocus
          spellCheck={false}
        />
        <span className="text-[10px] text-slate-600 font-sans hidden sm:inline ml-2">
          TAB autocomplete • ↑↓ history
        </span>
      </div>
    </aside>
  );
};
