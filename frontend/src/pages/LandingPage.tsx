import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Space, User } from '../types';
import { getSpaces } from '../services/spaces';
import CursorGrid from '../components/common/CursorGrid';
import { useTheme } from '../context/ThemeContext';
import { LandingFeaturedSpacesSkeleton } from '../components/common/Skeletons';

interface LandingPageProps {
  currentUser?: User | null;
}

export const LandingPage: React.FC<LandingPageProps> = ({ currentUser }) => {
  const navigate = useNavigate();
  const { theme } = useTheme();
  const [featuredSpaces, setFeaturedSpaces] = useState<Space[]>([]);
  const [loading, setLoading] = useState(true);

  // Parallax DOM References for 60/120fps direct transform updates
  const glow1Ref = useRef<HTMLDivElement>(null);
  const glow2Ref = useRef<HTMLDivElement>(null);
  const spatialNetworkRef = useRef<HTMLDivElement>(null);
  const orbitRef = useRef<HTMLDivElement>(null);

  // Smooth lerp parallax engine (requestAnimationFrame, zero React state re-renders)
  useEffect(() => {
    // Respect user's accessibility preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    let targetY = window.scrollY;
    let currentY = window.scrollY;
    let animationFrameId: number | null = null;

    const animate = () => {
      const diff = targetY - currentY;
      if (Math.abs(diff) > 0.05) {
        currentY += diff * 0.085;
        if (glow1Ref.current) {
          glow1Ref.current.style.transform = `translate3d(0, ${(currentY * 0.12).toFixed(2)}px, 0)`;
        }
        if (glow2Ref.current) {
          glow2Ref.current.style.transform = `translate3d(0, ${(-currentY * 0.08).toFixed(2)}px, 0)`;
        }
        if (spatialNetworkRef.current) {
          spatialNetworkRef.current.style.transform = `translate3d(0, ${(currentY * 0.05).toFixed(2)}px, 0)`;
        }
        if (orbitRef.current) {
          orbitRef.current.style.transform = `translate3d(0, ${(-currentY * 0.14).toFixed(2)}px, 0)`;
        }
        animationFrameId = requestAnimationFrame(animate);
      } else {
        currentY = targetY;
        animationFrameId = null;
      }
    };

    const onScroll = () => {
      targetY = window.scrollY;
      if (animationFrameId === null) {
        animationFrameId = requestAnimationFrame(animate);
      }
    };

    window.addEventListener('scroll', onScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', onScroll);
      if (animationFrameId !== null) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, []);

  useEffect(() => {
    const fetchFeatured = async () => {
      try {
        const data = await getSpaces();
        setFeaturedSpaces(data.slice(0, 6));
      } catch (err) {
        console.error('Failed to load featured spaces:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchFeatured();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased selection:bg-indigo-500 selection:text-white">
      {/* =========================================================================
          1. HERO SECTION WITH SUBTLE PARALLAX & SPATIAL TOPOLOGY NETWORK
          ========================================================================= */}
      <section className="relative overflow-hidden pt-12 pb-20 md:pt-20 md:pb-28 border-b border-slate-800/80 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950">
        
        {/* Layer A: Interactive Cursor Grid Background */}
        <div className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden z-0">
          <CursorGrid
            cellSize={70}
            color={theme === 'dark' ? '#D946EF' : '#3BA7F2'}
            radius={140}
            falloff="smooth"
            holdTime={400}
            fadeDuration={800}
            lineWidth={1.2}
            maxOpacity={1}
            fillOpacity={0}
            gridOpacity={0}
            cellRadius={0}
            clickPulse
            pulseSpeed={600}
          />
        </div>

        {/* Layer B: Parallax Glowing Background Lights (Depth 1) */}
        <div
          ref={glow1Ref}
          className="absolute -top-40 left-1/2 -translate-x-1/2 w-[850px] h-[450px] bg-indigo-600/15 blur-[140px] rounded-full pointer-events-none will-change-transform z-0"
        />
        <div
          ref={glow2Ref}
          className="absolute top-36 right-4 sm:right-20 w-[420px] h-[420px] bg-violet-600/10 blur-[120px] rounded-full pointer-events-none will-change-transform z-0"
        />

        {/* Layer C: Abstract Connected Spatial Topology Grid (Parallax Depth 2) */}
        <div
          ref={spatialNetworkRef}
          className="absolute inset-0 pointer-events-none overflow-hidden opacity-35 will-change-transform z-0"
        >
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="spatialGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#6366f1" stopOpacity="0.6" />
                <stop offset="50%" stopColor="#a855f7" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.1" />
              </linearGradient>
              <pattern id="microDots" x="0" y="0" width="48" height="48" patternUnits="userSpaceOnUse">
                <circle cx="2" cy="2" r="1.2" fill="#6366f1" fillOpacity="0.25" />
              </pattern>
            </defs>
            {/* Ambient Micro-Dot Matrix */}
            <rect width="100%" height="100%" fill="url(#microDots)" />

            {/* Connecting Vector Lines Between Spatial Hubs */}
            <g stroke="url(#spatialGrad)" strokeWidth="1" strokeDasharray="5,6" fill="none">
              <path d="M 120 220 L 340 180 L 520 300 L 780 210 L 960 320 L 1180 190" />
              <path d="M 280 400 L 520 300 L 720 440 L 960 320 L 1120 450" />
              <path d="M 340 180 L 460 80 L 780 210" />
            </g>

            {/* Pulsing Node Rings */}
            <circle cx="340" cy="180" r="4" fill="#818cf8" />
            <circle cx="340" cy="180" r="12" stroke="#818cf8" strokeOpacity="0.3" strokeWidth="1.5" fill="none" />

            <circle cx="520" cy="300" r="5" fill="#a855f7" />
            <circle cx="520" cy="300" r="18" stroke="#a855f7" strokeOpacity="0.25" strokeWidth="1.5" fill="none" />

            <circle cx="780" cy="210" r="4" fill="#38bdf8" />
            <circle cx="780" cy="210" r="14" stroke="#38bdf8" strokeOpacity="0.3" strokeWidth="1.5" fill="none" />

            <circle cx="960" cy="320" r="5" fill="#818cf8" />
            <circle cx="960" cy="320" r="20" stroke="#818cf8" strokeOpacity="0.2" strokeWidth="1.5" fill="none" />
          </svg>
        </div>

        {/* Layer D: Decorative Orbit Ring (Parallax Depth 3) */}
        <div
          ref={orbitRef}
          className="absolute -top-12 -left-20 w-96 h-96 border border-indigo-500/10 rounded-full pointer-events-none will-change-transform z-0"
        />

        {/* Main Foreground Content (Completely Stable, High Readability, No Transform) */}
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative z-20 text-center">
          
          {/* Eyebrow Pill & Purpose Track */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-2 mb-6">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/25 text-indigo-300 text-xs font-semibold shadow-sm backdrop-blur-md">
              <span className="flex h-2 w-2 rounded-full bg-indigo-400 animate-ping" />
              <span>India’s First AI-Powered Micro-Space Network</span>
            </div>
            <button
              onClick={() => navigate('/architecture')}
              className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-indigo-950/40 hover:bg-indigo-900/60 border border-indigo-500/30 hover:border-indigo-400/60 text-indigo-300 text-[11px] font-bold tracking-wide transition shadow-sm"
              title="Meet the Team & System Architecture"
            >
              <i className="fa-solid fa-cubes text-indigo-400 text-[10px]" />
              <span>Architecture & Team →</span>
            </button>
          </div>

          {/* Main Headline */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight text-white leading-tight max-w-4xl mx-auto drop-shadow-sm">
            Turn unused space into <br className="hidden sm:inline" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-violet-300 to-indigo-300">
              living opportunity.
            </span>
          </h1>

          {/* Subtitle */}
          <p className="mt-6 text-base sm:text-xl text-slate-300 leading-relaxed max-w-3xl mx-auto font-normal">
            Discover and book verified spaces for remote work, client meetings, creative studios, workshops, and study — by the hour. Powered by natural-language AI matching, instant micro-leases, and zero-hardware QR access.
          </p>

          {/* Dual Primary CTAs */}
          <div className="mt-9 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-700 hover:from-indigo-500 hover:to-violet-500 text-white font-extrabold text-base shadow-xl shadow-indigo-600/30 flex items-center justify-center gap-3 transition transform hover:-translate-y-0.5 active:translate-y-0"
            >
              <i className="fa-solid fa-compass" />
              <span>Find a Space</span>
              <i className="fa-solid fa-arrow-right text-xs" />
            </button>

            <button
              type="button"
              onClick={() => navigate('/host')}
              className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-slate-900/90 hover:bg-amber-500/10 text-amber-300 hover:text-amber-200 font-bold text-base border border-amber-500/30 hover:border-amber-400 shadow-lg flex items-center justify-center gap-3 transition transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
            >
              <i className="fa-solid fa-warehouse text-amber-400" />
              <span>Become a Host / Host OS</span>
            </button>
          </div>

          {/* Trust Badges Strip Directly Below CTAs */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3 sm:gap-6 text-xs text-slate-400">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900/70 border border-slate-800 text-slate-300">
              <i className="fa-solid fa-bolt text-indigo-400 text-xs" />
              <span>Instant QR / GPS Unlock</span>
            </div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900/70 border border-slate-800 text-slate-300">
              <i className="fa-solid fa-shield-check text-emerald-400 text-xs" />
              <span>₹100 UPI Micro-Escrow</span>
            </div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900/70 border border-slate-800 text-slate-300">
              <i className="fa-solid fa-file-contract text-violet-400 text-xs" />
              <span>Legal Indian Easements Lease</span>
            </div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900/70 border border-slate-800 text-slate-300">
              <i className="fa-solid fa-id-card text-sky-400 text-xs" />
              <span>DigiLocker KYC Verified</span>
            </div>
          </div>

          {/* Quick Stats Metric Ribbon */}
          <div className="mt-14 pt-8 border-t border-slate-800/80 grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6 max-w-4xl mx-auto">
            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 floating-interactive text-center">
              <div className="text-2xl sm:text-3xl font-black text-white">
                ₹35<span className="text-indigo-400 text-lg">/hr</span>
              </div>
              <div className="text-xs text-slate-400 mt-1 font-medium">Starting Hourly Rates</div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 floating-interactive text-center">
              <div className="text-2xl sm:text-3xl font-black text-white">100%</div>
              <div className="text-xs text-slate-400 mt-1 font-medium">Discom Meter Verified</div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 floating-interactive text-center">
              <div className="text-2xl sm:text-3xl font-black text-white">30s</div>
              <div className="text-xs text-slate-400 mt-1 font-medium">Instant AI Micro-Lease</div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 floating-interactive text-center">
              <div className="text-2xl sm:text-3xl font-black text-white">₹100</div>
              <div className="text-xs text-slate-400 mt-1 font-medium">UPI Escrow Auto-Release</div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          2. HOW SPACELOOP WORKS (6-STEP WORKFLOW)
          ========================================================================= */}
      <section id="how-it-works" className="py-20 bg-slate-950 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-xs font-extrabold uppercase tracking-wider text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-full">
              End-to-End Workflow
            </span>
            <h2 className="text-3xl sm:text-4xl font-black text-white mt-4">How SpaceLoop Works</h2>
            <p className="text-slate-300 text-sm sm:text-base mt-2">
              A seamless 6-step lifecycle engineered for friction-free urban space sharing.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Step 1 */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 hover:border-indigo-500/40 floating-interactive relative group">
              <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center text-xl font-black mb-4 group-hover:bg-indigo-600 group-hover:text-white transition">
                1
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Discover</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Search in natural English (e.g. "podcast studio for 2", "client meeting room near Indiranagar", or "quiet focus desk under ₹70/hr"). Our AI understands exact intent.
              </p>
            </div>

            {/* Step 2 */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 hover:border-indigo-500/40 floating-interactive relative group">
              <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center text-xl font-black mb-4 group-hover:bg-indigo-600 group-hover:text-white transition">
                2
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Match</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Candidate spaces are ranked based on suitability score, distance radius, amenities, and Objective Telemetry Index (OTI).
              </p>
            </div>

            {/* Step 3 */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 hover:border-indigo-500/40 floating-interactive relative group">
              <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center text-xl font-black mb-4 group-hover:bg-indigo-600 group-hover:text-white transition">
                3
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Book</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Select hourly or daily slots with instant confirmation. ₹100 UPI escrow hold secures the premise with zero paperwork.
              </p>
            </div>

            {/* Step 4 */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 hover:border-indigo-500/40 floating-interactive relative group">
              <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center text-xl font-black mb-4 group-hover:bg-indigo-600 group-hover:text-white transition">
                4
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Sign</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Instant digital micro-lease automatically compiled under the Indian Easements Act (1882) protecting both parties legally.
              </p>
            </div>

            {/* Step 5 */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 hover:border-indigo-500/40 floating-interactive relative group">
              <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center text-xl font-black mb-4 group-hover:bg-indigo-600 group-hover:text-white transition">
                5
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Access</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Zero-hardware entry via phone GPS geofence handshake (within 50m) or host door QR scan. Live in-room countdown timer.
              </p>
            </div>

            {/* Step 6 */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 hover:border-indigo-500/40 floating-interactive relative group">
              <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center text-xl font-black mb-4 group-hover:bg-indigo-600 group-hover:text-white transition">
                6
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Complete</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Snap a quick exit photo. AI checks cleanliness, lights off, and punctuality, immediately releasing the ₹100 UPI deposit.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          3. DUAL VALUE PROPOSITIONS (FOR SEEKERS VS FOR HOSTS)
          ========================================================================= */}
      <section className="py-20 bg-slate-900/40 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* For Seekers */}
            <div id="for-seekers" className="bg-slate-950/80 border border-slate-800 rounded-3xl p-8 lg:p-10 floating-container relative overflow-hidden">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-300 text-xs font-bold mb-4">
                <i className="fa-solid fa-briefcase" /> For Creators, Remote Workers & Teams
              </div>
              <h3 className="text-2xl sm:text-3xl font-black text-white mb-4">Professional Space on Demand</h3>
              <p className="text-slate-300 text-xs sm:text-sm leading-relaxed mb-6">
                Say goodbye to crowded cafes and rigid commercial leases. Book client meeting rooms, ergonomic focus desks, podcast & photo studios, workshop bays, or private study pods whenever you need them.
              </p>

              <ul className="space-y-3 text-xs text-slate-300 mb-8">
                <li className="flex items-center gap-3">
                  <i className="fa-solid fa-circle-check text-emerald-400" />
                  <span>Pay only for what you use by the hour (starting at ₹35/hr)</span>
                </li>
                <li className="flex items-center gap-3">
                  <i className="fa-solid fa-circle-check text-emerald-400" />
                  <span>Verified premises with high-speed fiber WiFi, power, and meeting amenities</span>
                </li>
                <li className="flex items-center gap-3">
                  <i className="fa-solid fa-circle-check text-emerald-400" />
                  <span>Digital micro-lease generated in seconds under Indian Easements Act</span>
                </li>
                <li className="flex items-center gap-3">
                  <i className="fa-solid fa-circle-check text-emerald-400" />
                  <span>Zero key friction: enter with device GPS handshake or QR scan</span>
                </li>
              </ul>

              <button
                type="button"
                onClick={() => navigate('/explore')}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition"
              >
                <span>Explore Verified Spaces</span>
                <i className="fa-solid fa-arrow-right text-[10px]" />
              </button>
            </div>

            {/* For Hosts */}
            <div id="for-hosts" className="bg-slate-950/80 border border-slate-800 rounded-3xl p-8 lg:p-10 floating-container relative overflow-hidden">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 text-amber-300 text-xs font-bold mb-4">
                <i className="fa-solid fa-house-chimney-user" /> For Property & Space Owners
              </div>
              <h3 className="text-2xl sm:text-3xl font-black text-white mb-4">Turn Idle Capacity into Revenue</h3>
              <p className="text-slate-300 text-xs sm:text-sm leading-relaxed mb-6">
                Have an unused meeting room, garage workshop, creative studio, off-peak cafe space, or spare room? Monetize unused square footage by the hour with zero operational friction.
              </p>

              <ul className="space-y-3 text-xs text-slate-300 mb-8">
                <li className="flex items-center gap-3">
                  <i className="fa-solid fa-circle-check text-amber-400" />
                  <span>AI Multimodal Vision Room Scanner estimates optimal hourly pricing</span>
                </li>
                <li className="flex items-center gap-3">
                  <i className="fa-solid fa-circle-check text-amber-400" />
                  <span>Strict guest identity verification via DigiLocker Aadhaar tokens</span>
                </li>
                <li className="flex items-center gap-3">
                  <i className="fa-solid fa-circle-check text-amber-400" />
                  <span>Automated ₹100 UPI escrow security deposit prevents room damage</span>
                </li>
                <li className="flex items-center gap-3">
                  <i className="fa-solid fa-circle-check text-amber-400" />
                  <span>Zero hardware required: host signs, geofencing, and smart checkouts</span>
                </li>
              </ul>

              <button
                type="button"
                onClick={() => navigate('/host/spaces/create')}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white font-bold text-xs shadow-md transition cursor-pointer"
              >
                <span>List Your Space in Host OS</span>
                <i className="fa-solid fa-arrow-right text-[10px]" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          4. TRUST & SAFETY SECTION
          ========================================================================= */}
      <section id="trust-safety" className="py-20 bg-slate-950 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-xs font-extrabold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full">
              Enterprise Security & Compliance
            </span>
            <h2 className="text-3xl sm:text-4xl font-black text-white mt-4">Trust & Safety by Design</h2>
            <p className="text-slate-300 text-sm sm:text-base mt-2">
              Engineered for national-level trust with the India Stack and verifiable telemetry.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 floating-interactive">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-xl mb-4">
                <i className="fa-solid fa-id-card" />
              </div>
              <h3 className="text-base font-bold text-white mb-2">DigiLocker Dual KYC</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Seekers verify via OTP-backed DigiLocker Aadhaar tokens and institutional (.ac.in) domains. DPDP Act 2023 compliant: zero plaintext Aadhaar stored.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 floating-interactive">
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center text-xl mb-4">
                <i className="fa-solid fa-bolt" />
              </div>
              <h3 className="text-base font-bold text-white mb-2">Discom Premise Proof</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Hosts confirm physical legal possession by matching electricity utility bills (BESCOM, TPDDL) and instant UPI Penny Drop bank account verification.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 floating-interactive">
              <div className="w-12 h-12 rounded-2xl bg-violet-500/10 text-violet-400 flex items-center justify-center text-xl mb-4">
                <i className="fa-solid fa-scale-balanced" />
              </div>
              <h3 className="text-base font-bold text-white mb-2">Legal Micro-Lease</h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Every booking compiles a digital license agreement under the Indian Easements Act (1882), establishing licensee status with zero tenancy risk.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          5. FEATURED SPACES SHOWCASE
          ========================================================================= */}
      <section id="featured-spaces" className="py-20 bg-slate-900/40 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-12 gap-4">
            <div>
              <span className="text-xs font-extrabold uppercase tracking-wider text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-full">
                Live Marketplace
              </span>
              <h2 className="text-3xl font-black text-white mt-3">Featured Micro-Spaces</h2>
              <p className="text-slate-300 text-xs sm:text-sm mt-1">
                Explore top-rated verified spaces across Delhi, Bengaluru, Pune, and Mumbai.
              </p>
            </div>
            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="text-xs font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1.5 transition"
            >
              <span>View all spaces</span>
              <i className="fa-solid fa-arrow-right text-[10px]" />
            </button>
          </div>

          {loading ? (
            <LandingFeaturedSpacesSkeleton count={3} />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {featuredSpaces.map((space) => (
                <div
                  key={space.id}
                  onClick={() => navigate(`/space/${space.id}`)}
                  className="bg-slate-950/90 border border-slate-800/80 hover:border-indigo-500/50 rounded-3xl overflow-hidden group floating-interactive flex flex-col cursor-pointer"
                >
                  <div className="relative aspect-[16/10] overflow-hidden bg-slate-900">
                    <img
                      src={
                        space.photos && space.photos.length > 0
                          ? space.photos[0]
                          : 'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80'
                      }
                      alt={space.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                    />
                    <div className="absolute top-3 left-3 bg-slate-950/80 backdrop-blur-md px-2.5 py-1 rounded-xl text-[11px] font-bold text-white border border-slate-700/60">
                      {space.category}
                    </div>
                    <div className="absolute top-3 right-3 bg-indigo-600/90 backdrop-blur-md px-2.5 py-1 rounded-xl text-[11px] font-extrabold text-white shadow-md">
                      ₹{Math.round(space.hourly_rate)}/hr
                    </div>
                  </div>

                  <div className="p-5 flex flex-col flex-grow">
                    <div className="flex items-center gap-2 text-[11px] text-slate-400 mb-1.5">
                      <i className="fa-solid fa-location-dot text-indigo-400" />
                      <span>{space.neighborhood || space.city}, {space.state || 'India'}</span>
                    </div>
                    <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition line-clamp-1 mb-2">
                      {space.title}
                    </h3>
                    <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed mb-4">
                      {space.description}
                    </p>

                    <div className="mt-auto pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                      <span className="text-slate-400">
                        <i className="fa-solid fa-users text-slate-500 mr-1" /> Up to {space.max_capacity || 4}
                      </span>
                      <span className="text-emerald-400 font-semibold flex items-center gap-1">
                        <i className="fa-solid fa-shield-check" /> Verified
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* =========================================================================
          6. FINAL CTA BANNER
          ========================================================================= */}
      <section className="py-20 bg-gradient-to-b from-slate-950 to-slate-900">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="bg-gradient-to-tr from-indigo-950/80 via-slate-900/90 to-violet-950/80 border border-indigo-500/30 rounded-3xl p-10 sm:p-14 floating-container">
            <h2 className="text-3xl sm:text-4xl font-black text-white leading-tight">
              Ready to optimize urban space?
            </h2>
            <p className="text-slate-300 text-sm sm:text-base mt-4 max-w-xl mx-auto leading-relaxed">
              Whether you are a creator recording a podcast, a consultant meeting clients, a founder running a team sprint, or a host with space to spare — SpaceLoop connects you securely.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                type="button"
                onClick={() => navigate('/explore')}
                className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-bold text-sm shadow-lg shadow-indigo-600/30 hover:opacity-90 transition"
              >
                Find a Space
              </button>
              <button
                type="button"
                onClick={() => navigate('/host')}
                className="w-full sm:w-auto px-8 py-4 rounded-xl bg-slate-950 text-amber-300 font-bold text-sm border border-amber-500/40 hover:bg-slate-800 transition cursor-pointer"
              >
                Launch Host Portal
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
