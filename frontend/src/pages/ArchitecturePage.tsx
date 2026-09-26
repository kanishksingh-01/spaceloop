import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface TeamMember {
  id: string;
  name: string;
  role: string;
  focus: string;
  initials: string;
  avatarGradient: string;
  accentColor: 'indigo' | 'cyan' | 'violet' | 'amber';
  badge: string;
  thesis: string;
  bio: string;
  architecturalContributions: {
    system: string;
    description: string;
    metric: string;
  }[];
  stack: string[];
  links: {
    label: string;
    icon: string;
    url: string;
  }[];
}

const teamMembers: TeamMember[] = [
  {
    id: 'kanishk-singh',
    name: 'Kanishk Singh',
    role: 'Founding Architect & Systems Lead',
    focus: 'Distributed State • Micro-Escrow Protocols • Contract Automata',
    initials: 'KS',
    avatarGradient: 'from-indigo-600 via-violet-600 to-indigo-900',
    accentColor: 'indigo',
    badge: 'Core Engine & Ledger',
    thesis:
      'Physical capacity is the ultimate perishable asset. We design idempotent micro-leases that settle in seconds rather than months of commercial bureaucracy.',
    bio:
      'Specializes in deterministic state machines and transactional escrow systems. Architected SpaceLoop’s dual-ledger settlement protocol and zero-friction ₹100 UPI hold engine.',
    architecturalContributions: [
      {
        system: 'Deterministic Micro-Lease Automaton',
        description: 'Auto-compiles legally binding licensee licenses under the Indian Easements Act (1882) without tenancy exposure.',
        metric: '100% Deterministic',
      },
      {
        system: 'UPI Hold-and-Release Micro-Escrow',
        description: 'Real-time security hold dispatch with zero-cost cancellation and automatic instant release upon checkout audit.',
        metric: '₹100 Instant Hold',
      },
      {
        system: 'Fault-Tolerant Transaction Router',
        description: 'Multi-tier routing separating synchronous booking commits from asynchronous transactional email dispatch via Resend.',
        metric: '< 180ms Latency',
      },
    ],
    stack: ['Python / Flask', 'Distributed SQLite', 'SQLAlchemy Core', 'Resend API', 'UPI Autopay'],
    links: [
      { label: 'GitHub', icon: 'fa-brands fa-github', url: 'https://github.com/kanishksingh-01' },
      { label: 'LinkedIn', icon: 'fa-brands fa-linkedin', url: 'https://linkedin.com' },
      { label: 'Architecture Spec', icon: 'fa-solid fa-file-code', url: '#' },
    ],
  },
  {
    id: 'ananya-sharma',
    name: 'Ananya Sharma',
    role: 'Head of Multimodal AI & Spatial Vision',
    focus: 'Multimodal Vision Models • Room Scanners • Semantic Match',
    initials: 'AS',
    avatarGradient: 'from-cyan-600 via-blue-600 to-indigo-900',
    accentColor: 'cyan',
    badge: 'Multimodal Intelligence',
    thesis:
      'AI shouldn’t control commerce; it should remove cognitive friction. A host should be able to snap a room photo and have optimal pricing and telemetry extracted in real time.',
    bio:
      'Leads the AI vision pipeline and semantic space ranking heuristics. Designed the Multimodal Room Inspector that detects furniture density, monitors, acoustics, and natural lighting.',
    architecturalContributions: [
      {
        system: 'Multimodal Room Capacity Scanner',
        description: 'Evaluates workspace photos to identify ergonomic seating, monitors, power outlets, and suggest fair hourly tariff bounds.',
        metric: '94% Valuation Accuracy',
      },
      {
        system: 'Natural-Language Intent Matchmaker',
        description: 'Groq + Gemini intent parsing with deterministic Haversine distance, budget fit, and amenity overlap scoring.',
        metric: '< 250ms Ranking Pass',
      },
      {
        system: 'Post-Occupancy Vision Delta Check',
        description: 'Differential edge detection comparing check-in vs check-out photos to verify tidiness and lights-off protocol.',
        metric: 'Automated Room Audit',
      },
    ],
    stack: ['Gemini 1.5 Pro/Flash', 'Groq LPU', 'PyTorch / OpenCV', 'Vector Embeddings', 'FastAPI'],
    links: [
      { label: 'GitHub', icon: 'fa-brands fa-github', url: 'https://github.com' },
      { label: 'HuggingFace', icon: 'fa-solid fa-brain', url: 'https://huggingface.co' },
      { label: 'Scholar', icon: 'fa-solid fa-graduation-cap', url: '#' },
    ],
  },
  {
    id: 'kabir-verma',
    name: 'Kabir Verma',
    role: 'Head of Trust, Verification & Cryptography',
    focus: 'DigiLocker Tokens • Sovereign Identity • Discom Audit',
    initials: 'KV',
    avatarGradient: 'from-violet-600 via-purple-600 to-slate-900',
    accentColor: 'violet',
    badge: 'Sovereign Verification',
    thesis:
      'True peer-to-peer sharing cannot survive on star ratings alone. We anchor trust in cryptographic government identity tokens and utility possession records.',
    bio:
      'Specializes in Zero-Knowledge proof patterns and DPDP Act (2023) privacy compliance. Built the twin-gate trust pipeline verifying seekers via DigiLocker and hosts via Discom records.',
    architecturalContributions: [
      {
        system: 'Aadhaar Tokenized DigiLocker KYC',
        description: 'Zero plaintext Aadhaar storage. Generates salted irreversible SHA-256 tokens linked to verified institutional domains.',
        metric: '0 Plaintext PII Stored',
      },
      {
        system: 'Electricity Discom Legal CA Verifier',
        description: 'Validates commercial/residential possession against BESCOM and TPDDL utility consumer accounts and penny drops.',
        metric: '100% Premise Proof',
      },
      {
        system: 'Immutable Audit Log Ledger',
        description: 'Tamper-evident event stream capturing every authentication challenge, geofence handshake, and payout trigger.',
        metric: 'Append-Only Telemetry',
      },
    ],
    stack: ['DigiLocker API', 'NPCI Bharat BillPay', 'Argon2id', 'DPDP Compliance', 'Audit Streaming'],
    links: [
      { label: 'GitHub', icon: 'fa-brands fa-github', url: 'https://github.com' },
      { label: 'Keybase', icon: 'fa-brands fa-keybase', url: 'https://keybase.io' },
      { label: 'Security Advisory', icon: 'fa-solid fa-shield-halved', url: '#' },
    ],
  },
  {
    id: 'rhea-kapoor',
    name: 'Rhea Kapoor',
    role: 'Head of Product Experience & Spatial Systems',
    focus: 'Zero-Hardware Access • Tactile UI • Realtime Telemetry',
    initials: 'RK',
    avatarGradient: 'from-amber-500 via-orange-600 to-slate-900',
    accentColor: 'amber',
    badge: 'Spatial Experience & HUD',
    thesis:
      'The best hardware is no hardware. We replace ₹50,000 smart lock installations with mobile geofencing and dynamic temporal QR handshakes.',
    bio:
      'Passionate about high-density information architecture, tactile feedback, and accessible mobile design. Designed SpaceLoop’s live in-room countdown HUD and door access passes.',
    architecturalContributions: [
      {
        system: 'Zero-Hardware Geofence Handshake',
        description: 'Sub-50m Haversine GPS proximity check coupled with rotating dynamic OTPs, eliminating proprietary lock hardware.',
        metric: '< 50m Proximity Unlock',
      },
      {
        system: 'Live In-Room Session Console',
        description: 'Real-time countdown timer, noise guidance, extension request flow, and WiFi credentials embedded directly in browser.',
        metric: 'Zero App Install Required',
      },
      {
        system: 'Dual-Theme Motion Design System',
        description: 'One-directional downward-right shadow hierarchy with WCAG AAA contrast, tactile button glows, and zero sticky states.',
        metric: '60 FPS Tactile HUD',
      },
    ],
    stack: ['React 18 / TypeScript', 'Tailwind CSS', 'Vite', 'HTML5 Geolocation', 'Framer Motion'],
    links: [
      { label: 'GitHub', icon: 'fa-brands fa-github', url: 'https://github.com' },
      { label: 'Dribbble', icon: 'fa-brands fa-dribbble', url: 'https://dribbble.com' },
      { label: 'Design Specs', icon: 'fa-solid fa-compass-drafting', url: '#' },
    ],
  },
];

