import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Compass,
  Sparkles,
  Activity,
  X,
  Check,
  Mail,
  Linkedin,
  ExternalLink,
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { ThemeToggle } from '../components/common/ThemeToggle';
import { TEAM_MEMBERS, ACCENT_TOKENS } from './architect/teamData';
import { TeamMember } from './architect/types';
import { ArchitectLoader } from './architect/ArchitectLoader';
import { RevealHeading } from './architect/RevealHeading';
import { ArchitectCard } from './architect/ArchitectCard';
import './ArchitecturePage.css';

/**
 * ============================================================================
 * SPACELOOP ARCHITECT PAGE — ANTIGRAVITY-INSPIRED PRODUCTION EXPERIENCE
 * ----------------------------------------------------------------------------
 * 1. Page Entry + Entrance Loader (plays fresh on every browser refresh F5/Ctrl+R)
 * 2. SpaceLoop Wordmark with branded light sweep dissolving into Hero
 * 3. Letter-by-Letter Progressive Heading Reveal (word-preserving wrapping)
 * 4. Dual-layer Colourful Reveal Scanner Bar synchronized with typography
 * 5. Performant Pointer Tracking (CSS custom properties & requestAnimationFrame)
 * 6. Multi-tiered Subtle Scroll & Mouse Parallax with coordinate marks
 * 7. 4 Real Architect Profiles with working LinkedIn & Email mailto links
 * 8. Interactive Glassmorphic Profile Surfaces with dampened 3D tilt
 * 9. Deep-Dive Full Subsystem Architecture Inspection Glass Modal
 * 10. Dual-Theme Support: Ocean Breeze (#0B3D91, #3BA7F2) & Midnight Neon (#020617)
 * ============================================================================
 */

