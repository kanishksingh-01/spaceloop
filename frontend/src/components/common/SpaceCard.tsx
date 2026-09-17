import React, { useState } from 'react';
import { View, Text, Pressable, Image } from 'react-native';
import { Space } from '../../types';
import { getCategoryFallbackImage } from '../../services/spaces';

interface SpaceCardProps {
  space: Space;
  onPress: (spaceId: number) => void;
}

export const SpaceCard: React.FC<SpaceCardProps> = ({ space, onPress }) => {
  const [imgSrc, setImgSrc] = useState(
    space.photos && space.photos.length > 0 ? space.photos[0] : getCategoryFallbackImage(space.category)
  );

  const rating = space.rating ?? 4.9;
  const locationText = space.location || (space.neighborhood ? `${space.neighborhood}, ${space.city}` : space.city || 'Pune');
  const hourlyRate = Math.round(space.hourly_rate ?? space.price_hourly ?? 50);
  const dailyRate = space.daily_rate ?? space.price_daily ? Math.round(space.daily_rate ?? space.price_daily ?? 0) : hourlyRate * 6;
  const matchScore = space.ai_match_score ? Math.round(space.ai_match_score) : 94;

  return (
    <div className="space-card group bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden hover:border-indigo-500/50 transition-all duration-300 flex flex-col hover:shadow-xl hover:shadow-indigo-950/40">
      {/* Image Card Header */}
      <div
        onClick={() => onPress(space.id)}
        className="relative aspect-[16/10] overflow-hidden bg-slate-950 cursor-pointer"
      >
        <img
          src={imgSrc}
          alt={space.title}
          onError={() => setImgSrc(getCategoryFallbackImage(space.category))}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-transparent to-black/30" />

        {/* Category & Verified Badges (Top Left) */}
        <div className="absolute top-3 left-3 flex items-center gap-1.5">
          <span className="px-2.5 py-1 rounded-lg text-xs font-semibold backdrop-blur-md bg-slate-900/80 text-white border border-white/10 shadow-sm">
            {space.category}
          </span>
          {(space.host_verified !== false) && (
            <span
              className="px-2 py-1 rounded-lg text-[10px] font-bold backdrop-blur-md bg-emerald-600/90 text-white shadow-sm flex items-center gap-1"
              title="SpaceLoop Verified Host"
            >
              <i className="fa-solid fa-shield-check" /> Verified
            </span>
          )}
        </div>

        {/* Match Score Pill (Top Right) */}
        <div className="absolute top-3 right-3 match-badge-container">
          <span className="px-2.5 py-1 rounded-lg text-xs font-bold backdrop-blur-md bg-emerald-500/90 text-white shadow-sm flex items-center gap-1">
            <i className="fa-solid fa-sparkles text-[10px]" />
            <span className="match-score-text">{matchScore}%</span> Match
          </span>
        </div>

        {/* Price overlay at bottom of photo */}
        <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between">
          <div>
            <span className="text-2xl font-extrabold text-white">₹{hourlyRate}</span>
            <span className="text-xs text-slate-300 font-medium">/hour</span>
            <span className="text-xs text-slate-400 ml-1.5">• ₹{dailyRate}/day</span>
          </div>
          <div className="text-xs text-slate-300 flex items-center gap-1 font-medium bg-black/40 px-2 py-0.5 rounded backdrop-blur-sm">
            <i className="fa-solid fa-star text-amber-400 text-[11px]" /> {rating}
          </div>
        </div>
      </div>

      {/* Space Content Body */}
      <div className="p-5 flex flex-col flex-grow">
        <div className="flex items-center gap-2 text-xs text-slate-400 mb-1.5 flex-wrap">
          <span className="flex items-center gap-1">
            <i className="fa-solid fa-location-dot text-indigo-400" />
            <span>{locationText}, {space.state || 'India'}</span>
          </span>
          {space.distance_km !== undefined && (
            <>
              <span>•</span>
              <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 flex items-center gap-1">
                <i className="fa-solid fa-location-arrow text-[10px] text-indigo-400" /> {space.distance_km} km
              </span>
            </>
          )}
          <span>•</span>
          <span>{space.sqft || 250} sqft</span>
          <span>•</span>
          <span>Up to {space.max_capacity || 4} ppl</span>
        </div>

        <h3
          onClick={() => onPress(space.id)}
          className="text-base font-bold text-white group-hover:text-indigo-300 transition line-clamp-1 mb-2 cursor-pointer"
        >
          {space.title}
        </h3>

        <p className="text-xs text-slate-400 line-clamp-2 mb-4 flex-grow leading-relaxed">
          {space.description}
        </p>

        {/* AI Space Highlights */}
        <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800/80 mb-4 space-y-1.5 text-xs">
          <div className="flex items-center gap-2 text-slate-300">
            <i className="fa-solid fa-sun text-amber-400 w-4 text-center" />
            <span className="text-slate-400 truncate">Natural daylight window + neutral-white LED</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <i className="fa-solid fa-volume-xmark text-cyan-400 w-4 text-center" />
            <span className="text-slate-400 truncate">Ultra Quiet (&lt;35 dB ambient)</span>
          </div>
        </div>

        {/* Dynamic Match Reason (Shown on AI search) */}
        {space.ai_match_reasoning && (
          <div className="mb-3 p-2 rounded-lg bg-indigo-950/40 border border-indigo-500/20 text-xs text-indigo-300">
            <i className="fa-solid fa-check text-emerald-400 mr-1" />
            <span>{space.ai_match_reasoning}</span>
          </div>
        )}

        {/* Action Footer with Verification Indicator */}
        <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-3">
          <span className="text-[11px] text-slate-400 flex items-center gap-1">
            <i className="fa-solid fa-circle-check text-emerald-400 text-xs" />
            <span className="text-slate-300 font-medium">Verified</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-500 font-mono">OTI 99.2</span>
          </span>
          <button
            type="button"
            onClick={() => onPress(space.id)}
            className="px-3.5 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 text-xs font-semibold transition"
          >
            View & Book Space
          </button>
        </div>
      </div>
    </div>
  );
};
