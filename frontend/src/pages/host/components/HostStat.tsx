import React from 'react';

interface HostStatProps {
  label: string;
  value: string | number;
  subvalue?: React.ReactNode;
  icon?: string;
  iconColor?: string;
  badge?: React.ReactNode;
  trend?: {
    value: string;
    isPositive?: boolean;
    label?: string;
  };
  onClick?: () => void;
  className?: string;
}

export const HostStat: React.FC<HostStatProps> = ({
  label,
  value,
  subvalue,
  icon,
  iconColor = 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  badge,
  trend,
  onClick,
  className = '',
}) => {
  return (
    <div
      onClick={onClick}
      className={`bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 sm:p-5 flex flex-col justify-between transition-all duration-200 ${
        onClick ? 'cursor-pointer hover:border-slate-700 hover:bg-slate-900/90' : ''
      } ${className}`}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <span className="text-xs font-semibold text-slate-400 tracking-tight leading-snug">
          {label}
        </span>
        <div className="flex items-center gap-1.5 shrink-0">
          {badge}
          {icon && (
            <div
              className={`w-7 h-7 rounded-lg border flex items-center justify-center text-xs ${iconColor}`}
            >
              <i className={icon} />
            </div>
          )}
        </div>
      </div>

      <div className="space-y-1">
        <div className="text-xl sm:text-2xl font-black text-white font-mono tracking-tight">
          {value}
        </div>

        {(subvalue || trend) && (
          <div className="flex items-center gap-2 text-[11px] text-slate-400 pt-0.5">
            {trend && (
              <span
                className={`font-semibold flex items-center gap-0.5 ${
                  trend.isPositive ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                <i
                  className={`fa-solid ${
                    trend.isPositive ? 'fa-arrow-trend-up' : 'fa-arrow-trend-down'
                  } text-[10px]`}
                />
                <span>{trend.value}</span>
              </span>
            )}
            {subvalue && <span className="truncate">{subvalue}</span>}
          </div>
        )}
      </div>
    </div>
  );
};
