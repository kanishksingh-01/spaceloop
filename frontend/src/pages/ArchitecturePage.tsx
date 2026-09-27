import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Compass,
  Mail,
  Linkedin,
  Copy,
  Check,
  ExternalLink,
  Maximize2,
  X,
  Shield,
  Cpu,
  Sparkles,
  Layers,
  Activity,
  Terminal,
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { ThemeToggle } from '../components/common/ThemeToggle';
import './ArchitecturePage.css';

/**
 * ============================================================================
 * SPACELOOP ARCHITECT PAGE — ANTIGRAVITY-INSPIRED PREMIUM UI/UX
 * ----------------------------------------------------------------------------
 * High-precision engineering showcase inspired by Google Antigravity:
 * - Architectural blueprint gridlines and fine coordinate crosshairs (+)
 * - Cursor-reactive specular spotlight following pointer within each card
 * - Dampened 3D tilt & elevation lift on hover (GPU-accelerated)
 * - Multi-tiered scroll & mouse parallax with reduced-motion respect
 * - 4 Real Core Architect Profiles (Indrayani, Kanishk, Zara, Aarya)
 * - Expandable Deep-Dive Architecture Inspection Glass Modal
 * - Verified LinkedIn (target="_blank") and Mailto integrations with copy toast
 * - Dual-palette support: Ocean Breeze (#0B3D91, #3BA7F2) & Midnight Neon (#020617)
 * ============================================================================
 */

export interface TeamMember {
  id: string;
  badgeNumber: string;
  name: string;
  role: string;
  domain: string;
  intro: string;
  email: string;
  linkedin: string;
  photoUrl: string;
  accent: 'cyan' | 'indigo' | 'violet' | 'amber';
  subsystem: {
    title: string;
    codename: string;
    metric: {
      label: string;
      value: string;
    };
    highlights: string[];
    techStack: string[];
  };
}

export const TEAM_MEMBERS: TeamMember[] = [
  {
    id: 'architect-indrayani',
    badgeNumber: '01',
    name: 'Indrayani Mazumder',
    role: 'AI / ML & Computer Vision Specialist',
    domain: 'Multimodal Room Vision & Section 52 Matching Engine',
    intro:
      'Leads SpaceLoop’s multimodal computer vision and spatial intelligence pipeline. Architected the post-occupancy room condition delta analyzer, automatic electrical appliance off-detection, and the Groq + Gemini dual-engine intent parser.',
    email: 'indrayani@spaceloop.in',
    linkedin: 'https://www.linkedin.com/in/indrayani-mazumder',
    photoUrl:
      'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=900&q=85',
    accent: 'cyan',
    subsystem: {
      title: 'Multimodal Room Vision & Semantic Matcher',
      codename: 'CV-ROOM-DELTA-SCAN',
      metric: {
        label: 'Match Accuracy',
        value: '98.4%',
      },
      highlights: [
        'Multimodal room inspector analyzing acoustic dampening, ergonomics, natural lighting, and monitor availability.',
        'Post-occupancy visual delta scanner comparing check-in and check-out photos to verify zero damages.',
        'Automated computer vision edge checks confirming lights, monitors, and electrical appliances are turned off.',
      ],
      techStack: ['Python 3.11', 'OpenCV', 'Gemini 1.5 Pro', 'Groq LPU', 'PyTorch', 'NumPy'],
    },
  },
  {
    id: 'architect-kanishk',
    badgeNumber: '02',
    name: 'Kanishk Singh',
    role: 'Founding Architect & Backend Lead',
    domain: 'High-Concurrency WSGI Services & Section 52 Protocol',
    intro:
      'Engineered SpaceLoop’s high-performance Flask 3.0 backend, Section 52 revocable micro-leasing protocol under the Indian Easements Act (1882), automated ₹100 UPI micro-escrow holds, and hybrid semantic search engine.',
    email: 'kanishk@spaceloop.in',
    linkedin: 'https://www.linkedin.com/in/kanishksingh01',
    photoUrl:
      'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=900&q=85',
    accent: 'indigo',
    subsystem: {
      title: 'Section 52 Engine & UPI Micro-Escrow',
      codename: 'CORE-WSGI-TRANSACT',
      metric: {
        label: 'P95 API Latency',
        value: '28ms',
      },
      highlights: [
        'Section 52 Indian Easements Act legal framework generating instant enforceable temporary space licenses.',
        'Automated ₹100 UPI micro-escrow hold protocol with instant conditional release upon GPS and QR checkout.',
        'Scalable Flask 3.0 WSGI architecture pre-configured with SQLite WAL concurrency and PostgreSQL containers.',
      ],
      techStack: ['Python 3.11', 'Flask 3.0', 'SQLAlchemy Core', 'PostgreSQL', 'UPI / NPCI API', 'Docker'],
    },
  },
  {
    id: 'architect-zara',
    badgeNumber: '03',
    name: 'Zara Quadri',
    role: 'Frontend / UI-UX Lead Developer',
    domain: 'High-Fidelity React Systems & Interactive HUDs',
    intro:
      'Crafted SpaceLoop’s responsive React 18 client architecture, Ocean Breeze light theme and Midnight Neon dark theme design systems, tactile glassmorphic controls, and mobile navigation HUD.',
    email: 'zara.quadri@spaceloop.in',
    linkedin: 'https://www.linkedin.com/in/zara-quadri',
    photoUrl:
      'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=900&q=85',
    accent: 'violet',
    subsystem: {
      title: 'Reactive Viewport & Dual-Theme System',
      codename: 'UI-REACT-VIEWPORT',
      metric: {
        label: 'Lighthouse Score',
        value: '99/100',
      },
      highlights: [
        'Zero-overflow mobile HUD interface featuring synchronized session timers, passes, and offline credentials.',
        'Dual-palette design token system powering Ocean Breeze (#0B3D91, #3BA7F2) and Midnight Neon (#020617).',
        'Interactive geospatial explore view with dynamic radius slider, category chips, and instant listing preview cards.',
      ],
      techStack: ['React 18', 'TypeScript', 'Tailwind CSS', 'Vite 5', 'Lucide Icons', 'HTML5 Canvas'],
    },
  },
  {
    id: 'architect-aarya',
    badgeNumber: '04',
    name: 'Aarya Maurya',
    role: 'System Architect & Security Lead',
    domain: 'Zero-Trust Boundary, DPDP Act 2023 & Fraud Prevention',
    intro:
      'Architected SpaceLoop’s zero-trust security perimeter, DPDP Act 2023 tokenized Aadhaar identity verification, and multi-tier fraud & collusion detection engine.',
    email: 'aaryamaurya.dev@gmail.com',
    linkedin: 'https://www.linkedin.com/in/aarya-maurya',
    photoUrl:
      'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=900&q=85',
    accent: 'amber',
    subsystem: {
      title: 'Zero-Trust Defense & Multi-Tier Anomaly Engine',
      codename: 'SEC-ZERO-TRUST-SHIELD',
      metric: {
        label: 'Audit Security',
        value: '100%',
      },
      highlights: [
        'DPDP Act 2023 compliant zero-raw-storage tokenization pipeline hashing Aadhaar OTP credentials via SHA-256 salts.',
        '26-feature Isolation Forest unsupervised anomaly detection layer trained on tabular behavior metrics.',
        'Strict IDOR protection, sliding-window rate limiters, session cookie regeneration, and immutable audit telemetry.',
      ],
      techStack: ['Zero-Trust', 'Isolation Forest', 'Scikit-Learn', 'DigiLocker', 'DPDP Act 2023', 'NetworkX'],
    },
  },
];

