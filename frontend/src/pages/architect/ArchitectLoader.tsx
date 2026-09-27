import React, { useEffect, useState } from 'react';
import { Sparkles } from 'lucide-react';

interface ArchitectLoaderProps {
  onComplete: () => void;
  prefersReducedMotion?: boolean;
}

export const ArchitectLoader: React.FC<ArchitectLoaderProps> = ({
  onComplete,
  prefersReducedMotion = false,
}) => {
  const [isExiting, setIsExiting] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // If reduced motion is requested, complete immediately without animation delay
    if (prefersReducedMotion) {
      setIsVisible(false);
      onComplete();
      return;
    }

    // Phase 1 -> Phase 2 (Settle and start exit dissolve at 750ms)
    const exitTimer = setTimeout(() => {
      setIsExiting(true);
    }, 750);

    // Phase 3 (Completely dissolve and unmount at 1050ms)
    const finishTimer = setTimeout(() => {
      setIsVisible(false);
      onComplete();
    }, 1050);

    return () => {
      clearTimeout(exitTimer);
      clearTimeout(finishTimer);
    };
  }, [onComplete, prefersReducedMotion]);

  if (!isVisible) return null;

  return (
    <div
      aria-hidden="true"
      className={`ag-loader-backdrop ${isExiting ? 'ag-loader-exit' : ''}`}
    >
      {/* Soft Ambient Radial Glow */}
      <div className="ag-loader-pulse-glow" />

      {/* SpaceLoop Wordmark & Initialization Telemetry */}
      <div className="relative z-10 flex flex-col items-center text-center px-4 ag-loader-wordmark">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#0B3D91]/10 dark:bg-white/10 border border-[#0B3D91]/20 dark:border-white/15 text-[#0B3D91] dark:text-cyan-400 text-[10px] font-mono font-bold tracking-widest uppercase mb-4 shadow-xs">
          <Sparkles className="w-3 h-3 text-[#3BA7F2] dark:text-cyan-400" />
          <span>SYSTEM CALIBRATION // 2026</span>
        </div>

        {/* SpaceLoop App Wordmark with Theme Gradients */}
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight font-display select-none">
          <span className="text-slate-900 dark:text-white">Space</span>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#0B3D91] via-[#1E40AF] to-[#3BA7F2] dark:from-cyan-400 dark:via-indigo-300 dark:to-violet-400">
            Loop
          </span>
        </h1>

        <div className="mt-3 flex items-center gap-2 text-xs font-mono font-medium text-slate-500 dark:text-slate-400">
          <span className="w-1.5 h-1.5 rounded-full bg-[#3BA7F2] dark:bg-cyan-400 animate-ping" />
          <span>INITIALIZING ARCHITECTURAL DIRECTORY</span>
        </div>
      </div>
    </div>
  );
};

export default ArchitectLoader;
