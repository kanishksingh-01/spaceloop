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
      {/* 1. FOCUSED DISCOVERY HEADER & NATURAL LANGUAGE AI SEARCH */}
      <section className="relative overflow-hidden pt-8 pb-8 md:pt-12 md:pb-12 border-b border-slate-800/60 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950">
        {/* Glowing Background Ambience */}
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-indigo-600/15 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute top-10 right-10 w-[240px] h-[240px] bg-violet-600/10 blur-[100px] rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-3xl mx-auto mb-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium mb-3 shadow-sm">
              <span className="flex h-2 w-2 rounded-full bg-indigo-400 animate-ping" />
              <span className="font-semibold">AI Matchmaker</span> • Real-time Instant Availability
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-tight">
              Find Flexible Space Near You
            </h1>

            <p className="mt-3 text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl mx-auto">
              Instantly discover and reserve workspaces, client meeting rooms, creative studios, maker bays, and study pods by the hour.
            </p>
          </div>

          {/* AI Intent-Based Search Engine Bar */}
          <div className="max-w-3xl mx-auto">
            <div className="bg-slate-900/90 backdrop-blur-xl border border-indigo-500/30 rounded-2xl p-3 sm:p-3.5 floating-panel transition-all hover:border-indigo-500/50 shadow-xl">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleAiSearch();
                }}
                className="flex flex-col sm:flex-row gap-2.5"
              >
                <div className="relative flex-grow flex items-center">
                  <div className="absolute left-4 text-indigo-400 text-base">
                    <i className="fa-solid fa-wand-magic-sparkles" />
                  </div>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Describe your ideal space (e.g. 'podcast studio for 2' or 'client meeting room near Koramangala')..."
                    className="w-full bg-slate-800 border border-slate-700/80 rounded-xl pl-11 pr-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isAiSearching}
                  className="bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-700 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold text-sm px-5 py-3 rounded-xl shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 transition shrink-0 group disabled:opacity-60"
                >
                  {isAiSearching ? (
                    <>
                      <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Matching...</span>
                    </>
                  ) : (
                    <>
                      <span>Match with AI</span>
                      <i className="fa-solid fa-arrow-right text-xs group-hover:translate-x-0.5 transition" />
                    </>
                  )}
                </button>
              </form>

              {/* Prompt Suggestion Chips */}
              <div className="mt-3 pt-2.5 border-t border-slate-800/70 flex items-center gap-2 text-xs overflow-x-auto whitespace-nowrap pb-1 scrollbar-none">
                <span className="text-slate-400 font-medium shrink-0 flex items-center gap-1 text-[11px]">
                  <i className="fa-regular fa-compass text-indigo-400" /> Try prompts:
                </span>
                <button
                  type="button"
                  onClick={() => {
                    const p = 'quiet place for 6 people near Kharadi for a 4-hour team meeting';
                    setSearchQuery(p);
                    handleAiSearch(p);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-indigo-950/70 hover:bg-indigo-900/80 text-indigo-200 hover:text-white border border-indigo-500/40 text-[11px] font-medium transition flex items-center gap-1.5"
                >
                  <span>✨</span> Kharadi Team Meeting
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const p = 'quiet room for 4 people';
                    setSearchQuery(p);
                    handleAiSearch(p);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-[11px] transition flex items-center gap-1.5"
                >
                  <span>📚</span> Quiet Room (4 ppl)
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const p = 'workspace near Kharadi';
                    setSearchQuery(p);
                    handleAiSearch(p);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-[11px] transition flex items-center gap-1.5"
                >
                  <span>💼</span> Workspace in Kharadi
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const p = 'place for a small team meeting';
                    setSearchQuery(p);
                    handleAiSearch(p);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-[11px] transition flex items-center gap-1.5"
                >
                  <span>👥</span> Small Team Meeting
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const p = 'studio for a photography session';
                    setSearchQuery(p);
                    handleAiSearch(p);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-[11px] transition flex items-center gap-1.5"
                >
                  <span>📸</span> Photography Studio
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const p = 'office space under ₹1000 per hour';
                    setSearchQuery(p);
                    handleAiSearch(p);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-[11px] transition flex items-center gap-1.5"
                >
                  <span>💰</span> Under ₹1000/hr
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. SPACE EXPLORER & CONTROLS */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex-1 w-full">
        {/* Controls Bar: Category Pills & Stats */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          {/* Category Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 md:pb-0 scrollbar-none">
            {categories.map((cat) => {
              const isSelected = activeCategory === cat.value;
              return (
                <button
                  key={cat.value}
                  type="button"
                  onClick={() => handleSelectCategory(cat.value)}
                  className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-medium transition whitespace-nowrap floating-interactive ${
                    isSelected
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
                  }`}
                >
                  <i className={`fa-solid ${cat.icon} mr-1.5 ${cat.color || ''}`} />
                  <span>{cat.label}</span>
                </button>
              );
            })}
          </div>

          {/* Active Indicator */}
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span>
              {displaySpaces.length} {displaySpaces.length === 1 ? 'space' : 'spaces'} available
              {selectedRadius ? ` within ${selectedRadius} km` : ''}
            </span>
            <span className="w-1 h-1 rounded-full bg-slate-700" />
            <span className="flex items-center gap-1 text-emerald-400">
              <i className="fa-solid fa-shield-check" /> 100% Host Verified
            </span>
          </div>
        </div>

        {/* Location & Radius Dynamic Discovery Filter Bar */}
        <div className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-4 mb-8 floating-container">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              fetchSpaces();
            }}
            className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3"
          >
            {/* Location Input with Geolocation Action */}
            <div className="flex-grow flex items-center gap-2 bg-slate-800 border border-slate-700/80 rounded-xl px-3 py-2">
              <i className="fa-solid fa-location-dot text-indigo-400 shrink-0" />
              <input
                type="text"
                value={locationInput}
                onChange={(e) => setLocationInput(e.target.value)}
                placeholder="Enter location or college (e.g. Wagholi, Hauz Khas, Koramangala)..."
                className="bg-transparent border-none text-xs sm:text-sm text-slate-100 placeholder-slate-400 focus:outline-none w-full"
              />
              <button
                type="button"
                onClick={detectCurrentLocation}
                className="shrink-0 text-[11px] font-semibold text-indigo-300 hover:text-white bg-indigo-950/80 hover:bg-indigo-900/80 border border-indigo-500/30 px-2.5 py-1 rounded-lg flex items-center gap-1 transition"
                title="Use my current GPS coordinates"
              >
                <i className="fa-solid fa-crosshairs text-indigo-400" />
                <span className="hidden sm:inline">Use GPS</span>
              </button>
            </div>

            {/* Radius Selector */}
            <div className="flex items-center gap-2 shrink-0">
              <label className="text-xs text-slate-400 font-medium shrink-0 flex items-center gap-1">
                <i className="fa-solid fa-ruler-combined text-slate-500" /> Radius:
              </label>
              <select
                value={selectedRadius}
                onChange={(e) => handleRadiusChange(e.target.value)}
                className="bg-slate-800 border border-slate-700/80 rounded-xl px-3 py-2 text-xs sm:text-sm text-slate-100 focus:outline-none focus:border-indigo-500 transition"
              >
                <option value="">Any Distance</option>
                <option value="1">Within 1 km</option>
                <option value="3">Within 3 km</option>
                <option value="5">Within 5 km</option>
                <option value="10">Within 10 km</option>
              </select>
            </div>

            {/* Max Budget Filter */}
            <div className="flex items-center gap-2 shrink-0">
              <label className="text-xs text-slate-400 font-medium shrink-0 flex items-center gap-1">
                <i className="fa-solid fa-indian-rupee-sign text-slate-500" /> Max Price:
              </label>
              <select
                value={selectedMaxPrice}
                onChange={(e) => handleMaxPriceChange(e.target.value)}
                className="bg-slate-800 border border-slate-700/80 rounded-xl px-3 py-2 text-xs sm:text-sm text-slate-100 focus:outline-none focus:border-indigo-500 transition"
              >
                <option value="">Any Budget</option>
                <option value="60">Under ₹60/hr</option>
                <option value="80">Under ₹80/hr</option>
                <option value="100">Under ₹100/hr</option>
                <option value="150">Under ₹150/hr</option>
                <option value="200">Under ₹200/hr</option>
              </select>
            </div>

            {/* Submit & Reset Actions */}
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs sm:text-sm font-semibold transition flex items-center justify-center gap-1.5 shadow-md shadow-indigo-600/20"
              >
                <i className="fa-solid fa-filter text-xs" /> Apply Filter
              </button>
              <button
                type="button"
                onClick={resetAllFilters}
                className={`px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold transition flex items-center justify-center gap-1.5 border ${
                  locationInput || selectedRadius || selectedMaxPrice || activeCategory !== 'All' || searchQuery || aiMatchActive
                    ? 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700 shadow-sm'
                    : 'bg-slate-950/60 hover:bg-slate-850 text-slate-400 hover:text-slate-200 border-slate-800'
                }`}
                title="Reset all filters to default"
              >
                <i className="fa-solid fa-rotate-left text-xs" />
                <span>Reset</span>
              </button>
            </div>
          </form>

          {/* Quick Hub Chips */}
          <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center gap-2 text-xs overflow-x-auto whitespace-nowrap scrollbar-none">
            <span className="text-slate-500 text-[11px] font-medium shrink-0">Quick Hubs:</span>
            {quickHubs.map((hub, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelectQuickHub(hub)}
                className="px-2 py-0.5 rounded-lg bg-slate-950/70 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 text-[11px] transition"
              >
                {hub.label}
              </button>
            ))}
          </div>
        </div>

        {/* AI Matching Banner */}
        {aiMatchActive && (
          <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-indigo-950/60 via-slate-900 to-indigo-950/60 border border-indigo-500/30 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-600/30 text-indigo-300 flex items-center justify-center shrink-0">
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
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium px-3 py-1.5 rounded-lg bg-indigo-950 border border-indigo-800/60 shrink-0"
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
