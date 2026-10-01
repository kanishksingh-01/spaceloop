import React from 'react';

/**
 * SpaceCardSkeleton
 * Reflects the exact structure of SpaceCard to eliminate Layout Shifts (CLS)
 * during initial catalog loads and filter changes.
 */
export const SpaceCardSkeleton: React.FC = () => {
  return (
    <div className="flex flex-col bg-slate-900/90 border border-slate-800/80 rounded-2xl overflow-hidden animate-pulse">
      {/* Photo Container */}
      <div className="relative w-full aspect-[16/10] bg-slate-800/70 overflow-hidden">
        {/* Category Pill Tag Skeleton */}
        <div className="absolute top-3 left-3 w-20 h-5 bg-slate-700/80 rounded-lg" />
        {/* Match / Verified Pill Skeleton */}
        <div className="absolute top-3 right-3 w-16 h-5 bg-slate-700/80 rounded-full" />
        {/* Location Tag Skeleton */}
        <div className="absolute bottom-3 left-3 w-28 h-5 bg-slate-700/80 rounded-full" />
      </div>

      {/* Body Container */}
      <div className="p-4 sm:p-5 flex flex-col flex-grow justify-between gap-3.5">
        <div>
          {/* Title & Host row */}
          <div className="flex items-start justify-between gap-2 mb-2">
            <div className="h-5 bg-slate-800 rounded w-3/4" />
            <div className="h-4 bg-slate-800/80 rounded w-10" />
          </div>

          {/* Description line */}
          <div className="h-3.5 bg-slate-800/60 rounded w-full mb-1.5" />
          <div className="h-3.5 bg-slate-800/50 rounded w-4/5" />
        </div>

        {/* Feature Pills */}
        <div className="flex items-center gap-1.5 pt-1">
          <div className="h-4 bg-slate-800/70 rounded w-16" />
          <div className="h-4 bg-slate-800/70 rounded w-20" />
          <div className="h-4 bg-slate-800/70 rounded w-14" />
        </div>

        {/* Price & Rating Footer */}
        <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
          <div className="space-y-1">
            <div className="h-5 bg-slate-800 rounded w-20" />
            <div className="h-2.5 bg-slate-800/50 rounded w-14" />
          </div>
          <div className="h-8 bg-indigo-600/30 border border-indigo-500/30 rounded-xl w-24" />
        </div>
      </div>
    </div>
  );
};

export const SpaceCardGridSkeleton: React.FC<{ count?: number }> = ({ count = 6 }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <SpaceCardSkeleton key={i} />
      ))}
    </div>
  );
};

/**
 * SpaceDetailSkeleton
 * Reflects the exact 2-column layout of SpaceDetailPage.
 */
export const SpaceDetailSkeleton: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 antialiased pb-20 animate-pulse">
      {/* Top Breadcrumbs */}
      <div className="border-b border-slate-800/80 bg-slate-900/40 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="h-4 w-32 bg-slate-800 rounded" />
          <div className="h-4 w-24 bg-slate-800 rounded" />
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Left Column (2 Cols) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Title & Metadata */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="h-5 w-24 bg-slate-800 rounded-md" />
                <div className="h-5 w-32 bg-slate-800 rounded-md" />
              </div>
              <div className="h-8 w-3/4 bg-slate-800 rounded-lg" />
              <div className="h-4 w-1/2 bg-slate-800/60 rounded" />
            </div>

            {/* Photo Gallery Grid Skeleton */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 rounded-2xl overflow-hidden">
              <div className="sm:col-span-2 aspect-[16/10] bg-slate-800/80 rounded-xl" />
              <div className="grid grid-rows-2 gap-3">
                <div className="aspect-[16/10] bg-slate-800/70 rounded-xl" />
                <div className="aspect-[16/10] bg-slate-800/70 rounded-xl" />
              </div>
            </div>

            {/* Host Info Card Skeleton */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 rounded-xl bg-slate-800" />
                <div className="space-y-1.5">
                  <div className="h-4 w-28 bg-slate-800 rounded" />
                  <div className="h-3 w-40 bg-slate-800/60 rounded" />
                </div>
              </div>
              <div className="h-7 w-24 bg-slate-800 rounded-lg" />
            </div>

            {/* Space Highlights & Amenities Skeleton */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
              <div className="h-5 w-36 bg-slate-800 rounded" />
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-14 bg-slate-800/60 rounded-xl" />
                ))}
              </div>
              <div className="space-y-2 pt-2">
                <div className="h-3.5 bg-slate-800/50 rounded w-full" />
                <div className="h-3.5 bg-slate-800/50 rounded w-5/6" />
                <div className="h-3.5 bg-slate-800/50 rounded w-4/6" />
              </div>
            </div>
          </div>

          {/* Sidebar Right Column (1 Col) */}
          <div className="space-y-6">
            <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 space-y-5 sticky top-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="space-y-1">
                  <div className="h-7 w-28 bg-slate-800 rounded" />
                  <div className="h-3 w-20 bg-slate-800/50 rounded" />
                </div>
                <div className="h-6 w-16 bg-slate-800 rounded-full" />
              </div>

              {/* Time Slots & Duration Skeleton */}
              <div className="space-y-3">
                <div className="h-3 w-24 bg-slate-800 rounded" />
                <div className="grid grid-cols-2 gap-2">
                  <div className="h-10 bg-slate-800/80 rounded-xl" />
                  <div className="h-10 bg-slate-800/80 rounded-xl" />
                </div>
              </div>

              {/* Cost Summary Breakdown Skeleton */}
              <div className="space-y-2 bg-slate-950/60 p-4 rounded-xl border border-slate-800/60">
                <div className="flex justify-between">
                  <div className="h-3 w-24 bg-slate-800/60 rounded" />
                  <div className="h-3 w-12 bg-slate-800/60 rounded" />
                </div>
                <div className="flex justify-between">
                  <div className="h-3 w-28 bg-slate-800/60 rounded" />
                  <div className="h-3 w-16 bg-slate-800/60 rounded" />
                </div>
                <div className="pt-2 border-t border-slate-800 flex justify-between">
                  <div className="h-4 w-20 bg-slate-800 rounded" />
                  <div className="h-4 w-16 bg-slate-800 rounded" />
                </div>
              </div>

              {/* Button Skeleton */}
              <div className="h-12 bg-indigo-600/40 border border-indigo-500/30 rounded-xl w-full" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * LandingFeaturedSpacesSkeleton
 * Reflects the 3 featured space cards on the Landing Page.
 */
