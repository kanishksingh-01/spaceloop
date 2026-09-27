import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * ============================================================================
 * SPACELOOP SYSTEM ARCHITECTURE & CORE ENGINEERING TEAM
 * ----------------------------------------------------------------------------
 * Team LOGIC LOOP — GH Raisoni International Skill Tech University, Pune
 *
 * 1. Indrayani Mazumder — AI/ML / Research & Integration
 * 2. Kanishk Singh      — Backend Developer & Product Designer
 * 3. Zara Quadri        — Frontend / UI-UX Developer
 * 4. Aarya Maurya       — System Architect & Security
 * ============================================================================
 */

export interface SubsystemDetail {
  title: string;
  codename: string;
  status: string;
  highlights: string[];
  techStack: string[];
  metric: { label: string; value: string };
}

export interface TeamArchitect {
  id: string;
  badgeNumber: string;
  name: string;
  role: string;
  domain: string;
  bio: string;
  coordinates: string;
  email: string;
  linkedin: string;
  photoUrl: string;
  accent: 'cyan' | 'indigo' | 'violet' | 'amber';
  subsystem: SubsystemDetail;
}

export const SPACE_ARCHITECTS: TeamArchitect[] = [
  {
    id: 'architect-indrayani',
    badgeNumber: '01',
    name: 'Indrayani Mazumder',
    role: 'AI/ML / Research & Integration',
    domain: 'Multimodal Vision & Matchmaking Intelligence',
    bio: 'Pioneered SpaceLoop’s multimodal Space Inspector, acoustic background noise profiler (<36 dB), dynamic micro-pricing engine, and explainable semantic matchmaking algorithms.',
    coordinates: '18.5204° N, 73.8567° E',
    email: 'indrayani.mazumder@spaceloop.in',
    linkedin: 'https://www.linkedin.com/in/indrayani-mazumder',
    photoUrl: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=900&q=85',
    accent: 'cyan',
    subsystem: {
      title: 'Multimodal Space Inspector & Matchmaking Pipeline',
      codename: 'ENGINE-VISION-NEURAL',
      status: 'PRODUCTION ACTIVE',
      highlights: [
        'Multi-provider LLM routing between Google Gemini 1.5 Flash and Groq Llama 3.3 Versatile with deterministic rule fallbacks.',
        'Computer vision usable square footage estimation and acoustic noise profile (<36 dB) classification from uploaded space photography.',
        'High-converting plain-English listing synthesizer generating amenities checklists, electrical ratings, and photographic tags.',
        'Semantic intent matchmaker ranking candidate spaces with a 0–100% Compatibility Score and explainable pros/cons breakdown.',
      ],
      techStack: ['Gemini 1.5 Flash', 'Groq Llama-3.3', 'PyTorch Vision', 'Embeddings', 'NumPy'],
      metric: { label: 'Match Confidence', value: '98.4%' },
    },
  },
  {
    id: 'architect-kanishk',
    badgeNumber: '02',
    name: 'Kanishk Singh',
    role: 'Backend Developer & Product Designer',
    domain: 'High-Concurrency WSGI Services & Section 52 Protocol',
    bio: 'Engineered the high-performance Flask 3.0 backend, Section 52 revocable micro-leasing protocol, automated ₹100 UPI micro-escrow holds, and hybrid semantic search engine.',
    coordinates: '18.5204° N, 73.8567° E',
    email: 'kanishk@spaceloop.in',
    linkedin: 'https://www.linkedin.com/in/kanishksingh01',
    photoUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=900&q=85',
    accent: 'indigo',
    subsystem: {
      title: 'Zero-Hardware India Stack & Micro-Leasing Engine',
      codename: 'CORE-WSGI-TRANSACT',
      status: 'PRODUCTION ACTIVE',
      highlights: [
        'Section 52, Indian Easements Act 1882 legal framework generating instantaneous enforceable temporary space use licenses.',
        'Automated ₹100 UPI micro-escrow hold protocol with instant conditional release upon GPS and QR checkout handshake.',
        'Scalable Flask 3.0 WSGI architecture pre-configured with SQLite WAL concurrency and PostgreSQL multi-stage containers.',
        'Hybrid semantic AI search engine orchestrating vectorized listing embeddings with deterministic geospatial bounding.',
      ],
      techStack: ['Python 3.11', 'Flask 3.0', 'SQLAlchemy', 'PostgreSQL', 'UPI / NPCI API', 'Docker'],
      metric: { label: 'API Response P95', value: '28ms' },
    },
  },
  {
    id: 'architect-zara',
    badgeNumber: '03',
    name: 'Zara Quadri',
    role: 'Frontend / UI-UX Developer',
    domain: 'High-Fidelity React Systems & Interactive HUDs',
    bio: 'Crafted SpaceLoop’s responsive React 18 client architecture, unified permanent dark-mode design system (#020617), tactile glassmorphic controls, and mobile navigation HUD.',
    coordinates: '18.5204° N, 73.8567° E',
    email: 'zara.quadri@spaceloop.in',
    linkedin: 'https://www.linkedin.com/in/zara-quadri',
    photoUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=900&q=85',
    accent: 'violet',
    subsystem: {
      title: 'Permanent Dark-Canvas (#020617) Reactive Interface',
      codename: 'UI-REACT-VIEWPORT',
      status: 'PRODUCTION ACTIVE',
      highlights: [
        'Zero-overflow mobile HUD interface featuring synchronized timers, session passes, and offline fallback credentials.',
        'Unified SL-SYS-COLOR-2026-V1 design tokens with customized directional shadow hierarchy and glassmorphic depth.',
        'Interactive geospatial explore view with dynamic radius slider, category chips, and instant listing preview cards.',
        'Accessible, keyboard-navigable dialogs, animated modals, and multi-persona UI operational context switching.',
      ],
      techStack: ['React 18', 'TypeScript', 'Tailwind CSS', 'Vite 5', 'Lucide Icons', 'HTML5 Canvas'],
      metric: { label: 'Lighthouse Score', value: '99/100' },
    },
  },
  {
    id: 'architect-aarya',
    badgeNumber: '04',
    name: 'Aarya Maurya',
    role: 'System Architect & Security',
    domain: 'Zero-Trust Boundary, DPDP Act & Fraud Prevention',
    bio: 'Architected SpaceLoop’s zero-trust security perimeter, DPDP Act 2023 tokenized Aadhaar identity verification, and multi-tier fraud & collusion detection engine.',
    coordinates: '18.5204° N, 73.8567° E',
    email: 'aaryamaurya.dev@gmail.com',
    linkedin: 'https://www.linkedin.com/in/aarya-maurya',
    photoUrl: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=900&q=85',
    accent: 'amber',
    subsystem: {
      title: 'Zero-Trust Defense & Multi-Tier Anomaly Engine',
      codename: 'SEC-ZERO-TRUST-SHIELD',
      status: 'PRODUCTION ACTIVE',
      highlights: [
        'DPDP Act 2023 compliant zero-raw-storage tokenization pipeline hashing Aadhaar OTP credentials via SHA-256 salts.',
        '26-feature Isolation Forest unsupervised anomaly detection layer trained on tabular behavior metrics (Scikit-Learn).',
        'Entity graph cycle detection algorithms preventing cyclic wash-booking collusion rings across counterparty accounts.',
        'Strict IDOR protection, sliding-window rate limiters, session cookie regeneration, and immutable audit telemetry persistence.',
      ],
      techStack: ['Zero-Trust', 'Isolation Forest', 'Scikit-Learn', 'DigiLocker', 'DPDP Act 2023', 'NetworkX'],
      metric: { label: 'Audit Security Score', value: '100%' },
    },
  },
];

