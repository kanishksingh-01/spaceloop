import React from 'react';

interface StatusBadgeProps {
  status: string;
  type?: 'space' | 'booking' | 'escrow' | 'verification' | 'session' | 'general';
  className?: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  type = 'booking',
  className = '',
  size = 'md',
}) => {
  const norm = (status || '').toLowerCase().trim();

  let label = status;
  let bgClass = 'bg-slate-800/80 text-slate-300 border-slate-700/60';
  let dotClass = 'bg-slate-400';

  if (type === 'space') {
    if (norm === 'published' || norm === 'active' || norm === 'true') {
      label = 'Published';
      bgClass = 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20';
      dotClass = 'bg-emerald-400';
    } else if (norm === 'draft') {
      label = 'Draft';
      bgClass = 'bg-slate-800/60 text-slate-400 border-slate-700/60';
      dotClass = 'bg-slate-400';
    } else if (norm === 'verification_pending' || norm === 'pending') {
      label = 'Pending Verification';
      bgClass = 'bg-amber-500/10 text-amber-300 border-amber-500/20';
      dotClass = 'bg-amber-400';
    } else {
      label = 'Unavailable';
      bgClass = 'bg-slate-800/60 text-slate-400 border-slate-700/60';
      dotClass = 'bg-slate-500';
    }
  } else if (type === 'escrow') {
    if (norm === 'released' || norm === 'instant_release_complete') {
      label = 'Released';
      bgClass = 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20';
      dotClass = 'bg-emerald-400';
    } else if (norm === 'held' || norm === 'pending') {
      label = 'Held (₹100 Escrow)';
      bgClass = 'bg-amber-500/10 text-amber-300 border-amber-500/20';
      dotClass = 'bg-amber-400';
    } else if (norm === 'disputed') {
      label = 'Dispute Hold';
      bgClass = 'bg-rose-500/10 text-rose-300 border-rose-500/20';
      dotClass = 'bg-rose-400';
    } else if (norm === 'refunded') {
      label = 'Refunded';
      bgClass = 'bg-sky-500/10 text-sky-300 border-sky-500/20';
      dotClass = 'bg-sky-400';
    }
  } else if (type === 'verification') {
    if (norm === 'verified' || norm === 'true') {
      label = 'Verified';
      bgClass = 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20';
      dotClass = 'bg-emerald-400';
    } else if (norm === 'pending' || norm === 'action_required') {
      label = 'Action Required';
      bgClass = 'bg-amber-500/10 text-amber-300 border-amber-500/20';
      dotClass = 'bg-amber-400';
    } else {
      label = 'Unverified';
      bgClass = 'bg-slate-800/60 text-slate-400 border-slate-700/60';
      dotClass = 'bg-slate-500';
    }
  } else {
    // Default: booking or session
    if (norm === 'active' || norm === 'checked_in') {
      label = 'In Session';
      bgClass = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
      dotClass = 'bg-emerald-400 animate-pulse';
    } else if (norm === 'confirmed') {
      label = 'Confirmed';
      bgClass = 'bg-sky-500/10 text-sky-300 border-sky-500/20';
      dotClass = 'bg-sky-400';
    } else if (norm === 'pending') {
      label = 'Awaiting Approval';
      bgClass = 'bg-amber-500/10 text-amber-300 border-amber-500/20';
      dotClass = 'bg-amber-400';
    } else if (norm === 'completed' || norm === 'checked_out') {
      label = 'Completed';
      bgClass = 'bg-slate-800/70 text-slate-300 border-slate-700/60';
      dotClass = 'bg-slate-400';
    } else if (norm === 'cancelled' || norm === 'rejected') {
      label = norm === 'rejected' ? 'Declined' : 'Cancelled';
      bgClass = 'bg-rose-500/10 text-rose-300 border-rose-500/20';
      dotClass = 'bg-rose-400';
    } else if (norm === 'disputed') {
      label = 'Disputed';
      bgClass = 'bg-rose-500/15 text-rose-300 border-rose-500/30';
      dotClass = 'bg-rose-400';
    }
  }

  const sizeClass =
    size === 'sm'
      ? 'px-2 py-0.5 text-[10px]'
      : 'px-2.5 py-1 text-[11px]';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold tracking-tight border ${sizeClass} ${bgClass} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotClass}`} />
      <span>{label}</span>
    </span>
  );
};
