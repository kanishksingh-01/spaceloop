import React from 'react';

export const HostStatSkeleton: React.FC<{ count?: number }> = ({ count = 4 }) => {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 sm:p-5 space-y-3 animate-pulse"
        >
          <div className="flex items-center justify-between">
            <div className="h-3 w-20 bg-slate-800 rounded" />
            <div className="w-7 h-7 bg-slate-800 rounded-lg" />
          </div>
          <div className="h-6 w-28 bg-slate-800 rounded" />
          <div className="h-3 w-16 bg-slate-800/60 rounded" />
        </div>
      ))}
    </div>
  );
};

export const HostCardSkeleton: React.FC<{
  lines?: number;
  height?: string;
  className?: string;
}> = ({ lines = 3, height, className = '' }) => {
  return (
    <div
      className={`bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 space-y-4 animate-pulse ${height || ''} ${className}`}
    >
      <div className="flex items-center justify-between">
        <div className="h-4 w-36 bg-slate-800 rounded" />
        <div className="h-4 w-12 bg-slate-800/60 rounded" />
      </div>
      <div className="space-y-2.5 pt-2">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className="h-3 bg-slate-800/60 rounded"
            style={{ width: `${Math.max(40, 95 - i * 15)}%` }}
          />
        ))}
      </div>
    </div>
  );
};

export const HostTableSkeleton: React.FC<{
  rows?: number;
  columns?: number;
  cols?: number;
}> = ({ rows = 5, columns = 5, cols }) => {
  const actualCols = cols !== undefined ? cols : columns;
  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl overflow-hidden animate-pulse">
      <div className="p-4 border-b border-slate-800/80 flex items-center gap-4 bg-slate-950/40">
        {Array.from({ length: actualCols }).map((_, i) => (
          <div key={i} className="h-3 bg-slate-800 rounded flex-1" />
        ))}
      </div>
      <div className="divide-y divide-slate-800/50">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="p-4 flex items-center gap-4">
            {Array.from({ length: actualCols }).map((_, c) => (
              <div
                key={c}
                className="h-3.5 bg-slate-800/60 rounded flex-1"
                style={{ opacity: 1 - c * 0.1 }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export const HostDetailSkeleton: React.FC = () => {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-5 w-48 bg-slate-800 rounded" />
            <div className="h-3 w-32 bg-slate-800/60 rounded" />
          </div>
          <div className="h-8 w-24 bg-slate-800 rounded-xl" />
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 h-64" />
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 h-64" />
      </div>
    </div>
  );
};
