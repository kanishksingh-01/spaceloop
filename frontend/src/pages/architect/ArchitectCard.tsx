import React, { useRef, useState, useCallback, useEffect } from 'react';
import {
  Mail,
  Linkedin,
  Copy,
  Check,
  ExternalLink,
  Maximize2,
} from 'lucide-react';
import { TeamMember, AccentThemeToken } from './types';

interface ArchitectCardProps {
  member: TeamMember;
  accent: AccentThemeToken;
  isLight: boolean;
  onInspect: () => void;
  onCopyEmail: (email: string, id: string) => void;
  isCopied: boolean;
  prefersReducedMotion?: boolean;
  isTouchDevice?: boolean;
}

export const ArchitectCard: React.FC<ArchitectCardProps> = ({
  member,
  accent,
  isLight,
  onInspect,
  onCopyEmail,
  isCopied,
  prefersReducedMotion = false,
  isTouchDevice = false,
}) => {
  const cardRef = useRef<HTMLElement>(null);
  const [hasImageFailed, setHasImageFailed] = useState(false);
  const rafRef = useRef<number | null>(null);

  const AccentIcon = accent.icon;

  // Performant Pointer Tracking using direct CSS variables & requestAnimationFrame (Section 4 & 15)
  const handlePointerMove = useCallback(
    (e: React.PointerEvent<HTMLElement>) => {
      if (prefersReducedMotion || isTouchDevice || !cardRef.current) return;

      const rect = cardRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      if (rafRef.current) cancelAnimationFrame(rafRef.current);

      rafRef.current = requestAnimationFrame(() => {
        if (!cardRef.current) return;

        // Set CSS variables directly on element to bypass React re-renders
        cardRef.current.style.setProperty('--mouse-x', `${x}px`);
        cardRef.current.style.setProperty('--mouse-y', `${y}px`);

        // Calculate subtle 3D tilt (max ±2.2 degrees)
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const tiltX = ((x - centerX) / centerX) * 2.2;
        const tiltY = ((centerY - y) / centerY) * 2.2;

        cardRef.current.style.transform = `perspective(1000px) rotateX(${tiltY}deg) rotateY(${tiltX}deg) translateY(-5px)`;
      });
    },
    [prefersReducedMotion, isTouchDevice]
  );

  const handlePointerLeave = useCallback(() => {
    if (prefersReducedMotion || isTouchDevice || !cardRef.current) return;

    if (rafRef.current) cancelAnimationFrame(rafRef.current);

    cardRef.current.style.removeProperty('--mouse-x');
    cardRef.current.style.removeProperty('--mouse-y');
    cardRef.current.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)';
  }, [prefersReducedMotion, isTouchDevice]);

  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return (
    <article
      ref={cardRef}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      className={`ag-glass-card group p-6 sm:p-8 flex flex-col justify-between overflow-hidden relative border ${
        isLight ? accent.borderLight : accent.borderDark
      }`}
      style={{
        // Define localized spotlight glow token
        ['--card-spotlight-color' as string]: `rgba(${accent.rgb}, ${isLight ? 0.16 : 0.25})`,
      }}
    >
      {/* Precision Corner Crosshairs (+) (Section 11) */}
      <div className="ag-crosshair top-3 left-3 text-slate-400 dark:text-slate-500" />
      <div className="ag-crosshair top-3 right-3 text-slate-400 dark:text-slate-500" />
      <div className="ag-crosshair bottom-3 left-3 text-slate-400 dark:text-slate-500" />
      <div className="ag-crosshair bottom-3 right-3 text-slate-400 dark:text-slate-500" />

      {/* Cursor-Reactive Specular Spotlight Layer (Section 4) */}
      {!prefersReducedMotion && !isTouchDevice && (
        <div className="ag-card-spotlight" aria-hidden="true" />
      )}

      {/* Top Telemetry & Status Bar */}
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
          className="inline-flex items-center gap-1.5 text-[11px] font-mono font-bold text-slate-600 hover:text-[#0B3D91] dark:text-slate-400 dark:hover:text-cyan-300 transition focus-visible:ring-2 focus-visible:ring-[#0B3D91] focus-visible:outline-hidden rounded-md px-1.5 py-0.5"
          title={`Inspect ${member.name}'s architecture specifications`}
          aria-label={`Inspect ${member.name}'s architecture specifications`}
        >
          <Maximize2 className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Inspect Specs</span>
        </button>
      </div>

      {/* Profile Overview Row */}
      <div className="relative z-10 flex flex-col sm:flex-row items-center sm:items-start gap-6 mb-6">
        {/* Face-Safe 4:5 Portrait Frame with Shimmer & Lighting Shift (Section 8) */}
        <div className="w-32 sm:w-36 shrink-0 aspect-[4/5] ag-portrait-frame bg-slate-100 dark:bg-slate-900 border border-[#D0E6F7] dark:border-white/10 shadow-md">
          {!hasImageFailed ? (
            <>
              <img
                src={member.photoUrl}
                alt={member.name}
                onError={() => setHasImageFailed(true)}
                className="w-full h-full object-cover object-top filter contrast-[1.02]"
              />
              <div className="ag-portrait-shimmer" />
            </>
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
          {/* Role Pill */}
          <div
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono font-bold uppercase border mb-2 shadow-2xs"
            style={{
              backgroundColor: `rgba(${accent.rgb}, 0.1)`,
              borderColor: `rgba(${accent.rgb}, 0.3)`,
              color: accent.color,
            }}
          >
            <AccentIcon className="w-3 h-3" />
            <span>{member.role}</span>
          </div>

          {/* Member Name */}
          <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-snug font-display">
            {member.name}
          </h3>

          {/* Domain Focus */}
          <div className="text-xs font-mono font-medium text-slate-500 dark:text-slate-400 mt-1 mb-3">
            Domain: <span className="text-slate-700 dark:text-slate-300 font-semibold">{member.domain}</span>
          </div>

          {/* Bio Introduction */}
          <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-normal">
            {member.intro}
          </p>
        </div>
      </div>

      {/* Technical Subsystem Console Box */}
      <div className="relative z-10 p-4 rounded-2xl bg-[#F0F8FF]/80 dark:bg-slate-950/50 border border-[#D0E6F7] dark:border-white/[0.08] mb-6 ag-subsystem-box">
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
            {member.subsystem.metric.label}:{' '}
            <span className="font-extrabold" style={{ color: accent.color }}>
              {member.subsystem.metric.value}
            </span>
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

      {/* Interactive Contact Actions: LinkedIn & Email (Section 9) */}
      <div className="relative z-10 pt-4 border-t border-[#D0E6F7] dark:border-white/[0.08] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {/* Email Mailto Link */}
          <a
            href={`mailto:${member.email}`}
            className="ag-contact-btn bg-white hover:bg-[#F0F8FF] text-slate-800 hover:text-[#0B3D91] border border-[#D0E6F7] hover:border-[#3BA7F2] dark:bg-slate-800/90 dark:hover:bg-slate-750 dark:border-white/10 dark:text-slate-200 dark:hover:text-white shadow-2xs focus-visible:ring-2 focus-visible:ring-[#0B3D91]"
            title={`Send email to ${member.email}`}
            aria-label={`Send direct email to ${member.name} at ${member.email}`}
          >
            <Mail className="w-3.5 h-3.5 text-[#0B3D91] dark:text-cyan-400" />
            <span className="font-mono text-[11px]">{member.email}</span>
          </a>

          {/* Copy Email Helper */}
          <button
            type="button"
            onClick={() => onCopyEmail(member.email, member.id)}
            className="ag-contact-btn w-8 h-8 p-0 bg-white hover:bg-[#F0F8FF] text-slate-500 hover:text-[#0B3D91] border border-[#D0E6F7] dark:bg-slate-800/90 dark:hover:bg-slate-700 dark:border-white/10 dark:text-slate-400 dark:hover:text-white shadow-2xs focus-visible:ring-2 focus-visible:ring-[#0B3D91]"
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

        {/* Real LinkedIn Profile Link (target="_blank" rel="noopener noreferrer") */}
        <a
          href={member.linkedin}
          target="_blank"
          rel="noopener noreferrer"
          className="ag-contact-btn bg-white hover:bg-[#0A66C2]/10 border border-[#D0E6F7] hover:border-[#0A66C2]/50 text-slate-800 hover:text-[#0A66C2] dark:bg-slate-800/90 dark:hover:bg-[#0A66C2]/20 dark:border-white/10 dark:hover:border-[#0A66C2]/60 dark:text-slate-200 dark:hover:text-white shadow-2xs focus-visible:ring-2 focus-visible:ring-[#0B3D91]"
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

export default ArchitectCard;
