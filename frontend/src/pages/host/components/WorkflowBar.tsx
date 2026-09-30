import React from 'react';

export interface WorkflowStep {
  id: string;
  label: string;
  status: 'completed' | 'current' | 'upcoming' | 'failed';
  icon?: string;
  detail?: string;
}

interface WorkflowBarProps {
  steps: WorkflowStep[];
  onStepClick?: (stepId: string) => void;
  className?: string;
}

export const WorkflowBar: React.FC<WorkflowBarProps> = ({
  steps,
  onStepClick,
  className = '',
}) => {
  return (
    <div
      className={`bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 sm:p-5 ${className}`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Booking Lifecycle Progression
        </span>
        <span className="text-[10px] text-slate-500 font-mono">
          State Engine • 5-Stage Protocol
        </span>
      </div>

      <div className="flex items-center overflow-x-auto no-scrollbar gap-2 py-1">
        {steps.map((step, idx) => {
          const isCompleted = step.status === 'completed';
          const isCurrent = step.status === 'current';
          const isFailed = step.status === 'failed';

          return (
            <React.Fragment key={step.id}>
              {idx > 0 && (
                <div
                  className={`h-0.5 w-4 sm:w-6 shrink-0 transition-colors ${
                    isCompleted
                      ? 'bg-emerald-500/50'
                      : isCurrent
                      ? 'bg-amber-500/40'
                      : 'bg-slate-800'
                  }`}
                />
              )}

              <button
                type="button"
                disabled={!onStepClick}
                onClick={() => onStepClick && onStepClick(step.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-semibold shrink-0 transition-all ${
                  isCompleted
                    ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                    : isCurrent
                    ? 'bg-amber-500/15 text-amber-300 border-amber-500/40 ring-1 ring-amber-500/20'
                    : isFailed
                    ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                    : 'bg-slate-950/40 text-slate-500 border-slate-800/80'
                } ${onStepClick ? 'cursor-pointer hover:border-slate-700' : 'cursor-default'}`}
              >
                <span
                  className={`w-2 h-2 rounded-full shrink-0 ${
                    isCompleted
                      ? 'bg-emerald-400'
                      : isCurrent
                      ? 'bg-amber-400 animate-pulse'
                      : isFailed
                      ? 'bg-rose-400'
                      : 'bg-slate-600'
                  }`}
                />
                {step.icon && <i className={`${step.icon} text-xs`} />}
                <span>{step.label}</span>
                {step.detail && (
                  <span className="text-[10px] text-slate-400 font-mono hidden md:inline">
                    ({step.detail})
                  </span>
                )}
              </button>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
