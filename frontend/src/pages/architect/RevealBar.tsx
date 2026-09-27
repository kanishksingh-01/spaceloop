import React from 'react';

interface RevealBarProps {
  x: number;
  y?: number;
  height?: number;
  isVisible: boolean;
  prefersReducedMotion?: boolean;
}

/**
 * RevealBar — High-Precision Optical Scanner Cursor Line
 * ----------------------------------------------------------------------------
 * Precision 2px optical cursor line with delicate, restrained halo and
 * micro trailing optical sheen. Follows active characters with GPU-accelerated
 * 3D transforms and smoothly reveals typography as it passes through.
 */
export const RevealBar: React.FC<RevealBarProps> = ({
  x,
  y = 0,
  height,
  isVisible,
  prefersReducedMotion = false,
}) => {
  if (prefersReducedMotion || !isVisible) {
    return null;
  }

  return (
    <div
      aria-hidden="true"
      className="ag-optical-cursor"
      style={{
        transform: `translate3d(${x}px, ${y}px, 0)`,
        height: height && height > 0 ? `${height}px` : '1.15em',
        opacity: isVisible ? 1 : 0,
      }}
    >
      {/* Precision Core Cursor Line (2px) */}
      <div className="ag-cursor-core" />
      {/* Delicate Trailing Optical Sheen */}
      <div className="ag-cursor-trail" />
    </div>
  );
};

export default RevealBar;
