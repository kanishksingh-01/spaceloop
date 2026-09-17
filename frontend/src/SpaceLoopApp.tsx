import React, { useState } from 'react';

// --- TYPES ---
interface SpaceListing {
  id: string;
  title: string;
  location: string;
  category: string;
  mood: 'sunny' | 'intimate' | 'industrial' | 'greenery';
  pricePerHour: number;
  rating: number;
  reviewsCount: number;
  imageUrl: string;
  aspectRatio: string;
  hostName: string;
  hostAvatar: string;
  tags: string[];
}

// --- PURE INLINE SVGS ---
const InfinityIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M12 12c-2-2.67-4-4-6.5-4a4.5 4.5 0 1 0 0 9c2.5 0 4.5-1.33 6.5-4Zm0 0c2 2.67 4 4 6.5 4a4.5 4.5 0 1 0 0-9c-2.5 0-4.5 1.33-6.5 4Z" />
  </svg>
);

const SearchIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="11" cy="11" r="8" />
    <path d="m21 21-4.35-4.35" />
  </svg>
);

const SparklesIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3z" />
  </svg>
);

const SunIcon: React.FC<{ className?: string }> = ({ className = 'w-3.5 h-3.5' }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
  </svg>
);

const CoffeeIcon: React.FC<{ className?: string }> = ({ className = 'w-3.5 h-3.5' }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M10 2v2M14 2v2M6 2v2M18 9h1a3 3 0 0 1 3 3 3 3 0 0 1-3 3h-1M4 9h14v8a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4V9z" />
  </svg>
);

const BuildingIcon: React.FC<{ className?: string }> = ({ className = 'w-3.5 h-3.5' }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="4" y="2" width="16" height="20" rx="2" />
    <path d="M9 22v-4h6v4M8 6h.01M16 6h.01M8 10h.01M16 10h.01M8 14h.01M16 14h.01" />
  </svg>
);

const TreesIcon: React.FC<{ className?: string }> = ({ className = 'w-3.5 h-3.5' }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M10 10v.2A3 3 0 0 1 8.9 16v0H5v0h0a3 3 0 0 1-1-5.8V10a3 3 0 0 1 6 0Z" />
    <path d="M7 16v6M17 14v8M21 14a3 3 0 0 0-3-3h-.1a3 3 0 0 0-5.8 0H12a3 3 0 0 0-3 3v0h12Z" />
  </svg>
);

const CheckIcon: React.FC<{ className?: string }> = ({ className = 'w-3 h-3' }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
  </svg>
);

const ArrowUpRightIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M7 17 17 7M7 7h10v10" />
  </svg>
);

const SlidersIcon: React.FC<{ className?: string }> = ({ className = 'w-3.5 h-3.5' }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <line x1="4" x2="4" y1="21" y2="14" />
    <line x1="4" x2="4" y1="10" y2="3" />
    <line x1="12" x2="12" y1="21" y2="12" />
    <line x1="12" x2="12" y1="8" y2="3" />
    <line x1="20" x2="20" y1="21" y2="16" />
    <line x1="20" x2="20" y1="12" y2="3" />
    <line x1="1" x2="7" y1="14" y2="14" />
    <line x1="9" x2="15" y1="8" y2="8" />
    <line x1="17" x2="23" y1="16" y2="16" />
  </svg>
);

