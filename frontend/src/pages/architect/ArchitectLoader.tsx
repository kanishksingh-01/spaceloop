import React, { useEffect, useState } from 'react';

interface ArchitectLoaderProps {
  onComplete: () => void;
  prefersReducedMotion?: boolean;
}

/**
 * ArchitectLoader
 * ----------------------------------------------------------------------------
 * S P A C E   L O O P   Cinematic Loading Transition
 * - ONLY element visible: the SpaceLoop wordmark.
 * - Slower, deliberate, and premium duration (~1.8–2.0s total).
 * - Focus-in -> subtle scale pop -> stable wordmark -> continuous left-to-right glow sweep -> short hold -> smooth dissolve.
 * - Always runs on browser refresh (F5/Ctrl+R). Zero localStorage/sessionStorage suppression.
 * - Never restarts on React state changes, scroll, hover, or theme toggling.
 */
export const ArchitectLoader: React.FC<ArchitectLoaderProps> = ({
  onComplete,
  prefersReducedMotion = false,
}) => {
  const [isExiting, setIsExiting] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // If user prefers reduced motion, skip the animation immediately
    if (prefersReducedMotion) {
      setIsVisible(false);
      onComplete();
      return;
    }

    // Choreographed timing target (~1.9s - 2.05s total):
    // 0ms - 400ms: Wordmark subtle focus-in + slight scale pop to stable
    // 400ms - 1350ms: Smooth continuous left-to-right glow sweep across S P A C E   L O O P
    // 1350ms - 1500ms: Short illuminated hold with wordmark settled and crisp
    // 1500ms: Loader layer begins smooth dissolve into the Architect hero (480ms transition)
    // 2020ms: Loader fully dissolved, unmounts cleanly
    const exitTimer = setTimeout(() => {
      setIsExiting(true);
    }, 1500);

    const finishTimer = setTimeout(() => {
      setIsVisible(false);
      onComplete();
    }, 2020);

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
      {/* Restrained Ambient Radial Aura */}
      <div className="ag-loader-pulse-glow" />

      {/* S P A C E   L O O P Wordmark — The ONLY element visible during loading */}
      <div className="relative z-10 flex items-center justify-center ag-loader-wordmark">
        <div className="ag-wordmark-wrapper">
          {/* Base Crisp Wordmark */}
          <span className="ag-wordmark-text">
            S&nbsp;P&nbsp;A&nbsp;C&nbsp;E&nbsp;&nbsp;&nbsp;L&nbsp;O&nbsp;O&nbsp;P
          </span>

          {/* Continuous Left-to-Right Luminous Sweep */}
          <span className="ag-wordmark-sweep" aria-hidden="true">
            S&nbsp;P&nbsp;A&nbsp;C&nbsp;E&nbsp;&nbsp;&nbsp;L&nbsp;O&nbsp;O&nbsp;P
          </span>
        </div>
      </div>
    </div>
  );
};

export default ArchitectLoader;
