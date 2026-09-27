import React, { useEffect, useState, useRef } from 'react';
import { RevealBar } from './RevealBar';

interface RevealHeadingProps {
  text: string;
  as?: 'h1' | 'h2' | 'h3';
  className?: string;
  delay?: number;
  duration?: number;
  triggerOnScroll?: boolean;
  gradientFromIndex?: number;
  gradientClassName?: string;
  onComplete?: () => void;
  prefersReducedMotion?: boolean;
}

/**
 * RevealHeading — Antigravity Precision Optical Reveal
 * ----------------------------------------------------------------------------
 * - Characters are strictly hidden (opacity: 0) before the cursor passes through.
 * - NOTHING is displayed ahead of the optical cursor.
 * - Each letter reveals in crisp focus ONLY after the cursor has crossed it.
 * - The precision optical cursor leads the uncover sequence with exact DOM tracking.
 * - Natural word grouping preserves responsive wrapping without mid-word breaks.
 */
export const RevealHeading: React.FC<RevealHeadingProps> = ({
  text,
  as: Component = 'h1',
  className = '',
  delay = 200,
  duration = 850,
  triggerOnScroll = false,
  gradientFromIndex = -1,
  gradientClassName = 'text-transparent bg-clip-text bg-gradient-to-r from-[#0B3D91] via-[#1E40AF] to-[#3BA7F2] dark:from-cyan-400 dark:via-indigo-300 dark:to-violet-400',
  onComplete,
  prefersReducedMotion = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const charRefs = useRef<(HTMLSpanElement | null)[]>([]);
  const [hasStarted, setHasStarted] = useState(false);
  // -1 means no characters revealed yet (initial state: 100% hidden)
  const [revealedCount, setRevealedCount] = useState<number>(prefersReducedMotion ? text.length : 0);
  const [cursorPos, setCursorPos] = useState<{
    x: number;
    y: number;
    height: number;
    visible: boolean;
  }>({
    x: 0,
    y: 0,
    height: 0,
    visible: false,
  });

  // Reduced motion: reveal all characters immediately without animation delay
  useEffect(() => {
    if (prefersReducedMotion) {
      setRevealedCount(text.length);
      setCursorPos((prev) => ({ ...prev, visible: false }));
      onComplete?.();
    }
  }, [prefersReducedMotion, text.length, onComplete]);

  // Trigger reveal on scroll intersection or scheduled delay
  useEffect(() => {
    if (prefersReducedMotion || hasStarted) return;

    if (triggerOnScroll && containerRef.current) {
      const observer = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting) {
            setHasStarted(true);
            observer.disconnect();
          }
        },
        { threshold: 0.25 }
      );

      observer.observe(containerRef.current);
      return () => observer.disconnect();
    } else {
      const timer = setTimeout(() => {
        setHasStarted(true);
      }, delay);
      return () => clearTimeout(timer);
    }
  }, [triggerOnScroll, delay, hasStarted, prefersReducedMotion]);

  // Synchronized Optical Cursor & Letter Reveal Loop
  useEffect(() => {
    if (!hasStarted || prefersReducedMotion) return;

    let startTime: number | null = null;
    let rafId: number;
    const totalChars = text.length;

    // Helper to measure character boundaries relative to heading wrapper
    const getMetrics = () => {
      if (!containerRef.current) return null;
      const cRect = containerRef.current.getBoundingClientRect();
      const metrics = charRefs.current.map((el) => {
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return {
          left: r.left - cRect.left,
          right: r.right - cRect.left,
          top: r.top - cRect.top,
          height: r.height,
        };
      });
      return { cRect, metrics };
    };

    let cached = getMetrics();

    const animate = (timestamp: number) => {
      if (!startTime) {
        startTime = timestamp;
        cached = getMetrics();
      }

      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Current position along the character index sequence
      const currentPos = progress * totalChars;
      const activeCharIdx = Math.min(Math.floor(currentPos), totalChars - 1);
      const charFraction = currentPos - Math.floor(currentPos);

      // Only reveal characters whose right/trailing edge has been reached/passed
      // Characters ahead of the cursor remain strictly opacity: 0
      const count = Math.min(Math.floor(currentPos), totalChars);
      setRevealedCount(count);

      // Compute optical cursor coordinates
      if (cached && cached.metrics[activeCharIdx]) {
        const m = cached.metrics[activeCharIdx];
        let targetX = m.left + (m.right - m.left) * charFraction;
        let targetY = m.top;
        let targetH = m.height || 28;

        if (progress >= 1) {
          targetX = m.right;
        }

        setCursorPos({
          x: targetX,
          y: targetY,
          height: targetH,
          visible: progress < 1,
        });
      } else if (containerRef.current) {
        // Fallback relative to container width
        const w = containerRef.current.offsetWidth;
        setCursorPos({
          x: progress * w,
          y: 0,
          height: containerRef.current.offsetHeight,
          visible: progress < 1,
        });
      }

      if (progress < 1) {
        rafId = requestAnimationFrame(animate);
      } else {
        setRevealedCount(totalChars);
        setCursorPos((prev) => ({ ...prev, visible: false }));
        onComplete?.();
      }
    };

    rafId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafId);
  }, [hasStarted, duration, text.length, prefersReducedMotion, onComplete]);

  const words = text.split(' ');
  let charCounter = 0;

  return (
    <Component className={className} aria-label={text}>
      <div
        ref={containerRef}
        className="ag-reveal-heading-wrapper"
        aria-hidden="true"
      >
        {/* Precision Optical Scanner Cursor Bar */}
        <RevealBar
          x={cursorPos.x}
          y={cursorPos.y}
          height={cursorPos.height}
          isVisible={cursorPos.visible}
          prefersReducedMotion={prefersReducedMotion}
        />

        {/* Word-grouped Character Spans (Natural Responsive Wrapping) */}
        {words.map((word, wordIdx) => {
          const wordChars = Array.from(word);
          const startIndex = charCounter;
          charCounter += word.length + 1; // +1 for the space

          return (
            <React.Fragment key={wordIdx}>
              <span className="inline-block whitespace-nowrap">
                {wordChars.map((char, charInWordIdx) => {
                  const absoluteCharIdx = startIndex + charInWordIdx;
                  // REVEALED ONLY AFTER CURSOR HAS PASSED THROUGH
                  // Ahead of cursor: strictly false (opacity: 0)
                  const isRevealed = prefersReducedMotion || absoluteCharIdx < revealedCount;
                  const isGradient = gradientFromIndex >= 0 && absoluteCharIdx >= gradientFromIndex;

                  return (
                    <span
                      key={charInWordIdx}
                      ref={(el) => {
                        charRefs.current[absoluteCharIdx] = el;
                      }}
                      className={`ag-reveal-char ${isRevealed ? 'ag-char-revealed' : ''} ${
                        isGradient ? gradientClassName : ''
                      }`}
                    >
                      {char}
                    </span>
                  );
                })}
              </span>
              {wordIdx < words.length - 1 && (
                <span className="ag-reveal-space"> </span>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </Component>
  );
};

export default RevealHeading;