// --- LISTINGS DATA ---
const LISTINGS_DATA: SpaceListing[] = [
  {
    id: '1',
    title: 'North Campus Quiet Study Pod',
    location: 'Hauz Khas, Delhi',
    category: 'Study Pod',
    mood: 'sunny',
    pricePerHour: 60,
    rating: 4.95,
    reviewsCount: 32,
    imageUrl: 'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=800&q=80',
    aspectRatio: 'aspect-[4/5]',
    hostName: 'Sunita K.',
    hostAvatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80',
    tags: ['Fiber 300 Mbps', 'DigiLocker Verified', 'Ergonomic Desk'],
  },
  {
    id: '2',
    title: 'Acoustic Podcast & Vocal Den',
    location: 'Indiranagar, Bangalore',
    category: 'Acoustic Suite',
    mood: 'intimate',
    pricePerHour: 350,
    rating: 4.98,
    reviewsCount: 47,
    imageUrl: 'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=800&q=80',
    aspectRatio: 'aspect-[3/4]',
    hostName: 'Aarav P.',
    hostAvatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=120&q=80',
    tags: ['Rode PodMic', 'Soundproofed', '₹100 UPI Escrow'],
  },
  {
    id: '3',
    title: 'Koramangala 4th Block Student Den',
    location: 'Koramangala, Bangalore',
    category: 'Co-work Den',
    mood: 'sunny',
    pricePerHour: 80,
    rating: 4.88,
    reviewsCount: 56,
    imageUrl: 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80',
    aspectRatio: 'aspect-[4/3]',
    hostName: 'Rohan M.',
    hostAvatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=120&q=80',
    tags: ['High-speed Fiber', 'Power Backup', 'Coffee on Tap'],
  },
  {
    id: '4',
    title: 'Quiet Study Pod & Hackathon Suite',
    location: 'Wagholi, Pune',
    category: 'Project Lab',
    mood: 'industrial',
    pricePerHour: 50,
    rating: 4.91,
    reviewsCount: 29,
    imageUrl: 'https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=800&q=80',
    aspectRatio: 'aspect-[4/5]',
    hostName: 'Vikram N.',
    hostAvatar: 'https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?auto=format&fit=crop&w=120&q=80',
    tags: ['Near JSPM Wagholi', '300 Mbps', 'Whiteboard'],
  },
  {
    id: '5',
    title: 'Sun-Drenched Garden Courtyard',
    location: 'Koregaon Park, Pune',
    category: 'Garden Loft',
    mood: 'greenery',
    pricePerHour: 420,
    rating: 4.99,
    reviewsCount: 64,
    imageUrl: 'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&w=800&q=80',
    aspectRatio: 'aspect-[3/4]',
    hostName: 'Ananya D.',
    hostAvatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=120&q=80',
    tags: ['Plant Nursery', 'Natural Lighting', 'Tea House'],
  },
  {
    id: '6',
    title: 'The Minimalist Industrial Loft',
    location: 'Whitefield, Bangalore',
    category: 'Maker Studio',
    mood: 'industrial',
    pricePerHour: 280,
    rating: 4.89,
    reviewsCount: 18,
    imageUrl: 'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80',
    aspectRatio: 'aspect-[4/3]',
    hostName: 'Priya S.',
    hostAvatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=120&q=80',
    tags: ['Soldering Station', '3D Printer', 'High Ceilings'],
  },
];

