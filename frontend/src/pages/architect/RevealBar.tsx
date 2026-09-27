import React from 'react';

interface RevealBarProps {
  leftPercent: number; // 0 to 100
  isVisible: boolean;
  prefersReducedMotion?: boolean;
}

export const RevealBar: React.FC<RevealBarProps> = ({
  leftPercent,
  isVisible,
  prefersReducedMotion = false,
}) => {
  if (prefersReducedMotion || !isVisible) {
    return null;
  }

  const clampedPercent = Math.min(Math.max(leftPercent, 0), 100);

  return (
    <div
      aria-hidden="true"
      className="ag-reveal-scanner-container"
      style={{
        left: `${clampedPercent}%`,
        opacity: isVisible && clampedPercent < 100 ? 1 : 0,
      }}
    >
      {/* Soft Blurred Duplicate / Glow Layer */}
      <div className="ag-reveal-scanner-glow" />
      {/* 1.5px Razor-Thin Crisp Scanner Core Line */}
      <div className="ag-reveal-scanner-core" />
    </div>
  );
};

export default RevealBar;
