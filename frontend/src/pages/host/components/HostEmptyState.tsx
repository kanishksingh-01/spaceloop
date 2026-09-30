import React from 'react';

interface HostEmptyStateProps {
  icon?: string;
  iconColor?: string;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: string;
  };
  primaryAction?: {
    label: string;
    onClick: () => void;
    icon?: string;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export const HostEmptyState: React.FC<HostEmptyStateProps> = ({
  icon = 'fa-solid fa-box-open',
  iconColor = 'text-slate-500 bg-slate-850 border-slate-700/60',
  title,
  description,
  action,
  primaryAction,
  secondaryAction,
  className = '',
}) => {
  const effectiveAction = primaryAction || action;

  return (
    <div
      className={`p-10 sm:p-14 text-center bg-slate-900/40 border border-slate-800/80 rounded-2xl flex flex-col items-center justify-center max-w-lg mx-auto ${className}`}
    >
      <div
        className={`w-14 h-14 rounded-2xl border flex items-center justify-center text-xl mb-4 ${iconColor}`}
      >
        <i className={icon} />
      </div>

      <h3 className="text-base font-bold text-white mb-1.5">{title}</h3>
      <p className="text-xs text-slate-400 leading-relaxed max-w-sm mb-6">
        {description}
      </p>

      {(effectiveAction || secondaryAction) && (
        <div className="flex items-center gap-3 flex-wrap justify-center">
          {effectiveAction && (
            <button
              type="button"
              onClick={effectiveAction.onClick}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md shadow-amber-500/15 transition flex items-center gap-2"
            >
              {effectiveAction.icon && <i className={effectiveAction.icon} />}
              <span>{effectiveAction.label}</span>
            </button>
          )}

          {secondaryAction && (
            <button
              type="button"
              onClick={secondaryAction.onClick}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs font-semibold border border-slate-700 transition"
            >
              {secondaryAction.label}
            </button>
          )}
        </div>
      )}
    </div>
  );
};