// Helper styles for accent palettes
const ACCENT_MAP = {
  cyan: {
    border: 'border-cyan-500/30 hover:border-cyan-400/60',
    glow: 'rgba(6, 182, 212, 0.15)',
    bgPill: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/25',
    dot: 'bg-cyan-400',
    text: 'text-cyan-400',
    gradient: 'from-cyan-500/20 via-blue-500/5 to-transparent',
    radarColor: '#06b6d4',
  },
  indigo: {
    border: 'border-indigo-500/30 hover:border-indigo-400/60',
    glow: 'rgba(99, 102, 241, 0.15)',
    bgPill: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/25',
    dot: 'bg-indigo-400',
    text: 'text-indigo-400',
    gradient: 'from-indigo-500/20 via-violet-500/5 to-transparent',
    radarColor: '#6366f1',
  },
  violet: {
    border: 'border-violet-500/30 hover:border-violet-400/60',
    glow: 'rgba(139, 92, 246, 0.15)',
    bgPill: 'bg-violet-500/10 text-violet-300 border-violet-500/25',
    dot: 'bg-violet-400',
    text: 'text-violet-400',
    gradient: 'from-violet-500/20 via-purple-500/5 to-transparent',
    radarColor: '#8b5cf6',
  },
  amber: {
    border: 'border-amber-500/30 hover:border-amber-400/60',
    glow: 'rgba(245, 158, 11, 0.15)',
    bgPill: 'bg-amber-500/10 text-amber-300 border-amber-500/25',
    dot: 'bg-amber-400',
    text: 'text-amber-400',
    gradient: 'from-amber-500/20 via-orange-500/5 to-transparent',
    radarColor: '#f59e0b',
  },
};

