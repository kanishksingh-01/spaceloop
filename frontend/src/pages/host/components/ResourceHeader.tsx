import React from 'react';
import { useNavigate } from 'react-router-dom';
import { StatusBadge } from './StatusBadge';

export interface BreadcrumbItem {
  label: string;
  path?: string;
  href?: string;
  onClick?: () => void;
}

interface ResourceHeaderProps {
  breadcrumbs: BreadcrumbItem[];
  title: string;
  subtitle?: string;
  status?: string;
  statusType?: 'space' | 'booking' | 'escrow' | 'verification';
  statusBadge?: React.ReactNode;
  actions?: React.ReactNode;
  tags?: string[];
  metrics?: Array<{ label: string; value: string | number; color?: string }>;
  className?: string;
}

export const ResourceHeader: React.FC<ResourceHeaderProps> = ({
  breadcrumbs,
  title,
  subtitle,
  status,
  statusType = 'space',
  statusBadge,
  actions,
  tags,
  metrics,
  className = '',
}) => {
  const navigate = useNavigate();

  return (
    <div
      className={`bg-slate-900/80 border-b border-slate-800/80 px-4 sm:px-6 lg:px-8 py-5 backdrop-blur-sm ${className}`}
    >
      <div className="max-w-7xl mx-auto">
        {/* Breadcrumb Trail */}
        <nav className="flex items-center gap-2 text-xs text-slate-500 mb-2.5 flex-wrap">
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={idx}>
              {idx > 0 && <span className="text-slate-600">/</span>}
              {crumb.onClick ? (
                <button
                  type="button"
                  onClick={crumb.onClick}
                  className="hover:text-amber-400 transition font-medium text-slate-400"
                >
                  {crumb.label}
                </button>
              ) : crumb.path ? (
                <button
                  type="button"
                  onClick={() => navigate(crumb.path!)}
                  className="hover:text-amber-400 transition font-medium text-slate-400"
                >
                  {crumb.label}
                </button>
              ) : (
                <span
                  className={
                    idx === breadcrumbs.length - 1
                      ? 'text-slate-200 font-semibold'
                      : 'text-slate-400'
                  }
                >
                  {crumb.label}
                </span>
              )}
            </React.Fragment>
          ))}
        </nav>

        {/* Main Title & Action Row */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white truncate">
                {title}
              </h1>
              {statusBadge ? (
                statusBadge
              ) : status ? (
                <StatusBadge status={status} type={statusType} />
              ) : null}
              {tags &&
                tags.map((tag, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700/60"
                  >
                    {tag}
                  </span>
                ))}
            </div>
            {subtitle && (
              <p className="text-xs text-slate-400 max-w-3xl leading-relaxed">
                {subtitle}
              </p>
            )}
          </div>

          {/* Action Controls */}
          {actions && (
            <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
              {actions}
            </div>
          )}
        </div>

        {/* Optional In-Header Metric Ribbon */}
        {metrics && metrics.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-slate-800/60">
            {metrics.map((m, idx) => (
              <div
                key={idx}
                className="bg-slate-950/40 border border-slate-800/80 px-3.5 py-2 rounded-xl"
              >
                <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                  {m.label}
                </div>
                <div
                  className={`text-base font-bold font-mono tracking-tight ${
                    m.color || 'text-white'
                  }`}
                >
                  {m.value}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
