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

  const isTopMatch = space.ai_match_score !== undefined && space.ai_match_score !== null && space.ai_match_score >= 80;

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
      role="button"
      tabIndex={0}
      aria-label={`View space ${space.title}`}
      onClick={() => onPress(space.id)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onPress(space.id);
        }
      }}
      className="group flex flex-col bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-xl overflow-hidden cursor-pointer transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
    >
      {/* Photo Container */}
      <div className="relative w-full aspect-[16/10] bg-slate-950 overflow-hidden">
        {!loaded && !error && (
          <div className="absolute inset-0 bg-slate-800/40 animate-pulse" />
        )}

        {error ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900 text-slate-500 text-xs">
            <i className="fa-solid fa-image text-xl mb-1 text-slate-600" />
            <span>Space Photo</span>
          </div>
        ) : (
          <img
            src={imgSrc}
            alt={space.title}
            loading="lazy"
            decoding="async"
            onLoad={() => setLoaded(true)}
            onError={handleImageError}
            className={`w-full h-full object-cover transition-transform duration-300 group-hover:scale-105 ${
              loaded ? 'opacity-100' : 'opacity-0'
            }`}
          />
        )}

        {/* Top Badges (Subtle & Clean) */}
        <div className="absolute top-2.5 left-2.5 right-2.5 flex items-center justify-between pointer-events-none">
          <span className="px-2 py-0.5 rounded bg-slate-900/90 backdrop-blur-sm border border-slate-800 text-[10px] font-semibold text-slate-200">
            {space.category || 'Workspace'}
          </span>

          {isTopMatch ? (
            <span className="px-2 py-0.5 rounded bg-indigo-600/90 text-white text-[10px] font-bold shadow-sm">
              ✨ Top Match
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-900/90 backdrop-blur-sm text-[10px] font-bold text-amber-300">
              <span>★</span> {rating}
            </span>
          )}
        </div>
      </div>

      {/* Content Body */}
      <div className="p-4 flex flex-col flex-1 justify-between gap-3">
        <div>
          {/* Header Row: Title & Price */}
          <div className="flex items-start justify-between gap-2 mb-1">
            <h3 className="text-sm font-bold text-white group-hover:text-indigo-400 transition-colors line-clamp-1">
              {space.title}
            </h3>
            <div className="text-right shrink-0">
              <span className="text-sm font-extrabold text-white">₹{hourlyRate}</span>
              <span className="text-[11px] text-slate-400 font-normal">/hr</span>
            </div>
          </div>

          {/* Location */}
          <p className="text-xs text-slate-400 line-clamp-1 mb-2">
            <i className="fa-solid fa-location-dot text-slate-500 text-[10px] mr-1" />
            {locationText}
          </p>

          {/* Description */}
          <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed mb-3">
            {space.description}
          </p>

          {/* Specs Ribbon */}
          <div className="flex items-center gap-2 text-[11px] text-slate-400 flex-wrap">
            {space.distance_km !== undefined && (
              <span className="px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300 font-medium">
                {space.distance_km} km away
              </span>
            )}
            <span>{space.sqft || 240} sqft</span>
            <span>•</span>
            <span>Up to {space.max_capacity || 4} ppl</span>
          </div>

          {/* AI Match Explanation */}
          {space.ai_match_reasoning && (
            <div className="mt-3 p-2.5 rounded-lg bg-indigo-950/40 border border-indigo-500/20 text-xs">
              <div className="flex items-center gap-1 text-indigo-300 font-semibold text-[11px] mb-0.5">
                <i className="fa-solid fa-sparkles text-[10px]" />
                <span>Match reasoning:</span>
              </div>
              <p className="text-[11px] text-slate-300 leading-normal line-clamp-2">
                {space.ai_match_reasoning}
              </p>
            </div>
          )}
        </div>

        {/* Footer Row */}
        <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400">
            <i className="fa-solid fa-shield-halved text-[10px]" />
            <span>DigiLocker Verified</span>
          </span>

          <span className="font-semibold text-indigo-400 group-hover:text-indigo-300 flex items-center gap-1 transition">
            <span>View Space</span>
            <i className="fa-solid fa-arrow-right text-[10px] group-hover:translate-x-0.5 transition-transform" />
          </span>
        </div>
      </div>
    </div>
  );
};
