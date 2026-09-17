import React, { useState } from 'react';

export interface SpaceItem {
  id: string | number;
  title: string;
  category: string;
  location: string;
  pricePerHour: number;
  description: string;
  imageUrl: string;
  imageAlt: string;
  isDigiLockerVerified: boolean;
}

export const INITIAL_SPACES: SpaceItem[] = [
  {
    id: 'delhi-study-pod',
    title: 'North Campus Quiet Study Pod (Delhi...)',
    category: 'STUDIO',
    location: 'New Delhi',
    pricePerHour: 75,
    description: 'Silent reading and study suite located 2 minutes from Vishwavidyalaya Metro and Hansraj College. Ideal for semester exam sprints.',
    imageUrl: 'https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?auto=format&fit=crop&w=800&q=80',
    imageAlt: 'Quiet study pod workstation with desk lamp and acoustic privacy panels in North Campus Delhi',
    isDigiLockerVerified: true
  },
  {
    id: 'pune-wagholi-pod',
    title: 'Quiet Study Pod & Hackathon...',
    category: 'STUDIO',
    location: 'Pune',
    pricePerHour: 50,
    description: 'Acoustically damped project studio and study suite situated 300 meters from JSPM Imperial College campus in Wagholi.',
    imageUrl: 'https://images.unsplash.com/photo-1497215728101-856f4ea42174?auto=format&fit=crop&w=800&q=80',
    imageAlt: 'Individual project study room with glass partition in Wagholi Pune',
    isDigiLockerVerified: true
  },
  {
    id: 'bangalore-podcast-studio',
    title: 'Acoustic Podcast & Vocal Recording...',
    category: 'STUDIO',
    location: 'Bangalore',
    pricePerHour: 350,
    description: 'Soundproofed audio recording suite featuring Rode PodMic microphones, Focusrite Scarlett audio interface, and boom arms.',
    imageUrl: 'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=800&q=80',
    imageAlt: 'Professional soundproofed vocal studio with recording gear in Bangalore',
    isDigiLockerVerified: true
  },
  {
    id: 'koramangala-student-den-1',
    title: 'Koramangala 4th Block Student Den',
    category: 'STUDIO',
    location: 'Bengaluru',
    pricePerHour: 80,
    description: 'High-speed optical fiber, comfortable desks, ergonomic chairs for coding sprints, and uninterrupted power backup.',
    imageUrl: 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=800&q=80',
    imageAlt: 'Collaborative student coding space with dual monitor setup in Koramangala',
    isDigiLockerVerified: true
  },
  {
    id: 'pune-maker-loft',
    title: 'Wagholi Hardware & IoT Prototyping Bay',
    category: 'STUDIO',
    location: 'Pune',
    pricePerHour: 110,
    description: 'Equipped with anti-static mats, digital soldering stations, bench power supplies, and high ventilation for tech projects.',
    imageUrl: 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=800&q=80',
    imageAlt: 'Electronics testing workbench with equipment in Wagholi Pune',
    isDigiLockerVerified: true
  },
  {
    id: 'indiranagar-creator-den',
    title: 'Indiranagar Creator Lounge & Photo Bay',
    category: 'STUDIO',
    location: 'Bengaluru',
    pricePerHour: 280,
    description: 'Evenly lit creator nook with backdrop stands, continuous softbox lighting, and 300 Mbps broadband for instant 4K uploads.',
    imageUrl: 'https://images.unsplash.com/photo-1590602847861-f357a9332bbc?auto=format&fit=crop&w=800&q=80',
    imageAlt: 'Content creator studio with softbox photography lighting in Indiranagar Bengaluru',
    isDigiLockerVerified: true
  }
];