// Accent theme tokens and color mappings
const ACCENT_TOKENS = {
  cyan: {
    color: '#06B6D4',
    rgb: '6, 182, 212',
    border: 'border-cyan-500/40 hover:border-cyan-400',
    lightBorder: 'border-cyan-600/30 hover:border-cyan-600',
    text: 'text-cyan-600 dark:text-cyan-400',
    badge: 'bg-cyan-500/10 text-cyan-700 dark:text-cyan-300 border-cyan-500/30',
    glow: 'rgba(6, 182, 212, 0.22)',
    icon: Cpu,
  },
  indigo: {
    color: '#4F46E5',
    rgb: '79, 70, 229',
    border: 'border-indigo-500/40 hover:border-indigo-400',
    lightBorder: 'border-indigo-600/30 hover:border-indigo-600',
    text: 'text-indigo-600 dark:text-indigo-400',
    badge: 'bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border-indigo-500/30',
    glow: 'rgba(79, 70, 229, 0.22)',
    icon: Terminal,
  },
  violet: {
    color: '#8B5CF6',
    rgb: '139, 92, 246',
    border: 'border-violet-500/40 hover:border-violet-400',
    lightBorder: 'border-violet-600/30 hover:border-violet-600',
    text: 'text-violet-600 dark:text-violet-400',
    badge: 'bg-violet-500/10 text-violet-700 dark:text-violet-300 border-violet-500/30',
    glow: 'rgba(139, 92, 246, 0.22)',
    icon: Layers,
  },
  amber: {
    color: '#F59E0B',
    rgb: '245, 158, 11',
    border: 'border-amber-500/40 hover:border-amber-400',
    lightBorder: 'border-amber-600/30 hover:border-amber-600',
    text: 'text-amber-600 dark:text-amber-400',
    badge: 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30',
    glow: 'rgba(245, 158, 11, 0.22)',
    icon: Shield,
  },
};