export const ArchitecturePage: React.FC = () => {
  const navigate = useNavigate();

  // Selected architect for the expanded deep-dive inspection drawer
  const [selectedArchitect, setSelectedArchitect] = useState<TeamArchitect | null>(null);
  const [activeTab, setActiveTab] = useState<'grid' | 'telemetry'>('grid');
  const [copiedEmail, setCopiedEmail] = useState<string | null>(null);
  const [isCalibrating, setIsCalibrating] = useState<boolean>(true);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(false);

  // Viewport & Cursor parallax tracking
  const [mousePos, setMousePos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [scrollProgress, setScrollProgress] = useState<number>(0);
  const pageContainerRef = useRef<HTMLDivElement>(null);

  // Check reduced motion preference
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mq.matches);
    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  // Quick initial calibration entrance (750ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsCalibrating(false);
    }, 750);
    return () => clearTimeout(timer);
  }, []);

  // Scroll listener for subtle layered parallax
  useEffect(() => {
    if (prefersReducedMotion) return;

    let ticking = false;
    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
          const current = Math.min(1, Math.max(0, window.scrollY / (maxScroll || 1)));
          setScrollProgress(current);
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [prefersReducedMotion]);

  // Global mousemove for ambient background glow tracking
  const handleGlobalMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (prefersReducedMotion) return;
      const { clientX, clientY } = e;
      const xPercent = (clientX / window.innerWidth - 0.5) * 2;
      const yPercent = (clientY / window.innerHeight - 0.5) * 2;
      setMousePos({ x: xPercent, y: yPercent });
    },
    [prefersReducedMotion]
  );

  // Keyboard accessibility: Escape to close modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && selectedArchitect) {
        setSelectedArchitect(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedArchitect]);

  // Email copy handler with feedback
  const handleCopyEmail = (email: string, id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(email);
    setCopiedEmail(id);
    setTimeout(() => setCopiedEmail(null), 2200);
  };

  return (
    <div
      ref={pageContainerRef}
      onMouseMove={handleGlobalMouseMove}
      className="min-h-screen bg-canvas text-slate-100 flex flex-col relative selection:bg-indigo-500 selection:text-white overflow-x-hidden font-sans"
    >
      {/* =====================================================================
          1. ARCHITECTURAL CALIBRATION ENTRANCE OVERLAY
          Subtle hairline initialization sequence (750ms)
          ===================================================================== */}
      {isCalibrating && (
        <div
          className="fixed inset-0 z-50 bg-[#020617] flex flex-col items-center justify-center transition-opacity duration-500 pointer-events-none"
          style={{ opacity: isCalibrating ? 1 : 0 }}
        >
          <div className="flex flex-col items-center gap-4 max-w-xs text-center px-4">
            <div className="relative w-12 h-12 flex items-center justify-center">
              <div className="absolute inset-0 rounded-xl border border-indigo-500/40 animate-ping" />
              <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500 flex items-center justify-center text-indigo-400">
                <i className="fa-solid fa-cube text-sm animate-spin" />
              </div>
            </div>
            <div className="space-y-1.5">
              <div className="text-[11px] font-mono tracking-widest text-indigo-400 font-bold uppercase">
                SpaceLoop // System Architecture
              </div>
              <div className="text-xs text-slate-400 font-medium">
                Calibrating core team telemetry...
              </div>
            </div>
            <div className="w-36 h-0.5 bg-slate-800 rounded-full overflow-hidden mt-1">
              <div className="h-full bg-gradient-to-r from-cyan-400 via-indigo-500 to-violet-500 animate-pulse w-full" />
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          2. ATMOSPHERIC BACKGROUND LAYERS (Google Antigravity inspired)
          Multi-depth ambient light, subtle coordinate grid & hairline geometry
          ===================================================================== */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" aria-hidden="true">
        {/* Subtle Architectural Grid */}
        <div
          className="absolute inset-0 opacity-[0.035]"
          style={{
            backgroundImage: `
              linear-gradient(to right, rgba(255, 255, 255, 0.4) 1px, transparent 1px),
              linear-gradient(to bottom, rgba(255, 255, 255, 0.4) 1px, transparent 1px)
            `,
            backgroundSize: '48px 48px',
          }}
        />

        {/* Ambient Primary Glow Orb - Reacts to Cursor & Scroll */}
        <div
          className="absolute -top-40 left-1/2 -translate-x-1/2 w-[850px] h-[550px] rounded-full blur-[140px] pointer-events-none opacity-40 transition-transform duration-700 ease-out will-change-transform"
          style={{
            background: 'radial-gradient(circle, rgba(99, 102, 241, 0.35) 0%, rgba(139, 92, 246, 0.15) 50%, transparent 70%)',
            transform: prefersReducedMotion
              ? 'translate(-50%, 0)'
              : `translate(calc(-50% + ${mousePos.x * 25}px), ${mousePos.y * 20 + scrollProgress * 40}px)`,
          }}
        />

        {/* Cyan Ambient Accent Light */}
        <div
          className="absolute top-1/3 -left-32 w-[600px] h-[600px] rounded-full blur-[150px] pointer-events-none opacity-25 transition-transform duration-1000 ease-out will-change-transform"
          style={{
            background: 'radial-gradient(circle, rgba(6, 182, 212, 0.3) 0%, transparent 70%)',
            transform: prefersReducedMotion
              ? 'none'
              : `translate(${-mousePos.x * 20}px, ${-mousePos.y * 20}px)`,
          }}
        />

        {/* Amber Grounding Accent Light */}
        <div
          className="absolute bottom-10 -right-32 w-[650px] h-[650px] rounded-full blur-[160px] pointer-events-none opacity-20 transition-transform duration-1000 ease-out will-change-transform"
          style={{
            background: 'radial-gradient(circle, rgba(245, 158, 11, 0.25) 0%, transparent 70%)',
            transform: prefersReducedMotion
              ? 'none'
              : `translate(${mousePos.x * 20}px, ${mousePos.y * 15}px)`,
          }}
        />

        {/* Subtle Horizontal Hairline Axis Indicator */}
        <div className="absolute top-[28rem] left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />
      </div>

      {/* =====================================================================
          3. COMPACT ARCHITECTURAL STATUS & BREADCRUMB BAR
          Sticky, frosted glass HUD bar with navigation & telemetry
          ===================================================================== */}
      <header className="sticky top-16 z-30 border-b border-white/[0.08] bg-[#020617]/85 backdrop-blur-xl transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between gap-4">
          {/* Breadcrumb & Home Return */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/')}
              className="group inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface hover:bg-slate-800 text-xs font-semibold text-slate-300 hover:text-white border border-white/[0.08] hover:border-indigo-500/40 transition-all shadow-sm"
              title="Return to SpaceLoop Marketplace"
            >
              <i className="fa-solid fa-arrow-left text-[11px] group-hover:-translate-x-0.5 transition-transform" />
              <span>Marketplace</span>
            </button>
            <span className="text-slate-700 select-none">/</span>
            <div className="inline-flex items-center gap-2 text-xs font-mono font-medium text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="hidden sm:inline text-slate-400">SYS.ARCH //</span>
              <span className="font-semibold text-white">Logic Loop Core</span>
            </div>
          </div>

          {/* Quick HUD Telemetry & View Mode */}
          <div className="flex items-center gap-3">
            {/* View Switcher: Interactive Cards vs Telemetry Split */}
            <div className="inline-flex items-center p-0.5 rounded-lg bg-surface border border-white/[0.08] text-[11px] font-mono">
              <button
                type="button"
                onClick={() => setActiveTab('grid')}
                className={`px-2.5 py-1 rounded-md transition-all ${
                  activeTab === 'grid'
                    ? 'bg-indigo-600 text-white font-bold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <i className="fa-solid fa-cubes text-[10px] mr-1.5" />
                Architects
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('telemetry')}
                className={`px-2.5 py-1 rounded-md transition-all ${
                  activeTab === 'telemetry'
                    ? 'bg-indigo-600 text-white font-bold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <i className="fa-solid fa-network-wired text-[10px] mr-1.5" />
                System Matrix
              </button>
            </div>

            {/* Quick Explore Button */}
            <button
              onClick={() => navigate('/explore')}
              className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-semibold transition"
            >
              <i className="fa-solid fa-compass text-[11px]" />
              <span>Explore Spaces</span>
            </button>
          </div>
        </div>
      </header>

      {/* =====================================================================
          4. HERO SECTION: "Meet the Architects Behind SpaceLoop"
          Antigravity-inspired layered depth, typography & blueprint telemetry
          ===================================================================== */}
      <section className="relative z-10 pt-16 pb-16 md:pt-24 md:pb-20 border-b border-white/[0.08]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative">
          {/* Subtle Technical Annotation Pill */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.1] text-xs font-mono text-slate-300 mb-8 backdrop-blur-md shadow-sm">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            <span className="text-indigo-300 font-bold uppercase tracking-wider">TEAM LOGIC LOOP</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-400">GH Raisoni ISTU, Pune</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-400 font-mono">4 Core Architects</span>
          </div>

          {/* Main Hero Heading */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight text-white leading-[1.08] max-w-4xl mx-auto">
            Meet the Architects <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-300 via-violet-200 to-cyan-300">
              Behind SpaceLoop
            </span>
          </h1>

          {/* Supporting Text */}
          <p className="mt-6 text-base sm:text-lg lg:text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed font-normal">
            SpaceLoop is designed and engineered end-to-end by a focused four-person team. Discover the individuals responsible for our multimodal AI, zero-trust security, distributed backend, and interface craftsmanship.
          </p>

          {/* Architectural Telemetry Bar */}
          <div className="mt-10 pt-6 border-t border-white/[0.06] flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-xs font-mono text-slate-400">
            <div className="flex items-center gap-2">
              <span className="text-indigo-400">COORD:</span>
              <span className="text-slate-300">18.5204° N, 73.8567° E</span>
            </div>
            <span className="text-slate-700 hidden sm:inline">|</span>
            <div className="flex items-center gap-2">
              <span className="text-cyan-400">STACK:</span>
              <span className="text-slate-300">Zero-Hardware India Stack</span>
            </div>
            <span className="text-slate-700 hidden sm:inline">|</span>
            <div className="flex items-center gap-2">
              <span className="text-emerald-400">STATUS:</span>
              <span className="text-slate-300">4/4 Subsystems Live</span>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================================
          5. MAIN ARCHITECT INTERACTIVE PROFILE SECTION
          Interactive cards with cursor-reactive lighting, 3D tilt, and deep-dive
          ===================================================================== */}
      <main className="relative z-10 flex-1 py-14 lg:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {activeTab === 'grid' ? (
            /* -------------------------------------------------------------
               VIEW MODE A: 4-MEMBER INTERACTIVE GLASS CARDS MATRIX
               ------------------------------------------------------------- */
            <div>
              {/* Section Subheading */}
              <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-10 pb-4 border-b border-white/[0.06]">
                <div>
                  <div className="text-[11px] font-mono tracking-widest text-indigo-400 uppercase font-bold mb-1">
                    ENGINEERING DIRECTORY // 01 - 04
                  </div>
                  <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                    Core System Architects
                  </h2>
                </div>
                <div className="text-xs text-slate-400 font-mono flex items-center gap-2">
                  <i className="fa-solid fa-hand-pointer text-indigo-400 text-[11px]" />
                  <span>Click card to inspect architectural subsystem</span>
                </div>
              </div>

              {/* 4 Cards in 2x2 Responsive Matrix */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-10">
                {SPACE_ARCHITECTS.map((architect, idx) => (
                  <ArchitectInteractiveCard
                    key={architect.id}
                    architect={architect}
                    index={idx}
                    copiedEmail={copiedEmail}
                    onCopyEmail={handleCopyEmail}
                    onSelect={() => setSelectedArchitect(architect)}
                    prefersReducedMotion={prefersReducedMotion}
                  />
                ))}
              </div>
            </div>
          ) : (
            /* -------------------------------------------------------------
               VIEW MODE B: DEEP TELEMETRY & SYSTEM MATRIX VIEW
               ------------------------------------------------------------- */
            <div className="space-y-8">
              <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-4 border-b border-white/[0.06]">
                <div>
                  <div className="text-[11px] font-mono tracking-widest text-indigo-400 uppercase font-bold mb-1">
                    SYSTEM TOPOLOGY // ARCHITECTURAL ALLOCATION
                  </div>
                  <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                    Subsystem Architecture Breakdown
                  </h2>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveTab('grid')}
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface hover:bg-slate-800 border border-white/[0.08] text-xs font-semibold text-slate-300"
                >
                  <i className="fa-solid fa-grip text-xs" />
                  <span>Switch to Profile Cards</span>
                </button>
              </div>

              {/* Detailed Breakdown Panels */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {SPACE_ARCHITECTS.map((architect) => {
                  const accent = ACCENT_MAP[architect.accent];
                  return (
                    <div
                      key={`matrix-${architect.id}`}
                      className="p-6 sm:p-8 rounded-2xl bg-surface/75 border border-white/[0.08] backdrop-blur-xl relative overflow-hidden group hover:border-white/[0.18] transition-all"
                    >
                      {/* Accent Header */}
                      <div className="flex items-start justify-between gap-4 mb-4">
                        <div>
                          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase mb-1">
                            <span className={accent.text}>SLOT {architect.badgeNumber}</span>
                            <span className="text-slate-600">//</span>
                            <span className="text-slate-400">{architect.subsystem.codename}</span>
                          </div>
                          <h3 className="text-xl font-bold text-white tracking-tight">
                            {architect.subsystem.title}
                          </h3>
                        </div>
                        <span className={`px-2.5 py-1 rounded-md text-[10px] font-mono font-bold uppercase ${accent.bgPill}`}>
                          {architect.subsystem.metric.label}: {architect.subsystem.metric.value}
                        </span>
                      </div>

                      {/* Lead Architect Attribution */}
                      <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-900/80 border border-white/[0.04] mb-5">
                        <img
                          src={architect.photoUrl}
                          alt={architect.name}
                          className="w-10 h-10 rounded-lg object-cover object-top border border-white/10"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-bold text-white truncate">{architect.name}</div>
                          <div className="text-xs text-slate-400 truncate">{architect.role}</div>
                        </div>
                        <button
                          type="button"
                          onClick={() => setSelectedArchitect(architect)}
                          className="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-semibold transition"
                        >
                          Details →
                        </button>
                      </div>

                      {/* Core Highlights */}
                      <div className="space-y-2 mb-6 text-xs text-slate-300">
                        {architect.subsystem.highlights.map((h, i) => (
                          <div key={i} className="flex items-start gap-2.5">
                            <span className={`w-1.5 h-1.5 rounded-full ${accent.dot} mt-1.5 shrink-0`} />
                            <span className="leading-relaxed">{h}</span>
                          </div>
                        ))}
                      </div>

                      {/* Stack Tags */}
                      <div className="pt-4 border-t border-white/[0.06] flex flex-wrap items-center gap-2">
                        {architect.subsystem.techStack.map((tech) => (
                          <span
                            key={tech}
                            className="px-2.5 py-1 rounded-md bg-white/[0.04] border border-white/[0.06] text-[11px] font-mono text-slate-300"
                          >
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* =====================================================================
          6. EXPANDED ARCHITECTURAL INSPECTOR MODAL (Interactive Spotlight)
          Detailed view with deep-dive, technical highlights, and direct actions
          ===================================================================== */}
      {selectedArchitect && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-architect-name"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 lg:p-8 animate-fadeIn"
        >
          {/* Backdrop blur */}
          <div
            onClick={() => setSelectedArchitect(null)}
            className="absolute inset-0 bg-slate-950/85 backdrop-blur-2xl transition-opacity"
          />

          {/* Modal Container */}
          <div className="relative z-10 w-full max-w-3xl rounded-3xl bg-[#0f172a] border border-white/[0.12] shadow-[0_30px_90px_rgba(0,0,0,0.85)] overflow-hidden max-h-[92vh] flex flex-col">
            {/* Header with Close Button */}
            <div className="px-6 sm:px-8 py-5 border-b border-white/[0.08] flex items-center justify-between bg-slate-900/60">
              <div className="flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
                  ARCHITECT PROFILE // SLOT {selectedArchitect.badgeNumber}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedArchitect(null)}
                className="w-8 h-8 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] text-slate-300 hover:text-white flex items-center justify-center transition"
                title="Close modal (Esc)"
              >
                <i className="fa-solid fa-xmark text-sm" />
              </button>
            </div>

            {/* Scrollable Content Body */}
            <div className="p-6 sm:p-8 overflow-y-auto space-y-6">
              {/* Profile Intro Header */}
              <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 pb-6 border-b border-white/[0.08]">
                {/* 4:5 Aspect Ratio Portrait */}
                <div className="w-32 sm:w-36 shrink-0 aspect-[4/5] rounded-2xl overflow-hidden bg-slate-950 border border-white/10 shadow-lg relative">
                  <img
                    src={selectedArchitect.photoUrl}
                    alt={selectedArchitect.name}
                    className="w-full h-full object-cover object-top"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-transparent to-transparent pointer-events-none" />
                </div>

                <div className="flex-1 text-center sm:text-left">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-bold uppercase border mb-2 bg-indigo-500/10 text-indigo-300 border-indigo-500/30">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                    <span>{selectedArchitect.role}</span>
                  </div>
                  <h2 id="modal-architect-name" className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                    {selectedArchitect.name}
                  </h2>
                  <div className="text-xs font-mono text-slate-400 mt-1 mb-3">
                    GH Raisoni International Skill Tech University, Pune
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {selectedArchitect.bio}
                  </p>
                </div>
              </div>

              {/* Subsystem Specifications */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-indigo-300">
                    Architectural Subsystem Specifications
                  </h3>
                  <span className="text-[11px] font-mono text-slate-400">
                    {selectedArchitect.subsystem.codename}
                  </span>
                </div>

                <div className="p-5 rounded-2xl bg-slate-950/60 border border-white/[0.06] space-y-3">
                  <div className="text-base font-bold text-white">
                    {selectedArchitect.subsystem.title}
                  </div>
                  <div className="space-y-2.5">
                    {selectedArchitect.subsystem.highlights.map((item, idx) => (
                      <div key={idx} className="flex items-start gap-3 text-xs text-slate-300 leading-relaxed">
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Technical Stack Tags */}
              <div className="space-y-2">
                <div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
                  Core Technologies & Toolchain
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedArchitect.subsystem.techStack.map((tech) => (
                    <span
                      key={tech}
                      className="px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-xs font-mono text-slate-200"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>

              {/* Direct Actions: LinkedIn & Email */}
              <div className="pt-6 border-t border-white/[0.08] flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  {/* LinkedIn */}
                  <a
                    href={selectedArchitect.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-[#0A66C2]/15 hover:bg-[#0A66C2]/25 text-[#70b5f9] hover:text-white border border-[#0A66C2]/35 text-xs font-semibold transition"
                    title="Open LinkedIn profile"
                  >
                    <i className="fa-brands fa-linkedin-in text-sm" />
                    <span>LinkedIn Profile</span>
                    <i className="fa-solid fa-arrow-up-right-from-square text-[10px] ml-0.5 opacity-70" />
                  </a>

                  {/* Mailto */}
                  <a
                    href={`mailto:${selectedArchitect.email}`}
                    className="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition shadow-md shadow-indigo-600/20"
                    title={`Send email to ${selectedArchitect.email}`}
                  >
                    <i className="fa-solid fa-envelope text-xs" />
                    <span>Send Email</span>
                  </a>

                  {/* Copy Email Button */}
                  <button
                    type="button"
                    onClick={(e) => handleCopyEmail(selectedArchitect.email, selectedArchitect.id, e)}
                    className="inline-flex items-center gap-1.5 px-3 py-2.5 rounded-xl bg-white/[0.06] hover:bg-white/[0.12] text-slate-300 hover:text-white border border-white/[0.08] text-xs font-mono transition"
                    title="Copy email to clipboard"
                  >
                    {copiedEmail === selectedArchitect.id ? (
                      <>
                        <i className="fa-solid fa-check text-emerald-400" />
                        <span className="text-emerald-300 text-[11px]">Copied!</span>
                      </>
                    ) : (
                      <>
                        <i className="fa-regular fa-copy text-xs" />
                        <span className="text-[11px]">Copy</span>
                      </>
                    )}
                  </button>
                </div>

                <div className="text-[11px] font-mono text-slate-500">
                  {selectedArchitect.coordinates}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          7. CLOSING CALLOUT & RETURN ACTIONS
          Clean, purposeful transition back to the SpaceLoop experience
          ===================================================================== */}
      <footer className="relative z-10 py-16 border-t border-white/[0.08] bg-[#020617]/90 text-center">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/25 text-indigo-300 text-xs font-bold font-mono">
            <i className="fa-solid fa-trophy text-[11px]" />
            <span>BUILT FOR HACK2IGNITE 2026</span>
          </div>

          <h3 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
            Designed for India’s Next Wave of Flexible Spaces
          </h3>

          <p className="text-sm text-slate-400 max-w-xl mx-auto leading-relaxed">
            From empty garages and silent studios to after-hours retail, SpaceLoop bridges physical property with instant digital utility.
          </p>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition flex items-center justify-center gap-2"
            >
              <i className="fa-solid fa-compass text-xs" />
              <span>Explore Active Spaces</span>
            </button>
            <button
              type="button"
              onClick={() => navigate('/')}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-surface hover:bg-slate-800 text-slate-300 hover:text-white font-semibold text-xs border border-white/[0.08] transition flex items-center justify-center gap-2"
            >
              <i className="fa-solid fa-house text-xs" />
              <span>Return to Home</span>
            </button>
          </div>

          <div className="pt-8 text-xs font-mono text-slate-600">
            SPACELOOP V2.5.0 // GH RISONI ISTU PUNE // TEAM LOGIC LOOP
          </div>
        </div>
      </footer>
    </div>
  );
};

/**
 * ============================================================================
 * INDIVIDUAL ARCHITECT INTERACTIVE CARD (Google Antigravity-Inspired)
 * ----------------------------------------------------------------------------
 * Features:
 * - Local pointer-tracking radial highlight following cursor
 * - Subtle 3D perspective tilt (clamped to +/- 3 degrees for restraint)
 * - 4:5 aspect ratio prominent face portrait with zoom-on-hover
 * - Official LinkedIn & Mailto action buttons with tooltips
 * - Architectural hairline corner crosshairs (+)
 * ============================================================================
 */
interface ArchitectCardProps {
  architect: TeamArchitect;
  index: number;
  copiedEmail: string | null;
  onCopyEmail: (email: string, id: string, e: React.MouseEvent) => void;
  onSelect: () => void;
  prefersReducedMotion: boolean;
}

const ArchitectInteractiveCard: React.FC<ArchitectCardProps> = ({
  architect,
  copiedEmail,
  onCopyEmail,
  onSelect,
  prefersReducedMotion,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [localMouse, setLocalMouse] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState<boolean>(false);
  const [imgError, setImgError] = useState<boolean>(false);

  const accent = ACCENT_MAP[architect.accent];

  // Mousemove handler for card-local radial spotlight and subtle tilt
  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (prefersReducedMotion || !cardRef.current) return;
      const rect = cardRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      setLocalMouse({ x, y });
    },
    [prefersReducedMotion]
  );

  // Subtle 3D tilt calculation (restrained to 3 degrees max)
  const tiltStyle = React.useMemo(() => {
    if (prefersReducedMotion || !isHovered || !cardRef.current) {
      return {
        transform: 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)',
        transition: 'transform 0.5s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.4s ease',
      };
    }
    const rect = cardRef.current.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const tiltX = ((localMouse.y - centerY) / centerY) * -3;
    const tiltY = ((localMouse.x - centerX) / centerX) * 3;

    return {
      transform: `perspective(1000px) rotateX(${tiltX.toFixed(2)}deg) rotateY(${tiltY.toFixed(2)}deg) translateZ(6px)`,
      transition: 'transform 0.15s ease-out, box-shadow 0.3s ease',
    };
  }, [isHovered, localMouse, prefersReducedMotion]);

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onSelect}
      style={tiltStyle}
      className={`group relative rounded-3xl p-6 sm:p-8 bg-[#0f172a]/75 border border-white/[0.08] backdrop-blur-xl cursor-pointer will-change-transform ${accent.border} shadow-[0_10px_35px_-5px_rgba(0,0,0,0.45)] hover:shadow-[0_24px_60px_-10px_rgba(0,0,0,0.7),0_0_35px_rgba(99,102,241,0.18)] transition-all`}
    >
      {/* Dynamic Cursor Spotlight Layer (Antigravity Inspired) */}
      {!prefersReducedMotion && isHovered && (
        <div
          className="absolute inset-0 rounded-3xl pointer-events-none transition-opacity duration-300 opacity-100"
          style={{
            background: `radial-gradient(450px circle at ${localMouse.x}px ${localMouse.y}px, ${accent.glow}, transparent 75%)`,
          }}
        />
      )}

      {/* Decorative Blueprint Corner Crosshairs (+) */}
      <span className="absolute top-3 left-3 text-[10px] font-mono text-slate-700 select-none">+</span>
      <span className="absolute top-3 right-3 text-[10px] font-mono text-slate-700 select-none">+</span>
      <span className="absolute bottom-3 left-3 text-[10px] font-mono text-slate-700 select-none">+</span>
      <span className="absolute bottom-3 right-3 text-[10px] font-mono text-slate-700 select-none">+</span>

      <div className="relative z-10 flex flex-col sm:flex-row items-center sm:items-start gap-6 lg:gap-8">
        {/* 4:5 Aspect Ratio Portrait Container */}
        <div className="w-full sm:w-[190px] lg:w-[210px] shrink-0">
          <div className="relative aspect-[4/5] w-full rounded-2xl overflow-hidden bg-slate-950 border border-white/10 shadow-lg group-hover:border-white/20 transition-all duration-500">
            {!imgError ? (
              <img
                src={architect.photoUrl}
                alt={architect.name}
                onError={() => setImgError(true)}
                className="w-full h-full object-cover object-top filter contrast-[1.04] brightness-[0.98] group-hover:scale-105 transition-transform duration-700 ease-out"
                loading="lazy"
              />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center p-4 bg-slate-900 text-slate-400 text-center">
                <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-2 text-2xl">
                  <i className="fa-solid fa-user text-slate-500" />
                </div>
                <span className="text-[11px] font-mono font-bold text-slate-400 uppercase">
                  SLOT {architect.badgeNumber}
                </span>
              </div>
            )}

            {/* Bottom Dark Gradient for Image Legibility */}
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent pointer-events-none" />

            {/* Badge Indicator */}
            <div className="absolute top-3 left-3">
              <span className="px-2.5 py-0.5 rounded-md bg-[#020617]/85 backdrop-blur-md border border-white/10 text-[10px] font-mono font-bold text-slate-300">
                0{architect.badgeNumber}
              </span>
            </div>

            {/* Inspect hover chip */}
            <div className="absolute bottom-3 left-3 right-3 text-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-600/90 text-white text-[10px] font-semibold tracking-wide backdrop-blur-md shadow-md">
                <i className="fa-solid fa-magnifying-glass text-[9px]" />
                <span>Inspect Subsystem</span>
              </span>
            </div>
          </div>
        </div>

        {/* Content & Details Column */}
        <div className="flex-1 flex flex-col justify-between w-full text-left">
          <div>
            {/* Serial / Domain Header */}
            <div className="flex items-center justify-between gap-2 mb-2">
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400">
                SLOT {architect.badgeNumber} // {architect.coordinates}
              </span>
              <span className={`w-2 h-2 rounded-full ${accent.dot}`} />
            </div>

            {/* Architect Name */}
            <h3 className="text-2xl lg:text-3xl font-black text-white tracking-tight group-hover:text-indigo-200 transition-colors">
              {architect.name}
            </h3>

            {/* Official Role Badge */}
            <div className="mt-2 mb-3">
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono font-bold uppercase border ${accent.bgPill}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${accent.dot}`} />
                <span>{architect.role}</span>
              </span>
            </div>

            {/* Brief Bio / Responsibility Description */}
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed line-clamp-3 mb-4">
              {architect.bio}
            </p>

            {/* Key Subsystem Focus Pill */}
            <div className="p-2.5 rounded-xl bg-slate-900/60 border border-white/[0.04] mb-4">
              <div className="text-[10px] font-mono uppercase text-slate-500 font-bold mb-0.5">
                Primary Architecture Domain:
              </div>
              <div className="text-xs text-slate-300 font-medium truncate">
                {architect.domain}
              </div>
            </div>
          </div>

          {/* Action Row: Official LinkedIn & Mailto Icons */}
          <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              {/* LinkedIn Button */}
              <a
                href={architect.linkedin}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0A66C2]/15 hover:bg-[#0A66C2]/25 text-[#70b5f9] hover:text-white border border-[#0A66C2]/30 text-xs font-semibold transition"
                title={`Open ${architect.name}'s LinkedIn Profile`}
              >
                <i className="fa-brands fa-linkedin-in text-xs" />
                <span className="hidden sm:inline">LinkedIn</span>
                <i className="fa-solid fa-arrow-up-right-from-square text-[9px] opacity-70" />
              </a>

              {/* Email / Mailto Button */}
              <a
                href={`mailto:${architect.email}`}
                onClick={(e) => e.stopPropagation()}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] text-slate-200 hover:text-white border border-white/[0.08] text-xs font-semibold transition"
                title={`Send email to ${architect.email}`}
              >
                <i className="fa-solid fa-envelope text-indigo-400 text-xs" />
                <span className="hidden sm:inline">Email</span>
              </a>

              {/* Copy Email Helper */}
              <button
                type="button"
                onClick={(e) => onCopyEmail(architect.email, architect.id, e)}
                className="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-white/[0.04] hover:bg-white/[0.1] text-slate-400 hover:text-white border border-white/[0.06] text-xs transition"
                title="Copy email to clipboard"
              >
                {copiedEmail === architect.id ? (
                  <i className="fa-solid fa-check text-emerald-400 text-xs" />
                ) : (
                  <i className="fa-regular fa-copy text-xs" />
                )}
              </button>
            </div>

            <span className="text-[11px] font-mono text-indigo-400 group-hover:translate-x-1 transition-transform flex items-center gap-1 font-bold">
              <span>Inspect</span>
              <i className="fa-solid fa-arrow-right text-[10px]" />
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArchitecturePage;
