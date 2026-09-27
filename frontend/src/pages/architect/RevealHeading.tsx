import React, { useEffect, useState, useRef } from 'react';
import { RevealBar } from './RevealBar';

interface RevealHeadingProps {
  text: string;
  as?: 'h1' | 'h2' | 'h3';
  className?: string;
  delay?: number;
  duration?: number;
  triggerOnScroll?: boolean;
  gradientFromIndex?: number; // Optional character index where brand gradient begins
  gradientClassName?: string;
  onComplete?: () => void;
  prefersReducedMotion?: boolean;
}

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
  const [progress, setProgress] = useState(prefersReducedMotion ? 1 : 0);
  const [isRevealing, setIsRevealing] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);

  // If reduced motion is requested, reveal immediately
  useEffect(() => {
    if (prefersReducedMotion) {
      setProgress(1);
      setIsRevealing(false);
      onComplete?.();
    }
  }, [prefersReducedMotion, onComplete]);

  // Handle scroll trigger or delayed start
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

  // Synchronized scanner animation loop
  useEffect(() => {
    if (!hasStarted || prefersReducedMotion) return;

    setIsRevealing(true);
    let startTime: number | null = null;
    let rafId: number;

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const rawProgress = Math.min(elapsed / duration, 1);

      // Smooth cubic easing for natural deceleration
      // easeOutCubic: 1 - Math.pow(1 - progress, 3)
      const currentProgress = rawProgress;
      setProgress(currentProgress);

      if (rawProgress < 1) {
        rafId = requestAnimationFrame(animate);
      } else {
        setIsRevealing(false);
        onComplete?.();
      }
    };

    rafId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafId);
  }, [hasStarted, duration, prefersReducedMotion, onComplete]);

  const chars = Array.from(text);
  const totalChars = chars.length;

  return (
    <Component
      className={className}
      aria-label={text}
    >
      <div
        ref={containerRef}
        className="ag-reveal-heading-wrapper"
        aria-hidden="true"
      >
        {/* Synchronized Scanner Reveal Bar */}
        <RevealBar
          leftPercent={progress * 100}
          isVisible={isRevealing}
          prefersReducedMotion={prefersReducedMotion}
        />

        {/* Character-by-Character Elements */}
        {chars.map((char, index) => {
          const charThreshold = totalChars > 1 ? index / (totalChars - 1) : 0;
          const isRevealed = prefersReducedMotion || progress >= charThreshold;
          const isGradient = gradientFromIndex >= 0 && index >= gradientFromIndex;

          return (
            <span
              key={index}
              className={`ag-reveal-char ${isRevealed ? 'ag-char-revealed' : ''} ${
                isGradient ? gradientClassName : ''
              }`}
              style={{
                // Preserve spaces with white-space pre
                whiteSpace: char === ' ' ? 'pre' : 'normal',
                transitionDelay: prefersReducedMotion ? '0ms' : `${Math.max(0, (index / totalChars) * 120)}ms`,
              }}
            >
              {char}
            </span>
          );
        })}
      </div>
    </Component>
  );
};

export default RevealHeading;
