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
    { label: t('explore.filterAll') || 'All Spaces', icon: 'fa-border-all', value: 'All' },
    { label: t('explore.filterDesk') || 'Desks & Workstations', icon: 'fa-laptop-code', value: 'Workspace', color: 'text-indigo-500 dark:text-indigo-400' },
    { label: t('explore.filterMeeting') || 'Meeting Rooms', icon: 'fa-handshake', value: 'Meeting', color: 'text-blue-500 dark:text-blue-400' },
    { label: t('explore.filterStudio') || 'Podcast & Photo Studios', icon: 'fa-microphone-lines', value: 'Studio', color: 'text-purple-500 dark:text-purple-400' },
    { label: t('landing.studyCategory') || 'Workshops', icon: 'fa-screwdriver-wrench', value: 'Workshop', color: 'text-amber-500 dark:text-amber-400' },
    { label: t('landing.spacesTitle') || 'Retail', icon: 'fa-store', value: 'Retail', color: 'text-pink-500 dark:text-pink-400' },
    { label: t('explore.filterStorage') || 'Storage', icon: 'fa-boxes-stacked', value: 'Storage', color: 'text-yellow-500 dark:text-yellow-400' },
    { label: t('explore.filterStudy') || 'Quiet Study Pods', icon: 'fa-book-open', value: 'Study', color: 'text-emerald-500 dark:text-emerald-400' },
    { label: t('explore.filterEvent') || 'Event Spaces', icon: 'fa-users', value: 'Event', color: 'text-cyan-500 dark:text-cyan-400' },
  ];

  const quickHubs = [
    { label: 'Wagholi, Pune', loc: 'Wagholi, Pune', lat: 18.5793, lng: 73.9822 },
    { label: 'IIT Delhi / Hauz Khas', loc: 'Hauz Khas, New Delhi', lat: 28.5450, lng: 77.1926 },
    { label: 'Koramangala, Bangalore', loc: 'Koramangala, Bangalore', lat: 12.9352, lng: 77.6245 },
    { label: 'Shivajinagar / FC Road', loc: 'Shivajinagar, Pune', lat: 18.5204, lng: 73.8567 },
    { label: 'DU North Campus', loc: 'North Campus, New Delhi', lat: 28.6900, lng: 77.2100 },
    { label: 'Sector 62, Noida', loc: 'Sector 62, Noida', lat: 28.6270, lng: 77.3725 },
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
    if (!q.trim() && !locationInput.trim()) {
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
        query: q || 'any space',
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
      const fallback = await getSpaces({ q, city: locationInput.trim() || undefined });
      setSpaces(fallback);
      setExtractedConstraints({});
      setSearchSummary(`Showing results for "${q || locationInput}"`);
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
        setLocationInput(`${pos.coords.latitude.toFixed(3)}, ${pos.coords.longitude.toFixed(3)}`);
        fetchSpaces({ lat: pos.coords.latitude, lng: pos.coords.longitude, loc: `${pos.coords.latitude.toFixed(3)}, ${pos.coords.longitude.toFixed(3)}` });
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
    fetchSpaces({ category: 'All', loc: '', q: '', radius: '', maxPrice: '', lat: null, lng: null });
  };

  const hasActiveFilters = Boolean(
    searchQuery ||
    locationInput ||
    (selectedRadius && selectedRadius !== 'All') ||
    selectedMaxPrice ||
    activeCategory !== 'All' ||
    aiMatchActive
  );

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col antialiased">
      {/* 1. HERO & PRIMARY DISCOVERY SEARCH ENGINE */}
      <section className="bg-white dark:bg-slate-900/60 border-b border-slate-200 dark:border-slate-800/80 pt-10 pb-8 sm:pt-14 sm:pb-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Headline & Subtitle */}
          <div className="text-center max-w-2xl mx-auto mb-8">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800/60 text-indigo-700 dark:text-indigo-300 text-xs font-medium mb-3.5">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 dark:bg-indigo-400" />
              <span>{t('explore.aiMatchLabel')}</span>
              <span className="text-slate-300 dark:text-slate-700">•</span>
              <span className="text-slate-600 dark:text-slate-400">{t('common.availableNow')}</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 dark:text-white leading-tight">
              {t('explore.title')}
            </h1>

            <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-slate-300 leading-relaxed max-w-xl mx-auto">
              {t('explore.subtitle')}
            </p>
          </div>

          {/* Unified Discovery Search Component */}
          <div className="max-w-4xl mx-auto">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAiSearch();
              }}
              className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700/80 rounded-2xl shadow-sm hover:border-indigo-400 dark:hover:border-indigo-500/60 transition-all p-2 flex flex-col md:flex-row items-stretch md:items-center gap-2"
            >
              {/* Keyword / Vibe Input Segment */}
              <div className="flex-1 flex items-center gap-3 px-3 py-2">
                <i className="fa-solid fa-wand-magic-sparkles text-indigo-500 dark:text-indigo-400 text-sm shrink-0" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={t('explore.searchPlaceholder')}
                  className="w-full bg-transparent border-none text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-0"
                />
              </div>

              {/* Subtle Hairline Vertical Divider */}
              <div className="hidden md:block w-px h-8 bg-slate-200 dark:bg-slate-800 shrink-0" />

              {/* Location Input Segment with GPS */}
              <div className="flex-1 flex items-center gap-2 px-3 py-2">
                <i className="fa-solid fa-location-dot text-slate-400 dark:text-slate-500 text-sm shrink-0" />
                <input
                  type="text"
                  value={locationInput}
                  onChange={(e) => setLocationInput(e.target.value)}
                  placeholder={t('explore.filterLocation') + ' (e.g. Pune, Hauz Khas)'}
                  className="w-full bg-transparent border-none text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-0"
                />
                <button
                  type="button"
                  onClick={detectCurrentLocation}
                  className="shrink-0 text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-white bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-750 px-2.5 py-1.5 rounded-lg flex items-center gap-1.5 transition"
                  title="Detect my current location"
                >
                  <i className="fa-solid fa-crosshairs text-indigo-500 text-xs" />
                  <span className="hidden sm:inline">GPS</span>
                </button>
              </div>

              {/* Search Submit CTA Button */}
              <button
                type="submit"
                disabled={isAiSearching}
                className="bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white font-medium text-sm px-6 py-3 rounded-xl transition flex items-center justify-center gap-2 shrink-0 disabled:opacity-60 shadow-sm"
              >
                {isAiSearching ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>{t('common.loading')}</span>
                  </>
                ) : (
                  <>
                    <span>{t('common.search')}</span>
                    <i className="fa-solid fa-arrow-right text-xs" />
                  </>
                )}
              </button>
            </form>

            {/* Popular Location Suggestions */}
            <div className="mt-3.5 px-2 flex items-center gap-2 text-xs flex-wrap">
              <span className="text-slate-500 dark:text-slate-400 font-medium shrink-0">
                Popular:
              </span>
              {quickHubs.map((hub, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectQuickHub(hub)}
                  className="text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-300 font-medium transition py-0.5 px-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800/80"
                >
                  {hub.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 2. MAIN EXPLORER: CATEGORIES, FILTERS & LISTINGS */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        {/* Category Navigation Bar & Space Counter Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 mb-6 border-b border-slate-200 dark:border-slate-800">
          {/* Category Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
            {categories.map((cat) => {
              const isSelected = activeCategory === cat.value;
              return (
                <button
                  key={cat.value}
                  type="button"
                  onClick={() => handleSelectCategory(cat.value)}
                  className={`px-3.5 py-2 rounded-lg text-xs sm:text-sm font-medium transition whitespace-nowrap flex items-center gap-2 ${
                    isSelected
                      ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/70'
                  }`}
                >
                  <i className={`fa-solid ${cat.icon} text-xs ${isSelected ? '' : cat.color || ''}`} />
                  <span>{cat.label}</span>
                </button>
              );
            })}
          </div>

          {/* Results Count & Verified Telemetry Badge */}
          <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 shrink-0 self-end md:self-auto">
            <span className="font-medium text-slate-700 dark:text-slate-300">
              {displaySpaces.length} {t('explore.foundSpaces')}
            </span>
            <span className="w-1 h-1 rounded-full bg-slate-300 dark:bg-slate-700" />
            <span className="flex items-center gap-1 font-semibold text-emerald-600 dark:text-emerald-400">
              <i className="fa-solid fa-shield-check" /> {t('common.verified')}
            </span>
          </div>
        </div>

        {/* Secondary Filter Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-3 mb-8">
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Distance / Radius Select */}
            <div className="flex items-center gap-1.5 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-lg px-3 py-1.5 text-xs shadow-xs">
              <i className="fa-solid fa-ruler-combined text-slate-400 text-xs" />
              <span className="text-slate-500 dark:text-slate-400 font-medium">Distance:</span>
              <select
                value={selectedRadius}
                onChange={(e) => handleRadiusChange(e.target.value)}
                className="bg-transparent border-none text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer pl-1 pr-2 py-0.5"
              >
                <option value="" className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">{t('common.all')}</option>
                <option value="1" className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">Within 1 km</option>
                <option value="3" className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">Within 3 km</option>
                <option value="5" className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">Within 5 km</option>
                <option value="10" className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">Within 10 km</option>
              </select>
            </div>

            {/* Price Filter Select */}
            <div className="flex items-center gap-1.5 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-lg px-3 py-1.5 text-xs shadow-xs">
              <i className="fa-solid fa-indian-rupee-sign text-slate-400 text-xs" />
              <span className="text-slate-500 dark:text-slate-400 font-medium">Max Rate:</span>
              <select
                value={selectedMaxPrice}
                onChange={(e) => handleMaxPriceChange(e.target.value)}
                className="bg-transparent border-none text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer pl-1 pr-2 py-0.5"
              >
                <option value="" className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">{t('common.all')}</option>
                <option value="60" className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">{formatCurrency(60)}/hr</option>
                <option value="80" className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">{formatCurrency(80)}/hr</option>
                <option value="100" className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">{formatCurrency(100)}/hr</option>
                <option value="150" className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">{formatCurrency(150)}/hr</option>
                <option value="200" className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">{formatCurrency(200)}/hr</option>
              </select>
            </div>
          </div>

          {/* Reset Filters CTA */}
          {hasActiveFilters && (
            <button
              type="button"
              onClick={resetAllFilters}
              className="text-xs font-medium text-slate-600 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 flex items-center gap-1.5 py-1 px-2.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800/80 transition"
            >
              <i className="fa-solid fa-rotate-left text-[11px]" />
              <span>{t('common.reset') || 'Reset filters'}</span>
            </button>
          )}
        </div>

        {/* AI Matching Banner */}
        {aiMatchActive && (
          <div className="mb-6 p-4 rounded-xl bg-indigo-50/80 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800/60 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-600/10 dark:bg-indigo-600/30 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0">
                <i className="fa-solid fa-wand-magic-sparkles text-sm" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-900 dark:text-white">{t('explore.aiMatchLabel')}</h3>
                <p className="text-xs text-slate-600 dark:text-slate-400">
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
              className="text-xs text-indigo-700 dark:text-indigo-300 hover:text-indigo-900 dark:hover:text-white font-medium px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-indigo-200 dark:border-indigo-800/80 shrink-0 shadow-xs"
            >
              {t('explore.clearAllFilters')}
            </button>
          </div>
        )}

        {/* Spaces Grid */}
        {loading ? (
          <SpaceCardGridSkeleton count={6} />
        ) : displaySpaces.length === 0 ? (
          <div className="py-20 text-center bg-white dark:bg-slate-900/50 rounded-2xl border border-slate-200 dark:border-slate-800 p-8 max-w-lg mx-auto">
            <div className="w-14 h-14 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto mb-4 text-2xl text-slate-400">
              <i className="fa-solid fa-magnifying-glass text-xl" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">{t('explore.noSpacesFoundTitle')}</h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 mb-6 max-w-sm mx-auto">
              {t('explore.noSpacesFoundDesc')}
            </p>
            <button
              onClick={resetAllFilters}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg transition shadow-xs"
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
              <div className="mt-12 pt-6 border-t border-slate-200 dark:border-slate-800 flex flex-col items-center justify-center gap-3">
                <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                  {t('explore.showingSpaces', { count: visibleSpaces.length })}
                </div>
                <button
                  type="button"
                  onClick={() => setVisibleCount((prev) => prev + PAGE_SIZE)}
                  className="px-6 py-2.5 rounded-lg bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs sm:text-sm font-semibold border border-slate-300 dark:border-slate-700 transition shadow-xs flex items-center gap-2"
                >
                  <i className="fa-solid fa-chevron-down text-xs text-indigo-500" />
                  <span>{t('common.viewMore')}</span>
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};
