import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { User } from '../../types';
import { logoutUser } from '../../services/auth';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from '../../i18n';
import { LanguageSelector } from './LanguageSelector';

/**
 * ============================================================================
 * SPACELOOP INTERACTIVE NAVIGATION DRAWER & PHYSICAL DRAG ENGINE
 * ----------------------------------------------------------------------------
 * Proportioned & scaled for Mobile (320px-640px), Tablet (640px-1024px),
 * and Laptop/Desktop (>1024px).
 *
 * Features:
 * - 60fps Native Pointer & Touch Drag Physics with Spring Settling
 * - Edge-swipe / peek interaction when drawer is closed
 * - High-contrast visible typography and bounded flex containers
 * - Full Dual-Theme Support (Ocean Breeze Light Mode & Midnight Neon Dark Mode)
 * - Keyboard accessibility (ESC closes, focus management)
 * ============================================================================
 */

export interface NavigationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onOpen: () => void;
  currentUser: User | null;
  onOpenAuthModal: () => void;
  onOpenHostAuthModal?: () => void;
}

export interface HamburgerButtonProps {
  isOpen: boolean;
  onToggle: () => void;
  className?: string;
}

/**
 * Animated Hamburger Button
 * Smoothly morphs from 3 horizontal lines into an 'X'.
 */
export const HamburgerButton: React.FC<HamburgerButtonProps> = ({
  isOpen,
  onToggle,
  className = '',
}) => {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={isOpen ? 'Close navigation drawer' : 'Open navigation drawer'}
      aria-expanded={isOpen}
      className={`group relative flex flex-col justify-center items-center w-9 h-9 sm:w-10 sm:h-10 rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#0B3D91]/40 dark:focus:ring-indigo-500/50 shrink-0 ${
        isOpen
          ? 'bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-white'
          : 'bg-white hover:bg-[#F0F8FF] dark:bg-slate-900/90 dark:hover:bg-slate-800 text-[#0B2545] dark:text-slate-200 hover:text-[#0B3D91] dark:hover:text-white border border-[#D0E6F7] dark:border-slate-800 shadow-sm'
      } ${className}`}
    >
      <span className="sr-only">{isOpen ? 'Close menu' : 'Open menu'}</span>
      <div className="w-4 sm:w-5 h-3.5 sm:h-4 relative flex flex-col justify-between items-center pointer-events-none">
        {/* Top Bar */}
        <span
          className={`h-0.5 w-4 sm:w-5 bg-current rounded-full transform transition-all duration-300 ease-in-out origin-center ${
            isOpen ? 'rotate-45 translate-y-[6px] sm:translate-y-[7px]' : ''
          }`}
        />
        {/* Middle Bar */}
        <span
          className={`h-0.5 w-4 sm:w-5 bg-current rounded-full transition-all duration-200 ease-in-out ${
            isOpen ? 'opacity-0 scale-x-0' : 'opacity-100'
          }`}
        />
        {/* Bottom Bar */}
        <span
          className={`h-0.5 w-4 sm:w-5 bg-current rounded-full transform transition-all duration-300 ease-in-out origin-center ${
            isOpen ? '-rotate-45 -translate-y-[6px] sm:-translate-y-[7px]' : ''
          }`}
        />
      </div>
    </button>
  );
};

