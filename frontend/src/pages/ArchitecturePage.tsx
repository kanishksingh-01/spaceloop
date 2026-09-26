import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * ============================================================================
 * SPACELOOP TEAM ARCHITECTURE & PROFILE CONFIGURATION
 * ----------------------------------------------------------------------------
 * Replace the four placeholder profiles below with your team's real information.
 *
 * Requirements checklist:
 * - Photograph: High-resolution portrait URL or path (e.g. '/assets/team/name.jpg').
 *   Uses 4:5 aspect ratio with object-cover and top/center positioning to prevent
 *   awkward facial cropping.
 * - Name: Full name displayed with prominent refined typography.
 * - Role: Clear, visually distinct project role label.
 * - Intro: Short professional introduction highlighting key responsibilities.
 * - Email: Direct email address with compact recognizable icon.
 * - LinkedIn: Direct profile URL with recognizable LinkedIn button.
 * ============================================================================
 */

export interface TeamMember {
  id: string;
  badgeNumber: string;
  name: string;
  role: string;
  intro: string;
  email: string;
  linkedin: string;
  photoUrl: string;
  accent: 'indigo' | 'cyan' | 'violet' | 'amber';
}

export const TEAM_MEMBERS: TeamMember[] = [
  {
    id: 'member-1',
    badgeNumber: '01',
    name: '[Team Member 1 Full Name]',
    role: '[Official Project Role / Systems Architect]',
    intro:
      '[Short professional introduction: Describe your primary engineering focus, architecture responsibilities, and key project contributions for SpaceLoop.]',
    email: 'member1@spaceloop.in',
    linkedin: 'https://www.linkedin.com/in/placeholder-member-1',
    photoUrl:
      'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=800&q=80',
    accent: 'indigo',
  },
  {
    id: 'member-2',
    badgeNumber: '02',
    name: '[Team Member 2 Full Name]',
    role: '[Official Project Role / AI & Vision Specialist]',
    intro:
      '[Short professional introduction: Describe your primary engineering focus, architecture responsibilities, and key project contributions for SpaceLoop.]',
    email: 'member2@spaceloop.in',
    linkedin: 'https://www.linkedin.com/in/placeholder-member-2',
    photoUrl:
      'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=800&q=80',
    accent: 'cyan',
  },
  {
    id: 'member-3',
    badgeNumber: '03',
    name: '[Team Member 3 Full Name]',
    role: '[Official Project Role / Trust & Security Lead]',
    intro:
      '[Short professional introduction: Describe your primary engineering focus, architecture responsibilities, and key project contributions for SpaceLoop.]',
    email: 'member3@spaceloop.in',
    linkedin: 'https://www.linkedin.com/in/placeholder-member-3',
    photoUrl:
      'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=800&q=80',
    accent: 'violet',
  },
  {
    id: 'member-4',
    badgeNumber: '04',
    name: '[Team Member 4 Full Name]',
    role: '[Official Project Role / Product Experience Engineer]',
    intro:
      '[Short professional introduction: Describe your primary engineering focus, architecture responsibilities, and key project contributions for SpaceLoop.]',
    email: 'member4@spaceloop.in',
    linkedin: 'https://www.linkedin.com/in/placeholder-member-4',
    photoUrl:
      'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=800&q=80',
    accent: 'amber',
  },
];