export const ArchitecturePage: React.FC = () => {
  const navigate = useNavigate();
  const { theme } = useTheme();
  const isLight = theme === 'light';

  // State Management
  const [copiedEmail, setCopiedEmail] = useState<string | null>(null);
  const [imageErrors, setImageErrors] = useState<Record<string, boolean>>({});
  const [activeModalMember, setActiveModalMember] = useState<TeamMember | null>(null);
  const [calibrated, setCalibrated] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const [isTouchDevice, setIsTouchDevice] = useState(false);
  const [parallax, setParallax] = useState({ x: 0, y: 0 });

  // Initial Calibration Sweep (Step 8: 800ms subtle entrance, never blocking)
  useEffect(() => {
    const timer = setTimeout(() => {
      setCalibrated(true);
    }, 850);
    return () => clearTimeout(timer);
  }, []);

  // Motion and Touch Hardware Detection
  useEffect(() => {
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(motionQuery.matches);

    const handleMotionChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };
    motionQuery.addEventListener('change', handleMotionChange);

    const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    setIsTouchDevice(hasTouch);

    return () => {
      motionQuery.removeEventListener('change', handleMotionChange);
    };
  }, []);

  // Subtle Smooth Mouse Parallax for Hero Ambient Mesh
  useEffect(() => {
    if (prefersReducedMotion || isTouchDevice) return;

    let rafId: number;
    const handleMouseMove = (e: MouseEvent) => {
      cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        const x = ((e.clientX / window.innerWidth) - 0.5) * 16;
        const y = ((e.clientY / window.innerHeight) - 0.5) * 16;
        setParallax({ x, y });
      });
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, [prefersReducedMotion, isTouchDevice]);

  // Handle ESC key to dismiss modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && activeModalMember) {
        setActiveModalMember(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeModalMember]);

  // Lock body scroll when modal is active
  useEffect(() => {
    if (activeModalMember) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [activeModalMember]);

  const handleCopyEmail = (email: string, id: string) => {
    navigator.clipboard.writeText(email);
    setCopiedEmail(id);
    setTimeout(() => {
      setCopiedEmail(null);
    }, 2200);
  };

  const handleImageError = (id: string) => {
    setImageErrors((prev) => ({ ...prev, [id]: true }));
  };

  return (
    <div className={`min-h-screen ag-blueprint-grid bg-[#E8F6FF] dark:bg-[#020617] text-slate-800 dark:text-slate-100 flex flex-col antialiased selection:bg-[#0B3D91] selection:text-white dark:selection:bg-indigo-500 font-sans transition-colors duration-300 relative`}>
      {/* =========================================================================
          0. LIGHTWEIGHT CALIBRATION HUD (Step 8: Entrance Bar)
          ========================================================================= */}
      {!calibrated && (
        <div className="fixed top-0 left-0 right-0 z-50 pointer-events-none">
          <div className="h-[2px] bg-gradient-to-r from-[#0B3D91] via-[#3BA7F2] to-[#7FE7D6] dark:from-indigo-500 dark:via-cyan-400 dark:to-violet-400 ag-calibration-bar" />
        </div>
      )}

      {/* =========================================================================
          1. NAVIGATION & ARCHITECTURAL DIRECTORY HUD
          ========================================================================= */}
      <header className="border-b border-[#D0E6F7] dark:border-white/[0.08] bg-white/85 dark:bg-[#0F172A]/75 backdrop-blur-xl sticky top-0 z-30 transition-all duration-200 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {/* Return to SpaceLoop Home */}
            <button
              type="button"
              onClick={() => navigate('/')}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white hover:bg-[#F0F8FF] text-slate-700 hover:text-[#0B3D91] border border-[#D0E6F7] dark:bg-slate-800/90 dark:hover:bg-slate-750 text-xs font-semibold dark:text-slate-300 dark:hover:text-white dark:border-white/10 transition shadow-2xs focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0B3D91]"
              title="Return to SpaceLoop Home"
              aria-label="Return to SpaceLoop Home"
            >
              <ArrowLeft className="w-3.5 h-3.5 text-[#0B3D91] dark:text-indigo-400" />
              <span>Return to SpaceLoop</span>
            </button>
            <span className="text-[#D0E6F7] dark:text-slate-700">|</span>
            <div className="inline-flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-white">
              <span className="w-2 h-2 rounded-full bg-[#0B3D91] dark:bg-cyan-400 animate-pulse" />
              <span className="font-mono tracking-wider uppercase text-[11px]">ARCH // SYSTEM DIRECTORY</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Seamless Theme Toggle Button */}
            <ThemeToggle variant="pill" />

            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#0B3D91]/10 hover:bg-[#0B3D91]/20 text-[#0B3D91] border border-[#0B3D91]/30 dark:bg-indigo-500/15 dark:hover:bg-indigo-500/25 dark:text-indigo-300 dark:border-indigo-500/30 text-xs font-semibold transition focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0B3D91]"
              title="Explore SpaceLoop Marketplace"
            >
              <Compass className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Explore Spaces</span>
            </button>

            <span className="text-[10px] uppercase font-mono font-bold tracking-widest px-2.5 py-1 rounded-full bg-white dark:bg-slate-800/90 text-[#0B3D91] dark:text-slate-300 border border-[#D0E6F7] dark:border-white/10 shadow-2xs">
              4 CORE ARCHITECTS
            </span>
          </div>
        </div>
      </header>

      {/* =========================================================================
          2. ANTIGRAVITY HERO SECTION (Step 3: Meet the Architects Behind SpaceLoop)
          ========================================================================= */}
      <section className="relative overflow-hidden pt-16 pb-20 md:pt-24 md:pb-28 border-b border-[#D0E6F7] dark:border-white/[0.08] bg-gradient-to-b from-[#E8F6FF] via-[#F0F8FF]/80 to-white dark:from-[#020617] dark:via-[#0B132B]/50 dark:to-[#020617] transition-colors duration-300">
        {/* Layered Architectural Ambient Lighting & Parallax Mesh */}
        <div
          className={`absolute -top-32 left-1/2 -translate-x-1/2 w-[720px] h-[360px] bg-[#3BA7F2]/25 dark:bg-indigo-600/20 blur-[130px] rounded-full pointer-events-none transition-transform duration-300 ease-out will-change-transform ag-ambient-floating`}
          style={{
            transform: prefersReducedMotion
              ? 'translate3d(-50%, 0, 0)'
              : `translate3d(calc(-50% + ${parallax.x * 0.9}px), ${parallax.y * 0.9}px, 0)`,
          }}
        />
        <div
          className={`absolute top-20 right-10 w-[420px] h-[420px] bg-[#7FE7D6]/30 dark:bg-cyan-600/15 blur-[130px] rounded-full pointer-events-none transition-transform duration-300 ease-out will-change-transform ag-ambient-floating`}
          style={{
            transform: prefersReducedMotion
              ? 'translate3d(0, 0, 0)'
              : `translate3d(${-parallax.x * 0.7}px, ${-parallax.y * 0.7}px, 0)`,
          }}
        />

        {/* Precision Crosshairs in Hero Corners */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="flex flex-col items-center text-center max-w-4xl mx-auto">
            {/* Technical Subtitle Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/80 dark:bg-slate-900/80 border border-[#D0E6F7] dark:border-white/10 text-[#0B3D91] dark:text-cyan-300 text-xs font-mono font-bold mb-6 shadow-2xs backdrop-blur-md">
              <Sparkles className="w-3.5 h-3.5 text-[#3BA7F2] dark:text-cyan-400" />
              <span className="tracking-widest uppercase">SPACE-TECH ARCHITECTURE // VOL. 2026</span>
            </div>

            {/* Exact Required Heading */}
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.08] font-display">
              Meet the Architects <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#0B3D91] via-[#1E40AF] to-[#3BA7F2] dark:from-cyan-400 dark:via-indigo-300 dark:to-violet-400">
                Behind SpaceLoop
              </span>
            </h1>

            {/* Concise Supporting Text introducing the four-person team */}
            <p className="mt-6 text-lg sm:text-2xl text-slate-800 dark:text-slate-100 font-display italic font-semibold tracking-tight max-w-3xl leading-relaxed">
              “Four minds. One mission. Making every suitable space work smarter.”
            </p>

            <p className="mt-4 text-sm sm:text-base text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed font-normal">
              Introducing the multidisciplinary four-person engineering team responsible for designing, building, and securing India’s premier peer-to-peer physical space marketplace.
            </p>

            {/* Architectural Telemetry Matrix */}
            <div className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 w-full max-w-3xl">
              <div className="p-3.5 rounded-2xl bg-white/80 dark:bg-slate-900/50 border border-[#D0E6F7] dark:border-white/[0.08] backdrop-blur-md shadow-2xs">
                <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-widest">PROTOCOL</div>
                <div className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white mt-1">Section 52 Indian Easements</div>
              </div>
              <div className="p-3.5 rounded-2xl bg-white/80 dark:bg-slate-900/50 border border-[#D0E6F7] dark:border-white/[0.08] backdrop-blur-md shadow-2xs">
                <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-widest">AI ROUTING</div>
                <div className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white mt-1">Groq 120B + Gemini Failover</div>
              </div>
              <div className="p-3.5 rounded-2xl bg-white/80 dark:bg-slate-900/50 border border-[#D0E6F7] dark:border-white/[0.08] backdrop-blur-md shadow-2xs">
                <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-widest">SOVEREIGNTY</div>
                <div className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white mt-1">DPDP Act 2023 Tokenized</div>
              </div>
              <div className="p-3.5 rounded-2xl bg-white/80 dark:bg-slate-900/50 border border-[#D0E6F7] dark:border-white/[0.08] backdrop-blur-md shadow-2xs">
                <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-widest">ESCROW HOLD</div>
                <div className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white mt-1">₹100 NPCI Micro-Escrow</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Guide Hairline */}
      <div className="ag-guide-line-h" />

      {/* =========================================================================
          3. FOUR INTERACTIVE GLASSMORPHISM PROFILES (Step 4 & 5: Asymmetric Showcase)
          ========================================================================= */}
      <main className="py-16 sm:py-24 relative z-10 flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Section Section Header */}
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-12 sm:mb-16">
            <div>
              <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-widest text-[#0B3D91] dark:text-cyan-400 mb-2">
                <Activity className="w-3.5 h-3.5" />
                <span>CORE LEADERSHIP DIRECTORY // 4 PROFILES</span>
              </div>
              <h2 className="text-2xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight font-display">
                Engineering & Architecture Matrix
              </h2>
            </div>
            <p className="text-xs font-mono text-slate-500 dark:text-slate-400 max-w-sm">
              Hover cards for localized spotlight & tilt. Click <span className="text-[#0B3D91] dark:text-cyan-300 font-bold">Inspect Specs</span> for complete technical specs.
            </p>
          </div>

          {/* 4 Team Member Profiles rendered in an interactive glassmorphic matrix */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 sm:gap-10">
            {TEAM_MEMBERS.map((member, index) => (
              <ProfileGlassCard
                key={member.id}
                member={member}
                index={index}
                isLight={isLight}
                hasFailedImage={Boolean(imageErrors[member.id])}
                onImageError={() => handleImageError(member.id)}
                onInspect={() => setActiveModalMember(member)}
                onCopyEmail={() => handleCopyEmail(member.email, member.id)}
                isCopied={copiedEmail === member.id}
                prefersReducedMotion={prefersReducedMotion}
                isTouchDevice={isTouchDevice}
              />
            ))}
          </div>
        </div>
      </main>

      {/* =========================================================================
          4. EXPANDABLE GLASS MODAL (Step 5: Deep-Dive Architecture Inspection)
          ========================================================================= */}
      {activeModalMember && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby={`modal-title-${activeModalMember.id}`}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto bg-slate-950/70 ag-modal-backdrop"
          onClick={() => setActiveModalMember(null)}
        >
          <div
            className="relative w-full max-w-3xl rounded-3xl bg-white/95 dark:bg-[#0F172A]/95 border border-[#D0E6F7] dark:border-white/10 shadow-2xl p-6 sm:p-10 my-8 backdrop-blur-2xl transition-all duration-300 ag-custom-scroll"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Corner Crosshairs */}
            <div className="ag-crosshair-corner top-3 left-3 text-[#0B3D91] dark:text-cyan-400" />
            <div className="ag-crosshair-corner top-3 right-3 text-[#0B3D91] dark:text-cyan-400" />
            <div className="ag-crosshair-corner bottom-3 left-3 text-[#0B3D91] dark:text-cyan-400" />
            <div className="ag-crosshair-corner bottom-3 right-3 text-[#0B3D91] dark:text-cyan-400" />

            {/* Modal Header Bar */}
            <div className="flex items-center justify-between gap-4 pb-6 border-b border-[#D0E6F7] dark:border-white/10 mb-6">
              <div className="flex items-center gap-2.5">
                <span className="text-[10px] font-mono font-bold uppercase px-2.5 py-1 rounded-md bg-[#0B3D91]/10 text-[#0B3D91] dark:bg-cyan-500/10 dark:text-cyan-300 border border-[#0B3D91]/20 dark:border-cyan-500/30">
                  SLOT // {activeModalMember.badgeNumber}
                </span>
                <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                  SUBSYSTEM ARCHITECTURE SPEC
                </span>
              </div>
              <button
                type="button"
                onClick={() => setActiveModalMember(null)}
                className="w-9 h-9 rounded-xl flex items-center justify-center bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0B3D91]"
                aria-label="Close architecture inspection modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Member Profile Banner */}
            <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 mb-8">
              <div className="w-28 h-35 shrink-0 rounded-2xl overflow-hidden border border-[#D0E6F7] dark:border-white/10 shadow-md bg-slate-100 dark:bg-slate-800">
                <img
                  src={activeModalMember.photoUrl}
                  alt={activeModalMember.name}
                  className="w-full h-full object-cover object-top"
                />
              </div>

              <div className="text-center sm:text-left flex-1">
                <h3 id={`modal-title-${activeModalMember.id}`} className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display">
                  {activeModalMember.name}
                </h3>
                <div className="mt-1 text-sm font-semibold text-[#0B3D91] dark:text-cyan-400">
                  {activeModalMember.role}
                </div>
                <div className="text-xs font-mono text-slate-500 dark:text-slate-400 mt-1">
                  Focus: {activeModalMember.domain}
                </div>
                <p className="mt-3 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                  {activeModalMember.intro}
                </p>
              </div>
            </div>

            {/* Subsystem Deep Dive */}
            <div className="p-5 sm:p-6 rounded-2xl bg-[#F0F8FF] dark:bg-slate-950/60 border border-[#D0E6F7] dark:border-white/10 mb-8 ag-subsystem-console">
              <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#D0E6F7] dark:border-slate-800 mb-4">
                <div>
                  <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-widest">
                    PRIMARY SUBSYSTEM
                  </div>
                  <div className="text-base font-bold text-slate-900 dark:text-white">
                    {activeModalMember.subsystem.title}
                  </div>
                </div>
                <div className="px-3 py-1.5 rounded-full bg-white dark:bg-slate-800 border border-[#D0E6F7] dark:border-slate-700 text-xs font-mono font-bold text-[#0B3D91] dark:text-cyan-300">
                  {activeModalMember.subsystem.metric.label}: <span className="font-extrabold">{activeModalMember.subsystem.metric.value}</span>
                </div>
              </div>

              <div className="text-xs font-mono font-bold uppercase text-slate-600 dark:text-slate-400 mb-2">
                ARCHITECTURAL CAPABILITIES:
              </div>
              <ul className="space-y-2 mb-5">
                {activeModalMember.subsystem.highlights.map((h, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                    <Check className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
                    <span>{h}</span>
                  </li>
                ))}
              </ul>

              <div className="text-xs font-mono font-bold uppercase text-slate-600 dark:text-slate-400 mb-2">
                TECHNOLOGY STACK:
              </div>
              <div className="flex flex-wrap gap-2">
                {activeModalMember.subsystem.techStack.map((tech, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 border border-[#D0E6F7] dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-mono shadow-2xs"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            </div>

            {/* Direct Contact Actions (Step 7: Real Links) */}
            <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-[#D0E6F7] dark:border-white/10">
              <div className="flex items-center gap-3">
                <a
                  href={`mailto:${activeModalMember.email}`}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#0B3D91] hover:bg-[#082C6B] text-white dark:bg-indigo-600 dark:hover:bg-indigo-500 text-xs font-semibold transition shadow-md focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0B3D91]"
                >
                  <Mail className="w-4 h-4" />
                  <span>Send Direct Email</span>
                </a>

                <a
                  href={activeModalMember.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-800 border border-[#D0E6F7] hover:border-[#0A66C2] dark:bg-slate-800 dark:hover:bg-slate-700 dark:border-white/10 dark:text-white text-xs font-semibold transition shadow-2xs focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0B3D91]"
                >
                  <Linkedin className="w-4 h-4 text-[#0A66C2]" />
                  <span>LinkedIn Profile</span>
                  <ExternalLink className="w-3 h-3 text-slate-400" />
                </a>
              </div>

              <button
                type="button"
                onClick={() => setActiveModalMember(null)}
                className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold transition"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          5. CLOSING BANNER & RETURN NAVIGATION
          ========================================================================= */}
      <footer className="py-16 bg-gradient-to-b from-[#E8F6FF] via-[#F0F8FF] to-white dark:from-[#020617] dark:via-[#0F172A] dark:to-[#020617] border-t border-[#D0E6F7] dark:border-white/[0.08] relative transition-colors duration-300">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#0B3D91]/10 border border-[#0B3D91]/25 text-[#0B3D91] dark:bg-cyan-500/10 dark:border-cyan-500/25 dark:text-cyan-300 text-xs font-mono font-bold mb-4 shadow-2xs">
            <Activity className="w-3.5 h-3.5" />
            <span className="uppercase tracking-wider">HACKATHON GRAND FINALE // PRODUCTION READY</span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight font-display">
            Building the Future of Shared Physical Spaces
          </h2>

          <p className="mt-4 text-sm sm:text-base text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            SpaceLoop unlocks idle physical capacity across urban India through zero-hardware smart access, automated micro-leases under Section 52, and sovereign identity verification.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-[#0B3D91] hover:bg-[#072C6B] dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-[#0B3D91]/25 dark:shadow-indigo-600/30 transition flex items-center justify-center gap-2 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0B3D91]"
            >
              <Compass className="w-4 h-4" />
              <span>Explore Marketplace</span>
            </button>

            <button
              type="button"
              onClick={() => navigate('/')}
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-white hover:bg-[#F0F8FF] text-slate-800 hover:text-[#0B3D91] border border-[#D0E6F7] dark:bg-slate-900 dark:hover:bg-slate-800 dark:text-slate-200 dark:border-white/10 font-bold text-xs transition shadow-2xs flex items-center justify-center gap-2 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0B3D91]"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Return to Home</span>
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

// ============================================================================
// PROFILE GLASS CARD COMPONENT WITH CURSOR-REACTIVE LIGHTING & 3D TILT
// ============================================================================
interface ProfileGlassCardProps {
  member: TeamMember;
  index: number;
  isLight: boolean;
  hasFailedImage: boolean;
  onImageError: () => void;
  onInspect: () => void;
  onCopyEmail: () => void;
  isCopied: boolean;
  prefersReducedMotion: boolean;
  isTouchDevice: boolean;
}

const ProfileGlassCard: React.FC<ProfileGlassCardProps> = ({
  member,
  isLight,
  hasFailedImage,
  onImageError,
  onInspect,
  onCopyEmail,
  isCopied,
  prefersReducedMotion,
  isTouchDevice,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [mousePos, setMousePos] = useState({ x: -1000, y: -1000 });
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const accent = ACCENT_TOKENS[member.accent] || ACCENT_TOKENS.indigo;
  const AccentIcon = accent.icon;

  // Cursor Spotlight & Dampened 3D Tilt Interaction (Antigravity Style)
  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (prefersReducedMotion || isTouchDevice || !cardRef.current) return;

      const rect = cardRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      setMousePos({ x, y });

      // Subtle tilt: max ±2.5 degrees so it feels tactile and stable
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      const tiltX = ((x - centerX) / centerX) * 2.5;
      const tiltY = ((centerY - y) / centerY) * 2.5;

      setTilt({ x: tiltX, y: tiltY });
    },
    [prefersReducedMotion, isTouchDevice]
  );

  const handleMouseEnter = () => {
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    setTilt({ x: 0, y: 0 });
    setMousePos({ x: -1000, y: -1000 });
  };

  return (
    <article
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`group ag-glass-card p-6 sm:p-8 rounded-3xl bg-white/85 dark:bg-[#0F172A]/70 border ${isLight ? accent.lightBorder : accent.border} backdrop-blur-2xl shadow-md transition-all duration-300 flex flex-col justify-between overflow-hidden relative`}
      style={{
        transform: prefersReducedMotion || isTouchDevice
          ? 'none'
          : `perspective(1000px) rotateX(${tilt.y}deg) rotateY(${tilt.x}deg) translateY(${isHovered ? -4 : 0}px)`,
        boxShadow: isHovered
          ? isLight
            ? `0 20px 40px -10px rgba(11, 61, 145, 0.14), 0 0 24px ${accent.glow}`
            : `0 20px 50px -10px rgba(0, 0, 0, 0.7), 0 0 28px ${accent.glow}`
          : undefined,
      }}
    >
      {/* Precision Corner Crosshairs (+) */}
      <div className="ag-crosshair-corner top-3 left-3 text-slate-400 dark:text-slate-500" />
      <div className="ag-crosshair-corner top-3 right-3 text-slate-400 dark:text-slate-500" />
      <div className="ag-crosshair-corner bottom-3 left-3 text-slate-400 dark:text-slate-500" />
      <div className="ag-crosshair-corner bottom-3 right-3 text-slate-400 dark:text-slate-500" />

      {/* Cursor-Reactive Specular Spotlight Overlay */}
      {!prefersReducedMotion && !isTouchDevice && isHovered && (
        <div
          className="ag-spotlight-surface"
          style={{
            background: `radial-gradient(450px circle at ${mousePos.x}px ${mousePos.y}px, rgba(${accent.rgb}, ${isLight ? 0.14 : 0.22}), transparent 80%)`,
          }}
        />
      )}

      {/* Top Telemetry Header */}
      <div className="relative z-10 flex items-center justify-between gap-3 pb-4 border-b border-[#D0E6F7] dark:border-white/[0.08] mb-6">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono font-bold tracking-wider px-2.5 py-0.5 rounded-md bg-[#0B3D91]/10 dark:bg-white/10 text-[#0B3D91] dark:text-slate-200 border border-[#0B3D91]/20 dark:border-white/10">
            SLOT // {member.badgeNumber}
          </span>
          <div className="flex items-center gap-1.5 text-[11px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>ONLINE</span>
          </div>
        </div>

        <button
          type="button"
          onClick={onInspect}
          className="inline-flex items-center gap-1.5 text-[11px] font-mono font-bold text-slate-600 hover:text-[#0B3D91] dark:text-slate-400 dark:hover:text-cyan-300 transition focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0B3D91]"
          title="Inspect Full Subsystem Architecture"
          aria-label={`Inspect ${member.name}'s architecture specs`}
        >
          <Maximize2 className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Inspect Specs</span>
        </button>
      </div>

      {/* Main Profile Info Row */}
      <div className="relative z-10 flex flex-col sm:flex-row items-center sm:items-start gap-6 mb-6">
        {/* Face-Safe 4:5 Portrait Frame */}
        <div className="w-32 sm:w-36 shrink-0 aspect-[4/5] rounded-2xl overflow-hidden bg-slate-100 dark:bg-slate-900 border border-[#D0E6F7] dark:border-white/10 shadow-md relative group/photo">
          {!hasFailedImage ? (
            <img
              src={member.photoUrl}
              alt={member.name}
              onError={onImageError}
              className="w-full h-full object-cover object-top filter contrast-[1.02] group-hover:scale-105 transition-transform duration-500 ease-out"
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center p-4 bg-gradient-to-b from-slate-100 to-slate-200 dark:from-slate-900 dark:to-slate-950 text-slate-500 text-center">
              <div className="w-12 h-12 rounded-full bg-white dark:bg-slate-800 flex items-center justify-center text-[#0B3D91] dark:text-slate-300 mb-2 shadow-xs">
                <AccentIcon className="w-6 h-6" />
              </div>
              <span className="text-[10px] font-mono font-bold uppercase">{member.badgeNumber} // PHOTO</span>
            </div>
          )}

          {/* Bottom Depth Gradient */}
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 via-transparent to-transparent pointer-events-none" />
        </div>

        {/* Member Details */}
        <div className="flex-1 text-center sm:text-left">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono font-bold uppercase border mb-2 shadow-2xs" style={{
            backgroundColor: `rgba(${accent.rgb}, 0.1)`,
            borderColor: `rgba(${accent.rgb}, 0.3)`,
            color: accent.color,
          }}>
            <AccentIcon className="w-3 h-3" />
            <span>{member.role}</span>
          </div>

          <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-snug font-display">
            {member.name}
          </h3>

          <div className="text-xs font-mono font-medium text-slate-500 dark:text-slate-400 mt-1 mb-3">
            Domain: <span className="text-slate-700 dark:text-slate-300 font-semibold">{member.domain}</span>
          </div>

          <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-normal">
            {member.intro}
          </p>
        </div>
      </div>

      {/* Technical Subsystem Capsule */}
      <div className="relative z-10 p-4 rounded-2xl bg-[#F0F8FF]/80 dark:bg-slate-950/50 border border-[#D0E6F7] dark:border-white/[0.08] mb-6 ag-subsystem-console">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-[#D0E6F7] dark:border-slate-800/80 mb-3">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-[#D0E6F7] dark:border-slate-700">
              {member.subsystem.codename}
            </span>
            <span className="text-xs font-bold text-slate-900 dark:text-white font-display">
              {member.subsystem.title}
            </span>
          </div>
          <div className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-[#D0E6F7] dark:border-slate-700">
            {member.subsystem.metric.label}: <span className="font-extrabold" style={{ color: accent.color }}>{member.subsystem.metric.value}</span>
          </div>
        </div>

        {/* Highlights List */}
        <ul className="space-y-1.5 mb-3">
          {member.subsystem.highlights.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
              <Check className="w-3.5 h-3.5 mt-0.5 shrink-0" style={{ color: accent.color }} />
              <span>{item}</span>
            </li>
          ))}
        </ul>

        {/* Tech Stack Pills */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="text-[10px] font-mono font-bold uppercase text-slate-500 dark:text-slate-400 mr-1">
            Stack:
          </span>
          {member.subsystem.techStack.map((tech, idx) => (
            <span
              key={idx}
              className="px-2 py-0.5 rounded-md bg-white dark:bg-slate-800/90 border border-[#D0E6F7] dark:border-slate-700 text-slate-700 dark:text-slate-300 text-[10px] font-mono font-medium shadow-2xs"
            >
              {tech}
            </span>
          ))}
        </div>
      </div>

      {/* Dedicated Contact Actions (Step 7: Real LinkedIn and Email links) */}
      <div className="relative z-10 pt-4 border-t border-[#D0E6F7] dark:border-white/[0.08] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {/* Email Mailto Link */}
          <a
            href={`mailto:${member.email}`}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white hover:bg-[#F0F8FF] text-slate-800 hover:text-[#0B3D91] border border-[#D0E6F7] hover:border-[#3BA7F2] dark:bg-slate-800/90 dark:hover:bg-slate-750 dark:border-white/10 dark:text-slate-200 dark:hover:text-white text-xs font-semibold tracking-wide transition shadow-2xs focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0B3D91]"
            title={`Send email to ${member.email}`}
            aria-label={`Send email to ${member.name} at ${member.email}`}
          >
            <Mail className="w-3.5 h-3.5 text-[#0B3D91] dark:text-cyan-400" />
            <span className="font-mono text-[11px]">{member.email}</span>
          </a>

          {/* Copy Email Helper */}
          <button
            type="button"
            onClick={onCopyEmail}
            className="inline-flex items-center justify-center w-8 h-8 rounded-xl bg-white hover:bg-[#F0F8FF] text-slate-500 hover:text-[#0B3D91] border border-[#D0E6F7] dark:bg-slate-800/90 dark:hover:bg-slate-700 dark:border-white/10 dark:text-slate-400 dark:hover:text-white text-xs transition shadow-2xs focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0B3D91]"
            title="Copy email address"
            aria-label={`Copy ${member.name}'s email address`}
          >
            {isCopied ? (
              <Check className="w-3.5 h-3.5 text-emerald-500" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
          </button>
        </div>

        {/* LinkedIn Profile Real URL Link */}
        <a
          href={member.linkedin}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-white hover:bg-[#0A66C2]/10 border border-[#D0E6F7] hover:border-[#0A66C2]/50 text-slate-800 hover:text-[#0A66C2] dark:bg-slate-800/90 dark:hover:bg-[#0A66C2]/20 dark:border-white/10 dark:hover:border-[#0A66C2]/60 dark:text-slate-200 dark:hover:text-white text-xs font-semibold tracking-wide transition shadow-2xs focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0B3D91]"
          title={`View ${member.name}'s LinkedIn Profile`}
          aria-label={`Open ${member.name}'s LinkedIn profile in new tab`}
        >
          <Linkedin className="w-3.5 h-3.5 text-[#0A66C2]" />
          <span>LinkedIn</span>
          <ExternalLink className="w-3 h-3 text-slate-400" />
        </a>
      </div>
    </article>
  );
};

export default ArchitecturePage;