export const LandingFeaturedSpacesSkeleton: React.FC<{ count?: number }> = ({ count = 3 }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-slate-950/90 border border-slate-800/80 rounded-3xl overflow-hidden flex flex-col"
        >
          <div className="relative aspect-[16/10] bg-slate-800/70">
            <div className="absolute top-3 left-3 w-20 h-5 bg-slate-700/80 rounded-xl" />
            <div className="absolute top-3 right-3 w-16 h-5 bg-slate-700/80 rounded-xl" />
          </div>
          <div className="p-5 flex flex-col flex-grow space-y-3">
            <div className="h-3 w-28 bg-slate-800 rounded" />
            <div className="h-5 w-3/4 bg-slate-800 rounded" />
            <div className="h-3 bg-slate-800/60 rounded w-full" />
            <div className="h-3 bg-slate-800/50 rounded w-4/5" />
            <div className="pt-3 border-t border-slate-800/80 flex justify-between">
              <div className="h-3 w-16 bg-slate-800/60 rounded" />
              <div className="h-3 w-16 bg-slate-800/60 rounded" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * DashboardBookingSkeleton
 * Prevents flash of empty state in Dashboard when bookings are loading.
 */
export const DashboardBookingSkeleton: React.FC<{ count?: number }> = ({ count = 2 }) => {
  return (
    <div className="space-y-4 animate-pulse">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="p-5 bg-slate-900/80 border border-slate-800 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
        >
          <div className="flex items-center gap-4 flex-1">
            <div className="w-20 h-20 rounded-xl bg-slate-800 shrink-0" />
            <div className="space-y-2 flex-1">
              <div className="flex items-center gap-2">
                <div className="h-5 w-44 bg-slate-800 rounded" />
                <div className="h-4 w-16 bg-slate-800/70 rounded" />
              </div>
              <div className="h-3.5 w-60 bg-slate-800/60 rounded" />
              <div className="h-3.5 w-36 bg-slate-800/50 rounded" />
            </div>
          </div>
          <div className="flex items-center gap-2 self-end md:self-auto">
            <div className="h-9 w-24 bg-slate-800 rounded-xl" />
            <div className="h-9 w-20 bg-slate-800 rounded-xl" />
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * SessionPageSkeleton
 * Reflects the live in-room session console layout.
 */
export const SessionPageSkeleton: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-20 animate-pulse">
      {/* Top Breadcrumb */}
      <div className="border-b border-slate-800/80 bg-slate-900/40 px-4 py-3.5 sticky top-0 z-20">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="h-4 w-32 bg-slate-800 rounded" />
          <div className="h-6 w-28 bg-slate-800 rounded-full" />
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 space-y-6">
        {/* Header Space Summary Skeleton */}
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-3xl p-6 sm:p-8 space-y-4">
          <div className="flex gap-2">
            <div className="h-5 w-20 bg-slate-800 rounded-full" />
            <div className="h-5 w-28 bg-slate-800 rounded-full" />
          </div>
          <div className="h-8 w-2/3 bg-slate-800 rounded-lg" />
          <div className="h-4 w-1/3 bg-slate-800/60 rounded" />
        </div>

        {/* Live Timer & Access Controls Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 space-y-4">
            <div className="h-4 w-28 bg-slate-800 rounded" />
            <div className="h-16 w-48 bg-slate-800 rounded-2xl mx-auto" />
            <div className="h-3 w-40 bg-slate-800/60 rounded mx-auto" />
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 space-y-4">
            <div className="h-4 w-32 bg-slate-800 rounded" />
            <div className="h-28 w-28 bg-slate-800 rounded-2xl mx-auto" />
            <div className="h-9 bg-slate-800 rounded-xl w-full" />
          </div>
        </div>
      </div>
    </div>
  );
};