export default function SpaceLoopApp() {
  const [selectedMood, setSelectedMood] = useState<string>('all');
  const [query, setQuery] = useState<string>('');

  const filteredListings = LISTINGS_DATA.filter((listing) => {
    const matchesMood = selectedMood === 'all' || listing.mood === selectedMood;
    const matchesQuery =
      listing.title.toLowerCase().includes(query.toLowerCase()) ||
      listing.location.toLowerCase().includes(query.toLowerCase()) ||
      listing.tags.some((t) => t.toLowerCase().includes(query.toLowerCase()));
    return matchesMood && matchesQuery;
  });

  return (
    <div className="min-h-screen bg-[#FAF5EA] text-[#231E19] font-sans antialiased selection:bg-[#708D81]/20 selection:text-[#231E19]">
      {/* Micro Status Bar */}
      <div className="border-b border-[#EBE2CF] bg-[#F5EFE3]/80 px-6 py-2.5 text-xs text-[#6A5E50] flex items-center justify-between backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-[#708D81] animate-pulse" />
          <span>India Stack & DigiLocker Verified Spaces with automated ₹100 UPI micro-escrow</span>
        </div>
        <div className="hidden sm:flex items-center gap-4 text-[11px] uppercase tracking-wider font-semibold">
          <span className="text-[#708D81]">Demo Mode</span>
          <span>Pune • Bangalore • Delhi</span>
        </div>
      </div>

      {/* Main Navbar */}
      <header className="sticky top-0 z-40 bg-[#FAF5EA]/95 backdrop-blur-md border-b border-[#DFD4BC]/60">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#708D81] flex items-center justify-center text-[#FAF5EA] shadow-[0_4px_16px_rgba(112,141,129,0.25)]">
              <InfinityIcon className="w-6 h-6 stroke-[#FAF5EA]" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-[#231E19]">SpaceLoop</span>
              <span className="block text-[10px] tracking-widest uppercase font-semibold text-[#8C7E6D]">Boutique Spaces</span>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-[#6A5E50]">
            <a href="#explore" className="text-[#231E19] hover:text-[#708D81] transition-colors">Explore</a>
            <a href="#how" className="hover:text-[#708D81] transition-colors">How It Works</a>
            <a href="#host" className="hover:text-[#708D81] transition-colors">Host a Space</a>
            <a href="#calculator" className="hover:text-[#708D81] transition-colors">Earnings Calc</a>
          </nav>

          <div className="flex items-center gap-3">
            <button className="hidden sm:flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border border-[#DFD4BC] bg-[#F5EFE3] text-xs font-semibold text-[#544839] hover:bg-[#F0E9D8] transition-colors">
              <CheckIcon className="w-3.5 h-3.5 text-[#708D81]" />
              DigiLocker Auth
            </button>
            <img
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80"
              alt="Profile"
              className="w-9 h-9 rounded-full object-cover ring-2 ring-[#708D81]/30 p-0.5"
            />
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-12 pb-14 px-6 overflow-hidden">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Copy & Search */}
          <div className="lg:col-span-7 flex flex-col items-start">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#F5EFE3] border border-[#DFD4BC] text-xs font-medium text-[#6A5E50] mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-[#D90368]" />
              Verified Micro-Leasing Platform
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-serif tracking-tight text-[#231E19] leading-[1.12] mb-6">
              Spaces with character, <br />
              <span className="italic font-normal text-[#708D81]">booked by the hour.</span>
            </h1>

            <p className="text-base sm:text-lg text-[#6A5E50] max-w-xl font-normal leading-relaxed mb-8">
              Slow-living, sunlit, and tactile creative environments. Match with verified study rooms, audio pods, and garden work studios.
            </p>

            {/* Mood Segmented Buttons */}
            <div className="w-full max-w-xl bg-[#F0E9D8] p-1.5 rounded-2xl border border-[#DFD4BC] flex items-center gap-1 mb-5 overflow-x-auto">
              {[
                { id: 'all', label: 'All Moods', Icon: SparklesIcon },
                { id: 'sunny', label: 'Sunny', Icon: SunIcon },
                { id: 'intimate', label: 'Intimate', Icon: CoffeeIcon },
                { id: 'industrial', label: 'Industrial', Icon: BuildingIcon },
                { id: 'greenery', label: 'Greenery', Icon: TreesIcon },
              ].map(({ id, label, Icon }) => {
                const isActive = selectedMood === id;
                return (
                  <button
                    key={id}
                    onClick={() => setSelectedMood(id)}
                    className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-200 ${
                      isActive
                        ? 'bg-[#FAF5EA] text-[#231E19] shadow-sm border border-[#DFD4BC]'
                        : 'text-[#6A5E50] hover:text-[#231E19] hover:bg-[#F5EFE3]'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-[#708D81]' : 'text-[#8C7E6D]'}`} />
                    {label}
                  </button>
                );
              })}
            </div>

            {/* Natural Buttermilk Input Box */}
            <div className="w-full max-w-xl bg-[#FAF5EA] p-2 rounded-2xl border border-[#DFD4BC] shadow-[0_8px_24px_-4px_rgba(80,60,30,0.08)] flex flex-col sm:flex-row items-center gap-2">
              <div className="relative flex-1 w-full flex items-center pl-3">
                <SearchIcon className="w-4 h-4 text-[#8C7E6D] shrink-0" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Describe your ideal space (e.g. 'quiet study space in Wagholi under ₹50')..."
                  className="w-full pl-2.5 pr-4 py-2.5 bg-transparent text-sm placeholder-[#8C7E6D]/70 text-[#231E19] focus:outline-none font-medium"
                />
              </div>
              <button className="w-full sm:w-auto px-6 py-3 rounded-xl bg-[#708D81] hover:bg-[#5E796E] text-[#FAF5EA] font-semibold text-xs tracking-wider uppercase transition-all shadow-sm flex items-center justify-center gap-2">
                <SparklesIcon className="w-3.5 h-3.5 text-[#F5C768]" />
                Match with AI
              </button>
            </div>

            {/* Quick Chips */}
            <div className="flex flex-wrap items-center gap-2 mt-4 text-xs text-[#6A5E50]">
              <span className="font-semibold text-[#544839]">Try asking:</span>
              {['Wagholi study space under ₹50', 'Koramangala storage', 'Podcast studio Hauz Khas'].map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => setQuery(item)}
                  className="px-2.5 py-1 rounded-lg bg-[#F5EFE3] hover:bg-[#F0E9D8] text-[#544839] border border-[#DFD4BC] transition-colors"
                >
                  {item}
                </button>
              ))}
            </div>
          </div>

          {/* Right Column: Picture-Mat Collage */}
          <div className="lg:col-span-5 relative flex justify-center items-center">
            <div className="relative w-full max-w-[420px] aspect-[4/5] p-3 rounded-3xl bg-[#F5EFE3] border border-[#DFD4BC] shadow-[0_16px_36px_-6px_rgba(80,60,30,0.12)]">
              <div className="w-full h-full rounded-2xl overflow-hidden relative border border-[#DFD4BC]">
                <img
                  src="https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=1000&q=80"
                  alt="Featured space"
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#231E19]/70 via-transparent to-transparent" />
                <div className="absolute top-4 left-4 px-3 py-1.5 rounded-full bg-[#FAF5EA]/90 backdrop-blur-md text-[11px] font-semibold text-[#231E19] border border-[#DFD4BC] flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#708D81]" />
                  Sanctuary of the Day
                </div>
                <div className="absolute bottom-4 left-4 right-4 text-[#FAF5EA]">
                  <p className="text-xs font-semibold uppercase tracking-wider text-[#DFD4BC]">Koramangala, Bangalore</p>
                  <h3 className="text-lg font-serif font-bold text-[#FAF5EA]">Quiet Study Pod & Hackathon Suite</h3>
                </div>
              </div>

              {/* Tilted Floating Mini-Card */}
              <div className="absolute -bottom-6 -left-6 w-44 p-2 rounded-2xl bg-[#FAF5EA] border border-[#DFD4BC] shadow-[0_16px_36px_-6px_rgba(80,60,30,0.14)] -rotate-3 hover:rotate-0 transition-transform duration-300">
                <div className="w-full aspect-[4/3] rounded-xl overflow-hidden mb-2">
                  <img
                    src="https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=400&q=80"
                    alt="Space preview"
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="px-1">
                  <p className="text-[11px] font-bold text-[#231E19] truncate">Wagholi Pod</p>
                  <p className="text-[10px] text-[#6A5E50] font-medium">₹50 / hr</p>
                </div>
              </div>

              {/* Magenta Instant Sticker */}
              <div className="absolute -top-3 -right-3 px-3.5 py-1.5 rounded-full bg-[#D90368] text-white text-[11px] font-bold tracking-wide shadow-md rotate-6">
                ⚡ Instant Approval
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Masonry Listings Feed */}
      <main className="max-w-7xl mx-auto px-6 pt-8 pb-24">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-8 border-b border-[#EBE2CF]">
          <div>
            <span className="text-xs uppercase font-bold tracking-widest text-[#708D81]">Curated Listings</span>
            <h2 className="text-2xl sm:text-3xl font-serif text-[#231E19] mt-1">
              Spaces with Character
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#F5EFE3] border border-[#DFD4BC] text-xs font-semibold text-[#544839] hover:bg-[#F0E9D8] transition-colors">
              <SlidersIcon className="w-3.5 h-3.5" />
              Filter by Hourly Rate
            </button>
            <span className="text-xs font-semibold text-[#6A5E50] bg-[#F0E9D8] px-3 py-2 rounded-xl border border-[#DFD4BC]">
              {filteredListings.length} spaces available
            </span>
          </div>
        </div>

        {/* Dynamic Multi-Column Grid */}
        <div className="columns-1 sm:columns-2 lg:columns-3 gap-6 pt-8 space-y-6">
          {filteredListings.map((item) => (
            <div
              key={item.id}
              className="break-inside-avoid bg-[#F5EFE3] rounded-3xl p-3 border border-[#DFD4BC] shadow-[0_8px_24px_-4px_rgba(80,60,30,0.06)] hover:shadow-[0_16px_36px_-6px_rgba(80,60,30,0.12)] transition-all duration-300 group flex flex-col"
            >
              {/* Image Frame with Matte Border */}
              <div className={`w-full ${item.aspectRatio} rounded-2xl overflow-hidden relative bg-[#F0E9D8]`}>
                <img
                  src={item.imageUrl}
                  alt={item.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out"
                />
                <div className="absolute top-3 left-3">
                  <span className="px-2.5 py-1 rounded-full bg-[#FAF5EA]/90 backdrop-blur-md text-[10px] font-bold text-[#231E19] border border-[#DFD4BC] shadow-sm">
                    {item.category}
                  </span>
                </div>
                <div className="absolute top-3 right-3">
                  <button className="w-8 h-8 rounded-full bg-[#FAF5EA]/85 backdrop-blur-md flex items-center justify-center text-[#231E19] hover:text-[#D90368] transition-colors shadow-sm">
                    <ArrowUpRightIcon className="w-4 h-4" />
                  </button>
                </div>
                <div className="absolute bottom-3 right-3 px-3 py-1 rounded-xl bg-[#231E19]/85 backdrop-blur-md text-[#FAF5EA] text-xs font-semibold">
                  ₹{item.pricePerHour} <span className="text-[10px] font-normal text-[#DFD4BC]">/hr</span>
                </div>
              </div>

              {/* Information Row */}
              <div className="px-2 pt-3 pb-1 flex flex-col">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="text-[11px] font-semibold text-[#6A5E50] uppercase tracking-wider">
                    {item.location}
                  </span>
                  <div className="flex items-center gap-1 text-xs font-bold text-[#231E19]">
                    <span className="text-[#E0A020]">★</span>
                    <span>{item.rating}</span>
                    <span className="text-[10px] font-normal text-[#6A5E50]">({item.reviewsCount})</span>
                  </div>
                </div>

                <h3 className="font-serif font-bold text-base text-[#231E19] leading-snug group-hover:text-[#708D81] transition-colors mb-2">
                  {item.title}
                </h3>

                {/* Specs / Badges */}
                <div className="flex flex-wrap items-center gap-1.5 mb-3">
                  {item.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded-md bg-[#F0E9D8] border border-[#DFD4BC] text-[10px] font-medium text-[#544839]"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                {/* Host Metadata */}
                <div className="pt-2.5 border-t border-[#EBE2CF] flex items-center justify-between text-xs text-[#6A5E50]">
                  <div className="flex items-center gap-2">
                    <img
                      src={item.hostAvatar}
                      alt={item.hostName}
                      className="w-5 h-5 rounded-full object-cover ring-1 ring-[#708D81]"
                    />
                    <span className="text-[11px] font-medium text-[#544839]">By {item.hostName}</span>
                  </div>
                  <div className="flex items-center gap-1 text-[10px] font-semibold text-[#708D81]">
                    <CheckIcon className="w-3 h-3" />
                    <span>DigiLocker Verified</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Bottom Footer */}
      <footer className="border-t border-[#DFD4BC] bg-[#F0E9D8] px-6 py-10 text-xs text-[#6A5E50]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-serif font-bold text-sm text-[#231E19]">SpaceLoop</span>
            <span>— Boutique micro-leasing platform.</span>
          </div>
          <div className="flex items-center gap-6 font-medium">
            <a href="#escrow" className="hover:text-[#231E19]">UPI Micro-Escrow</a>
            <a href="#digilocker" className="hover:text-[#231E19]">Host Verification</a>
            <a href="#terms" className="hover:text-[#231E19]">Terms of Service</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
