import React, { useEffect, useRef } from 'react';
import { useLocation, useNavigationType } from 'react-router-dom';

/**
 * ScrollRestorationManager
 * 
 * SpaceLoop Unified Scroll & Navigation Experience Engine
 * - Automatically ensures new page routes arrive at the intended top (0, 0)
 * - Smoothly navigates to internal same-page and cross-page anchor sections (#...)
 * - Offsets scroll positions by 80px so headings are never covered by the sticky header (64px h-16 + 16px buffer)
 * - Preserves natural browser back / forward (POP) history restoration
 * - Respects prefers-reduced-motion for accessibility
 */
export const ScrollRestorationManager: React.FC = () => {
  const location = useLocation();
  const navigationType = useNavigationType();
  const prevPathRef = useRef<string>(location.pathname);
  const prevHashRef = useRef<string>(location.hash);

  const prefersReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const scrollBehavior: ScrollBehavior = prefersReducedMotion ? 'auto' : 'smooth';

  // Smooth scroll to an element by ID or selector accounting for sticky header offset
  const scrollToAnchor = (hash: string, attempt = 0) => {
    const rawId = hash.replace(/^#/, '');
    if (!rawId) return;

    // Decode in case of URI encoding
    let id = rawId;
    try {
      id = decodeURIComponent(rawId);
    } catch {}

    const element =
      document.getElementById(id) ||
      document.querySelector(`[id="${id}"]`) ||
      document.querySelector(`a[name="${id}"]`);

    if (element) {
      const headerOffset = 80; // 64px header height + 16px breathing room
      const elementPosition = element.getBoundingClientRect().top;
      const targetPosition = elementPosition + window.pageYOffset - headerOffset;

      window.scrollTo({
        top: Math.max(0, targetPosition),
        left: 0,
        behavior: scrollBehavior,
      });
    } else if (attempt < 12) {
      // Lazy-loaded routes / suspense chunks may take a short moment to mount
      setTimeout(() => {
        scrollToAnchor(hash, attempt + 1);
      }, 50 * (attempt + 1));
    }
  };

  useEffect(() => {
    const isNewRoute = prevPathRef.current !== location.pathname;
    const isNewHash = prevHashRef.current !== location.hash;

    if (location.hash) {
      // Anchor link: scroll smoothly to element with header offset
      scrollToAnchor(location.hash);
    } else if (isNewRoute) {
      // Navigating to a different route:
      // When navigating forward (PUSH or REPLACE), start cleanly at top: 0
      // When navigating back / forward (POP), preserve browser history scroll position
      if (navigationType !== 'POP') {
        window.scrollTo({
          top: 0,
          left: 0,
          behavior: 'auto',
        });
      }
    }

    prevPathRef.current = location.pathname;
    prevHashRef.current = location.hash;
  }, [location.pathname, location.search, location.hash, navigationType]);

  // Global handler for anchor links (<a href="#..."> or <a href="/#...">)
  useEffect(() => {
    const handleDocumentClick = (e: MouseEvent) => {
      const target = (e.target as HTMLElement)?.closest('a');
      if (!target) return;

      const href = target.getAttribute('href');
      if (!href) return;

      if (href.startsWith('#')) {
        e.preventDefault();
        window.history.pushState(null, '', href);
        scrollToAnchor(href);
      } else if (href.startsWith('/#') && location.pathname === '/') {
        e.preventDefault();
        const hash = href.slice(1);
        window.history.pushState(null, '', hash);
        scrollToAnchor(hash);
      }
    };

    document.addEventListener('click', handleDocumentClick, { passive: false });
    return () => {
      document.removeEventListener('click', handleDocumentClick);
    };
  }, [location.pathname]);

  return null;
};

export default ScrollRestorationManager;
