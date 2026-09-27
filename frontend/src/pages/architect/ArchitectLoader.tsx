import React, { useEffect, useState } from 'react';

interface ArchitectLoaderProps {
  onComplete: () => void;
  prefersReducedMotion?: boolean;
}

/**
 * ArchitectLoader — SpaceLoop Cinematic Floating Entrance
 * ----------------------------------------------------------------------------
 * - "SPACE LOOP" floating weightlessly in the open architectural canvas.
 * - NOT containerized in a loading page or separate splash box.
 * - Smooth, zero-gravity floating levitation (organic breathing motion).
 * - Subtle, refined metallic sheen across the letters (no harsh/blinding glow).
 * - Butter-smooth non-abrupt entrance and upward diffusion exit into the hero.
 * - Executes on every refresh (F5/Ctrl+R). Zero localStorage/sessionStorage suppression.
 */
export const ArchitectLoader: React.FC<ArchitectLoaderProps> = ({
  onComplete,
  prefersReducedMotion = false,
}) => {
  const [isExiting, setIsExiting] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (prefersReducedMotion) {
      setIsVisible(false);
      onComplete();
      return;
    }

    // Sequence Choreography:
    // 0ms - 750ms: Silk glide entrance with zero-gravity floating levitation
    // 750ms - 1750ms: Weightless floating state with subtle refined light sheen
    // 1750ms: Gentle upward levitation & soft atmospheric diffusion into hero (750ms transition)
    // 2500ms: Smoothly unmounts cleanly
    const exitTimer = setTimeout(() => {
      setIsExiting(true);
    }, 1750);

    const finishTimer = setTimeout(() => {
      setIsVisible(false);
      onComplete();
    }, 2500);

    return () => {
      clearTimeout(exitTimer);
      clearTimeout(finishTimer);
    };
  }, [onComplete, prefersReducedMotion]);

  if (!isVisible) return null;

  return (
    <div
      aria-hidden="true"
      className={`ag-entrance-layer ${isExiting ? 'ag-entrance-exit' : ''}`}
    >
      {/* Floating Wordmark in Open Canvas — Zero containerization */}
      <div className="ag-floating-wordmark-container">
        <div className="ag-floating-wordmark">
          {/* Base Crisp Wordmark */}
          <span className="ag-wordmark-text">
            SPACE LOOP
          </span>

          {/* Refined, non-blinding ambient sheen */}
          <span className="ag-wordmark-sheen" aria-hidden="true">
            SPACE LOOP
          </span>
        </div>
      </div>
    </div>
  );
};

export default ArchitectLoader;