export const SpaceCardItem: React.FC<{ space: SpaceItem; onSelect: (id: string | number) => void }> = ({ space, onSelect }) => {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  return (
    <div className="group flex flex-col bg-[#10152B]/90 hover:bg-[#151C38] border border-[#222B52] hover:border-[#4B599E] rounded-2xl overflow-hidden transition-all duration-300 shadow-[0_8px_24px_rgba(0,0,0,0.4)] hover:shadow-[0_16px_36px_rgba(30,40,90,0.3)] hover:-translate-y-1">
      {/* Photo Container */}
      <div className="relative w-full aspect-[16/10] bg-[#0A0E21] overflow-hidden">
        {!loaded && !error && (
          <div className="absolute inset-0 bg-[#161E3D] animate-pulse flex items-center justify-center">
            <span className="text-[11px] font-medium text-[#5F70A3]">Loading preview...</span>
          </div>
        )}

        {error ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#0D1226] text-[#606E9C] p-4 text-center">
            <svg className="w-8 h-8 mb-1.5 opacity-60 stroke-current" fill="none" viewBox="0 0 24 24">
              <rect width="18" height="18" x="3" y="3" rx="2" strokeWidth="2" />
              <path d="m3 15 5-5 4 4 6-6" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <span className="text-[11px] font-medium">SpaceLoop Verified Asset</span>
          </div>
        ) : (
          <img
            src={space.imageUrl}
            alt={space.imageAlt}
            loading="lazy"
            decoding="async"
            onLoad={() => setLoaded(true)}
            onError={() => setError(true)}
            className={`w-full h-full object-cover object-center transform transition-transform duration-500 ease-out group-hover:scale-[1.03] ${
              loaded ? 'opacity-100' : 'opacity-0'
            }`}
          />
        )}

        {/* Subtle Bottom Vignette */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#10152B] via-transparent to-black/35 pointer-events-none" />

        {/* Category Pill Tag */}
        <div className="absolute top-3 left-3 z-10">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded bg-[#1B2347]/90 backdrop-blur-md border border-[#37447E]/70 text-[10px] font-bold tracking-wider text-[#B4C2FF] uppercase shadow-sm">
            {space.category}
          </span>
        </div>

        {/* Location Tag */}
        <div className="absolute bottom-3 left-3 z-10">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#0A0D1C]/85 backdrop-blur-md border border-[#2B3563] text-[11px] font-medium text-[#D1D7F5]">
            <span className="text-[#818CF8]">📍</span>
            <span>{space.location}</span>
          </span>
        </div>
      </div>

      {/* Card Content */}
      <div className="flex flex-col flex-1 p-5">
        <div className="flex items-start justify-between gap-3 mb-2">
          <h3 className="text-base font-semibold text-white tracking-tight leading-snug line-clamp-1 group-hover:text-[#A5B4FC] transition-colors">
            {space.title}
          </h3>
          <div className="shrink-0 text-right">
            <span className="text-base font-bold text-white tracking-tight">₹{space.pricePerHour}</span>
            <span className="text-[11px] text-[#7A88B8] font-normal">/hr</span>
          </div>
        </div>

        <p className="text-xs text-[#8A96C2] leading-relaxed line-clamp-2 mb-4">
          {space.description}
        </p>

        {/* Trust & CTA Row */}
        <div className="mt-auto pt-3.5 border-t border-[#1F2749] flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-[#34D399]">
            <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
            </svg>
            <span>DigiLocker Verified</span>
          </div>

          <button
            type="button"
            onClick={() => onSelect(space.id)}
            className="inline-flex items-center gap-1 text-xs font-semibold text-[#818CF8] hover:text-[#C7D2FE] transition-colors"
          >
            <span>View Space</span>
            <span>→</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default function ExploreView() {
  const [spaces] = useState<SpaceItem[]>(INITIAL_SPACES);

  const handleSelect = (id: string | number) => {
    console.log('Selected space ID:', id);
  };

  return (
    <div className="w-full min-h-screen bg-[#0A0D1A] text-[#E2E8F0] px-4 sm:px-6 lg:px-8 py-8 font-sans antialiased selection:bg-[#6366F1]/30">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              Verified Available Spaces
            </h2>
            <p className="text-xs sm:text-sm text-[#7F8EA3] mt-1">
              Hourly micro-leases with automated ₹100 UPI escrow protection.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-[#141A33] border border-[#283256] text-[#93C5FD]">
              {spaces.length} Live Spaces Near You
            </span>
          </div>
        </div>

        {/* Balanced Grid: 1 col on mobile, 2 on tablet, 3 on desktop */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {spaces.map((space) => (
            <SpaceCardItem
              key={space.id}
              space={space}
              onSelect={handleSelect}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
