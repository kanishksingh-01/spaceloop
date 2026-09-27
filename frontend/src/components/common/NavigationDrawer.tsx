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
 * Fully isolated, undo-safe component providing:
 * - Animated 3-line to 'X' Hamburger Button
 * - 60fps gesture-based physical dragging (Touch & Pointer events)
 * - Edge-swipe / peek interaction when drawer is closed
 * - Spring-like velocity-aware settling on release
 * - Keyboard accessibility (ESC to close, focus management)
 * - Full dual-theme compatibility (Ocean Breeze & Midnight Neon)
 * - Zero external animation libraries (vanilla React + CSS transforms)
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
      className={`group relative flex flex-col justify-center items-center w-10 h-10 rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#0B3D91]/40 dark:focus:ring-indigo-500/50 ${
        isOpen
          ? 'bg-slate-200/80 dark:bg-slate-800 text-slate-900 dark:text-white'
          : 'bg-white/80 hover:bg-[#E8F6FF] dark:bg-slate-900/80 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 hover:text-[#0B3D91] dark:hover:text-white border border-[#D0E6F7] dark:border-slate-800 shadow-sm'
      } ${className}`}
    >
      <span className="sr-only">{isOpen ? 'Close menu' : 'Open menu'}</span>
      <div className="w-5 h-4 relative flex flex-col justify-between items-center pointer-events-none">
        {/* Top Bar */}
        <span
          className={`h-0.5 w-5 bg-current rounded-full transform transition-all duration-300 ease-in-out origin-center ${
            isOpen ? 'rotate-45 translate-y-[7px]' : ''
          }`}
        />
        {/* Middle Bar */}
        <span
          className={`h-0.5 w-5 bg-current rounded-full transition-all duration-200 ease-in-out ${
            isOpen ? 'opacity-0 scale-x-0' : 'opacity-100'
          }`}
        />
        {/* Bottom Bar */}
        <span
          className={`h-0.5 w-5 bg-current rounded-full transform transition-all duration-300 ease-in-out origin-center ${
            isOpen ? '-rotate-45 -translate-y-[7px]' : ''
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

  // Measure actual drawer width on mount/resize
  useEffect(() => {
    const updateWidth = () => {
      if (drawerRef.current) {
        setDrawerWidth(drawerRef.current.offsetWidth || 360);
      } else {
        const measured = Math.min(360, window.innerWidth * 0.85);
        setDrawerWidth(measured);
      }
    };
    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  // Keyboard navigation & accessibility: ESC to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Lock body scroll when drawer is open
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
        // Dragging open from left edge: offset goes from 0 up to drawerWidth
        const clamped = Math.max(0, Math.min(deltaX, drawerWidth));
        setDragOffset(clamped);
      } else {
        // Dragging to close from open drawer: offset is negative (pulling left)
        if (deltaX > 0) {
          // Rubber band resistance if pulling right past open position
          setDragOffset(deltaX * 0.2);
        } else {
          // Normal drag left (clamped to -drawerWidth)
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
      // Swipe open threshold: distance > 25% width OR positive flick velocity
      const threshold = drawerWidth * 0.25;
      if (totalDelta > threshold || velocity > 0.3) {
        onOpen();
      } else {
        onClose();
      }
    } else {
      // Swipe close threshold: pulled left > 25% width OR negative flick velocity
      const threshold = drawerWidth * -0.25;
      if (totalDelta < threshold || velocity < -0.3) {
        onClose();
      } else {
        // Reset to fully open
        onOpen();
      }
    }

    setDragOffset(null);
  }, [isDragging, drawerWidth, onOpen, onClose]);

  // Pointer event listeners (desktop mouse + tablet/mobile touch)
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
      translateX = dragOffset; // e.g. -60px when pulling left
      const progress = Math.max(0, Math.min(1, 1 + dragOffset / drawerWidth));
      backdropOpacity = progress;
    } else {
      translateX = 0;
      backdropOpacity = 1;
    }
  } else {
    if (dragOffset !== null && isEdgeDrag.current) {
      translateX = -drawerWidth + dragOffset; // starts at -drawerWidth, goes towards 0
      const progress = Math.max(0, Math.min(1, dragOffset / drawerWidth));
      backdropOpacity = progress;
    } else {
      translateX = -drawerWidth - 20; // completely offscreen
      backdropOpacity = 0;
    }
  }

  const isVisible = isOpen || (isDragging && isEdgeDrag.current);

  return (
    <>
      {/* =====================================================================
          1. INVISIBLE EDGE TRIGGER (Swipe-from-edge peek detector when closed)
          ===================================================================== */}
      {!isOpen && (
        <div
          onPointerDown={(e) => {
            // Only trigger on primary button / touch
            if (e.button === 0) {
              startDrag(e.clientX, true);
            }
          }}
          className="fixed top-0 left-0 bottom-0 w-4 z-40 cursor-grab active:cursor-grabbing touch-none select-none hover:w-6 transition-all duration-200"
          title="Drag from edge to open menu"
          aria-hidden="true"
        >
          {/* Subtle indicator bar on edge hover */}
          <div className="absolute top-1/2 -translate-y-1/2 left-0.5 w-1 h-12 rounded-r-full bg-[#0B3D91]/30 dark:bg-indigo-500/30 opacity-0 hover:opacity-100 transition-opacity" />
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
          3. INTERACTIVE PHYSICAL SLIDING DRAWER
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
        className="fixed top-0 left-0 bottom-0 w-[320px] sm:w-[360px] max-w-[85vw] z-50 flex flex-col bg-white dark:bg-slate-950 text-slate-800 dark:text-slate-100 border-r border-[#D0E6F7] dark:border-slate-800/90 shadow-[8px_0_35px_-5px_rgba(11,61,145,0.12)] dark:shadow-[8px_0_40px_-5px_rgba(0,0,0,0.8)] backdrop-blur-2xl will-change-transform select-none"
      >
        {/* PHYSICAL DRAG HANDLE TAB (Visible on the right edge of drawer) */}
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
            DRAWER HEADER (Brand, Active Portal, Close Button)
            ===================================================================== */}
        <div className="p-4 sm:p-5 border-b border-[#D0E6F7] dark:border-slate-800/80 flex items-center justify-between gap-3 bg-[#E8F6FF]/50 dark:bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center shadow-md ${
                isHostPortal
                  ? 'bg-gradient-to-tr from-amber-600 via-orange-600 to-amber-400 shadow-amber-500/20'
                  : 'bg-gradient-to-tr from-[#0B3D91] via-[#1E40AF] to-[#3BA7F2] dark:from-indigo-600 dark:via-violet-600 dark:to-indigo-400 shadow-indigo-500/20'
              }`}
            >
              <i className="fa-solid fa-infinity text-white text-lg" />
            </div>
            <div>
              <div className="text-lg font-extrabold tracking-tight text-slate-900 dark:text-white font-display flex items-center gap-1">
                Space<span className="text-[#0B3D91] dark:text-indigo-400">Loop</span>
              </div>
              <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                {isHostPortal ? '🏡 Host Space' : '⚡ Seeker Desk'}
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close navigation drawer"
            className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-800/80 transition"
          >
            <i className="fa-solid fa-xmark text-sm" />
          </button>
        </div>

        {/* =====================================================================
            DRAWER USER PROFILE CARD (Session Status & Quick Sign-In)
            ===================================================================== */}
        <div className="p-4 border-b border-[#D0E6F7] dark:border-slate-800/80 bg-white dark:bg-slate-950">
          {currentUser ? (
            <div className="p-3.5 rounded-2xl bg-[#F0F8FF] dark:bg-slate-900/80 border border-[#D0E6F7] dark:border-slate-800 flex items-center justify-between gap-3 shadow-2xs">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-10 h-10 rounded-xl bg-[#0B3D91] dark:bg-indigo-600 text-white font-bold text-sm flex items-center justify-center shrink-0 shadow-sm">
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
                    <i className="fa-solid fa-circle-check text-[9px]" /> Verified Member
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="p-2 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition text-xs shrink-0"
                title="Sign Out"
              >
                <i className="fa-solid fa-arrow-right-from-bracket" />
              </button>
            </div>
          ) : (
            <div className="p-3.5 rounded-2xl bg-gradient-to-br from-[#E8F6FF] to-[#F0F8FF] dark:from-slate-900 dark:to-slate-900/60 border border-[#D0E6F7] dark:border-slate-800 text-center">
              <div className="text-xs font-bold text-slate-900 dark:text-white mb-1">
                Welcome to SpaceLoop
              </div>
              <p className="text-[11px] text-slate-600 dark:text-slate-400 mb-3 leading-snug">
                Access verified micro-desks, studios, and unused workspaces across India starting at ₹35/hr.
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onOpenAuthModal();
                  }}
                  className="flex-1 py-2 px-3 rounded-xl bg-[#0B3D91] hover:bg-[#072C6B] dark:bg-indigo-600 dark:hover:bg-indigo-500 text-white text-xs font-bold shadow-sm transition"
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
                    className="flex-1 py-2 px-3 rounded-xl bg-white hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-750 text-slate-800 dark:text-slate-200 border border-[#D0E6F7] dark:border-slate-700 text-xs font-bold shadow-2xs transition"
                  >
                    Host Sign In
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* =====================================================================
            DRAWER NAVIGATION LINKS (Tactile Hover & Visible Labels)
            ===================================================================== */}
        <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-1">
          <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 px-3 py-1.5">
            Navigation Directory
          </div>

          {/* 1. Home */}
          <button
            type="button"
            onClick={() => handleNavigate('/')}
            className={`w-full group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
              location.pathname === '/'
                ? 'bg-[#0B3D91]/10 text-[#0B3D91] dark:bg-indigo-600/20 dark:text-indigo-300 font-bold'
                : 'text-slate-700 dark:text-slate-300 hover:bg-[#F0F8FF] dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <i className="fa-solid fa-house w-4 text-center text-[#0B3D91] dark:text-indigo-400 group-hover:scale-110 transition-transform" />
              <span>{t('nav.home') || 'Home'}</span>
            </div>
            <i className="fa-solid fa-chevron-right text-[10px] text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>

          {/* 2. Explore Spaces */}
          <button
            type="button"
            onClick={() => handleNavigate('/explore')}
            className={`w-full group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
              location.pathname === '/explore'
                ? 'bg-[#0B3D91]/10 text-[#0B3D91] dark:bg-indigo-600/20 dark:text-indigo-300 font-bold'
                : 'text-slate-700 dark:text-slate-300 hover:bg-[#F0F8FF] dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <i className="fa-solid fa-compass w-4 text-center text-[#3BA7F2] dark:text-cyan-400 group-hover:scale-110 transition-transform" />
              <span>{t('nav.explore') || 'Explore Spaces'}</span>
            </div>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold border border-emerald-500/20">
              Live
            </span>
          </button>

          {/* 3. My Bookings / Dashboard */}
          <button
            type="button"
            onClick={() => handleNavigate('/dashboard')}
            className={`w-full group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
              location.pathname === '/dashboard'
                ? 'bg-[#0B3D91]/10 text-[#0B3D91] dark:bg-indigo-600/20 dark:text-indigo-300 font-bold'
                : 'text-slate-700 dark:text-slate-300 hover:bg-[#F0F8FF] dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <i className="fa-solid fa-calendar-check w-4 text-center text-indigo-500 group-hover:scale-110 transition-transform" />
              <span>{t('nav.myBookings') || 'My Bookings & Passes'}</span>
            </div>
            <i className="fa-solid fa-chevron-right text-[10px] text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>

          {/* 4. Host Portal & List Space */}
          <button
            type="button"
            onClick={() => handleNavigate('/host/dashboard')}
            className={`w-full group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
              location.pathname.startsWith('/host')
                ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300 font-bold'
                : 'text-slate-700 dark:text-slate-300 hover:bg-amber-50 dark:hover:bg-amber-950/20 hover:text-amber-700 dark:hover:text-amber-300'
            }`}
          >
            <div className="flex items-center gap-3">
              <i className="fa-solid fa-chart-pie w-4 text-center text-amber-500 group-hover:scale-110 transition-transform" />
              <span>{t('nav.hostPortal') || 'Host Dashboard & Properties'}</span>
            </div>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-700 dark:text-amber-400 font-bold border border-amber-500/20">
              Host
            </span>
          </button>

          {/* 5. List a New Space */}
          <button
            type="button"
            onClick={() => handleNavigate('/list-space')}
            className={`w-full group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
              location.pathname === '/list-space'
                ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300 font-bold'
                : 'text-slate-700 dark:text-slate-300 hover:bg-[#F0F8FF] dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <i className="fa-solid fa-plus-circle w-4 text-center text-amber-500 group-hover:scale-110 transition-transform" />
              <span>{t('nav.listSpace') || 'List an Unused Space'}</span>
            </div>
            <i className="fa-solid fa-chevron-right text-[10px] text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>

          {/* 6. Yield Calculator */}
          <button
            type="button"
            onClick={() => handleNavigate('/calculator')}
            className={`w-full group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
              location.pathname === '/calculator'
                ? 'bg-[#0B3D91]/10 text-[#0B3D91] dark:bg-indigo-600/20 dark:text-indigo-300 font-bold'
                : 'text-slate-700 dark:text-slate-300 hover:bg-[#F0F8FF] dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <i className="fa-solid fa-calculator w-4 text-center text-emerald-500 group-hover:scale-110 transition-transform" />
              <span>{t('nav.calculator') || 'Earnings Yield Calculator'}</span>
            </div>
            <i className="fa-solid fa-chevron-right text-[10px] text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>

          {/* 7. Architecture & Team Directory */}
          <button
            type="button"
            onClick={() => handleNavigate('/architecture')}
            className={`w-full group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
              location.pathname === '/architecture'
                ? 'bg-[#0B3D91]/15 text-[#0B3D91] dark:bg-indigo-600/30 dark:text-indigo-200 font-bold border border-[#0B3D91]/30 dark:border-indigo-500/40 shadow-xs'
                : 'text-slate-700 dark:text-slate-300 hover:bg-[#F0F8FF] dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <i className="fa-solid fa-cubes w-4 text-center text-[#0B3D91] dark:text-indigo-400 group-hover:scale-110 transition-transform" />
              <span>{t('nav.architecture') || 'Architecture & Core Team'}</span>
            </div>
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#0B3D91]/10 text-[#0B3D91] dark:bg-indigo-500/20 dark:text-indigo-300 font-bold border border-[#0B3D91]/20 dark:border-indigo-500/30">
              Team
            </span>
          </button>

          {/* 8. Trust, Verification & KYC */}
          <button
            type="button"
            onClick={() => handleNavigate('/verify')}
            className={`w-full group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
              location.pathname === '/verify'
                ? 'bg-[#0B3D91]/10 text-[#0B3D91] dark:bg-indigo-600/20 dark:text-indigo-300 font-bold'
                : 'text-slate-700 dark:text-slate-300 hover:bg-[#F0F8FF] dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <i className="fa-solid fa-shield-halved w-4 text-center text-rose-500 group-hover:scale-110 transition-transform" />
              <span>{t('nav.verify') || 'Identity & Trust Verification'}</span>
            </div>
            <i className="fa-solid fa-chevron-right text-[10px] text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>

          {/* 9. How SpaceLoop Works */}
          <button
            type="button"
            onClick={() => handleNavigate('/how-it-works')}
            className={`w-full group flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-150 ${
              location.pathname === '/how-it-works'
                ? 'bg-[#0B3D91]/10 text-[#0B3D91] dark:bg-indigo-600/20 dark:text-indigo-300 font-bold'
                : 'text-slate-700 dark:text-slate-300 hover:bg-[#F0F8FF] dark:hover:bg-slate-900 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <div className="flex items-center gap-3">
              <i className="fa-solid fa-circle-question w-4 text-center text-violet-500 group-hover:scale-110 transition-transform" />
              <span>{t('nav.howItWorks') || 'How SpaceLoop Works'}</span>
            </div>
            <i className="fa-solid fa-chevron-right text-[10px] text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </button>
        </nav>

        {/* =====================================================================
            DRAWER FOOTER UTILITIES (Theme, Language, Portal Switcher)
            ===================================================================== */}
        <div className="p-4 border-t border-[#D0E6F7] dark:border-slate-800/80 bg-[#E8F6FF]/40 dark:bg-slate-900/60 space-y-2.5">
          {/* Theme & Language Bar */}
          <div className="flex items-center justify-between gap-2">
            <button
              type="button"
              onClick={toggleTheme}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition shadow-2xs border bg-white hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-750 text-[#0B2545] dark:text-slate-200 border-[#D0E6F7] dark:border-slate-700"
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
              <LanguageSelector />
            </div>
          </div>

          {/* Portal Switch CTA */}
          {isHostPortal ? (
            <button
              type="button"
              onClick={() => handleNavigate('/explore')}
              className="w-full py-2.5 px-3 rounded-xl bg-[#0B3D91]/10 hover:bg-[#0B3D91]/20 text-[#0B3D91] dark:bg-indigo-600/20 dark:hover:bg-indigo-600/30 dark:text-indigo-300 border border-[#0B3D91]/30 dark:border-indigo-500/30 text-xs font-bold transition flex items-center justify-center gap-2"
            >
              <span>🎓 Switch to Seeker Portal</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => handleNavigate('/host/dashboard')}
              className="w-full py-2.5 px-3 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 text-amber-700 dark:text-amber-300 border border-amber-500/30 text-xs font-bold transition flex items-center justify-center gap-2"
            >
              <span>🏡 Switch to Host Portal</span>
            </button>
          )}

          <div className="text-[10px] text-center text-slate-500 dark:text-slate-400 font-mono pt-1">
            SpaceLoop • Section 52 Micro-Leasing
          </div>
        </div>
      </aside>
    </>
  );
};

export default NavigationDrawer;
