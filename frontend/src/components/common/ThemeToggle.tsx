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
            : 'bg-surface border-border text-primary hover:bg-surface-elevated'
        } ${className}`}
        title={theme === 'dark' ? 'Switch to Light Theme (Sunset Architectural)' : 'Switch to Dark Theme (Twilight Architectural)'}
        aria-label="Toggle Theme"
      >
        {theme === 'dark' ? (
          <i className="fa-solid fa-sun text-sm" />
        ) : (
          <i className="fa-solid fa-moon text-sm text-primary" />
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
          : 'bg-surface hover:bg-surface-elevated text-text-primary hover:text-primary border-border'
      } ${className}`}
      title={theme === 'dark' ? 'Switch to Light Theme (Sunset Architectural)' : 'Switch to Dark Theme (Twilight Architectural)'}
      aria-label="Toggle Theme"
    >
      {theme === 'dark' ? (
        <>
          <span className="text-amber-400">☀️</span>
          <span>Light</span>
        </>
      ) : (
        <>
          <span className="text-amber-500">🌙</span>
          <span>Dark</span>
        </>
      )}
    </button>
  );
};