export const ArchitecturePage: React.FC = () => {
  const navigate = useNavigate();
  const [copiedEmail, setCopiedEmail] = useState<string | null>(null);
  const [imageErrors, setImageErrors] = useState<Record<string, boolean>>({});
  const [parallax, setParallax] = useState({ x: 0, y: 0 });

  // Lightweight, restrained parallax effect respecting reduced motion
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mediaQuery.matches) return;

    let rafId: number;
    const handleMouseMove = (e: MouseEvent) => {
      cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => {
        // Restrained subtle parallax calculation (max +/- 14px)
        const offsetX = ((e.clientX / window.innerWidth) - 0.5) * 24;
        const offsetY = ((e.clientY / window.innerHeight) - 0.5) * 24;
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
    }, 2000);
  };

  const handleImageError = (id: string) => {
    setImageErrors((prev) => ({ ...prev, [id]: true }));
  };

  const getAccentStyles = (accent: TeamMember['accent']) => {
    switch (accent) {
      case 'cyan':
        return {
          glow: 'from-cyan-500/20 via-blue-500/10 to-transparent',
          borderHover: 'group-hover:border-cyan-500/50',
          badgeBg: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30',
          dot: 'bg-cyan-400',
          iconColor: 'text-cyan-400',
        };
      case 'violet':
        return {
          glow: 'from-violet-500/20 via-purple-500/10 to-transparent',
          borderHover: 'group-hover:border-violet-500/50',
          badgeBg: 'bg-violet-500/10 text-violet-300 border-violet-500/30',
          dot: 'bg-violet-400',
          iconColor: 'text-violet-400',
        };
      case 'amber':
        return {
          glow: 'from-amber-500/20 via-orange-500/10 to-transparent',
          borderHover: 'group-hover:border-amber-500/50',
          badgeBg: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
          dot: 'bg-amber-400',
          iconColor: 'text-amber-400',
        };
      case 'indigo':
      default:
        return {
          glow: 'from-indigo-500/20 via-violet-500/10 to-transparent',
          borderHover: 'group-hover:border-indigo-500/50',
          badgeBg: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30',
          dot: 'bg-indigo-400',
          iconColor: 'text-indigo-400',
        };
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased selection:bg-indigo-500 selection:text-white">
      {/* 1. Page Return & Breadcrumb Bar */}
      <section className="border-b border-slate-800/80 bg-slate-900/70 backdrop-blur-xl sticky top-16 z-30 transition-all duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {/* Clear Way to Return to Main Application */}
            <button
              onClick={() => navigate('/')}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/90 hover:bg-slate-750 text-xs font-semibold text-slate-300 hover:text-white border border-slate-700/80 transition btn-purple-glow"
              title="Return to SpaceLoop Home"
            >
              <i className="fa-solid fa-arrow-left text-[11px]" />
              <span>Return to SpaceLoop</span>
            </button>
            <span className="text-slate-700">|</span>
            <div className="inline-flex items-center gap-2 text-xs font-bold text-white">
              <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
              <span>Architecture & Team Directory</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/explore')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600/15 hover:bg-indigo-600/25 text-indigo-300 border border-indigo-500/30 text-xs font-semibold transition btn-purple-glow"
            >
              <i className="fa-solid fa-compass text-[11px]" />
              <span className="hidden sm:inline">Explore Spaces</span>
            </button>
            <span className="text-[10px] uppercase font-extrabold tracking-wider px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              4 Core Profiles
            </span>
          </div>
        </div>
      </section>

      {/* 2. Distinctive Hero Section with Restrained Parallax */}
      <section className="relative overflow-hidden pt-16 pb-20 md:pt-24 md:pb-24 border-b border-slate-800/80 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950 animate-entrance">
        {/* Subtle Background Pattern */}
        <div
          className="absolute inset-0 pointer-events-none opacity-20"
          style={{
            backgroundImage:
              'radial-gradient(rgba(99, 102, 241, 0.3) 1px, transparent 1px)',
            backgroundSize: '36px 36px',
          }}
        />

        {/* Ambient Glowing Orbs with Restrained Parallax */}
        <div
          className="absolute -top-32 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-indigo-600/15 blur-[130px] rounded-full pointer-events-none transition-transform duration-300 ease-out will-change-transform"
          style={{
            transform: `translate3d(calc(-50% + ${parallax.x * 0.8}px), ${parallax.y * 0.8}px, 0)`,
          }}
        />
        <div
          className="absolute top-20 right-10 w-[380px] h-[380px] bg-cyan-600/10 blur-[120px] rounded-full pointer-events-none transition-transform duration-300 ease-out will-change-transform"
          style={{
            transform: `translate3d(${-parallax.x * 0.6}px, ${-parallax.y * 0.6}px, 0)`,
          }}
        />

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/25 text-indigo-300 text-xs font-bold mb-6">
            <i className="fa-solid fa-users text-[11px]" />
            <span>Core Engineering & Leadership Team</span>
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
            The multidisciplinary team designing, building, and deploying India’s premier peer-to-peer physical space marketplace.
          </p>
        </div>
      </section>

      {/* 3. Four Spacious Editorial Team Profiles (Alternating Layout & Gentle Float on Hover) */}
      <section className="py-20 lg:py-28 bg-slate-950 border-b border-slate-800/80 relative">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="space-y-20 lg:space-y-28">
            {TEAM_MEMBERS.map((member, index) => {
              const isEven = index % 2 === 0;
              const accent = getAccentStyles(member.accent);
              const hasImageFailed = imageErrors[member.id] || !member.photoUrl;

              return (
                <article
                  key={member.id}
                  className={`group relative rounded-3xl p-6 sm:p-10 lg:p-12 bg-slate-900/60 border border-slate-800/90 transition-all duration-300 ease-out hover:-translate-y-2 hover:shadow-[6px_20px_45px_-4px_rgba(0,0,0,0.65),3px_6px_18px_-2px_rgba(0,0,0,0.38),0_0_24px_rgba(99,102,241,0.2)] floating-panel ${accent.borderHover}`}
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
                    {/* Portrait Area (Large, 4:5 Proportion, Face-Safe Framing, Gentle Parallax Elevation) */}
                    <div className="w-full sm:w-[360px] lg:w-[400px] shrink-0">
                      <div className="relative aspect-[4/5] w-full rounded-2xl sm:rounded-3xl overflow-hidden bg-slate-950 border border-slate-800/90 shadow-2xl group-hover:border-slate-700 transition duration-500 group-hover:-translate-y-1.5">
                        {!hasImageFailed ? (
                          <img
                            src={member.photoUrl}
                            alt={member.name}
                            onError={() => handleImageError(member.id)}
                            className="w-full h-full object-cover object-top filter contrast-[1.03] brightness-[0.98] group-hover:scale-105 transition-transform duration-700 ease-out"
                          />
                        ) : (
                          /* High-fidelity Fallback Portrait Frame */
                          <div className="w-full h-full flex flex-col items-center justify-center p-8 bg-gradient-to-b from-slate-900 to-slate-950 text-slate-500 relative">
                            <div className="w-24 h-24 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center mb-4 text-slate-400 text-3xl">
                              <i className="fa-solid fa-user" />
                            </div>
                            <div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider text-center">
                              Photograph Slot {member.badgeNumber}
                            </div>
                            <div className="text-[11px] text-slate-500 text-center mt-1">
                              4:5 Portrait Ratio (Face-Centered)
                            </div>
                          </div>
                        )}

                        {/* Subtle Bottom Shade for Visual Depth */}
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent pointer-events-none" />

                        {/* Slot Identifier Overlay */}
                        <div className="absolute top-4 left-4">
                          <span className="px-3 py-1 rounded-full bg-slate-950/80 backdrop-blur-md border border-white/10 text-[11px] font-mono font-bold text-slate-300">
                            PROFILE // {member.badgeNumber}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Editorial Content Area */}
                    <div className="flex-1 flex flex-col justify-center text-left w-full">
                      {/* Serial Tag */}
                      <div className="flex items-center gap-3 text-xs font-mono font-bold uppercase tracking-widest text-slate-400 mb-3">
                        <span className="w-8 h-px bg-slate-700" />
                        <span className={accent.iconColor}>
                          SpaceLoop Core Team // Slot {member.badgeNumber}
                        </span>
                      </div>

                      {/* Prominent Member Name */}
                      <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white tracking-tight leading-tight group-hover:text-slate-100 transition">
                        {member.name}
                      </h2>

                      {/* Official Role Label */}
                      <div className="mt-3 mb-6">
                        <span
                          className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-mono font-bold uppercase tracking-wider border ${accent.badgeBg}`}
                        >
                          <span className={`w-2 h-2 rounded-full ${accent.dot}`} />
                          <span>{member.role}</span>
                        </span>
                      </div>

                      {/* Short Professional Introduction */}
                      <div className="relative mb-8">
                        <p className="text-base sm:text-lg text-slate-300 leading-relaxed font-normal">
                          {member.intro}
                        </p>
                      </div>

                      {/* Dedicated Email and LinkedIn Profile Buttons with Subtle Purple Glow */}
                      <div className="pt-6 border-t border-slate-800/80 flex flex-wrap items-center gap-3">
                        {/* Email Button */}
                        <a
                          href={`mailto:${member.email}`}
                          className="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-slate-800/90 hover:bg-slate-750 border border-slate-700/80 text-slate-200 hover:text-white text-xs font-semibold tracking-wide transition shadow-sm floating-container btn-purple-glow group/btn"
                          title={`Send email to ${member.email}`}
                        >
                          <i className="fa-solid fa-envelope text-indigo-400 text-sm" />
                          <span className="font-mono">{member.email}</span>
                        </a>

                        {/* Copy Email Helper */}
                        <button
                          type="button"
                          onClick={() => handleCopyEmail(member.email, member.id)}
                          className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-slate-800/90 hover:bg-slate-700 border border-slate-700/80 text-slate-400 hover:text-white text-xs transition btn-purple-glow"
                          title="Copy email address"
                        >
                          {copiedEmail === member.id ? (
                            <i className="fa-solid fa-check text-emerald-400" />
                          ) : (
                            <i className="fa-regular fa-copy" />
                          )}
                        </button>

                        {/* LinkedIn Profile Button */}
                        <a
                          href={member.linkedin}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-slate-800/90 hover:bg-[#0A66C2]/20 border border-slate-700/80 hover:border-[#0A66C2]/60 text-slate-200 hover:text-white text-xs font-semibold tracking-wide transition shadow-sm floating-container btn-purple-glow group/btn"
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

      {/* 4. Professional Hackathon Closing Section with Return CTAs */}
      <section className="py-20 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 relative overflow-hidden">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-cyan-300 text-xs font-bold mb-4">
            <i className="fa-solid fa-trophy text-[11px]" />
            <span>Hackathon Grand Finale Presentation</span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-black text-white tracking-tight">
            Building the Future of <br className="hidden sm:inline" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-indigo-300 to-violet-400">
              Shared Physical Spaces
            </span>
          </h2>

          <p className="mt-4 text-sm sm:text-base text-slate-300 max-w-2xl mx-auto leading-relaxed">
            SpaceLoop unlocks idle physical capacity across urban India through zero-hardware smart access, automated micro-leases, and sovereign identity verification.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            {/* Primary Return to Marketplace CTA with Purple Glow */}
            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition btn-glow-primary btn-purple-glow flex items-center justify-center gap-2"
            >
              <i className="fa-solid fa-compass" />
              <span>Explore Marketplace</span>
            </button>

            {/* Back to Home CTA */}
            <button
              type="button"
              onClick={() => navigate('/')}
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 font-bold text-xs border border-slate-700 transition btn-purple-glow flex items-center justify-center gap-2"
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