export const NavigationDrawer: React.FC<NavigationDrawerProps> = ({
  isOpen,
  onClose,
  onOpen,
  currentUser,
  onOpenAuthModal,
  onOpenHostAuthModal,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const { t } = useTranslation();

  // Drawer geometry and drag state
  const drawerRef = useRef<HTMLDivElement>(null);
  const [drawerWidth, setDrawerWidth] = useState(360);
  const [dragOffset, setDragOffset] = useState<number | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Drag physics tracking refs
  const dragStartX = useRef<number>(0);
  const dragStartTime = useRef<number>(0);
  const currentDragX = useRef<number>(0);
  const isEdgeDrag = useRef<boolean>(false);

  // Measure actual drawer width dynamically across mobile/tablet/laptop
  useEffect(() => {
    const updateWidth = () => {
      if (drawerRef.current) {
        setDrawerWidth(drawerRef.current.offsetWidth || 360);
      } else {
        const measured = Math.min(400, Math.max(300, window.innerWidth * 0.85));
        setDrawerWidth(measured);
      }
    };
    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  // Keyboard accessibility: ESC to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Lock body scrolling when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const isHostPortal =
    location.pathname.startsWith('/host') ||
    location.pathname === '/list-space' ||
    location.pathname === '/calculator' ||
    location.pathname === '/verify';

  const handleLogout = async () => {
    try {
      await logoutUser();
      onClose();
      window.location.reload();
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  const handleNavigate = (path: string) => {
    navigate(path);
    onClose();
  };

  // =========================================================================
  // GESTURE & DRAGGING PHYSICS ENGINE
  // =========================================================================

  const startDrag = useCallback(
    (clientX: number, edge: boolean = false) => {
      setIsDragging(true);
      isEdgeDrag.current = edge;
      dragStartX.current = clientX;
      currentDragX.current = clientX;
      dragStartTime.current = performance.now();
      setDragOffset(0);
    },
    []
  );

  const updateDrag = useCallback(
    (clientX: number) => {
      if (!isDragging) return;
      currentDragX.current = clientX;
      const deltaX = clientX - dragStartX.current;

      if (isEdgeDrag.current) {
        const clamped = Math.max(0, Math.min(deltaX, drawerWidth));
        setDragOffset(clamped);
      } else {
        if (deltaX > 0) {
          // Rubber band resistance if pulling right past open position
          setDragOffset(deltaX * 0.2);
        } else {
          setDragOffset(Math.max(-drawerWidth, deltaX));
        }
      }
    },
    [isDragging, drawerWidth]
  );

  const endDrag = useCallback(() => {
    if (!isDragging) return;
    setIsDragging(false);

    const timeElapsed = Math.max(1, performance.now() - dragStartTime.current);
    const totalDelta = currentDragX.current - dragStartX.current;
    const velocity = totalDelta / timeElapsed; // px per ms

    if (isEdgeDrag.current) {
      const threshold = drawerWidth * 0.25;
      if (totalDelta > threshold || velocity > 0.3) {
        onOpen();
      } else {
        onClose();
      }
    } else {
      const threshold = drawerWidth * -0.25;
      if (totalDelta < threshold || velocity < -0.3) {
        onClose();
      } else {
        onOpen();
      }
    }

    setDragOffset(null);
  }, [isDragging, drawerWidth, onOpen, onClose]);

  // Pointer event listeners (desktop mouse + touch)
  useEffect(() => {
    if (!isDragging) return;

    const handlePointerMove = (e: PointerEvent) => {
      updateDrag(e.clientX);
    };

    const handlePointerUp = () => {
      endDrag();
    };

    window.addEventListener('pointermove', handlePointerMove, { passive: true });
    window.addEventListener('pointerup', handlePointerUp);
    window.addEventListener('pointercancel', handlePointerUp);

    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
      window.removeEventListener('pointercancel', handlePointerUp);
    };
  }, [isDragging, updateDrag, endDrag]);

  // Calculate transform translation
  let translateX = 0;
  let backdropOpacity = 0;

  if (isOpen) {
    if (dragOffset !== null) {
      translateX = dragOffset;
      const progress = Math.max(0, Math.min(1, 1 + dragOffset / drawerWidth));
      backdropOpacity = progress;
    } else {
      translateX = 0;
      backdropOpacity = 1;
    }
  } else {
    if (dragOffset !== null && isEdgeDrag.current) {
      translateX = -drawerWidth + dragOffset;
      const progress = Math.max(0, Math.min(1, dragOffset / drawerWidth));
      backdropOpacity = progress;
    } else {
      translateX = -drawerWidth - 25; // completely offscreen
      backdropOpacity = 0;
    }
  }

  const isVisible = isOpen || (isDragging && isEdgeDrag.current);

  // Navigation Items Definition with Scaled Typography
  const seekerNavItems = [
    {
      path: '/',
      label: t('nav.home') || 'Home',
      subtitle: 'SpaceLoop marketplace & discovery',
      icon: 'fa-solid fa-house',
      iconColor: 'text-[#0B3D91] dark:text-indigo-400',
      iconBg: 'bg-[#0B3D91]/10 dark:bg-indigo-500/15',
    },
    {
      path: '/dashboard',
      label: t('nav.myBookings') || 'My Bookings',
      subtitle: 'Active sessions, passes & QR codes',
      icon: 'fa-solid fa-calendar-check',
      iconColor: 'text-indigo-600 dark:text-indigo-400',
      iconBg: 'bg-indigo-500/10 dark:bg-indigo-500/15',
      badge: 'Sessions',
      badgeStyle: 'bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border-indigo-500/25',
    },
    {
      path: '/how-it-works',
      label: t('nav.howItWorks') || 'How It Works',
      subtitle: 'Section 52 lease & zero-hardware',
      icon: 'fa-solid fa-circle-question',
      iconColor: 'text-violet-600 dark:text-violet-400',
      iconBg: 'bg-violet-500/10 dark:bg-violet-500/15',
    },
    {
      path: '/admin/trust-safety',
      label: t('nav.trustSafety') || 'Trust & Safety',
      subtitle: 'Verification, fraud defense & safety console',
      icon: 'fa-solid fa-shield-halved',
      iconColor: 'text-rose-600 dark:text-rose-400',
      iconBg: 'bg-rose-500/10 dark:bg-rose-500/15',
      badge: 'Defense',
      badgeStyle: 'bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-500/25',
    },
  ];

  const hostNavItems = [
    {
      path: '/host/dashboard',
      label: t('nav.hostPortal') || 'Host Dashboard',
      subtitle: 'Manage listings, rates & occupancy',
      icon: 'fa-solid fa-chart-pie',
      iconColor: 'text-amber-600 dark:text-amber-400',
      iconBg: 'bg-amber-500/10 dark:bg-amber-500/15',
      badge: 'Host',
      badgeStyle: 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/25',
    },
    {
      path: '/list-space',
      label: t('nav.listSpace') || 'List a Space',
      subtitle: 'Monetize unused capacity in minutes',
      icon: 'fa-solid fa-plus-circle',
      iconColor: 'text-amber-600 dark:text-amber-400',
      iconBg: 'bg-amber-500/10 dark:bg-amber-500/15',
    },
    {
      path: '/calculator',
      label: t('nav.calculator') || 'Yield Calculator',
      subtitle: 'Calculate estimated earnings',
      icon: 'fa-solid fa-calculator',
      iconColor: 'text-emerald-600 dark:text-emerald-400',
      iconBg: 'bg-emerald-500/10 dark:bg-emerald-500/15',
    },
    {
      path: '/architecture',
      label: t('nav.architecture') || 'Architecture & Team',
      subtitle: '4 Core Profiles, subsystems & stack',
      icon: 'fa-solid fa-cubes',
      iconColor: 'text-[#0B3D91] dark:text-indigo-400',
      iconBg: 'bg-[#0B3D91]/10 dark:bg-indigo-500/15',
      badge: 'Team',
      badgeStyle: 'bg-[#0B3D91]/10 text-[#0B3D91] dark:bg-indigo-500/20 dark:text-indigo-300 border-[#0B3D91]/25 dark:border-indigo-500/30',
    },
    {
      path: '/verify',
      label: t('nav.verify') || 'Identity & Trust KYC',
      subtitle: 'Aadhaar tokenized verification',
      icon: 'fa-solid fa-shield-halved',
      iconColor: 'text-rose-600 dark:text-rose-400',
      iconBg: 'bg-rose-500/10 dark:bg-rose-500/15',
    },
  ];

  const navItems = isHostPortal ? hostNavItems : seekerNavItems;

  return (
    <>
      {/* =====================================================================
          1. EDGE TRIGGER (Swipe-from-edge peek detector when closed)
          ===================================================================== */}
      {!isOpen && (
        <div
          onPointerDown={(e) => {
            if (e.button === 0) {
              startDrag(e.clientX, true);
            }
          }}
          className="fixed top-0 left-0 bottom-0 w-4 z-40 cursor-grab active:cursor-grabbing touch-none select-none hover:w-6 transition-all duration-200"
          title="Drag from edge to open menu"
          aria-hidden="true"
        >
          <div className="absolute top-1/2 -translate-y-1/2 left-0.5 w-1 h-14 rounded-r-full bg-[#0B3D91]/30 dark:bg-indigo-500/30 opacity-0 hover:opacity-100 transition-opacity" />
        </div>
      )}

      {/* =====================================================================
          2. DIMMED BACKDROP OVERLAY
          ===================================================================== */}
      {isVisible && (
        <div
          onClick={onClose}
          style={{
            opacity: backdropOpacity,
            pointerEvents: isOpen && !isDragging ? 'auto' : isDragging ? 'none' : 'none',
          }}
          className={`fixed inset-0 z-40 bg-black/60 backdrop-blur-xs transition-opacity ${
            isDragging ? 'duration-0' : 'duration-300 ease-out'
          }`}
          aria-hidden="true"
        />
      )}

      {/* =====================================================================
          3. SCALED & RESPONSIVE PHYSICAL SLIDING DRAWER
          ===================================================================== */}
      <aside
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-label="Site Navigation Drawer"
        style={{
          transform: `translate3d(${translateX}px, 0, 0)`,
          transition: isDragging ? 'none' : 'transform 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
        className="fixed top-0 left-0 bottom-0 h-[100dvh] max-h-[100dvh] w-[85vw] min-w-[280px] max-w-[380px] sm:max-w-[400px] z-50 flex flex-col bg-white dark:bg-slate-950 text-slate-800 dark:text-slate-100 border-r border-[#D0E6F7] dark:border-slate-800/90 shadow-[8px_0_35px_-5px_rgba(11,61,145,0.12)] dark:shadow-[8px_0_40px_-5px_rgba(0,0,0,0.85)] sm:rounded-r-3xl overflow-hidden will-change-transform select-none"
      >
        {/* DRAG HANDLE TAB (Grab handle on right edge) */}
        <div
          onPointerDown={(e) => {
            if (e.button === 0) {
              startDrag(e.clientX, false);
            }
          }}
          className="absolute top-0 bottom-0 -right-4 w-7 flex items-center justify-center cursor-grab active:cursor-grabbing touch-none z-10 group"
          title="Drag drawer to slide"
          aria-hidden="true"
        >
          <div className="w-1.5 h-14 rounded-full bg-slate-400/40 dark:bg-slate-600/40 group-hover:bg-[#0B3D91] dark:group-hover:bg-indigo-400 group-hover:h-20 transition-all duration-200" />
        </div>

        {/* =====================================================================
            DRAWER HEADER (Compact, Responsive Header with Close Button)
            ===================================================================== */}
        <div className="h-14 sm:h-16 px-4 sm:px-5 border-b border-[#D0E6F7] dark:border-slate-800/80 flex items-center justify-between gap-3 bg-[#E8F6FF]/60 dark:bg-slate-900/60 shrink-0">
          <div className="flex items-center gap-2.5 min-w-0">
            <div
              className={`w-8 h-8 sm:w-9 sm:h-9 rounded-xl flex items-center justify-center shadow-md shrink-0 ${
                isHostPortal
                  ? 'bg-gradient-to-tr from-amber-600 via-orange-600 to-amber-400 shadow-amber-500/20'
                  : 'bg-gradient-to-tr from-[#0B3D91] via-[#1E40AF] to-[#3BA7F2] dark:from-indigo-600 dark:via-violet-600 dark:to-indigo-400 shadow-indigo-500/20'
              }`}
            >
              <i className="fa-solid fa-infinity text-white text-base sm:text-lg" />
            </div>
            <div className="min-w-0">
              <div className="text-base sm:text-lg font-extrabold tracking-tight text-slate-900 dark:text-white font-display flex items-center gap-1 leading-tight">
                Space<span className="text-[#0B3D91] dark:text-indigo-400">Loop</span>
              </div>
              <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 truncate">
                {isHostPortal ? '🏡 Host Space' : '⚡ Seeker Desk'}
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close navigation drawer"
            className="w-8 h-8 rounded-xl flex items-center justify-center text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800/80 transition shrink-0"
          >
            <i className="fa-solid fa-xmark text-base" />
          </button>
        </div>

        {/* =====================================================================
            DRAWER USER PROFILE CARD (Responsive & Compact)
            ===================================================================== */}
        <div className="p-3 sm:p-4 border-b border-[#D0E6F7] dark:border-slate-800/80 bg-white dark:bg-slate-950 shrink-0">
          {currentUser ? (
            <div className="p-3 rounded-2xl bg-[#F0F8FF] dark:bg-slate-900/80 border border-[#D0E6F7] dark:border-slate-800 flex items-center justify-between gap-2.5 shadow-2xs">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-9 h-9 rounded-xl bg-[#0B3D91] dark:bg-indigo-600 text-white font-bold text-xs sm:text-sm flex items-center justify-center shrink-0 shadow-sm">
                  {currentUser.name ? currentUser.name.charAt(0).toUpperCase() : 'U'}
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-900 dark:text-white truncate">
                    {currentUser.name}
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate font-mono">
                    {currentUser.email}
                  </div>
                  <div className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1 mt-0.5">
                    <i className="fa-solid fa-circle-check text-[9px]" /> Verified
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="p-2 rounded-xl text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition text-xs shrink-0"
                title="Sign Out"
              >
                <i className="fa-solid fa-arrow-right-from-bracket" />
              </button>
            </div>
          ) : (
            <div className="p-3 rounded-2xl bg-gradient-to-br from-[#E8F6FF] to-[#F0F8FF] dark:from-slate-900 dark:to-slate-900/60 border border-[#D0E6F7] dark:border-slate-800 text-center">
              <div className="text-xs font-bold text-slate-900 dark:text-white mb-0.5">
                Welcome to SpaceLoop
              </div>
              <p className="text-[11px] text-slate-600 dark:text-slate-400 mb-2.5 leading-snug">
                Verified micro-desks & unused spaces starting at ₹35/hr.
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onOpenAuthModal();
                  }}
                  className="flex-1 py-1.5 px-2.5 rounded-xl bg-[#0B3D91] hover:bg-[#072C6B] dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white text-xs font-bold shadow-sm transition"
                >
                  Seeker Sign In
                </button>
                {onOpenHostAuthModal && (
                  <button
                    type="button"
                    onClick={() => {
                      onClose();
                      onOpenHostAuthModal();
                    }}
                    className="flex-1 py-1.5 px-2.5 rounded-xl bg-white hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-750 text-slate-800 dark:text-slate-200 border border-[#D0E6F7] dark:border-slate-700 text-xs font-bold shadow-2xs transition"
                  >
                    Host Sign In
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* =====================================================================
            DRAWER NAVIGATION DIRECTORY (Bounded, Scaled & High-Contrast)
            ===================================================================== */}
        <nav className="flex-1 overflow-y-auto overscroll-contain px-3 sm:px-4 py-2 space-y-1 focus:outline-none">
          <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 px-2 py-1">
            {isHostPortal ? 'Host Navigation' : 'Seeker Navigation'}
          </div>

          {navItems.map((item) => {
            const isActive =
              location.pathname === item.path ||
              (item.path !== '/' && location.pathname.startsWith(item.path));

            return (
              <button
                key={item.path}
                type="button"
                onClick={() => handleNavigate(item.path)}
                className={`w-full group flex items-center gap-2.5 sm:gap-3 px-2.5 sm:px-3 py-2 rounded-xl text-left transition-all duration-150 ${
                  isActive
                    ? 'bg-[#0B3D91]/10 text-[#0B3D91] border border-[#0B3D91]/25 dark:bg-indigo-600/20 dark:text-indigo-300 dark:border-indigo-500/30 font-bold shadow-2xs'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-[#F0F8FF] dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-white border border-transparent'
                }`}
              >
                {/* Fixed Icon Container */}
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-sm transition-transform group-hover:scale-105 ${item.iconBg}`}
                >
                  <i className={`${item.icon} ${item.iconColor}`} />
                </div>

                {/* Scaled Text & Subtitle Container (Always fits without breaking) */}
                <div className="flex-1 min-w-0 pr-1">
                  <div className="flex items-center justify-between gap-1.5">
                    <span
                      className={`text-xs sm:text-sm font-semibold truncate ${
                        isActive
                          ? 'text-[#0B3D91] dark:text-indigo-300 font-bold'
                          : 'text-slate-900 dark:text-white'
                      }`}
                    >
                      {item.label}
                    </span>
                    {item.badge && (
                      <span
                        className={`text-[9px] font-mono px-1.5 py-0.5 rounded-full font-bold border shrink-0 ${item.badgeStyle}`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </div>
                  <p
                    className={`text-[10px] sm:text-[11px] truncate mt-0.5 font-normal ${
                      isActive
                        ? 'text-[#0B3D91]/80 dark:text-indigo-300/80 font-medium'
                        : 'text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    {item.subtitle}
                  </p>
                </div>

                {/* Trailing Chevron */}
                <i className="fa-solid fa-chevron-right text-[9px] text-slate-400 group-hover:translate-x-0.5 transition-transform shrink-0" />
              </button>
            );
          })}
        </nav>

        {/* =====================================================================
            DRAWER FOOTER UTILITIES (Theme, Language, Portal Switcher)
            ===================================================================== */}
        <div className="p-3 sm:p-4 border-t border-[#D0E6F7] dark:border-slate-800/80 bg-[#E8F6FF]/40 dark:bg-slate-900/60 space-y-2 shrink-0">
          {/* Row 1: Theme & Language Bar */}
          <div className="flex items-center justify-between gap-2">
            <button
              type="button"
              onClick={toggleTheme}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition shadow-2xs border bg-white hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-750 text-[#0B2545] dark:text-slate-200 border-[#D0E6F7] dark:border-slate-700"
              title={theme === 'dark' ? 'Switch to Light Theme (Ocean Breeze)' : 'Switch to Dark Theme (Midnight Neon)'}
            >
              {theme === 'dark' ? (
                <>
                  <span className="text-amber-400">☀️</span>
                  <span>Ocean Breeze</span>
                </>
              ) : (
                <>
                  <span className="text-[#0B3D91]">🌙</span>
                  <span>Midnight Neon</span>
                </>
              )}
            </button>

            <div className="shrink-0">
              <LanguageSelector dropUp={true} />
            </div>
          </div>

          {/* Row 2: Portal Switch CTA */}
          {isHostPortal ? (
            <button
              type="button"
              onClick={() => handleNavigate('/explore')}
              className="w-full py-2 px-3 rounded-xl bg-[#0B3D91]/10 hover:bg-[#0B3D91]/20 text-[#0B3D91] dark:bg-indigo-600/20 dark:hover:bg-indigo-600/30 dark:text-indigo-300 border border-[#0B3D91]/30 dark:border-indigo-500/30 text-xs font-bold transition flex items-center justify-center gap-1.5 shadow-2xs"
            >
              <span>🎓 Switch to Seeker Portal</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => handleNavigate('/host/dashboard')}
              className="w-full py-2 px-3 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 text-amber-700 dark:text-amber-300 border border-amber-500/30 text-xs font-bold transition flex items-center justify-center gap-1.5 shadow-2xs"
            >
              <span>🏡 Switch to Host Portal</span>
            </button>
          )}

          <div className="text-[10px] text-center text-slate-500 dark:text-slate-400 font-mono">
            SpaceLoop • Section 52 Micro-Leasing
          </div>
        </div>
      </aside>
    </>
  );
};

export default NavigationDrawer;
