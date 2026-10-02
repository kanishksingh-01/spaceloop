import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { User } from '../../types';
import { useTranslation } from '../../i18n';

export interface AccountDropdownProps {
  currentUser: User;
  isHostPortal?: boolean;
  onOpenAuthModal?: () => void;
  onOpenHostAuthModal?: () => void;
  onLogout: () => Promise<void> | void;
  className?: string;
}

/**
 * Derives compact initials from user name or email
 */
const getInitials = (name?: string | null, email?: string | null): string => {
  if (name) {
    const stripped = name.replace(/^SpaceLoop\s*/i, '').trim();
    const parts = stripped.split(/\s+/).filter(Boolean);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    if (parts.length === 1 && parts[0].length >= 1) {
      return parts[0].substring(0, 2).toUpperCase();
    }
  }
  if (email) {
    const userPart = email.split('@')[0];
    return userPart.substring(0, 2).toUpperCase();
  }
  return 'SL';
};

/**
 * Derives a clean first name for the top navigation pill
 */
const getBadgeName = (name: string | undefined | null, fallback: string): string => {
  if (!name) return fallback;
  const stripped = name.replace(/^SpaceLoop\s*/i, '').trim();
  const first = stripped.split(' ')[0];
  if (!first || first.toLowerCase() === 'spaceloop') return fallback;
  return first;
};

/**
 * Polished Google-Style Account Dropdown Control for SpaceLoop Navigation
 */