export const ArchitecturePage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedMember, setSelectedMember] = useState<string>(teamMembers[0].id);
  const [activeTab, setActiveTab] = useState<'all' | 'systems' | 'ai' | 'security' | 'experience'>('all');

  const filteredMembers = teamMembers.filter((m) => {
    if (activeTab === 'all') return true;
    if (activeTab === 'systems') return m.id === 'kanishk-singh';
    if (activeTab === 'ai') return m.id === 'ananya-sharma';
    if (activeTab === 'security') return m.id === 'kabir-verma';
    if (activeTab === 'experience') return m.id === 'rhea-kapoor';
    return true;
  });

  const activeMemberData = teamMembers.find((m) => m.id === selectedMember) || teamMembers[0];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased selection:bg-indigo-500 selection:text-white">
      {/* 1. Minimal Page Header */}
      <section className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-xl sticky top-16 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/')}
              className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition"
            >
              <i className="fa-solid fa-arrow-left text-[11px]" />
              <span>Back to SpaceLoop</span>
            </button>
            <span className="text-slate-700">|</span>
            <div className="inline-flex items-center gap-2 text-xs font-bold text-white">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
              <span>Meet the Team & System Architecture</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono font-medium text-slate-400 hidden sm:inline">
              Core Protocol v2.5.0
            </span>
            <span className="text-[10px] uppercase font-extrabold tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
              100% Production Audit
            </span>
          </div>
        </div>
      </section>

      {/* 2. Distinctive Hero Section */}
      <section className="relative overflow-hidden pt-16 pb-20 md:pt-24 md:pb-28 border-b border-slate-800/80 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950">
        <div
          className="absolute inset-0 pointer-events-none opacity-20"
          style={{
            backgroundImage: "radial-gradient(rgba(99, 102, 241, 0.3) 1px, transparent 1px)",
            backgroundSize: "36px 36px",
          }}
        />

        <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-indigo-600/15 blur-[130px] rounded-full pointer-events-none" />
        <div className="absolute top-20 right-10 w-[380px] h-[380px] bg-cyan-600/10 blur-[120px] rounded-full pointer-events-none" />

        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/25 text-indigo-300 text-xs font-bold mb-6">
            <i className="fa-solid fa-layer-group text-[11px]" />
            <span>Founding Engineering & Product Collective</span>
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight text-white leading-tight">
            The People Behind <br className="hidden sm:inline" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-violet-300 to-cyan-300">
              SpaceLoop
            </span>
          </h1>

          <p className="mt-6 text-xl sm:text-2xl text-slate-200 font-semibold tracking-tight max-w-3xl mx-auto">
            “Four minds. One mission. Making every suitable space work smarter.”
          </p>

          <p className="mt-4 text-sm sm:text-base text-slate-400 max-w-2xl mx-auto leading-relaxed">
            We are systems engineers, AI researchers, cryptographers, and product designers building a frictionless physical space network anchored in sovereign verification, zero-hardware access, and automated micro-leases.
          </p>

          {/* System Metrics Strip */}
          <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto text-left">
            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 floating-container">
              <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Zero-Hardware Mesh</div>
              <div className="text-2xl font-black text-white mt-1">50m GPS / QR</div>
              <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
                <i className="fa-solid fa-check text-[9px]" /> Instant Proximity Entry
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 floating-container">
              <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Settlement Engine</div>
              <div className="text-2xl font-black text-white mt-1">₹100 UPI Hold</div>
              <div className="text-[11px] text-indigo-400 mt-1 flex items-center gap-1">
                <i className="fa-solid fa-shield text-[9px]" /> Auto Micro-Escrow
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 floating-container">
              <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Sovereign Identity</div>
              <div className="text-2xl font-black text-white mt-1">0 Plaintext</div>
              <div className="text-[11px] text-cyan-400 mt-1 flex items-center gap-1">
                <i className="fa-solid fa-id-card text-[9px]" /> DigiLocker DPDP Token
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 floating-container">
              <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Transactional Rail</div>
              <div className="text-2xl font-black text-white mt-1">Resend API</div>
              <div className="text-[11px] text-amber-400 mt-1 flex items-center gap-1">
                <i className="fa-solid fa-envelope text-[9px]" /> Real Verified Mailer
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Creative Team & Architecture Showcase */}
      <section className="py-20 bg-slate-950 border-b border-slate-800/80 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
            <div>
              <div className="inline-flex items-center gap-1.5 text-xs font-bold text-cyan-400 uppercase tracking-wider mb-2">
                <i className="fa-solid fa-microchip" /> Cross-Functional Engineering Leads
              </div>
              <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
                Architectural Leadership & Core Disciplines
              </h2>
              <p className="text-slate-400 text-sm mt-1 max-w-xl">
                Explore the specialized technical domains that form the bedrock of SpaceLoop’s zero-hardware peer-to-peer marketplace.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2 p-1.5 bg-slate-900/90 rounded-2xl border border-slate-800">
              {[
                { key: 'all', label: 'All Disciplines' },
                { key: 'systems', label: 'Systems & Ledger' },
                { key: 'ai', label: 'Multimodal AI' },
                { key: 'security', label: 'Identity & Trust' },
                { key: 'experience', label: 'Spatial HUD' },
              ].map((tab) => (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setActiveTab(tab.key as any)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition ${
                    activeTab === tab.key
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Member Card Showcase */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
            {filteredMembers.map((member) => {
              const isSelected = selectedMember === member.id;
              return (
                <div
                  key={member.id}
                  onClick={() => setSelectedMember(member.id)}
                  className={`bg-slate-900/90 border rounded-3xl p-6 sm:p-8 flex flex-col justify-between transition-all cursor-pointer floating-panel relative overflow-hidden group ${
                    isSelected
                      ? 'border-indigo-500/70 ring-1 ring-indigo-500/40'
                      : 'border-slate-800/80 hover:border-slate-700'
                  }`}
                >
                  <div
                    className={`absolute -top-24 -right-24 w-48 h-48 rounded-full blur-[80px] pointer-events-none transition opacity-30 group-hover:opacity-70 ${
                      member.accentColor === 'cyan'
                        ? 'bg-cyan-500'
                        : member.accentColor === 'amber'
                        ? 'bg-amber-500'
                        : member.accentColor === 'violet'
                        ? 'bg-violet-500'
                        : 'bg-indigo-500'
                    }`}
                  />

                  <div>
                    <div className="flex items-start justify-between gap-4 mb-5">
                      <div className="flex items-center gap-4">
                        <div
                          className={`w-16 h-16 rounded-2xl bg-gradient-to-tr ${member.avatarGradient} flex items-center justify-center text-white font-black text-xl shadow-lg border border-white/10 shrink-0`}
                        >
                          {member.initials}
                        </div>
                        <div>
                          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700/80 text-[10px] font-mono text-slate-300 font-bold mb-1">
                            <span>{member.badge}</span>
                          </div>
                          <h3 className="text-xl font-extrabold text-white group-hover:text-indigo-300 transition">
                            {member.name}
                          </h3>
                          <div className="text-xs font-semibold text-slate-400">
                            {member.role}
                          </div>
                        </div>
                      </div>

                      <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-mono text-slate-400">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            isSelected ? 'bg-emerald-400 animate-ping' : 'bg-slate-600'
                          }`}
                        />
                        <span>{isSelected ? 'Selected' : 'Click to Inspect'}</span>
                      </div>
                    </div>

                    <blockquote className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80 text-xs text-slate-300 italic leading-relaxed mb-5">
                      “{member.thesis}”
                    </blockquote>

                    <p className="text-xs text-slate-400 leading-relaxed mb-6 font-normal">
                      {member.bio}
                    </p>

                    <div className="space-y-3 mb-6">
                      <div className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400">
                        Key Systems & Innovations
                      </div>
                      {member.architecturalContributions.map((c, i) => (
                        <div
                          key={i}
                          className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/60 flex items-start justify-between gap-3 text-xs"
                        >
                          <div>
                            <div className="font-bold text-white flex items-center gap-1.5">
                              <i className="fa-solid fa-cube text-[10px] text-indigo-400" />
                              <span>{c.system}</span>
                            </div>
                            <div className="text-[11px] text-slate-400 mt-0.5">
                              {c.description}
                            </div>
                          </div>
                          <span className="shrink-0 px-2 py-0.5 rounded-md bg-slate-800 text-[10px] font-mono font-bold text-indigo-300 border border-indigo-500/20">
                            {c.metric}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex flex-wrap gap-1.5">
                      {member.stack.slice(0, 3).map((tech, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded-md bg-slate-800/80 border border-slate-700/60 text-[10px] font-mono text-slate-300"
                        >
                          {tech}
                        </span>
                      ))}
                      {member.stack.length > 3 && (
                        <span className="px-1.5 py-0.5 rounded-md text-[10px] font-mono text-slate-500">
                          +{member.stack.length - 3} more
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {member.links.map((link, idx) => (
                        <a
                          key={idx}
                          href={link.url}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center text-xs transition border border-slate-700/60"
                          title={link.label}
                        >
                          <i className={link.icon} />
                        </a>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Deep-Dive Banner */}
          <div className="bg-gradient-to-tr from-slate-900 via-indigo-950/20 to-slate-900 border border-indigo-500/30 rounded-3xl p-8 lg:p-10 floating-container">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8">
              <div className="max-w-2xl">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/25 text-indigo-300 text-xs font-bold mb-3">
                  <i className="fa-solid fa-code-commit" />
                  <span>Deep-Dive Focus: {activeMemberData.name}</span>
                </div>
                <h3 className="text-2xl sm:text-3xl font-black text-white">
                  {activeMemberData.focus}
                </h3>
                <p className="text-sm text-slate-300 mt-2 leading-relaxed">
                  {activeMemberData.bio} Every subsystem passes strict deterministic unit tests, 14-point functional audits, and zero-PII security reviews.
                </p>

                <div className="mt-6 flex flex-wrap gap-2">
                  {activeMemberData.stack.map((item, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 rounded-xl bg-slate-900 border border-indigo-500/30 text-xs font-mono text-indigo-200 font-semibold"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex flex-col sm:flex-row lg:flex-col gap-3 shrink-0">
                <button
                  type="button"
                  onClick={() => navigate('/how-it-works')}
                  className="px-6 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition flex items-center justify-center gap-2 btn-glow-primary"
                >
                  <i className="fa-solid fa-diagram-project" />
                  <span>Inspect Complete Flow</span>
                </button>

                <button
                  type="button"
                  onClick={() => navigate('/explore')}
                  className="px-6 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 font-bold text-xs border border-slate-700 transition flex items-center justify-center gap-2"
                >
                  <i className="fa-solid fa-compass" />
                  <span>Explore Live Spaces</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Professional Closing Section */}
      <section className="py-20 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 relative overflow-hidden">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-cyan-300 text-xs font-bold mb-4">
            <i className="fa-solid fa-handshake" /> Collaboration & Institutional Partnerships
          </div>

          <h2 className="text-3xl sm:text-5xl font-black text-white tracking-tight">
            Building the Infrastructure for <br className="hidden sm:inline" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-indigo-300 to-violet-400">
              Tomorrow’s Shared Real Estate
            </span>
          </h2>

          <p className="mt-4 text-sm sm:text-base text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Whether you are an enterprise property owner with underutilized square footage, an educational institution looking for campus workspace exchange, or an engineer passionate about distributed spatial telemetry — we welcome partnerships.
          </p>

          <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-3xl mx-auto text-left">
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 floating-container">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/15 text-indigo-400 flex items-center justify-center mb-3 text-lg">
                <i className="fa-solid fa-building-columns" />
              </div>
              <div className="text-sm font-bold text-white">Campus & Enterprise</div>
              <div className="text-xs text-slate-400 mt-1 mb-3">Partner your spaces or institutional domain.</div>
              <a
                href="mailto:partners@spaceloop.in"
                className="text-xs font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition"
              >
                <span>partners@spaceloop.in</span>
                <i className="fa-solid fa-arrow-right text-[10px]" />
              </a>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 floating-container">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/15 text-cyan-400 flex items-center justify-center mb-3 text-lg">
                <i className="fa-solid fa-code" />
              </div>
              <div className="text-sm font-bold text-white">Systems & Research</div>
              <div className="text-xs text-slate-400 mt-1 mb-3">Telemetry, IoT mesh & AI vision reviews.</div>
              <a
                href="mailto:architecture@spaceloop.in"
                className="text-xs font-bold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition"
              >
                <span>architecture@spaceloop.in</span>
                <i className="fa-solid fa-arrow-right text-[10px]" />
              </a>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 floating-container">
              <div className="w-10 h-10 rounded-xl bg-violet-500/15 text-violet-400 flex items-center justify-center mb-3 text-lg">
                <i className="fa-solid fa-shield-halved" />
              </div>
              <div className="text-sm font-bold text-white">Security & Audits</div>
              <div className="text-xs text-slate-400 mt-1 mb-3">Vulnerability disclosure & compliance inquiries.</div>
              <a
                href="mailto:security@spaceloop.in"
                className="text-xs font-bold text-violet-400 hover:text-violet-300 flex items-center gap-1 transition"
              >
                <span>security@spaceloop.in</span>
                <i className="fa-solid fa-arrow-right text-[10px]" />
              </a>
            </div>
          </div>

          <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              type="button"
              onClick={() => navigate('/list-space')}
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-sm shadow-lg shadow-amber-500/20 transition btn-glow-amber flex items-center justify-center gap-2"
            >
              <i className="fa-solid fa-warehouse" />
              <span>Become a Space Host</span>
            </button>

            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm border border-slate-700 transition flex items-center justify-center gap-2"
            >
              <i className="fa-solid fa-compass" />
              <span>Explore Available Spaces</span>
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};
