import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { ThemeToggle } from '../components/common/ThemeToggle';

/**
 * ============================================================================
 * SPACELOOP TEAM ARCHITECTURE & PROFILE DIRECTORY
 * ----------------------------------------------------------------------------
 * Dual-palette support:
 * - Ocean Breeze (Light Theme): #0B3D91 Primary Blue, #3BA7F2 Secondary Blue,
 *   #7FE7D6 Aqua, #E8F6FF Canvas, #FFFFFF Surface, #D0E6F7 Border, #0B2545 Deep Navy.
 * - Midnight Neon (Dark Theme): #020617 Obsidian Canvas, #0F172A Slate Surface,
 *   Indigo #4F46E5, Cyan #06B6D4, Violet #8B5CF6, Amber #F59E0B.
 *
 * Alternating editorial profile architecture with face-safe 4:5 portraits,
 * restrained mouse parallax, high-contrast readable information typography,
 * and dedicated contact integrations.
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

export const ArchitecturePage: React.FC = () => {
  const navigate = useNavigate();
  const { theme } = useTheme();
  const [copiedEmail, setCopiedEmail] = useState<string | null>(null);
  const [imageErrors, setImageErrors] = useState<Record<string, boolean>>({});
  const [parallax, setParallax] = useState({ x: 0, y: 0 });

  // Restrained mouse parallax respecting user motion preferences
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mediaQuery.matches) return;

    let rafId: number;
    const handleMouseMove = (e: MouseEvent) => {
      cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        const offsetX = ((e.clientX / window.innerWidth) - 0.5) * 20;
        const offsetY = ((e.clientY / window.innerHeight) - 0.5) * 20;
        setParallax({ x: offsetX, y: offsetY });
      });
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

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

  const getAccentStyles = (accent: TeamMember['accent']) => {
    switch (accent) {
      case 'cyan':
        return {
          glow: 'from-cyan-500/20 via-blue-500/10 to-transparent',
          borderHover: 'hover:border-cyan-500/50',
          badgeBg: 'bg-cyan-500/10 text-cyan-700 dark:text-cyan-300 border-cyan-500/30',
          dot: 'bg-cyan-500 dark:bg-cyan-400',
          iconColor: 'text-cyan-600 dark:text-cyan-400',
          metricPill: 'text-cyan-700 dark:text-cyan-300 bg-cyan-50 dark:bg-cyan-950/40 border-cyan-200 dark:border-cyan-800/60',
        };
      case 'violet':
        return {
          glow: 'from-violet-500/20 via-purple-500/10 to-transparent',
          borderHover: 'hover:border-violet-500/50',
          badgeBg: 'bg-violet-500/10 text-violet-700 dark:text-violet-300 border-violet-500/30',
          dot: 'bg-violet-500 dark:bg-violet-400',
          iconColor: 'text-violet-600 dark:text-violet-400',
          metricPill: 'text-violet-700 dark:text-violet-300 bg-violet-50 dark:bg-violet-950/40 border-violet-200 dark:border-violet-800/60',
        };
      case 'amber':
        return {
          glow: 'from-amber-500/20 via-orange-500/10 to-transparent',
          borderHover: 'hover:border-amber-500/50',
          badgeBg: 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30',
          dot: 'bg-amber-500 dark:bg-amber-400',
          iconColor: 'text-amber-600 dark:text-amber-400',
          metricPill: 'text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800/60',
        };
      case 'indigo':
      default:
        return {
          glow: 'from-indigo-500/20 via-violet-500/10 to-transparent',
          borderHover: 'hover:border-indigo-500/50',
          badgeBg: 'bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border-indigo-500/30',
          dot: 'bg-indigo-500 dark:bg-indigo-400',
          iconColor: 'text-indigo-600 dark:text-indigo-400',
          metricPill: 'text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-950/40 border-indigo-200 dark:border-indigo-800/60',
        };
    }
  };

  const isLight = theme === 'light';

  return (
    <div className="min-h-screen bg-[#E8F6FF] dark:bg-slate-950 text-slate-800 dark:text-slate-100 flex flex-col antialiased selection:bg-[#0B3D91] selection:text-white dark:selection:bg-indigo-500 font-sans transition-colors duration-300">
      {/* =========================================================================
          1. PAGE RETURN & BREADCRUMB BAR (Clean Navigation & Theme Switcher)
          ========================================================================= */}
      <section className="border-b border-[#D0E6F7] dark:border-slate-800/80 bg-white/90 dark:bg-slate-900/80 backdrop-blur-xl sticky top-16 z-30 transition-all duration-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {/* Return to SpaceLoop Home */}
            <button
              onClick={() => navigate('/')}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white hover:bg-[#F0F8FF] text-slate-700 hover:text-[#0B3D91] border border-[#D0E6F7] dark:bg-slate-800/90 dark:hover:bg-slate-750 text-xs font-semibold dark:text-slate-300 dark:hover:text-white dark:border-slate-700/80 transition shadow-sm"
              title="Return to SpaceLoop Home"
            >
              <i className="fa-solid fa-arrow-left text-[11px] text-[#0B3D91] dark:text-indigo-400" />
              <span>Return to SpaceLoop</span>
            </button>
            <span className="text-[#D0E6F7] dark:text-slate-700">|</span>
            <div className="inline-flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-white">
              <span className="w-2 h-2 rounded-full bg-[#0B3D91] dark:bg-indigo-500 animate-pulse" />
              <span className="font-display tracking-tight">Architecture & Team Directory</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Seamless Theme Toggle Button */}
            <ThemeToggle variant="pill" />

            <button
              onClick={() => navigate('/explore')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#0B3D91]/10 hover:bg-[#0B3D91]/20 text-[#0B3D91] border border-[#0B3D91]/30 dark:bg-indigo-600/15 dark:hover:bg-indigo-600/25 dark:text-indigo-300 dark:border-indigo-500/30 text-xs font-semibold transition"
            >
              <i className="fa-solid fa-compass text-[11px]" />
              <span className="hidden sm:inline">Explore Spaces</span>
            </button>
            <span className="text-[10px] uppercase font-mono font-extrabold tracking-wider px-2.5 py-1 rounded-full bg-white dark:bg-slate-800 text-[#0B3D91] dark:text-slate-300 border border-[#D0E6F7] dark:border-slate-700 shadow-sm">
              4 Core Profiles
            </span>
          </div>
        </div>
      </section>

      {/* =========================================================================
          2. DISTINCTIVE HERO SECTION (Ocean Breeze / Midnight Neon Dual Glow)
          ========================================================================= */}
      <section className="relative overflow-hidden pt-16 pb-20 md:pt-24 md:pb-24 border-b border-[#D0E6F7] dark:border-slate-800/80 bg-gradient-to-b from-[#E8F6FF] via-[#F0F8FF] to-white dark:from-slate-900 dark:via-slate-950 dark:to-slate-950 transition-colors duration-300">
        {/* Subtle Background Pattern */}
        <div
          className="absolute inset-0 pointer-events-none opacity-30 dark:opacity-20"
          style={{
            backgroundImage: isLight
              ? 'radial-gradient(rgba(11, 61, 145, 0.15) 1px, transparent 1px)'
              : 'radial-gradient(rgba(99, 102, 241, 0.3) 1px, transparent 1px)',
            backgroundSize: '36px 36px',
          }}
        />

        {/* Ambient Glowing Orbs with Restrained Mouse Parallax */}
        <div
          className="absolute -top-32 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-[#3BA7F2]/20 dark:bg-indigo-600/15 blur-[130px] rounded-full pointer-events-none transition-transform duration-300 ease-out will-change-transform"
          style={{
            transform: `translate3d(calc(-50% + ${parallax.x * 0.8}px), ${parallax.y * 0.8}px, 0)`,
          }}
        />
        <div
          className="absolute top-20 right-10 w-[380px] h-[380px] bg-[#7FE7D6]/25 dark:bg-cyan-600/10 blur-[120px] rounded-full pointer-events-none transition-transform duration-300 ease-out will-change-transform"
          style={{
            transform: `translate3d(${-parallax.x * 0.6}px, ${-parallax.y * 0.6}px, 0)`,
          }}
        />

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#0B3D91]/10 border border-[#0B3D91]/25 text-[#0B3D91] dark:bg-indigo-500/10 dark:border-indigo-500/25 dark:text-indigo-300 text-xs font-bold mb-6 shadow-sm">
            <i className="fa-solid fa-users text-[11px]" />
            <span className="font-display tracking-wide uppercase">Core Engineering & Leadership Team</span>
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-tight font-display">
            The People Behind <br className="hidden sm:inline" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#0B3D91] via-[#1E40AF] to-[#3BA7F2] dark:from-indigo-400 dark:via-violet-300 dark:to-cyan-300">
              SpaceLoop
            </span>
          </h1>

          <p className="mt-6 text-xl sm:text-2xl text-slate-800 dark:text-slate-100 font-display italic font-semibold tracking-tight max-w-3xl mx-auto leading-relaxed">
            “Four minds. One mission. Making every suitable space work smarter.”
          </p>

          <p className="mt-4 text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed font-normal">
            The multidisciplinary team designing, building, and deploying India’s premier peer-to-peer physical space marketplace.
          </p>
        </div>
      </section>

      {/* =========================================================================
          3. FOUR SPACIOUS EDITORIAL TEAM PROFILES (Alternating Layout & Clean Cards)
          ========================================================================= */}
      <section className="py-20 lg:py-28 bg-[#E8F6FF]/40 dark:bg-slate-950 border-b border-[#D0E6F7] dark:border-slate-800/80 relative transition-colors duration-300">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="space-y-20 lg:space-y-28">
            {TEAM_MEMBERS.map((member, index) => {
              const isEven = index % 2 === 0;
              const accent = getAccentStyles(member.accent);
              const hasImageFailed = imageErrors[member.id] || !member.photoUrl;

              return (
                <article
                  key={member.id}
                  className={`group relative rounded-3xl p-6 sm:p-10 lg:p-12 bg-white dark:bg-slate-900/60 border border-[#D0E6F7] dark:border-slate-800/90 transition-all duration-300 ease-out hover:-translate-y-2 shadow-[2.5px_5px_16px_-2px_rgba(11,61,145,0.08),1px_2px_5px_-1px_rgba(11,61,145,0.04)] hover:shadow-[4px_14px_30px_-4px_rgba(11,61,145,0.14),0_0_24px_rgba(59,167,242,0.16)] dark:hover:shadow-[6px_20px_45px_-4px_rgba(0,0,0,0.65),3px_6px_18px_-2px_rgba(0,0,0,0.38),0_0_24px_rgba(99,102,241,0.2)] ${accent.borderHover}`}
                >
                  {/* Ambient Backdrop Accent Glow */}
                  <div
                    className={`absolute -inset-0.5 rounded-3xl bg-gradient-to-br ${accent.glow} opacity-0 group-hover:opacity-100 blur-2xl transition-opacity duration-500 pointer-events-none`}
                  />

                  <div
                    className={`relative z-10 flex flex-col ${
                      isEven ? 'lg:flex-row' : 'lg:flex-row-reverse'
                    } items-center gap-10 lg:gap-16`}
                  >
                    {/* Portrait Area (Face-Safe Framing, 4:5 Proportion) */}
                    <div className="w-full sm:w-[360px] lg:w-[400px] shrink-0">
                      <div className="relative aspect-[4/5] w-full rounded-2xl sm:rounded-3xl overflow-hidden bg-slate-100 dark:bg-slate-950 border border-[#D0E6F7] dark:border-slate-800/90 shadow-xl group-hover:border-[#3BA7F2]/60 dark:group-hover:border-slate-700 transition duration-500 group-hover:-translate-y-1.5">
                        {!hasImageFailed ? (
                          <img
                            src={member.photoUrl}
                            alt={member.name}
                            onError={() => handleImageError(member.id)}
                            className="w-full h-full object-cover object-top filter contrast-[1.03] brightness-[0.99] group-hover:scale-105 transition-transform duration-700 ease-out"
                          />
                        ) : (
                          /* High-Fidelity Fallback Portrait Frame */
                          <div className="w-full h-full flex flex-col items-center justify-center p-8 bg-gradient-to-b from-slate-100 to-slate-200 dark:from-slate-900 dark:to-slate-950 text-slate-500 relative">
                            <div className="w-24 h-24 rounded-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 flex items-center justify-center mb-4 text-[#0B3D91] dark:text-slate-400 text-3xl shadow-md">
                              <i className="fa-solid fa-user" />
                            </div>
                            <div className="text-xs font-mono font-bold text-slate-700 dark:text-slate-400 uppercase tracking-wider text-center">
                              Photograph Slot {member.badgeNumber}
                            </div>
                            <div className="text-[11px] text-slate-500 dark:text-slate-500 text-center mt-1">
                              4:5 Portrait Ratio (Face-Centered)
                            </div>
                          </div>
                        )}

                        {/* Subtle Bottom Shade for Visual Depth */}
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-transparent to-transparent pointer-events-none" />

                        {/* Slot Identifier Overlay */}
                        <div className="absolute top-4 left-4">
                          <span className="px-3 py-1 rounded-full bg-slate-950/80 backdrop-blur-md border border-white/20 text-[11px] font-mono font-bold text-white shadow-sm">
                            PROFILE // {member.badgeNumber}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Editorial Content Area */}
                    <div className="flex-1 flex flex-col justify-center text-left w-full">
                      {/* Serial Tag */}
                      <div className="flex items-center gap-3 text-xs font-mono font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400 mb-2">
                        <span className="w-8 h-px bg-[#D0E6F7] dark:bg-slate-700" />
                        <span className={accent.iconColor}>
                          SpaceLoop Core Team // Slot {member.badgeNumber}
                        </span>
                      </div>

                      {/* Prominent Member Name */}
                      <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight font-display">
                        {member.name}
                      </h2>

                      {/* Official Role Label */}
                      <div className="mt-3 mb-2">
                        <span
                          className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-mono font-bold uppercase tracking-wider border shadow-sm ${accent.badgeBg}`}
                        >
                          <span className={`w-2 h-2 rounded-full ${accent.dot}`} />
                          <span>{member.role}</span>
                        </span>
                      </div>

                      {/* Domain Focus Label */}
                      <div className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-5">
                        Domain: <span className="text-slate-700 dark:text-slate-300">{member.domain}</span>
                      </div>

                      {/* Highly Visible Professional Introduction */}
                      <div className="relative mb-6">
                        <p className="text-base sm:text-lg text-slate-700 dark:text-slate-200 leading-relaxed font-normal">
                          {member.intro}
                        </p>
                      </div>

                      {/* Technical Subsystem Architecture Box */}
                      <div className="mb-6 p-5 sm:p-6 rounded-2xl bg-[#F0F8FF] dark:bg-slate-950/70 border border-[#D0E6F7] dark:border-slate-800/80 shadow-sm">
                        <div className="flex flex-wrap items-center justify-between gap-3 mb-3 pb-3 border-b border-[#D0E6F7] dark:border-slate-800">
                          <div className="flex items-center gap-2.5">
                            <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded-md bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-[#D0E6F7] dark:border-slate-700">
                              {member.subsystem.codename}
                            </span>
                            <h3 className="text-sm font-bold text-slate-900 dark:text-white font-display">
                              {member.subsystem.title}
                            </h3>
                          </div>
                          <div className={`px-2.5 py-1 rounded-full text-xs font-mono font-bold border ${accent.metricPill}`}>
                            {member.subsystem.metric.label}: <span className="font-extrabold">{member.subsystem.metric.value}</span>
                          </div>
                        </div>

                        {/* Visible Highlights Bullet List */}
                        <ul className="space-y-2 mb-4">
                          {member.subsystem.highlights.map((highlight, hIdx) => (
                            <li key={hIdx} className="flex items-start gap-2.5 text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                              <i className={`fa-solid fa-check-circle mt-0.5 text-xs shrink-0 ${accent.iconColor}`} />
                              <span>{highlight}</span>
                            </li>
                          ))}
                        </ul>

                        {/* Tech Stack Pills */}
                        <div className="flex flex-wrap items-center gap-1.5 pt-2">
                          <span className="text-[10px] font-mono font-bold uppercase text-slate-500 dark:text-slate-400 mr-1">
                            Stack:
                          </span>
                          {member.subsystem.techStack.map((tech, tIdx) => (
                            <span
                              key={tIdx}
                              className="px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800/90 border border-[#D0E6F7] dark:border-slate-700/80 text-slate-700 dark:text-slate-300 text-[11px] font-mono font-medium shadow-2xs"
                            >
                              {tech}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Dedicated Email and LinkedIn Profile Buttons */}
                      <div className="pt-6 border-t border-[#D0E6F7] dark:border-slate-800/80 flex flex-wrap items-center gap-3">
                        {/* Email Button */}
                        <a
                          href={`mailto:${member.email}`}
                          className="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-white hover:bg-[#F0F8FF] text-slate-800 hover:text-[#0B3D91] border border-[#D0E6F7] hover:border-[#3BA7F2] dark:bg-slate-800/90 dark:hover:bg-slate-750 dark:border-slate-700/80 dark:text-slate-200 dark:hover:text-white text-xs font-semibold tracking-wide transition shadow-sm group/btn"
                          title={`Send email to ${member.email}`}
                        >
                          <i className="fa-solid fa-envelope text-[#0B3D91] dark:text-indigo-400 text-sm" />
                          <span className="font-mono">{member.email}</span>
                        </a>

                        {/* Copy Email Helper */}
                        <button
                          type="button"
                          onClick={() => handleCopyEmail(member.email, member.id)}
                          className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-white hover:bg-[#F0F8FF] text-slate-500 hover:text-[#0B3D91] border border-[#D0E6F7] dark:bg-slate-800/90 dark:hover:bg-slate-700 dark:border-slate-700/80 dark:text-slate-400 dark:hover:text-white text-xs transition shadow-sm"
                          title="Copy email address"
                        >
                          {copiedEmail === member.id ? (
                            <i className="fa-solid fa-check text-emerald-500" />
                          ) : (
                            <i className="fa-regular fa-copy" />
                          )}
                        </button>

                        {/* LinkedIn Profile Button */}
                        <a
                          href={member.linkedin}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-white hover:bg-[#0A66C2]/10 border border-[#D0E6F7] hover:border-[#0A66C2]/50 text-slate-800 hover:text-[#0A66C2] dark:bg-slate-800/90 dark:hover:bg-[#0A66C2]/20 dark:border-slate-700/80 dark:hover:border-[#0A66C2]/60 dark:text-slate-200 dark:hover:text-white text-xs font-semibold tracking-wide transition shadow-sm group/btn"
                          title="View LinkedIn Profile"
                        >
                          <i className="fa-brands fa-linkedin-in text-[#0A66C2] text-sm" />
                          <span>LinkedIn</span>
                          <i className="fa-solid fa-arrow-up-right-from-square text-[10px] text-slate-400 ml-0.5" />
                        </a>
                      </div>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      {/* =========================================================================
          4. PROFESSIONAL HACKATHON CLOSING SECTION (Return CTAs)
          ========================================================================= */}
      <section className="py-20 bg-gradient-to-b from-[#E8F6FF] via-[#F0F8FF] to-white dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 relative overflow-hidden border-t border-[#D0E6F7] dark:border-slate-800/80 transition-colors duration-300">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#0B3D91]/10 border border-[#0B3D91]/25 text-[#0B3D91] dark:bg-cyan-500/10 dark:border-cyan-500/25 dark:text-cyan-300 text-xs font-bold mb-4 shadow-sm">
            <i className="fa-solid fa-trophy text-[11px]" />
            <span className="font-display tracking-wide uppercase">Hackathon Grand Finale Presentation</span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-white tracking-tight font-display">
            Building the Future of <br className="hidden sm:inline" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#0B3D91] via-[#3BA7F2] to-[#7FE7D6] dark:from-cyan-400 dark:via-indigo-300 dark:to-violet-400">
              Shared Physical Spaces
            </span>
          </h2>

          <p className="mt-4 text-sm sm:text-base text-slate-700 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed font-normal">
            SpaceLoop unlocks idle physical capacity across urban India through zero-hardware smart access, automated micro-leases under Section 52, and sovereign identity verification.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            {/* Primary Return to Marketplace CTA */}
            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-[#0B3D91] hover:bg-[#072C6B] dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-[#0B3D91]/25 dark:shadow-indigo-600/30 transition flex items-center justify-center gap-2"
            >
              <i className="fa-solid fa-compass" />
              <span>Explore Marketplace</span>
            </button>

            {/* Back to Home CTA */}
            <button
              type="button"
              onClick={() => navigate('/')}
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-white hover:bg-[#F0F8FF] text-slate-800 hover:text-[#0B3D91] border border-[#D0E6F7] dark:bg-slate-900 dark:hover:bg-slate-800 dark:text-slate-200 dark:border-slate-700 font-bold text-xs transition shadow-sm flex items-center justify-center gap-2"
            >
              <i className="fa-solid fa-house" />
              <span>Return to Home</span>
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default ArchitecturePage;
