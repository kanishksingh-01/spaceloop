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

  return (
    <div
      aria-hidden="true"
      className="ag-reveal-scanner-bar"
      style={{
        left: `${Math.min(Math.max(leftPercent, 0), 100)}%`,
        opacity: isVisible && leftPercent < 100 ? 1 : 0,
        transform: 'translateX(-50%)',
      }}
    />
  );
};

export default RevealBar;
