import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Space, User } from '../types';
import { getSpaces } from '../services/spaces';
import CursorGrid from '../components/common/CursorGrid';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from '../i18n';
import { LandingFeaturedSpacesSkeleton } from '../components/common/Skeletons';

interface LandingPageProps {
  currentUser?: User | null;
}

export const LandingPage: React.FC<LandingPageProps> = ({ currentUser }) => {
  const navigate = useNavigate();
  const { theme } = useTheme();
  const { t, formatCurrency } = useTranslation();
  const [featuredSpaces, setFeaturedSpaces] = useState<Space[]>([]);
  const [loading, setLoading] = useState(true);

  // Parallax DOM References for 60/120fps direct transform updates
  const glow1Ref = useRef<HTMLDivElement>(null);
  const glow2Ref = useRef<HTMLDivElement>(null);
  const spatialNetworkRef = useRef<HTMLDivElement>(null);
  const orbitRef = useRef<HTMLDivElement>(null);

  // Smooth lerp parallax engine (requestAnimationFrame, zero React state re-renders)
  useEffect(() => {
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
    <div className="min-h-screen bg-background text-text-primary flex flex-col antialiased selection:bg-primary selection:text-white">
      {/* =========================================================================
          1. HERO SECTION WITH SUBTLE PARALLAX & SPATIAL TOPOLOGY NETWORK
          ========================================================================= */}
      <section className="relative overflow-hidden pt-12 pb-20 md:pt-20 md:pb-28 border-b border-border bg-gradient-to-b from-surface via-background to-background">
        
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
          className="absolute -top-40 left-1/2 -translate-x-1/2 w-[850px] h-[450px] bg-primary/10 blur-[140px] rounded-full pointer-events-none will-change-transform z-0"
        />
        <div
          ref={glow2Ref}
          className="absolute top-36 right-4 sm:right-20 w-[420px] h-[420px] bg-amber-500/10 blur-[120px] rounded-full pointer-events-none will-change-transform z-0"
        />

        {/* Layer C: Abstract Connected Spatial Topology Grid (Parallax Depth 2) */}
        <div
          ref={spatialNetworkRef}
          className="absolute inset-0 pointer-events-none overflow-hidden opacity-30 will-change-transform z-0"
        >
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="spatialGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#d97706" stopOpacity="0.5" />
                <stop offset="50%" stopColor="#f59e0b" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#fbbf24" stopOpacity="0.1" />
              </linearGradient>
              <pattern id="microDots" x="0" y="0" width="48" height="48" patternUnits="userSpaceOnUse">
                <circle cx="2" cy="2" r="1.2" fill="#d97706" fillOpacity="0.2" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#microDots)" />

            <g stroke="url(#spatialGrad)" strokeWidth="1" strokeDasharray="5,6" fill="none">
              <path d="M 120 220 L 340 180 L 520 300 L 780 210 L 960 320 L 1180 190" />
              <path d="M 280 400 L 520 300 L 720 440 L 960 320 L 1120 450" />
              <path d="M 340 180 L 460 80 L 780 210" />
            </g>

            <circle cx="340" cy="180" r="4" fill="#f59e0b" />
            <circle cx="340" cy="180" r="12" stroke="#f59e0b" strokeOpacity="0.3" strokeWidth="1.5" fill="none" />

            <circle cx="520" cy="300" r="5" fill="#d97706" />
            <circle cx="520" cy="300" r="18" stroke="#d97706" strokeOpacity="0.25" strokeWidth="1.5" fill="none" />

            <circle cx="780" cy="210" r="4" fill="#fbbf24" />
            <circle cx="780" cy="210" r="14" stroke="#fbbf24" strokeOpacity="0.3" strokeWidth="1.5" fill="none" />

            <circle cx="960" cy="320" r="5" fill="#f59e0b" />
            <circle cx="960" cy="320" r="20" stroke="#f59e0b" strokeOpacity="0.2" strokeWidth="1.5" fill="none" />
          </svg>
        </div>

        {/* Layer D: Decorative Orbit Ring (Parallax Depth 3) */}
        <div
          ref={orbitRef}
          className="absolute -top-12 -left-20 w-96 h-96 border border-primary/10 rounded-full pointer-events-none will-change-transform z-0"
        />

        {/* Main Foreground Content */}
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative z-20 text-center">
          
          {/* Eyebrow Pill */}
          <div className="flex items-center justify-center mb-6">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 border border-primary/25 text-primary text-xs font-semibold shadow-sm backdrop-blur-md">
              <span className="flex h-2 w-2 rounded-full bg-primary animate-ping" />
              <span>{t('hero.quickStats')}</span>
            </div>
          </div>

          {/* Main Headline */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-heading font-black tracking-tight text-text-primary leading-tight max-w-4xl mx-auto drop-shadow-sm">
            {t('hero.headline')} <br className="hidden sm:inline" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-amber-500 to-amber-600 dark:from-primary dark:via-amber-400 dark:to-amber-500">
              {t('hero.highlight')}
            </span>
          </h1>

          {/* Subtitle */}
          <p className="mt-6 text-base sm:text-xl text-text-secondary leading-relaxed max-w-3xl mx-auto font-normal">
            {t('hero.subtitle')}
          </p>

          {/* Dual Primary CTAs */}
          <div className="mt-9 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-primary hover:bg-primary-hover text-white font-extrabold text-base shadow-xl shadow-primary/25 flex items-center justify-center gap-3 transition transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
            >
              <i className="fa-solid fa-compass" />
              <span>{t('hero.findSpaceBtn')}</span>
              <i className="fa-solid fa-arrow-right text-xs" />
            </button>

            <button
              type="button"
              onClick={() => navigate('/host')}
              className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-surface-elevated hover:bg-surface text-text-primary hover:text-primary font-bold text-base border border-border hover:border-primary/40 shadow-sm flex items-center justify-center gap-3 transition transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
            >
              <i className="fa-solid fa-warehouse text-primary" />
              <span>{t('hero.listSpaceBtn')}</span>
            </button>
          </div>

          {/* Trust Badges Strip Directly Below CTAs */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3 sm:gap-6 text-xs text-text-secondary">
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface border border-border text-text-secondary shadow-sm">
              <i className="fa-solid fa-bolt text-primary text-xs" />
              <span>{t('hero.zeroHardwareBadge')}</span>
            </div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface border border-border text-text-secondary shadow-sm">
              <i className="fa-solid fa-shield-check text-emerald-500 text-xs" />
              <span>{t('hero.instantEscrowBadge')}</span>
            </div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface border border-border text-text-secondary shadow-sm">
              <i className="fa-solid fa-file-contract text-primary text-xs" />
              <span>{t('hero.sec52Badge')}</span>
            </div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface border border-border text-text-secondary shadow-sm">
              <i className="fa-solid fa-id-card text-sky-500 text-xs" />
              <span>{t('hero.digilockerBadge')}</span>
            </div>
          </div>

          {/* Quick Stats Metric Ribbon */}
          <div className="mt-14 pt-8 border-t border-border grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6 max-w-4xl mx-auto">
            <div className="p-4 rounded-2xl bg-surface border border-border floating-interactive text-center shadow-sm">
              <div className="text-2xl sm:text-3xl font-black text-text-primary font-heading">
                {formatCurrency(35)}<span className="text-primary text-lg">{t('common.perHour')}</span>
              </div>
              <div className="text-xs text-text-muted mt-1 font-medium">{t('hero.startingRateLabel')}</div>
            </div>
            <div className="p-4 rounded-2xl bg-surface border border-border floating-interactive text-center shadow-sm">
              <div className="text-2xl sm:text-3xl font-black text-text-primary font-heading">100%</div>
              <div className="text-xs text-text-muted mt-1 font-medium">{t('hero.discomVerifiedLabel')}</div>
            </div>
            <div className="p-4 rounded-2xl bg-surface border border-border floating-interactive text-center shadow-sm">
              <div className="text-2xl sm:text-3xl font-black text-text-primary font-heading">30s</div>
              <div className="text-xs text-text-muted mt-1 font-medium">{t('hero.instantLeaseLabel')}</div>
            </div>
            <div className="p-4 rounded-2xl bg-surface border border-border floating-interactive text-center shadow-sm">
              <div className="text-2xl sm:text-3xl font-black text-text-primary font-heading">₹100</div>
              <div className="text-xs text-text-muted mt-1 font-medium">{t('hero.escrowReleaseLabel')}</div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          2. HOW SPACELOOP WORKS (6-STEP WORKFLOW)
          ========================================================================= */}
      <section id="how-it-works" className="py-20 bg-background border-b border-border scroll-mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-xs font-extrabold uppercase tracking-wider text-primary bg-primary/10 border border-primary/20 px-3.5 py-1 rounded-full">
              {t('landing.howItWorksBadge')}
            </span>
            <h2 className="text-3xl sm:text-4xl font-heading font-black text-text-primary mt-4">{t('landing.howItWorksTitle')}</h2>
            <p className="text-text-secondary text-sm sm:text-base mt-2">
              {t('landing.howItWorksSubtitle')}
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Step 1: Discover */}
            <div className="bg-surface border border-border rounded-3xl p-6 hover:border-primary/40 hover:shadow-hover transition duration-200 relative group">
              <div className="step-number-badge w-12 h-12 rounded-2xl bg-surface-elevated text-primary border border-border flex items-center justify-center text-xl font-black mb-4 transition-all duration-200 shadow-sm group-hover:bg-primary group-hover:text-white">
                1
              </div>
              <h3 className="text-lg font-bold text-text-primary mb-2">{t('landing.step1Title')}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                {t('landing.step1Desc')}
              </p>
            </div>

            {/* Step 2: Match */}
            <div className="bg-surface border border-border rounded-3xl p-6 hover:border-primary/40 hover:shadow-hover transition duration-200 relative group">
              <div className="step-number-badge w-12 h-12 rounded-2xl bg-surface-elevated text-primary border border-border flex items-center justify-center text-xl font-black mb-4 transition-all duration-200 shadow-sm group-hover:bg-primary group-hover:text-white">
                2
              </div>
              <h3 className="text-lg font-bold text-text-primary mb-2">{t('landing.step2Title')}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                {t('landing.step2Desc')}
              </p>
            </div>

            {/* Step 3: Book */}
            <div className="bg-surface border border-border rounded-3xl p-6 hover:border-primary/40 hover:shadow-hover transition duration-200 relative group">
              <div className="step-number-badge w-12 h-12 rounded-2xl bg-surface-elevated text-primary border border-border flex items-center justify-center text-xl font-black mb-4 transition-all duration-200 shadow-sm group-hover:bg-primary group-hover:text-white">
                3
              </div>
              <h3 className="text-lg font-bold text-text-primary mb-2">{t('landing.step3Title')}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                {t('landing.step3Desc')}
              </p>
            </div>

            {/* Step 4: Sign */}
            <div className="bg-surface border border-border rounded-3xl p-6 hover:border-primary/40 hover:shadow-hover transition duration-200 relative group">
              <div className="step-number-badge w-12 h-12 rounded-2xl bg-surface-elevated text-primary border border-border flex items-center justify-center text-xl font-black mb-4 transition-all duration-200 shadow-sm group-hover:bg-primary group-hover:text-white">
                4
              </div>
              <h3 className="text-lg font-bold text-text-primary mb-2">{t('landing.step4Title')}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                {t('landing.step4Desc')}
              </p>
            </div>

            {/* Step 5: Access */}
            <div className="bg-surface border border-border rounded-3xl p-6 hover:border-primary/40 hover:shadow-hover transition duration-200 relative group">
              <div className="step-number-badge w-12 h-12 rounded-2xl bg-surface-elevated text-primary border border-border flex items-center justify-center text-xl font-black mb-4 transition-all duration-200 shadow-sm group-hover:bg-primary group-hover:text-white">
                5
              </div>
              <h3 className="text-lg font-bold text-text-primary mb-2">{t('landing.step5Title')}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                {t('landing.step5Desc')}
              </p>
            </div>

            {/* Step 6: Complete */}
            <div className="bg-surface border border-border rounded-3xl p-6 hover:border-primary/40 hover:shadow-hover transition duration-200 relative group">
              <div className="step-number-badge w-12 h-12 rounded-2xl bg-surface-elevated text-primary border border-border flex items-center justify-center text-xl font-black mb-4 transition-all duration-200 shadow-sm group-hover:bg-primary group-hover:text-white">
                6
              </div>
              <h3 className="text-lg font-bold text-text-primary mb-2">{t('landing.step6Title')}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                {t('landing.step6Desc')}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          3. DUAL AUDIENCE VALUE PROPOSITIONS (SEEKER VS HOST)
          ========================================================================= */}
      <section className="py-20 bg-surface/40 border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-heading font-black text-text-primary">{t('landing.dualAudienceTitle')}</h2>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-stretch">
            {/* For Seekers */}
            <div id="for-seekers" className="bg-surface border border-border rounded-3xl p-8 lg:p-10 shadow-sm hover:shadow-hover relative overflow-hidden flex flex-col justify-between scroll-mt-20 transition duration-200">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold mb-4">
                  <i className="fa-solid fa-briefcase" /> {t('landing.seekerBadge')}
                </div>
                <h3 className="text-2xl sm:text-3xl font-heading font-black text-text-primary mb-4">{t('landing.seekerTitle')}</h3>
                <p className="text-text-secondary text-xs sm:text-sm leading-relaxed mb-6">
                  {t('landing.seekerSubtitle')}
                </p>

                <ul className="space-y-3 text-xs text-text-secondary mb-8">
                  <li className="flex items-center gap-3">
                    <i className="fa-solid fa-circle-check text-emerald-500" />
                    <span>{t('landing.seekerBullet1')}</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <i className="fa-solid fa-circle-check text-emerald-500" />
                    <span>{t('landing.seekerBullet2')}</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <i className="fa-solid fa-circle-check text-emerald-500" />
                    <span>{t('landing.seekerBullet3')}</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <i className="fa-solid fa-circle-check text-emerald-500" />
                    <span>{t('landing.seekerBullet4')}</span>
                  </li>
                </ul>
              </div>

              <button
                type="button"
                onClick={() => navigate('/explore')}
                className="w-fit inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary hover:bg-primary-hover text-white font-bold text-xs shadow-md shadow-primary/20 transition cursor-pointer"
              >
                <span>{t('landing.seekerCta')}</span>
              </button>
            </div>

            {/* For Hosts */}
            <div id="for-hosts" className="bg-surface border border-border rounded-3xl p-8 lg:p-10 shadow-sm hover:shadow-hover relative overflow-hidden flex flex-col justify-between scroll-mt-20 transition duration-200">
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 text-amber-500 text-xs font-bold mb-4">
                  <i className="fa-solid fa-house-chimney-user" /> {t('landing.hostBadge')}
                </div>
                <h3 className="text-2xl sm:text-3xl font-heading font-black text-text-primary mb-4">{t('landing.hostTitle')}</h3>
                <p className="text-text-secondary text-xs sm:text-sm leading-relaxed mb-6">
                  {t('landing.hostSubtitle')}
                </p>

                <ul className="space-y-3 text-xs text-text-secondary mb-8">
                  <li className="flex items-center gap-3">
                    <i className="fa-solid fa-circle-check text-amber-500" />
                    <span>{t('landing.hostBullet1')}</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <i className="fa-solid fa-circle-check text-amber-500" />
                    <span>{t('landing.hostBullet2')}</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <i className="fa-solid fa-circle-check text-amber-500" />
                    <span>{t('landing.hostBullet3')}</span>
                  </li>
                  <li className="flex items-center gap-3">
                    <i className="fa-solid fa-circle-check text-amber-500" />
                    <span>{t('landing.hostBullet4')}</span>
                  </li>
                </ul>
              </div>

              <button
                type="button"
                onClick={() => navigate('/host')}
                className="w-fit inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-bold text-xs shadow-md shadow-amber-500/20 transition cursor-pointer"
              >
                <span>{t('landing.hostCta')}</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          4. TRUST & SAFETY SECTION
          ========================================================================= */}
      <section id="trust-safety" className="py-20 bg-background border-b border-border scroll-mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="text-xs font-extrabold uppercase tracking-wider text-emerald-500 bg-emerald-500/10 border border-emerald-500/20 px-3.5 py-1 rounded-full">
              {t('landing.trustBadge')}
            </span>
            <h2 className="text-3xl sm:text-4xl font-heading font-black text-text-primary mt-4">{t('landing.trustTitle')}</h2>
            <p className="text-text-secondary text-sm sm:text-base mt-2">
              {t('landing.trustSubtitle')}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-surface border border-border rounded-3xl p-6 hover:shadow-hover transition duration-200">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center text-xl mb-4">
                <i className="fa-solid fa-id-card" />
              </div>
              <h3 className="text-base font-bold text-text-primary mb-2">{t('landing.trustCard1Title')}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                {t('landing.trustCard1Desc')}
              </p>
            </div>

            <div className="bg-surface border border-border rounded-3xl p-6 hover:shadow-hover transition duration-200">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center text-xl mb-4">
                <i className="fa-solid fa-bolt" />
              </div>
              <h3 className="text-base font-bold text-text-primary mb-2">{t('landing.trustCard2Title')}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                {t('landing.trustCard2Desc')}
              </p>
            </div>

            <div className="bg-surface border border-border rounded-3xl p-6 hover:shadow-hover transition duration-200">
              <div className="w-12 h-12 rounded-2xl bg-amber-500/10 text-amber-500 flex items-center justify-center text-xl mb-4">
                <i className="fa-solid fa-scale-balanced" />
              </div>
              <h3 className="text-base font-bold text-text-primary mb-2">{t('landing.trustCard3Title')}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                {t('landing.trustCard3Desc')}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          5. FEATURED SPACES SHOWCASE
          ========================================================================= */}
      <section id="featured-spaces" className="py-20 bg-surface/40 border-b border-border scroll-mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-12 gap-4">
            <div>
              <span className="text-xs font-extrabold uppercase tracking-wider text-primary bg-primary/10 border border-primary/20 px-3.5 py-1 rounded-full">
                {t('landing.featuredBadge')}
              </span>
              <h2 className="text-3xl font-heading font-black text-text-primary mt-3">{t('landing.featuredTitle')}</h2>
              <p className="text-text-secondary text-xs sm:text-sm mt-1">
                {t('landing.featuredSubtitle')}
              </p>
            </div>
            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="text-xs font-bold text-primary hover:text-primary-hover flex items-center gap-1.5 transition cursor-pointer"
            >
              <span>{t('common.viewAll')}</span>
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
                  className="bg-surface border border-border hover:border-primary/40 rounded-3xl overflow-hidden group hover:shadow-hover flex flex-col cursor-pointer transition duration-200"
                >
                  <div className="relative aspect-[16/10] overflow-hidden bg-surface-elevated">
                    <img
                      src={
                        space.photos && space.photos.length > 0
                          ? space.photos[0]
                          : 'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80'
                      }
                      alt={space.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                    />
                    <div className="absolute top-3 left-3 bg-surface/90 backdrop-blur-md px-2.5 py-1 rounded-xl text-[11px] font-bold text-text-primary border border-border shadow-sm">
                      {space.category}
                    </div>
                    <div className="absolute top-3 right-3 bg-primary text-white backdrop-blur-md px-2.5 py-1 rounded-xl text-[11px] font-extrabold shadow-md">
                      {formatCurrency(Math.round(space.hourly_rate))}{t('common.perHour')}
                    </div>
                  </div>

                  <div className="p-5 flex flex-col flex-grow">
                    <div className="flex items-center gap-2 text-[11px] text-text-muted mb-1.5">
                      <i className="fa-solid fa-location-dot text-primary" />
                      <span>{space.neighborhood || space.city}, {space.state || 'India'}</span>
                    </div>
                    <h3 className="text-base font-bold text-text-primary group-hover:text-primary transition line-clamp-1 mb-2">
                      {space.title}
                    </h3>
                    <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed mb-4">
                      {space.description}
                    </p>

                    <div className="mt-auto pt-3 border-t border-border flex items-center justify-between text-xs">
                      <span className="text-text-muted">
                        <i className="fa-solid fa-users text-text-muted mr-1" /> {t('spaceCard.seatsCount', { count: space.max_capacity || 4 })}
                      </span>
                      <span className="text-emerald-500 font-semibold flex items-center gap-1">
                        <i className="fa-solid fa-shield-check" /> {t('common.verified')}
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
      <section className="py-20 bg-background">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="bg-surface border border-border rounded-3xl p-10 sm:p-14 shadow-xl">
            <h2 className="text-3xl sm:text-4xl font-heading font-black text-text-primary leading-tight">
              {t('landing.ctaTitle')}
            </h2>
            <p className="text-text-secondary text-sm sm:text-base mt-4 max-w-xl mx-auto leading-relaxed">
              {t('landing.ctaSubtitle')}
            </p>

            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                type="button"
                onClick={() => navigate('/explore')}
                className="w-full sm:w-auto px-8 py-4 rounded-xl bg-primary hover:bg-primary-hover text-white font-bold text-sm shadow-lg shadow-primary/25 transition cursor-pointer"
              >
                {t('landing.ctaSeekerBtn')}
              </button>
              <button
                type="button"
                onClick={() => navigate('/host')}
                className="w-full sm:w-auto px-8 py-4 rounded-xl bg-surface-elevated text-text-primary hover:text-primary font-bold text-sm border border-border hover:border-primary/40 transition cursor-pointer"
              >
                {t('landing.ctaHostBtn')}
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
