import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { View, Text, Pressable } from 'react-native';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Space } from '../types';
import { getSpaces, aiMatchSpaces } from '../services/spaces';
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
  const [userLat, setUserLat] = useState<number | null>(null);
  const [userLng, setUserLng] = useState<number | null>(null);

  const categories = [
    { label: 'All Spaces', icon: 'fa-border-all', value: 'All' },
    { label: 'Creative & Studio', icon: 'fa-camera', value: 'Studio', color: 'text-indigo-400' },
    { label: 'Garage & Storage', icon: 'fa-boxes-stacked', value: 'Storage', color: 'text-amber-400' },
    { label: 'Parking & EV', icon: 'fa-charging-station', value: 'Parking', color: 'text-emerald-400' },
    { label: 'Pop-up Retail', icon: 'fa-store', value: 'Workspace', color: 'text-pink-400' },
    { label: 'Off-Peak & Events', icon: 'fa-users', value: 'Meeting', color: 'text-cyan-400' },
  ];

  const quickHubs = [
    { label: '📍 Wagholi, Pune', loc: 'Wagholi, Pune' },
    { label: '📍 IIT Delhi / Hauz Khas', loc: 'Hauz Khas, New Delhi' },
    { label: '📍 Koramangala, Bangalore', loc: 'Koramangala, Bangalore' },
    { label: '📍 Shivajinagar / FC Road', loc: 'Shivajinagar, Pune' },
    { label: '📍 DU North Campus', loc: 'North Campus, New Delhi' },
    { label: '📍 Sector 62, Noida', loc: 'Sector 62, Noida' },
  ];

  // Fetch Spaces from API
  const fetchSpaces = useCallback(async () => {
    setLoading(true);
    try {
      const maxPriceVal = selectedMaxPrice ? Number(selectedMaxPrice) : undefined;
      const data = await getSpaces({
        category: activeCategory !== 'All' ? activeCategory : undefined,
        city: locationInput.trim() || undefined,
        q: searchQuery.trim() || undefined,
        max_price: maxPriceVal,
        lat: userLat || undefined,
        lng: userLng || undefined,
      });
      setSpaces(data);
    } catch (err) {
      console.error('Failed to load spaces:', err);
    } finally {
      setLoading(false);
    }
  }, [activeCategory, locationInput, searchQuery, selectedMaxPrice, userLat, userLng]);

  useEffect(() => {
    fetchSpaces();
  }, [activeCategory, selectedMaxPrice, selectedRadius]);

  // AI Match handler
  const handleAiSearch = async (queryText?: string) => {
    const q = (queryText !== undefined ? queryText : searchQuery).trim();
    if (!q) {
      setAiMatchActive(false);
      fetchSpaces();
      return;
    }

    setIsAiSearching(true);
    setLoading(true);
    try {
      const result = await aiMatchSpaces(q, userLat || undefined, userLng || undefined);
      setSpaces(result.spaces || []);
      setAiMatchActive(true);
    } catch (err) {
      console.warn('AI Match fallback to standard search:', err);
      const fallback = await getSpaces({ q });
      setSpaces(fallback);
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

            <p className="mt-3 text-sm sm:text-base text-slate-400 leading-relaxed max-w-2xl mx-auto">
              Instantly discover and reserve quiet study pods, creative studios, micro-workspaces, and event spaces by the hour.
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
                    placeholder="Describe your ideal space (e.g. 'Quiet study space for 3 people under ₹60/hr')..."
                    className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-11 pr-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
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
                    const p = 'Quiet study space for 3 people';
                    setSearchQuery(p);
                    handleAiSearch(p);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-[11px] transition flex items-center gap-1.5"
                >
                  <span>📚</span> Quiet study space for 3 people
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const p = 'Studio for a 2-hour shoot';
                    setSearchQuery(p);
                    handleAiSearch(p);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-[11px] transition flex items-center gap-1.5"
                >
                  <span>📸</span> Studio for a 2-hour shoot
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const p = 'Affordable workspace near me';
                    setSearchQuery(p);
                    handleAiSearch(p);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-[11px] transition flex items-center gap-1.5"
                >
                  <span>💼</span> Affordable workspace near me
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const p = 'Space for a small event';
                    setSearchQuery(p);
                    handleAiSearch(p);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 text-[11px] transition flex items-center gap-1.5"
                >
                  <span>🎉</span> Space for a small event
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
                  onClick={() => {
                    setActiveCategory(cat.value);
                    setAiMatchActive(false);
                  }}
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
            <span>{spaces.length} spaces available</span>
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
            <div className="flex-grow flex items-center gap-2 bg-slate-950/80 border border-slate-700/70 rounded-xl px-3 py-2">
              <i className="fa-solid fa-location-dot text-indigo-400 shrink-0" />
              <input
                type="text"
                value={locationInput}
                onChange={(e) => setLocationInput(e.target.value)}
                placeholder="Enter location or college (e.g. Wagholi, Hauz Khas, Koramangala)..."
                className="bg-transparent border-none text-xs sm:text-sm text-white placeholder-slate-500 focus:outline-none w-full"
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
                onChange={(e) => setSelectedRadius(e.target.value)}
                className="bg-slate-950 border border-slate-700/70 rounded-xl px-3 py-2 text-xs sm:text-sm text-white focus:outline-none focus:border-indigo-500 transition"
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
                onChange={(e) => setSelectedMaxPrice(e.target.value)}
                className="bg-slate-950 border border-slate-700/70 rounded-xl px-3 py-2 text-xs sm:text-sm text-white focus:outline-none focus:border-indigo-500 transition"
              >
                <option value="">Any Budget</option>
                <option value="60">Under ₹60/hr</option>
                <option value="80">Under ₹80/hr</option>
                <option value="100">Under ₹100/hr</option>
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
                onClick={() => {
                  setLocationInput(hub.loc);
                  fetchSpaces();
                }}
                className="px-2 py-0.5 rounded-lg bg-slate-950/70 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 text-[11px] transition"
              >
                {hub.label}
              </button>
            ))}
          </div>
        </div>

        {/* AI Matching Banner */}
        {aiMatchActive && (
          <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-indigo-950/60 via-slate-900 to-indigo-950/60 border border-indigo-500/30 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-600/30 text-indigo-300 flex items-center justify-center">
                <i className="fa-solid fa-sparkles text-sm" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">AI Compatibility Ranking Active</h3>
                <p className="text-xs text-slate-400">Sorted by best fit for your requirements</p>
              </div>
            </div>
            <button
              onClick={() => {
                setAiMatchActive(false);
                setSearchQuery('');
                fetchSpaces();
              }}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium px-3 py-1.5 rounded-lg bg-indigo-950 border border-indigo-800/60"
            >
              Clear AI Filter
            </button>
          </div>
        )}

        {/* Spaces Grid */}
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center">
            <div className="w-8 h-8 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3" />
            <span className="text-xs text-slate-400">Searching verified spaces...</span>
          </div>
        ) : spaces.length === 0 ? (
          <div className="py-20 text-center bg-slate-900/50 rounded-2xl border border-slate-800 p-8">
            <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4 text-2xl">
              📍
            </div>
            <h3 className="text-lg font-bold text-white mb-2">No spaces found matching this criteria</h3>
            <p className="text-xs text-slate-400 mb-6 max-w-sm mx-auto">
              Try adjusting your location, selecting "All Spaces", or increasing your budget limit.
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
            {spaces.map((space) => (
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
