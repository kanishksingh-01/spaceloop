import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Space, User } from '../types';
import { getSpaces } from '../services/spaces';
import { useTheme } from '../context/ThemeContext';

interface LandingPageProps {
  currentUser?: User | null;
}

export const LandingPage: React.FC<LandingPageProps> = ({ currentUser }) => {
  const navigate = useNavigate();
  const { theme } = useTheme();
  const [featuredSpaces, setFeaturedSpaces] = useState<Space[]>([]);
  const [loading, setLoading] = useState(true);

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
          1. HERO SECTION (CLEAN FIGMA PRODUCT COMPOSITION)
          ========================================================================= */}
      <section className="relative overflow-hidden pt-12 pb-16 md:pt-20 md:pb-24 border-b border-slate-800/80 bg-slate-900/30">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          {/* Eyebrow */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
            <span>India’s First Hourly Micro-Space Network</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
            Turn unused physical space into{' '}
            <span className="text-indigo-400">living opportunity.</span>
          </h1>

          {/* Subtitle */}
          <p className="mt-5 text-base sm:text-lg text-slate-300 leading-relaxed max-w-2xl mx-auto">
            Discover and reserve verified desks, meeting rooms, creative studios, and study pods by the hour. Protected by digital KYC, smart QR access, and ₹100 micro-escrow.
          </p>

          {/* Primary CTAs */}
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => navigate('/explore')}
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-sm flex items-center justify-center gap-2 transition"
            >
              <i className="fa-solid fa-compass" />
              <span>Explore Spaces</span>
              <i className="fa-solid fa-arrow-right text-xs" />
            </button>

            <button
              type="button"
              onClick={() => navigate('/host')}
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 hover:text-white font-semibold text-sm border border-slate-700 transition flex items-center justify-center gap-2"
            >
              <i className="fa-solid fa-warehouse text-amber-400" />
              <span>Host Operating System</span>
            </button>
          </div>

          {/* Trust Highlights */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3 text-xs text-slate-400">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
              <i className="fa-solid fa-bolt text-indigo-400 text-xs" />
              <span>Instant QR / GPS Unlock</span>
            </div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
              <i className="fa-solid fa-shield-check text-emerald-400 text-xs" />
              <span>₹100 UPI Micro-Escrow</span>
            </div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
              <i className="fa-solid fa-id-card text-indigo-400 text-xs" />
              <span>DigiLocker KYC Verified</span>
            </div>
          </div>

          {/* Quick Metrics Ribbon */}
          <div className="mt-12 pt-8 border-t border-slate-800/80 grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 max-w-3xl mx-auto">
            <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-center">
              <div className="text-xl sm:text-2xl font-bold text-white">₹35<span className="text-indigo-400 text-sm">/hr</span></div>
              <div className="text-[11px] text-slate-400 mt-0.5">Starting Hourly Rate</div>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-center">
              <div className="text-xl sm:text-2xl font-bold text-emerald-400">100%</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Discom Verified</div>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-center">
              <div className="text-xl sm:text-2xl font-bold text-white">30s</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Instant AI Micro-Lease</div>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-center">
              <div className="text-xl sm:text-2xl font-bold text-indigo-300">₹100</div>
              <div className="text-[11px] text-slate-400 mt-0.5">UPI Escrow Release</div>
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
            <div className="py-12 flex justify-center">
              <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
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
