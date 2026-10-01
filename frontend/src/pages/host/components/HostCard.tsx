import React from 'react';

interface HostCardProps {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  icon?: string;
  iconColor?: string;
  action?: React.ReactNode;
  badge?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
  headerClassName?: string;
  noPadding?: boolean;
}

export const HostCard: React.FC<HostCardProps> = ({
  title,
  subtitle,
  icon,
  iconColor = 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  action,
  badge,
  children,
  className = '',
  bodyClassName = '',
  headerClassName = '',
  noPadding = false,
}) => {
  const hasHeader = title || subtitle || action || icon || badge;

  return (
    <div
      className={`bg-slate-900 border border-slate-800 rounded-xl shadow-sm transition-all duration-200 overflow-hidden ${className}`}
    >
      {hasHeader && (
        <div
          className={`px-5 sm:px-6 py-3.5 border-b border-slate-800/80 flex items-center justify-between gap-4 flex-wrap ${headerClassName}`}
        >
          <div className="flex items-center gap-3 min-w-0">
            {icon && (
              <div
                className={`w-8 h-8 rounded-xl border flex items-center justify-center shrink-0 text-xs ${iconColor}`}
              >
                <i className={icon} />
              </div>
            )}
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                {title && (
                  <div className="text-sm font-bold text-white tracking-tight truncate">
                    {title}
                  </div>
                )}
                {badge}
              </div>
              {subtitle && (
                <div className="text-[11px] text-slate-400 mt-0.5 leading-tight">
                  {subtitle}
                </div>
              )}
            </div>
          </div>

          {action && <div className="shrink-0 flex items-center gap-2">{action}</div>}
        </div>
      )}

      <div className={noPadding ? bodyClassName : `p-5 sm:p-6 ${bodyClassName}`}>
        {children}
      </div>
    </div>
  );
};