export const ArchitecturePage: React.FC = () => {
  const navigate = useNavigate();
  const { theme } = useTheme();
  const isLight = theme === 'light';

  // State Management
  // Loader plays every time page is refreshed (F5/Ctrl+R). Zero localStorage/session suppression.
  const [loaderComplete, setLoaderComplete] = useState<boolean>(false);
  const [copiedEmail, setCopiedEmail] = useState<string | null>(null);
  const [activeModalMember, setActiveModalMember] = useState<TeamMember | null>(null);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const [isTouchDevice, setIsTouchDevice] = useState(false);
  const [parallaxOffset, setParallaxOffset] = useState({ x: 0, y: 0, scrollY: 0 });

  // Motion preference and hardware touch detection
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

  // Subtle Smooth Mouse & Scroll Parallax (Section 5)
  useEffect(() => {
    if (prefersReducedMotion || isTouchDevice) return;

    let rafId: number;
    const handleMouseMove = (e: MouseEvent) => {
      cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        const x = ((e.clientX / window.innerWidth) - 0.5) * 14;
        const y = ((e.clientY / window.innerHeight) - 0.5) * 14;
        setParallaxOffset((prev) => ({ ...prev, x, y }));
      });
    };

    const handleScroll = () => {
      cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        setParallaxOffset((prev) => ({ ...prev, scrollY: window.scrollY * 0.08 }));
      });
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('scroll', handleScroll);
    };
  }, [prefersReducedMotion, isTouchDevice]);

  // Modal dismissal via ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && activeModalMember) {
        setActiveModalMember(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeModalMember]);

  // Body scroll locking when modal is open
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

  const handleLoaderFinish = useCallback(() => {
    setLoaderComplete(true);
  }, []);

  const handleCopyEmail = useCallback((email: string, id: string) => {
    navigator.clipboard.writeText(email);
    setCopiedEmail(id);
    setTimeout(() => {
      setCopiedEmail(null);
    }, 2200);
  }, []);

  return (
    <div className="min-h-screen ag-blueprint-grid bg-[#E8F6FF] dark:bg-[#020617] text-slate-800 dark:text-slate-100 flex flex-col antialiased selection:bg-[#0B3D91] selection:text-white dark:selection:bg-indigo-500 font-sans transition-colors duration-300 relative">
      {/* =========================================================================
          1. CINEMATIC SPACELOOP WORDMARK LOADER (Triggers on refresh, no suppression)
          ========================================================================= */}
      {!loaderComplete && (
        <ArchitectLoader
          onComplete={handleLoaderFinish}
          prefersReducedMotion={prefersReducedMotion}
        />
      )}

      {/* =========================================================================
          2. NAVIGATION & ARCHITECTURAL DIRECTORY HUD
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
          3. ANTIGRAVITY HERO WITH LETTER-BY-LETTER REVEAL (Section 2, 3, 5, 10, 11)
          ========================================================================= */}
      <section className="relative overflow-hidden pt-16 pb-20 md:pt-24 md:pb-28 border-b border-[#D0E6F7] dark:border-white/[0.08] bg-gradient-to-b from-[#E8F6FF] via-[#F0F8FF]/80 to-white dark:from-[#020617] dark:via-[#0B132B]/50 dark:to-[#020617] transition-colors duration-300">
        {/* Layered Architectural Ambient Lighting & Parallax Mesh */}
        <div
          className="absolute -top-32 left-1/2 -translate-x-1/2 w-[720px] h-[360px] bg-[#3BA7F2]/25 dark:bg-indigo-600/20 blur-[130px] rounded-full pointer-events-none transition-transform duration-300 ease-out will-change-transform ag-ambient-float-1"
          style={{
            transform: prefersReducedMotion
              ? 'translate3d(-50%, 0, 0)'
              : `translate3d(calc(-50% + ${parallaxOffset.x * 0.9}px), ${parallaxOffset.y * 0.9 - parallaxOffset.scrollY}px, 0)`,
          }}
        />
        <div
          className="absolute top-20 right-10 w-[420px] h-[420px] bg-[#7FE7D6]/30 dark:bg-cyan-600/15 blur-[130px] rounded-full pointer-events-none transition-transform duration-300 ease-out will-change-transform ag-ambient-float-2"
          style={{
            transform: prefersReducedMotion
              ? 'translate3d(0, 0, 0)'
              : `translate3d(${-parallaxOffset.x * 0.7}px, ${-parallaxOffset.y * 0.7 - parallaxOffset.scrollY * 0.5}px, 0)`,
          }}
        />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="flex flex-col items-center text-center max-w-4xl mx-auto">
            {/* Technical Subtitle Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/80 dark:bg-slate-900/80 border border-[#D0E6F7] dark:border-white/10 text-[#0B3D91] dark:text-cyan-300 text-xs font-mono font-bold mb-6 shadow-2xs backdrop-blur-md">
              <Sparkles className="w-3.5 h-3.5 text-[#3BA7F2] dark:text-cyan-400" />
              <span className="tracking-widest uppercase">SPACE-TECH ARCHITECTURE // VOL. 2026</span>
            </div>

            {/* Letter-by-Letter Hero Heading with Colourful Dual-Layer Reveal Scanner Bar */}
            <div className="mb-4">
              <RevealHeading
                text="Meet the Architects Behind SpaceLoop"
                as="h1"
                className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.1] font-display"
                delay={loaderComplete ? 50 : 1900}
                duration={900}
                gradientFromIndex={20} // Starts gradient at "Behind SpaceLoop"
                gradientClassName="text-transparent bg-clip-text bg-gradient-to-r from-[#0B3D91] via-[#1E40AF] to-[#3BA7F2] dark:from-cyan-400 dark:via-indigo-300 dark:to-violet-400"
                prefersReducedMotion={prefersReducedMotion}
              />
            </div>

            {/* Supporting Content */}
            <p className="mt-4 text-lg sm:text-2xl text-slate-800 dark:text-slate-100 font-display italic font-semibold tracking-tight max-w-3xl leading-relaxed">
              “Four minds. One mission. Making every suitable space work smarter.”
            </p>

            <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed font-normal">
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
          4. ARCHITECT PROFILES SECTION (Section 6, 7, 8, 9, 10, 11)
          ========================================================================= */}
      <main className="py-16 sm:py-24 relative z-10 flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Section Header with Reusable RevealHeading (Section 10 & 16) */}
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-12 sm:mb-16">
            <div>
              <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-widest text-[#0B3D91] dark:text-cyan-400 mb-2">
                <Activity className="w-3.5 h-3.5" />
                <span>CORE LEADERSHIP DIRECTORY // 4 PROFILES</span>
              </div>
              <RevealHeading
                text="Core System Architects"
                as="h2"
                className="text-2xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight font-display"
                triggerOnScroll={true}
                duration={750}
                gradientFromIndex={12}
                prefersReducedMotion={prefersReducedMotion}
              />
            </div>
            <p className="text-xs font-mono text-slate-500 dark:text-slate-400 max-w-sm">
              Hover cards for localized spotlight & 3D tilt. Click <span className="text-[#0B3D91] dark:text-cyan-300 font-bold">Inspect Specs</span> for deep-dive architecture specs.
            </p>
          </div>

          {/* Exactly 4 Team Member Profiles Rendered via Reusable ArchitectCard (Section 6 & 16) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 sm:gap-10">
            {TEAM_MEMBERS.map((member) => (
              <ArchitectCard
                key={member.id}
                member={member}
                accent={ACCENT_TOKENS[member.accent]}
                isLight={isLight}
                onInspect={() => setActiveModalMember(member)}
                onCopyEmail={handleCopyEmail}
                isCopied={copiedEmail === member.id}
                prefersReducedMotion={prefersReducedMotion}
                isTouchDevice={isTouchDevice}
              />
            ))}
          </div>
        </div>
      </main>

      {/* =========================================================================
          5. EXPANDABLE GLASS MODAL FOR ARCHITECTURE SPEC (Section 7)
          ========================================================================= */}
      {activeModalMember && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby={`modal-title-${activeModalMember.id}`}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto bg-slate-950/70 backdrop-blur-xl"
          onClick={() => setActiveModalMember(null)}
        >
          <div
            className="relative w-full max-w-3xl rounded-3xl bg-white/95 dark:bg-[#0F172A]/95 border border-[#D0E6F7] dark:border-white/10 shadow-2xl p-6 sm:p-10 my-8 backdrop-blur-2xl transition-all duration-300"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Corner Crosshairs */}
            <div className="ag-crosshair top-3 left-3 text-[#0B3D91] dark:text-cyan-400" />
            <div className="ag-crosshair top-3 right-3 text-[#0B3D91] dark:text-cyan-400" />
            <div className="ag-crosshair bottom-3 left-3 text-[#0B3D91] dark:text-cyan-400" />
            <div className="ag-crosshair bottom-3 right-3 text-[#0B3D91] dark:text-cyan-400" />

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
            <div className="p-5 sm:p-6 rounded-2xl bg-[#F0F8FF] dark:bg-slate-950/60 border border-[#D0E6F7] dark:border-white/10 mb-8 ag-subsystem-box">
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

            {/* Direct Contact Actions */}
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
          6. CLOSING HACKATHON FINALE & RETURN NAVIGATION
          ========================================================================= */}
      <footer className="py-16 bg-gradient-to-b from-[#E8F6FF] via-[#F0F8FF] to-white dark:from-[#020617] dark:via-[#0F172A] dark:to-[#020617] border-t border-[#D0E6F7] dark:border-white/[0.08] relative transition-colors duration-300">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#0B3D91]/10 border border-[#0B3D91]/25 text-[#0B3D91] dark:bg-cyan-500/10 dark:border-cyan-500/25 dark:text-cyan-300 text-xs font-mono font-bold mb-4 shadow-2xs">
            <Activity className="w-3.5 h-3.5" />
            <span className="uppercase tracking-wider">HACKATHON GRAND FINALE // PRODUCTION READY</span>
          </div>

          <div className="mb-2">
            <RevealHeading
              text="Building the Future of Shared Physical Spaces"
              as="h2"
              className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight font-display"
              triggerOnScroll={true}
              duration={800}
              gradientFromIndex={24}
              gradientClassName="text-transparent bg-clip-text bg-gradient-to-r from-[#0B3D91] via-[#1E40AF] to-[#3BA7F2] dark:from-cyan-400 dark:via-indigo-300 dark:to-violet-400"
              prefersReducedMotion={prefersReducedMotion}
            />
          </div>

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

export default ArchitecturePage;
