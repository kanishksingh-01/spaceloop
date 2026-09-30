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
    <div className={`bg-slate-900/90 border border-slate-800 rounded-2xl p-3.5 sm:p-4 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Operational Workflow Progression
        </span>
        <span className="text-[10px] text-slate-500 font-mono">
          Level 3 • Connected Lifecycle
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
                    isCompleted ? 'bg-emerald-500/50' : isCurrent ? 'bg-amber-500/40' : 'bg-slate-800'
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
                    ? 'bg-amber-500/15 text-amber-300 border-amber-500/40 shadow-[0_0_12px_rgba(245,158,11,0.15)] ring-1 ring-amber-500/20'
                    : isFailed
                    ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                    : 'bg-slate-950/40 text-slate-500 border-slate-800/80'
                } ${onStepClick ? 'hover:scale-[1.02] cursor-pointer' : 'cursor-default'}`}
              >
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${
                    isCompleted
                      ? 'bg-emerald-500 text-slate-950'
                      : isCurrent
                      ? 'bg-amber-500 text-slate-950 animate-pulse'
                      : isFailed
                      ? 'bg-rose-500 text-white'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {isCompleted ? '✓' : idx + 1}
                </div>
                <span>{step.label}</span>
                {step.detail && <span className="text-[10px] text-slate-400">({step.detail})</span>}
              </button>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
