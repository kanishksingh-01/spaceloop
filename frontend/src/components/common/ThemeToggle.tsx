import React from 'react';
import { useTheme } from '../../context/ThemeContext';

interface ThemeToggleProps {
  variant?: 'compact' | 'pill' | 'switch';
  className?: string;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ variant = 'pill', className = '' }) => {
  const { theme, toggleTheme } = useTheme();

  if (variant === 'compact') {
    return (
      <button
        type="button"
        onClick={toggleTheme}
        className={`p-2 rounded-xl border transition-colors flex items-center justify-center ${
          theme === 'dark'
            ? 'bg-slate-800/80 border-slate-700/60 text-amber-400 hover:bg-slate-700'
            : 'bg-white border-[#D0E6F7] text-[#0B3D91] hover:bg-[#E8F6FF]'
        } ${className}`}
        title={theme === 'dark' ? 'Switch to Light Theme (Ocean Breeze)' : 'Switch to Dark Theme (Midnight Neon)'}
        aria-label="Toggle Theme"
      >
        {theme === 'dark' ? (
          <i className="fa-solid fa-sun text-sm" />
        ) : (
          <i className="fa-solid fa-moon text-sm text-[#0B3D91]" />
        )}
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition shadow-sm border ${
        theme === 'dark'
          ? 'bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border-slate-700/60'
          : 'bg-white hover:bg-[#E8F6FF] text-[#0B2545] hover:text-[#0B3D91] border-[#D0E6F7]'
      } ${className}`}
      title={theme === 'dark' ? 'Switch to Light Theme (Ocean Breeze)' : 'Switch to Dark Theme (Midnight Neon)'}
      aria-label="Toggle Theme"
    >
      {theme === 'dark' ? (
        <>
          <span className="text-amber-400">☀️</span>
          <span>Ocean Breeze</span>
        </>
      ) : (
        <>
          <span className="text-[#0B3D91]">🌙</span>
          <span>Midnight Neon</span>
        </>
      )}
    </button>
  );
};


