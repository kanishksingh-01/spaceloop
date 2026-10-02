import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Space } from '../types';
import { getSpaces, searchSpacesHybrid } from '../services/spaces';
import { SpaceCard } from '../components/common/SpaceCard';
import { SpaceCardGridSkeleton } from '../components/common/Skeletons';
import { useTranslation } from '../i18n';

const PAGE_SIZE = 12;

export const ExplorePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { t, formatCurrency } = useTranslation();

  // State
  const [spaces, setSpaces] = useState<Space[]>([]);
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
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
    { label: t('explore.filterAll'), icon: 'fa-border-all', value: 'All' },
    { label: t('explore.filterDesk'), icon: 'fa-laptop-code', value: 'Workspace', color: 'text-indigo-400' },
    { label: t('explore.filterMeeting'), icon: 'fa-handshake', value: 'Meeting', color: 'text-blue-400' },
    { label: t('explore.filterStudio'), icon: 'fa-microphone-lines', value: 'Studio', color: 'text-purple-400' },
    { label: t('landing.studyCategory'), icon: 'fa-screwdriver-wrench', value: 'Workshop', color: 'text-amber-400' },
    { label: t('landing.spacesTitle'), icon: 'fa-store', value: 'Retail', color: 'text-pink-400' },
    { label: t('explore.filterStorage'), icon: 'fa-boxes-stacked', value: 'Storage', color: 'text-yellow-400' },
    { label: t('explore.filterStudy'), icon: 'fa-book-open', value: 'Study', color: 'text-emerald-400' },
    { label: t('explore.filterEvent'), icon: 'fa-users', value: 'Event', color: 'text-cyan-400' },
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
      result = result.map((s) => {
        if (s.latitude && s.longitude) {
          const dist = computeHaversineKm(refLat!, refLng!, s.latitude, s.longitude);
          return { ...s, distance_km: dist };
        }
        return s;
      });

      if (selectedRadius && selectedRadius !== 'All') {
        const maxRad = Number(selectedRadius);
        if (!isNaN(maxRad) && maxRad > 0) {
          result = result.filter((s) => s.distance_km === undefined || s.distance_km <= maxRad);
        }
      }
    }

    if (selectedMaxPrice) {
      const maxP = Number(selectedMaxPrice);
      if (!isNaN(maxP) && maxP > 0) {
        result = result.filter((s) => (s.hourly_rate ?? 50) <= maxP);
      }
    }

    return result;
  }, [spaces, userLat, userLng, locationInput, selectedRadius, selectedMaxPrice]);

  const visibleSpaces = useMemo(() => {
    return displaySpaces.slice(0, visibleCount);
  }, [displaySpaces, visibleCount]);

  const handleSelectCategory = (cat: string) => {
    setActiveCategory(cat);
    setVisibleCount(PAGE_SIZE);
    setSearchParams((prev) => {
      const p = new URLSearchParams(prev);
      if (cat === 'All') p.delete('category');
      else p.set('category', cat);
      return p;
    });
  };

  const handleRadiusChange = (rad: string) => {
    setSelectedRadius(rad);
    setVisibleCount(PAGE_SIZE);
    setSearchParams((prev) => {
      const p = new URLSearchParams(prev);
      if (!rad || rad === 'All') p.delete('radius');
      else p.set('radius', rad);
      return p;
    });
  };

  const handleMaxPriceChange = (price: string) => {
    setSelectedMaxPrice(price);
    setVisibleCount(PAGE_SIZE);
    setSearchParams((prev) => {
      const p = new URLSearchParams(prev);
      if (!price) p.delete('max_price');
      else p.set('max_price', price);
      return p;
    });
  };

  const handleSelectQuickHub = (hub: { label: string; loc: string; lat: number; lng: number }) => {
    setLocationInput(hub.loc);
    setUserLat(hub.lat);
    setUserLng(hub.lng);
    setVisibleCount(PAGE_SIZE);
    fetchSpaces({ loc: hub.loc, lat: hub.lat, lng: hub.lng });
  };

  // Hybrid AI Search
  const handleAiSearch = async (overridePrompt?: string) => {
    const q = overridePrompt || searchQuery;
    if (!q.trim()) {
      fetchSpaces();
      return;
    }

    setIsAiSearching(true);
    setLoading(true);
    setVisibleCount(PAGE_SIZE);

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
    setVisibleCount(PAGE_SIZE);
    setSearchParams({});
    fetchSpaces();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased">
      {/* 1. FOCUSED DISCOVERY HEADER & NATURAL LANGUAGE AI SEARCH */}
      <section className="relative overflow-hidden pt-8 pb-8 md:pt-12 md:pb-12 border-b border-slate-800/60 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-indigo-600/15 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute top-10 right-10 w-[240px] h-[240px] bg-violet-600/10 blur-[100px] rounded-full pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-3xl mx-auto mb-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium mb-3 shadow-sm">
              <span className="flex h-2 w-2 rounded-full bg-indigo-400 animate-ping" />
              <span className="font-semibold">{t('explore.aiMatchLabel')}</span> • {t('common.availableNow')}
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-tight">
              {t('explore.title')}
            </h1>

            <p className="mt-3 text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl mx-auto">
              {t('explore.subtitle')}
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
                    placeholder={t('explore.searchPlaceholder')}
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
                      <span>{t('common.loading')}</span>
                    </>
                  ) : (
                    <>
                      <span>{t('common.search')}</span>
                      <i className="fa-solid fa-arrow-right text-xs group-hover:translate-x-0.5 transition" />
                    </>
                  )}
                </button>
              </form>
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
              {displaySpaces.length} {t('explore.foundSpaces')}
            </span>
            <span className="w-1 h-1 rounded-full bg-slate-700" />
            <span className="flex items-center gap-1 text-emerald-400">
              <i className="fa-solid fa-shield-check" /> {t('common.verified')}
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
                placeholder={t('explore.filterLocation')}
                className="bg-transparent border-none text-xs sm:text-sm text-slate-100 placeholder-slate-400 focus:outline-none w-full"
              />
              <button
                type="button"
                onClick={detectCurrentLocation}
                className="shrink-0 text-[11px] font-semibold text-indigo-300 hover:text-white bg-indigo-950/80 hover:bg-indigo-900/80 border border-indigo-500/30 px-2.5 py-1 rounded-lg flex items-center gap-1 transition"
                title="Use my current GPS coordinates"
              >
                <i className="fa-solid fa-crosshairs text-indigo-400" />
                <span className="hidden sm:inline">GPS</span>
              </button>
            </div>

            {/* Radius Selector */}
            <div className="flex items-center gap-2 shrink-0">
              <label className="text-xs text-slate-400 font-medium shrink-0 flex items-center gap-1">
                <i className="fa-solid fa-ruler-combined text-slate-500" /> {t('explore.filterAvailability')}:
              </label>
              <select
                value={selectedRadius}
                onChange={(e) => handleRadiusChange(e.target.value)}
                className="bg-slate-800 border border-slate-700/80 rounded-xl px-3 py-2 text-xs sm:text-sm text-slate-100 focus:outline-none focus:border-indigo-500 transition"
              >
                <option value="">{t('common.all')}</option>
                <option value="1">1 km</option>
                <option value="3">3 km</option>
                <option value="5">5 km</option>
                <option value="10">10 km</option>
              </select>
            </div>

            {/* Max Budget Filter */}
            <div className="flex items-center gap-2 shrink-0">
              <label className="text-xs text-slate-400 font-medium shrink-0 flex items-center gap-1">
                <i className="fa-solid fa-indian-rupee-sign text-slate-500" /> {t('explore.priceRange')}:
              </label>
              <select
                value={selectedMaxPrice}
                onChange={(e) => handleMaxPriceChange(e.target.value)}
                className="bg-slate-800 border border-slate-700/80 rounded-xl px-3 py-2 text-xs sm:text-sm text-slate-100 focus:outline-none focus:border-indigo-500 transition"
              >
                <option value="">{t('common.all')}</option>
                <option value="60">{formatCurrency(60)}</option>
                <option value="80">{formatCurrency(80)}</option>
                <option value="100">{formatCurrency(100)}</option>
                <option value="150">{formatCurrency(150)}</option>
                <option value="200">{formatCurrency(200)}</option>
              </select>
            </div>

            {/* Submit & Reset Actions */}
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs sm:text-sm font-semibold transition flex items-center justify-center gap-1.5 shadow-md shadow-indigo-600/20"
              >
                <i className="fa-solid fa-filter text-xs" /> {t('common.filter')}
              </button>
              <button
                type="button"
                onClick={resetAllFilters}
                className={`px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold transition flex items-center justify-center gap-1.5 border ${
                  locationInput || selectedRadius || selectedMaxPrice || activeCategory !== 'All' || searchQuery || aiMatchActive
                    ? 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700 shadow-sm'
                    : 'bg-slate-950/60 hover:bg-slate-850 text-slate-400 hover:text-slate-200 border-slate-800'
                }`}
                title={t('common.clearFilters')}
              >
                <i className="fa-solid fa-rotate-left text-xs" />
                <span>{t('common.reset')}</span>
              </button>
            </div>
          </form>

          {/* Quick Hub Chips */}
          <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center gap-2 text-xs overflow-x-auto whitespace-nowrap scrollbar-none">
            <span className="text-slate-500 text-[11px] font-medium shrink-0">{t('explore.filterLocation')}:</span>
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
                  <h3 className="text-sm font-semibold text-white">{t('explore.aiMatchLabel')}</h3>
                  <p className="text-xs text-slate-400">
                    {searchSummary || t('explore.aiMatchSubtitle')}
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
                {t('explore.clearAllFilters')}
              </button>
            </div>
          </div>
        )}

        {/* Spaces Grid */}
        {loading ? (
          <SpaceCardGridSkeleton count={6} />
        ) : displaySpaces.length === 0 ? (
          <div className="py-20 text-center bg-slate-900/50 rounded-2xl border border-slate-800 p-8">
            <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4 text-2xl">
              📍
            </div>
            <h3 className="text-lg font-bold text-white mb-2">{t('explore.noSpacesFoundTitle')}</h3>
            <p className="text-xs text-slate-400 mb-6 max-w-sm mx-auto">
              {t('explore.noSpacesFoundDesc')}
            </p>
            <button
              onClick={resetAllFilters}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition"
            >
              {t('explore.filterAll')}
            </button>
          </div>
        ) : (
          <div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {visibleSpaces.map((space) => (
                <SpaceCard
                  key={space.id}
                  space={space}
                  onPress={(id) => navigate(`/space/${id}`)}
                />
              ))}
            </div>

            {/* Incremental Loading / Pagination Control */}
            {displaySpaces.length > visibleSpaces.length && (
              <div className="mt-10 pt-6 border-t border-slate-800/80 flex flex-col items-center justify-center gap-3">
                <div className="text-xs text-slate-400 font-medium">
                  {t('explore.showingSpaces', { count: visibleSpaces.length })}
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setVisibleCount((prev) => prev + PAGE_SIZE)}
                    className="px-6 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-100 hover:text-white text-xs sm:text-sm font-semibold border border-slate-700 hover:border-slate-600 transition shadow-sm flex items-center gap-2"
                  >
                    <i className="fa-solid fa-chevron-down text-xs text-indigo-400" />
                    <span>{t('common.viewMore')}</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
};
