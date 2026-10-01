import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { View, Text, Pressable } from 'react-native';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Space } from '../types';
import { getSpaces, searchSpacesHybrid, aiMatchSpaces } from '../services/spaces';
import { SpaceCard } from '../components/common/SpaceCard';

export const ExplorePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // State
  const [spaces, setSpaces] = useState<Space[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
  const [locationInput, setLocationInput] = useState(searchParams.get('loc') || '');
  const [selectedRadius, setSelectedRadius] = useState(searchParams.get('radius') || '');
  const [selectedMaxPrice, setSelectedMaxPrice] = useState(searchParams.get('max_price') || '');
  const [activeCategory, setActiveCategory] = useState(searchParams.get('category') || 'All');
  const [isAiSearching, setIsAiSearching] = useState(false);
  const [aiMatchActive, setAiMatchActive] = useState(false);
  const [extractedConstraints, setExtractedConstraints] = useState<Record<string, any>>({});
  const [searchSummary, setSearchSummary] = useState<string>('');
  const [userLat, setUserLat] = useState<number | null>(null);
  const [userLng, setUserLng] = useState<number | null>(null);

  const categories = [
    { label: 'All Spaces', icon: 'fa-border-all', value: 'All' },
    { label: 'Workspaces', icon: 'fa-laptop-code', value: 'Workspace', color: 'text-indigo-400' },
    { label: 'Meeting Rooms', icon: 'fa-handshake', value: 'Meeting', color: 'text-blue-400' },
    { label: 'Creative & Studio', icon: 'fa-microphone-lines', value: 'Studio', color: 'text-purple-400' },
    { label: 'Maker Workshops', icon: 'fa-screwdriver-wrench', value: 'Workshop', color: 'text-amber-400' },
    { label: 'Pop-Up Retail', icon: 'fa-store', value: 'Retail', color: 'text-pink-400' },
    { label: 'Storage Units', icon: 'fa-boxes-stacked', value: 'Storage', color: 'text-yellow-400' },
    { label: 'Study Pods', icon: 'fa-book-open', value: 'Study', color: 'text-emerald-400' },
    { label: 'Event Spaces', icon: 'fa-users', value: 'Event', color: 'text-cyan-400' },
  ];

  const quickHubs = [
    { label: '📍 Wagholi, Pune', loc: 'Wagholi, Pune', lat: 18.5793, lng: 73.9822 },
    { label: '📍 IIT Delhi / Hauz Khas', loc: 'Hauz Khas, New Delhi', lat: 28.5450, lng: 77.1926 },
    { label: '📍 Koramangala, Bangalore', loc: 'Koramangala, Bangalore', lat: 12.9352, lng: 77.6245 },
    { label: '📍 Shivajinagar / FC Road', loc: 'Shivajinagar, Pune', lat: 18.5204, lng: 73.8567 },
    { label: '📍 DU North Campus', loc: 'North Campus, New Delhi', lat: 28.6900, lng: 77.2100 },
    { label: '📍 Sector 62, Noida', loc: 'Sector 62, Noida', lat: 28.6270, lng: 77.3725 },
  ];

  const resolveCoordinates = (name: string): { lat: number; lng: number } | null => {
    const clean = name.toLowerCase().trim();
    if (!clean) return null;
    for (const hub of quickHubs) {
      if (hub.loc.toLowerCase().includes(clean) || clean.includes(hub.loc.toLowerCase().split(',')[0].toLowerCase())) {
        return { lat: hub.lat, lng: hub.lng };
      }
    }
    if (clean.includes('pune') || clean.includes('wagholi') || clean.includes('viman') || clean.includes('kothrud') || clean.includes('aundh')) {
      return { lat: 18.5793, lng: 73.9822 };
    }
    if (clean.includes('delhi') || clean.includes('hauz khas') || clean.includes('noida') || clean.includes('campus')) {
      return { lat: 28.5450, lng: 77.1926 };
    }
    if (clean.includes('bangalore') || clean.includes('bengaluru') || clean.includes('koramangala') || clean.includes('indiranagar')) {
      return { lat: 12.9352, lng: 77.6245 };
    }
    if (clean.includes('mumbai') || clean.includes('bandra') || clean.includes('powai')) {
      return { lat: 19.1334, lng: 72.9133 };
    }
    return null;
  };

  const computeHaversineKm = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return Math.round(R * c * 10) / 10;
  };

  // Fetch Spaces from API with optional direct overrides
  const fetchSpaces = useCallback(async (overrides?: {
    category?: string;
    loc?: string;
    q?: string;
    radius?: string;
    maxPrice?: string;
    lat?: number | null;
    lng?: number | null;
  }) => {
    setLoading(true);
    try {
      const cat = overrides?.category !== undefined ? overrides.category : activeCategory;
      const loc = overrides?.loc !== undefined ? overrides.loc : locationInput;
      const qVal = overrides?.q !== undefined ? overrides.q : searchQuery;
      const rad = overrides?.radius !== undefined ? overrides.radius : selectedRadius;
      const priceStr = overrides?.maxPrice !== undefined ? overrides.maxPrice : selectedMaxPrice;
      let curLat = overrides?.lat !== undefined ? overrides.lat : userLat;
      let curLng = overrides?.lng !== undefined ? overrides.lng : userLng;

      if ((!curLat || !curLng) && loc) {
        const coords = resolveCoordinates(loc);
        if (coords) {
          curLat = coords.lat;
          curLng = coords.lng;
        }
      }

      const maxPriceVal = priceStr ? Number(priceStr) : undefined;
      const data = await getSpaces({
        category: cat !== 'All' ? cat : undefined,
        city: loc.trim() || undefined,
        q: qVal.trim() || undefined,
        radius: rad && rad !== 'All' ? rad : undefined,
        max_price: maxPriceVal,
        lat: curLat || undefined,
        lng: curLng || undefined,
      });
      setSpaces(data);
    } catch (err) {
      console.error('Failed to load spaces:', err);
    } finally {
      setLoading(false);
    }
  }, [activeCategory, locationInput, searchQuery, selectedMaxPrice, selectedRadius, userLat, userLng]);

  useEffect(() => {
    fetchSpaces();
  }, [activeCategory, selectedMaxPrice, selectedRadius]);

  // Reactive display spaces with distance & filter calculation
  const displaySpaces = useMemo(() => {
    let result = [...spaces];

    let refLat = userLat;
    let refLng = userLng;
    if ((!refLat || !refLng) && locationInput.trim()) {
      const coords = resolveCoordinates(locationInput);
      if (coords) {
        refLat = coords.lat;
        refLng = coords.lng;
      }
    }

    if (refLat && refLng) {
      result = result.map((sp) => {
        if (sp.latitude && sp.longitude) {
          const dist = computeHaversineKm(refLat!, refLng!, sp.latitude, sp.longitude);
          return { ...sp, distance_km: sp.distance_km ?? dist };
        }
        return sp;
      });

      if (selectedRadius && selectedRadius !== 'All') {
        const maxKm = Number(selectedRadius);
        if (!isNaN(maxKm) && maxKm > 0) {
          result = result.filter((sp) => sp.distance_km !== undefined && sp.distance_km <= maxKm);
        }
      }

      result.sort((a, b) => (a.distance_km ?? 9999) - (b.distance_km ?? 9999));
    }

    if (selectedMaxPrice) {
      const p = Number(selectedMaxPrice);
      if (!isNaN(p)) {
        result = result.filter((sp) => (sp.hourly_rate ?? sp.price_hourly ?? 50) <= p);
      }
    }

    if (activeCategory && activeCategory !== 'All') {
      const c = activeCategory.toLowerCase();
      result = result.filter((sp) => {
        const spCat = (sp.category || '').toLowerCase();
        const spTitle = (sp.title || '').toLowerCase();
        if (c === 'studio') return spCat.includes('studio') || spCat.includes('creative') || spTitle.includes('studio') || spTitle.includes('podcast');
        if (c === 'workspace') return spCat.includes('workspace') || spCat.includes('work') || spTitle.includes('hackathon') || spTitle.includes('coding');
        if (c === 'meeting') return spCat.includes('meeting') || spTitle.includes('discussion') || spTitle.includes('whiteboard') || spTitle.includes('sprint');
        if (c === 'study') return spCat.includes('study') || spCat.includes('pod') || spTitle.includes('study') || spTitle.includes('library');
        if (c === 'workshop') return spCat.includes('workshop') || spCat.includes('creative') || spTitle.includes('maker') || spTitle.includes('soldering');
        if (c === 'retail') return spCat.includes('retail') || spTitle.includes('retail') || spTitle.includes('pop-up') || spTitle.includes('store');
        if (c === 'storage') return spCat.includes('storage') || spTitle.includes('storage') || spTitle.includes('gear');
        if (c === 'event') return spCat.includes('event') || spTitle.includes('event');
        return spCat.includes(c) || spTitle.includes(c);
      });
    }

    return result;
  }, [spaces, userLat, userLng, locationInput, selectedRadius, selectedMaxPrice, activeCategory]);

  const handleSelectQuickHub = (hub: (typeof quickHubs)[0]) => {
    setLocationInput(hub.loc);
    setUserLat(hub.lat);
    setUserLng(hub.lng);
    fetchSpaces({ loc: hub.loc, lat: hub.lat, lng: hub.lng });
  };

  const handleSelectCategory = (catVal: string) => {
    setActiveCategory(catVal);
    setAiMatchActive(false);
    fetchSpaces({ category: catVal });
  };

  const handleRadiusChange = (rad: string) => {
    setSelectedRadius(rad);
    fetchSpaces({ radius: rad });
  };

  const handleMaxPriceChange = (price: string) => {
    setSelectedMaxPrice(price);
    fetchSpaces({ maxPrice: price });
  };

  // AI Match handler
  const handleAiSearch = async (queryText?: string) => {
    const q = (queryText !== undefined ? queryText : searchQuery).trim();
    if (!q) {
      setAiMatchActive(false);
      setExtractedConstraints({});
      setSearchSummary('');
      fetchSpaces();
      return;
    }

    setIsAiSearching(true);
    setLoading(true);
    try {
      let curLat = userLat;
      let curLng = userLng;
      if ((!curLat || !curLng) && locationInput.trim()) {
        const coords = resolveCoordinates(locationInput);
        if (coords) {
          curLat = coords.lat;
          curLng = coords.lng;
        }
      }

      const result = await searchSpacesHybrid({
        query: q,
        location: locationInput.trim() || undefined,
        category: activeCategory !== 'All' ? activeCategory : undefined,
        radius: selectedRadius && selectedRadius !== 'All' ? selectedRadius : undefined,
        max_price: selectedMaxPrice ? Number(selectedMaxPrice) : undefined,
        lat: curLat || undefined,
        lng: curLng || undefined,
      });

      setSpaces(result.spaces || []);
      setExtractedConstraints(result.extracted_constraints || {});
      setSearchSummary(result.match_summary || '');
      setAiMatchActive(true);
    } catch (err) {
      console.warn('Hybrid AI search fallback to standard search:', err);
      const fallback = await getSpaces({ q });
      setSpaces(fallback);
      setExtractedConstraints({});
      setSearchSummary(`Showing results for "${q}"`);
      setAiMatchActive(true);
    } finally {
      setIsAiSearching(false);
      setLoading(false);
    }
  };

  // GPS Geolocation
  const detectCurrentLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLat(pos.coords.latitude);
        setUserLng(pos.coords.longitude);
        setLocationInput(`GPS: ${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`);
        fetchSpaces();
      },
      (err) => {
        alert('Could not retrieve GPS location: ' + err.message);
      }
    );
  };

  const resetAllFilters = () => {
    setSearchQuery('');
    setLocationInput('');
    setSelectedRadius('');
    setSelectedMaxPrice('');
    setActiveCategory('All');
    setAiMatchActive(false);
    setExtractedConstraints({});
    setSearchSummary('');
    setUserLat(null);
    setUserLng(null);
    setSearchParams({});
    fetchSpaces();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased">
      {/* 1. DISCOVERY HEADER & SEARCH */}
      <section className="border-b border-slate-800/80 bg-slate-900/40 pt-10 pb-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-6">
            <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-white">
              Find Verified Spaces Near You
            </h1>
            <p className="mt-2 text-sm text-slate-400">
              Discover and reserve desks, meeting rooms, maker bays, and creative studios by the hour.
            </p>
          </div>

          {/* Search Input Bar */}
          <div className="max-w-2xl mx-auto">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAiSearch();
              }}
              className="flex items-center gap-2 p-1.5 bg-slate-900 border border-slate-700/80 rounded-xl shadow-md"
            >
              <div className="flex-1 flex items-center pl-3 pr-2 gap-2">
                <i className="fa-solid fa-magnifying-glass text-slate-400 text-sm" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Describe your ideal space (e.g. 'podcast studio' or 'meeting room in Pune')..."
                  className="w-full bg-transparent border-none text-xs sm:text-sm text-white placeholder-slate-400 focus:outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={isAiSearching}
                className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-lg transition shrink-0 flex items-center gap-1.5 disabled:opacity-60"
              >
                {isAiSearching ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Searching...</span>
                  </>
                ) : (
                  <>
                    <span>Match with AI</span>
                    <i className="fa-solid fa-arrow-right text-[10px]" />
                  </>
                )}
              </button>
            </form>

            {/* Prompt Quick Chips */}
            <div className="mt-3 flex items-center gap-1.5 text-xs overflow-x-auto whitespace-nowrap pb-1 scrollbar-none justify-center">
              <span className="text-slate-500 text-[11px] font-medium shrink-0">Try:</span>
              <button
                type="button"
                onClick={() => {
                  const p = 'quiet room for 4 people near Kharadi';
                  setSearchQuery(p);
                  handleAiSearch(p);
                }}
                className="px-2.5 py-0.5 rounded-full bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-white border border-slate-700 text-[11px] transition"
              >
                Team Meeting in Kharadi
              </button>
              <button
                type="button"
                onClick={() => {
                  const p = 'studio for photography session';
                  setSearchQuery(p);
                  handleAiSearch(p);
                }}
                className="px-2.5 py-0.5 rounded-full bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-white border border-slate-700 text-[11px] transition"
              >
                Photography Studio
              </button>
              <button
                type="button"
                onClick={() => {
                  const p = 'desk under ₹100 per hour';
                  setSearchQuery(p);
                  handleAiSearch(p);
                }}
                className="px-2.5 py-0.5 rounded-full bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-white border border-slate-700 text-[11px] transition"
              >
                Under ₹100/hr
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 2. SPACE EXPLORER & CONTROLS */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        {/* Category Filter Pills */}
        <div className="flex items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-2 md:pb-0 scrollbar-none">
            {categories.map((cat) => {
              const isSelected = activeCategory === cat.value;
              return (
                <button
                  key={cat.value}
                  type="button"
                  onClick={() => handleSelectCategory(cat.value)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap ${
                    isSelected
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
                  }`}
                >
                  <i className={`fa-solid ${cat.icon} mr-1.5`} />
                  <span>{cat.label}</span>
                </button>
              );
            })}
          </div>

          <div className="hidden lg:flex items-center gap-2 text-xs text-slate-400 shrink-0">
            <span>{displaySpaces.length} {displaySpaces.length === 1 ? 'space' : 'spaces'} available</span>
          </div>
        </div>

        {/* Secondary Filter Bar */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 mb-6">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              fetchSpaces();
            }}
            className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3"
          >
            {/* Location Input */}
            <div className="flex-1 flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5">
              <i className="fa-solid fa-location-dot text-slate-400 text-xs shrink-0" />
              <input
                type="text"
                value={locationInput}
                onChange={(e) => setLocationInput(e.target.value)}
                placeholder="Enter city or neighborhood (e.g. Wagholi, Koramangala)..."
                className="bg-transparent border-none text-xs text-white placeholder-slate-400 focus:outline-none w-full"
              />
              <button
                type="button"
                onClick={detectCurrentLocation}
                className="text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 bg-indigo-950/60 border border-indigo-500/30 px-2 py-0.5 rounded transition shrink-0"
              >
                GPS
              </button>
            </div>

            {/* Radius Selector */}
            <div className="flex items-center gap-1.5 shrink-0">
              <span className="text-xs text-slate-400">Distance:</span>
              <select
                value={selectedRadius}
                onChange={(e) => handleRadiusChange(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="">Any Distance</option>
                <option value="1">Within 1 km</option>
                <option value="3">Within 3 km</option>
                <option value="5">Within 5 km</option>
                <option value="10">Within 10 km</option>
              </select>
            </div>

            {/* Max Budget Filter */}
            <div className="flex items-center gap-1.5 shrink-0">
              <span className="text-xs text-slate-400">Max Rate:</span>
              <select
                value={selectedMaxPrice}
                onChange={(e) => handleMaxPriceChange(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="">Any Budget</option>
                <option value="60">Under ₹60/hr</option>
                <option value="80">Under ₹80/hr</option>
                <option value="100">Under ₹100/hr</option>
                <option value="150">Under ₹150/hr</option>
                <option value="200">Under ₹200/hr</option>
              </select>
            </div>

            {/* Filter Actions */}
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="submit"
                className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition"
              >
                Apply
              </button>
              <button
                type="button"
                onClick={resetAllFilters}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
              >
                Reset
              </button>
            </div>
          </form>

          {/* Quick Hubs */}
          <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center gap-1.5 text-xs overflow-x-auto whitespace-nowrap scrollbar-none">
            <span className="text-slate-500 text-[11px] font-medium shrink-0">Quick Hubs:</span>
            {quickHubs.map((hub, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelectQuickHub(hub)}
                className="px-2 py-0.5 rounded bg-slate-950 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 text-[11px] transition"
              >
                {hub.label}
              </button>
            ))}
          </div>
        </div>

        {/* AI Matching Banner */}
        {aiMatchActive && (
          <div className="mb-6 p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-600/20 text-indigo-400 flex items-center justify-center shrink-0">
                  <i className="fa-solid fa-sparkles text-sm" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">Hybrid Semantic Match Active</h3>
                  <p className="text-xs text-slate-400">
                    {searchSummary || 'Ranked by semantic intent and verified physical constraints'}
                  </p>
                </div>
              </div>
              <button
                onClick={() => {
                  setAiMatchActive(false);
                  setSearchQuery('');
                  setExtractedConstraints({});
                  setSearchSummary('');
                  fetchSpaces();
                }}
                className="text-xs text-slate-400 hover:text-white font-medium px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 shrink-0 transition"
              >
                Clear AI Filter
              </button>
            </div>

            {/* Extracted Structured Constraint Badges */}
            {Object.keys(extractedConstraints).length > 0 && (
              <div className="flex items-center gap-2 flex-wrap pt-2.5 border-t border-slate-800/70 text-xs">
                <span className="text-[11px] text-slate-400 font-medium shrink-0">Extracted constraints:</span>
                {extractedConstraints.location && (
                  <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[11px] font-medium flex items-center gap-1">
                    <span>📍</span> {extractedConstraints.location}
                  </span>
                )}
                {extractedConstraints.capacity && (
                  <span className="px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30 text-[11px] font-medium flex items-center gap-1">
                    <span>👥</span> {extractedConstraints.capacity}+ people
                  </span>
                )}
                {extractedConstraints.space_type && (
                  <span className="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[11px] font-medium flex items-center gap-1">
                    <span>🏷️</span> {extractedConstraints.space_type}
                  </span>
                )}
                {extractedConstraints.hours && (
                  <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[11px] font-medium flex items-center gap-1">
                    <span>⏱️</span> {extractedConstraints.hours} hr duration
                  </span>
                )}
                {extractedConstraints.max_price && (
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[11px] font-medium flex items-center gap-1">
                    <span>💰</span> Under ₹{extractedConstraints.max_price}/hr
                  </span>
                )}
                {Array.isArray(extractedConstraints.amenities) && extractedConstraints.amenities.map((am: string, i: number) => (
                  <span key={i} className="px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-[11px] font-medium">
                    {am}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Spaces Grid */}
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center">
            <div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3" />
            <span className="text-xs text-slate-400">Searching verified spaces...</span>
          </div>
        ) : displaySpaces.length === 0 ? (
          <div className="py-20 text-center bg-slate-900/50 rounded-2xl border border-slate-800 p-8">
            <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4 text-2xl">
              📍
            </div>
            <h3 className="text-lg font-bold text-white mb-2">No spaces found matching this criteria</h3>
            <p className="text-xs text-slate-400 mb-6 max-w-sm mx-auto">
              Try adjusting your location, selecting "All Spaces", or increasing your radius/budget limit.
            </p>
            <button
              onClick={resetAllFilters}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition"
            >
              Show All Available Spaces
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displaySpaces.map((space) => (
              <SpaceCard
                key={space.id}
                space={space}
                onPress={(id) => navigate(`/space/${id}`)}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
