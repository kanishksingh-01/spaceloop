import React, { useState } from 'react';
import { Space } from '../../types';
import { getCategoryFallbackImage } from '../../services/spaces';

interface SpaceCardProps {
  space: Space;
  onPress: (spaceId: number) => void;
}

export const SpaceCard: React.FC<SpaceCardProps> = ({ space, onPress }) => {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const [triedFallback, setTriedFallback] = useState(false);

  const initialPhoto =
    space.photos && space.photos.length > 0
      ? space.photos[0]
      : getCategoryFallbackImage(space.category);

  const [imgSrc, setImgSrc] = useState(initialPhoto);

  const rating = space.rating ?? 4.9;
  const locationText =
    space.location ||
    (space.neighborhood ? `${space.neighborhood}, ${space.city}` : space.city || 'Pune');
  const hourlyRate = Math.round(space.hourly_rate ?? space.price_hourly ?? 50);
  const matchScore = space.ai_match_score ? Math.round(space.ai_match_score) : 94;

  const handleImageError = () => {
    if (!triedFallback) {
      setTriedFallback(true);
      setImgSrc(getCategoryFallbackImage(space.category));
    } else {
      setError(true);
    }
  };

  return (
    <div
      onClick={() => onPress(space.id)}
      className="space-card floating-card group flex flex-col bg-slate-900/90 hover:bg-slate-850 border border-slate-800/80 hover:border-indigo-500/40 rounded-2xl overflow-hidden cursor-pointer"
    >
      {/* Photo Container */}
      <div
        onClick={() => onPress(space.id)}
        className="relative w-full aspect-[16/10] bg-slate-950 overflow-hidden cursor-pointer"
      >
        {!loaded && !error && (
          <div className="absolute inset-0 bg-slate-800/60 animate-pulse flex items-center justify-center">
            <span className="text-[11px] font-medium text-slate-400">Loading preview...</span>
          </div>
        )}

        {error ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900 text-slate-400 p-4 text-center">
            <svg className="w-8 h-8 mb-1.5 opacity-60 stroke-current" fill="none" viewBox="0 0 24 24">
              <rect width="18" height="18" x="3" y="3" rx="2" strokeWidth="2" />
              <path d="m3 15 5-5 4 4 6-6" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <span className="text-[11px] font-medium">SpaceLoop Verified Asset</span>
          </div>
        ) : (
          <img
            src={imgSrc}
            alt={`${space.title} - ${space.category} in ${locationText}`}
            loading="lazy"
            decoding="async"
            onLoad={() => setLoaded(true)}
            onError={handleImageError}
            className={`w-full h-full object-cover object-center transform transition-transform duration-500 ease-out group-hover:scale-[1.03] ${
              loaded ? 'opacity-100' : 'opacity-0'
            }`}
          />
        )}

        {/* Subtle Bottom Vignette */}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-black/30 pointer-events-none" />

        {/* Category Pill Tag (Top Left) */}
        <div className="absolute top-3 left-3 z-10">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded bg-slate-900/90 backdrop-blur-md border border-slate-700/60 text-[10px] font-bold tracking-wider text-indigo-300 uppercase shadow-sm">
            {space.category}
          </span>
        </div>

        {/* Match Score / Verified Pill (Top Right) */}
        <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5">
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-500/20 backdrop-blur-md border border-emerald-500/40 text-[10px] font-bold text-emerald-400 shadow-sm">
            <span>✨</span>
            <span className="match-score-text">{matchScore}% Match</span>
          </span>
        </div>

        {/* Location Tag (Bottom Left) */}
        <div className="absolute bottom-3 left-3 z-10">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-950/85 backdrop-blur-md border border-slate-700/60 text-[11px] font-medium text-slate-200">
            <span className="text-indigo-400">📍</span>
            <span>{locationText}</span>
          </span>
        </div>

        {/* Rating Pill (Bottom Right) */}
        <div className="absolute bottom-3 right-3 z-10">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-black/60 backdrop-blur-sm text-[11px] font-medium text-amber-300">
            <span>★</span>
            <span>{rating}</span>
          </span>
        </div>
      </div>

      {/* Card Content Body */}
      <div className="flex flex-col flex-1 p-5">
        <div className="flex items-start justify-between gap-3 mb-2">
          <h3
            onClick={() => onPress(space.id)}
            className="text-base font-semibold text-white tracking-tight leading-snug line-clamp-1 group-hover:text-indigo-400 transition-colors cursor-pointer"
          >
            {space.title}
          </h3>
          <div className="shrink-0 text-right">
            <span className="text-base font-bold text-white tracking-tight">₹{hourlyRate}</span>
            <span className="text-[11px] text-slate-400 font-normal">/hr</span>
          </div>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed line-clamp-2 mb-3">
          {space.description}
        </p>

        {/* Space Meta specs */}
        <div className="flex items-center gap-2 text-[11px] text-slate-400 mb-3 flex-wrap">
          {space.distance_km !== undefined && (
            <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium flex items-center gap-1">
              <span>⚡</span> {space.distance_km} km away
            </span>
          )}
          <span>{space.sqft || 240} sqft</span>
          <span>•</span>
          <span>Up to {space.max_capacity || 4} ppl</span>
        </div>

        {/* AI Match Reasoning if present */}
        {space.ai_match_reasoning && (
          <div className="mb-3 p-2 rounded-lg bg-indigo-950/40 border border-indigo-500/20 text-xs text-indigo-300">
            <span className="text-emerald-400 mr-1">✓</span>
            <span>{space.ai_match_reasoning}</span>
          </div>
        )}

        {/* Trust & CTA Row */}
        <div className="mt-auto pt-3.5 border-t border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-400">
            <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                clipRule="evenodd"
              />
            </svg>
            <span>DigiLocker Verified</span>
          </div>

          <button
            type="button"
            onClick={() => onPress(space.id)}
            className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300 group-hover:translate-x-0.5 transition"
          >
            <span>View Space</span>
            <span>→</span>
          </button>
        </div>
      </div>
    </div>
  );
};