export const AccountDropdown: React.FC<AccountDropdownProps> = ({
  currentUser,
  isHostPortal = false,
  onOpenAuthModal,
  onOpenHostAuthModal,
  onLogout,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const navigate = useNavigate();
  const { t } = useTranslation();

  const initials = getInitials(currentUser?.name, currentUser?.email);
  const displayName = currentUser?.name?.trim() || (isHostPortal ? 'SpaceLoop Host' : 'SpaceLoop Seeker');
  const displayEmail = currentUser?.email || 'user@spaceloop.in';
  const badgeFirstName = getBadgeName(currentUser?.name, isHostPortal ? 'Host' : 'Seeker');
  const trustScore = currentUser?.trust_score || currentUser?.objective_trust_score || 98;

  // Close dropdown on outside clicks
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [isOpen]);

  // Close dropdown on Escape key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
        triggerRef.current?.focus();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const handleManageAccount = () => {
    setIsOpen(false);
    if (isHostPortal) {
      navigate('/host/settings');
    } else {
      navigate('/dashboard');
    }
  };

  const handleAddAccount = () => {
    setIsOpen(false);
    if (isHostPortal && onOpenHostAuthModal) {
      onOpenHostAuthModal();
    } else if (onOpenAuthModal) {
      onOpenAuthModal();
    }
  };

  const handleSignOut = async () => {
    setIsOpen(false);
    try {
      await onLogout();
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  return (
    <div className={`relative inline-block text-left ${className}`} ref={dropdownRef}>
      {/* 1. TOP NAVIGATION TRIGGER BUTTON */}
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-haspopup="true"
        aria-expanded={isOpen}
        aria-label={`Account menu for ${displayName}`}
        className={`group flex items-center gap-2 px-2 sm:px-2.5 py-1 rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 select-none shrink-0 ${
          isHostPortal
            ? isOpen
              ? 'bg-amber-500/20 text-amber-200 border border-amber-500/50 shadow-md shadow-amber-500/10 focus:ring-amber-500/40'
              : 'bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-800 hover:border-amber-500/40 focus:ring-amber-500/30'
            : isOpen
              ? 'bg-indigo-600/20 text-indigo-200 border border-indigo-500/50 shadow-md shadow-indigo-500/10 focus:ring-indigo-500/40'
              : 'bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-800 hover:border-indigo-500/40 focus:ring-indigo-500/30'
        }`}
      >
        {/* Compact Avatar */}
        <div
          className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs shadow-sm transition-transform duration-200 group-hover:scale-105 ${
            isHostPortal
              ? 'bg-gradient-to-tr from-amber-500 via-orange-500 to-amber-400 text-slate-950 shadow-amber-500/20'
              : 'bg-gradient-to-tr from-indigo-600 via-violet-600 to-indigo-400 text-white shadow-indigo-500/20'
          }`}
        >
          {initials}
        </div>

        {/* User Role & Name */}
        <div className="flex items-center gap-1.5 text-xs font-semibold">
          <span className="text-slate-200 group-hover:text-white transition-colors duration-200">
            {isHostPortal ? `🏡 ${badgeFirstName}` : `🎓 ${badgeFirstName}`}
          </span>
        </div>

        {/* Chevron Indicator */}
        <i
          className={`fa-solid fa-chevron-down text-[10px] text-slate-400 transition-transform duration-200 ${
            isOpen ? 'rotate-180 text-white' : 'group-hover:text-slate-200'
          }`}
        />
      </button>

      {/* 2. FLOATING GOOGLE-STYLE ACCOUNT PANEL */}
      {isOpen && (
        <div
          role="menu"
          aria-orientation="vertical"
          className="absolute right-0 top-full mt-2.5 w-[310px] sm:w-[340px] max-w-[calc(100vw-1.5rem)] rounded-2xl sm:rounded-3xl shadow-2xl backdrop-blur-2xl z-50 overflow-hidden border transition-all duration-200 animate-in fade-in zoom-in-95 bg-white/95 dark:bg-slate-900/95 border-slate-200/90 dark:border-slate-800/90 shadow-slate-950/20 dark:shadow-[0_20px_50px_rgba(0,0,0,0.7)]"
        >
          {/* TOP SECTION: User Profile Info */}
          <div className="p-4 sm:p-5 flex flex-col items-center text-center bg-slate-50/60 dark:bg-slate-950/40 border-b border-slate-100 dark:border-slate-800/70">
            {/* Prominent Circular Avatar */}
            <div className="relative mb-3">
              <div
                className={`w-14 h-14 sm:w-16 sm:h-16 rounded-full flex items-center justify-center text-base sm:text-lg font-black tracking-wider shadow-lg ring-4 ring-white dark:ring-slate-800 select-none ${
                  isHostPortal
                    ? 'bg-gradient-to-tr from-amber-500 via-orange-500 to-amber-400 text-slate-950 shadow-amber-500/25'
                    : 'bg-gradient-to-tr from-indigo-600 via-violet-600 to-indigo-400 text-white shadow-indigo-500/25'
                }`}
              >
                {initials}
              </div>
              {/* Online / Active Verification Dot */}
              <span
                className={`absolute bottom-0 right-0 w-4 h-4 rounded-full border-2 border-white dark:border-slate-900 flex items-center justify-center ${
                  isHostPortal ? 'bg-amber-400' : 'bg-emerald-400'
                }`}
                title="Verified Session"
              >
                <i className="fa-solid fa-check text-[8px] text-slate-950" />
              </span>
            </div>

            {/* Full Name */}
            <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white tracking-tight truncate max-w-full px-2">
              {displayName}
            </h3>

            {/* Email Address */}
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400 truncate max-w-full px-2 mt-0.5">
              {displayEmail}
            </p>

            {/* Role & Telemetry Trust Badge */}
            <div className="mt-2.5 flex items-center gap-2 flex-wrap justify-center">
              <span
                className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border select-none ${
                  isHostPortal
                    ? 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30'
                    : 'bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border-indigo-500/30'
                }`}
              >
                <i className={isHostPortal ? 'fa-solid fa-house-chimney-user' : 'fa-solid fa-graduation-cap'} />
                <span>{isHostPortal ? 'Verified Host' : 'Verified Seeker'}</span>
              </span>

              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 select-none">
                <i className="fa-solid fa-shield-halved" />
                <span>OTI {trustScore}/100</span>
              </span>
            </div>

            {/* Manage Account Pill Button (Google-Style) */}
            <button
              type="button"
              onClick={handleManageAccount}
              className="mt-3.5 inline-flex items-center justify-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold border border-slate-200 dark:border-slate-700/80 bg-white dark:bg-slate-800/80 hover:bg-slate-100 dark:hover:bg-slate-700/90 text-slate-700 dark:text-slate-200 transition-all duration-200 shadow-sm hover:shadow hover:border-slate-300 dark:hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 dark:focus:ring-indigo-500/40"
            >
              <i className="fa-solid fa-user-gear text-slate-400 dark:text-slate-400 text-xs" />
              <span>{t('nav.profile') || 'Manage Account'}</span>
            </button>
          </div>

          {/* MIDDLE SECTION: Primary Account Actions */}
          <div className="p-2 space-y-1">
            {/* 1. Manage Account Action */}
            <button
              type="button"
              onClick={handleManageAccount}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-colors duration-200 group hover:bg-slate-100/90 dark:hover:bg-slate-800/70 focus:outline-none focus:bg-slate-100 dark:focus:bg-slate-800"
            >
              <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-xs shrink-0 transition-transform duration-200 group-hover:scale-105 border border-indigo-100 dark:border-indigo-900/40">
                <i className="fa-solid fa-id-card" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-300 transition-colors duration-200">
                  Manage Account
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                  Dashboard, telemetry & settings
                </div>
              </div>
              <i className="fa-solid fa-chevron-right text-[10px] text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300 group-hover:translate-x-0.5 transition-all duration-200" />
            </button>

            {/* 2. Add Another Account Action */}
            <button
              type="button"
              onClick={handleAddAccount}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-colors duration-200 group hover:bg-slate-100/90 dark:hover:bg-slate-800/70 focus:outline-none focus:bg-slate-100 dark:focus:bg-slate-800"
            >
              <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-xs shrink-0 transition-transform duration-200 group-hover:scale-105 border border-emerald-100 dark:border-emerald-900/40">
                <i className="fa-solid fa-user-plus" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-emerald-600 dark:group-hover:text-emerald-300 transition-colors duration-200">
                  Add another account
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                  Switch or sign into a different profile
                </div>
              </div>
              <i className="fa-solid fa-plus text-xs text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300 transition-colors duration-200" />
            </button>
          </div>

          {/* DIVIDER */}
          <div className="border-t border-slate-100 dark:border-slate-800/80" />

          {/* BOTTOM SECTION: Sign Out Action */}
          <div className="p-2">
            <button
              type="button"
              onClick={handleSignOut}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-colors duration-200 group hover:bg-rose-50 dark:hover:bg-rose-950/40 focus:outline-none focus:bg-rose-50 dark:focus:bg-rose-950/40"
            >
              <div className="w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400 flex items-center justify-center text-xs shrink-0 transition-transform duration-200 group-hover:scale-105 border border-rose-100 dark:border-rose-900/40">
                <i className="fa-solid fa-arrow-right-from-bracket" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold text-rose-600 dark:text-rose-400">
                  {t('nav.signOut') || 'Sign Out'}
                </div>
                <div className="text-[11px] text-rose-500/80 dark:text-rose-400/70 truncate">
                  Invalidate session & return to landing
                </div>
              </div>
            </button>
          </div>

          {/* MICRO FOOTER: Security & Legal Safeguards */}
          <div className="px-4 py-2 bg-slate-50/80 dark:bg-slate-950/60 border-t border-slate-100 dark:border-slate-800/60 text-center flex items-center justify-center gap-2 text-[10px] text-slate-400 dark:text-slate-500 select-none">
            <span>🔒 Section 52 Protected</span>
            <span>•</span>
            <span>₹100 UPI Micro-Escrow</span>
          </div>
        </div>
      )}
    </div>
  );
};
