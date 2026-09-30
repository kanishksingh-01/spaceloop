import React from 'react';

interface StatusBadgeProps {
  status: string;
  type?: 'space' | 'booking' | 'escrow' | 'verification' | 'session';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'booking', className = '' }) => {
  const norm = (status || '').toLowerCase().trim();

  let label = status;
  let bgClass = 'bg-slate-800 text-slate-300 border-slate-700';
  let dotClass = 'bg-slate-400';

  if (type === 'space') {
    if (norm === 'published' || norm === 'active' || norm === 'true') {
      label = 'Published';
      bgClass = 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25';
      dotClass = 'bg-emerald-400 shadow-[0_0_6px_rgba(16,185,129,0.7)]';
    } else if (norm === 'draft') {
      label = 'Draft';
      bgClass = 'bg-slate-500/10 text-slate-400 border-slate-700/60';
      dotClass = 'bg-slate-400';
    } else if (norm === 'verification_pending' || norm === 'pending') {
      label = 'Verification Pending';
      bgClass = 'bg-amber-500/10 text-amber-300 border-amber-500/25';
      dotClass = 'bg-amber-400 animate-pulse';
    } else {
      label = 'Unavailable';
      bgClass = 'bg-rose-500/10 text-rose-300 border-rose-500/25';
      dotClass = 'bg-rose-400';
    }
  } else if (type === 'escrow') {
    if (norm === 'released' || norm === 'instant_release_complete') {
      label = 'Released';
      bgClass = 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25';
      dotClass = 'bg-emerald-400';
    } else if (norm === 'held' || norm === 'pending') {
      label = 'Held (₹100 UPI)';
      bgClass = 'bg-amber-500/10 text-amber-300 border-amber-500/25';
      dotClass = 'bg-amber-400';
    } else if (norm === 'disputed') {
      label = 'Disputed';
      bgClass = 'bg-rose-500/10 text-rose-300 border-rose-500/25';
      dotClass = 'bg-rose-400 animate-pulse';
    } else if (norm === 'refunded') {
      label = 'Refunded';
      bgClass = 'bg-indigo-500/10 text-indigo-300 border-indigo-500/25';
      dotClass = 'bg-indigo-400';
    }
  } else if (type === 'verification') {
    if (norm === 'verified' || norm === 'true') {
      label = 'Verified';
      bgClass = 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25';
      dotClass = 'bg-emerald-400';
    } else if (norm === 'pending') {
      label = 'Action Required';
      bgClass = 'bg-amber-500/10 text-amber-300 border-amber-500/25';
      dotClass = 'bg-amber-400';
    } else {
      label = 'Unverified';
      bgClass = 'bg-slate-500/10 text-slate-400 border-slate-700/60';
      dotClass = 'bg-slate-400';
    }
  } else {
    // Default: booking or session
    if (norm === 'confirmed') {
      label = 'Confirmed';
      bgClass = 'bg-indigo-500/10 text-indigo-300 border-indigo-500/25';
      dotClass = 'bg-indigo-400';
    } else if (norm === 'active' || norm === 'checked_in') {
      label = 'In Session';
      bgClass = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
      dotClass = 'bg-emerald-400 animate-ping';
    } else if (norm === 'pending') {
      label = 'Awaiting Approval';
      bgClass = 'bg-amber-500/10 text-amber-300 border-amber-500/25';
      dotClass = 'bg-amber-400 animate-pulse';
    } else if (norm === 'completed' || norm === 'checked_out') {
      label = 'Completed';
      bgClass = 'bg-slate-500/10 text-slate-300 border-slate-700';
      dotClass = 'bg-slate-400';
    } else if (norm === 'cancelled' || norm === 'rejected') {
      label = norm === 'rejected' ? 'Declined' : 'Cancelled';
      bgClass = 'bg-rose-500/10 text-rose-300 border-rose-500/25';
      dotClass = 'bg-rose-400';
    } else if (norm === 'disputed') {
      label = 'Disputed';
      bgClass = 'bg-amber-600/15 text-amber-300 border-amber-500/30';
      dotClass = 'bg-amber-400';
    }
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-tight border ${bgClass} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotClass}`} />
      <span>{label}</span>
    </span>
  );
};
