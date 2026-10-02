import React, { useRef, useState, useEffect } from 'react';

/**
 * Lightweight Motion Adapter for React 18 / Vite
 * Emulates motion/react primitives with zero runtime bundle overhead.
 */

export const stagger = (delay = 0.1) => {
  return (index: number) => index * delay;
};

export const useInView = (ref: React.RefObject<any>, options?: IntersectionObserverInit) => {
  const [isInView, setIsInView] = useState(true);

  useEffect(() => {
    if (!ref.current || typeof IntersectionObserver === 'undefined') {
      setIsInView(true);
      return;
    }

    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsInView(true);
      }
    }, options);

    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [ref]);

  return isInView;
};

export const useAnimate = () => {
  const scope = useRef<HTMLDivElement>(null);

  const animate = (
    selector: string,
    keyframes: Record<string, any>,
    options?: { duration?: number; delay?: number | ((i: number) => number); ease?: string }
  ) => {
    if (!scope.current) return;
    const elements = scope.current.querySelectorAll(selector);
    elements.forEach((el, index) => {
      const htmlEl = el as HTMLElement;
      const delayMs = typeof options?.delay === 'function' ? options.delay(index) * 1000 : (options?.delay || 0) * 1000;
      const durationMs = (options?.duration || 0.3) * 1000;

      setTimeout(() => {
        htmlEl.style.transition = `all ${durationMs}ms ${options?.ease || 'ease-in-out'}`;
        if (keyframes.display) htmlEl.style.display = keyframes.display;
        if (keyframes.opacity !== undefined) htmlEl.style.opacity = String(keyframes.opacity);
        if (keyframes.width) htmlEl.style.width = keyframes.width;
      }, delayMs);
    });
  };

  return [scope, animate] as const;
};

const createMotionComponent = (tag: string) => {
  return React.forwardRef<any, any>(({ initial, animate, whileInView, transition, className, style, children, ...props }, ref) => {
    const internalRef = useRef<HTMLElement>(null);
    const combinedRef = ref || internalRef;
    const [inView, setInView] = useState(true);

    useEffect(() => {
      if (whileInView) {
        setInView(true);
      }
    }, [whileInView]);

    return React.createElement(
      tag,
      {
        ref: combinedRef,
        className,
        style: {
          ...style,
        },
        ...props,
      },
      children
    );
  });
};

export const motion = {
  div: createMotionComponent('div'),
  span: createMotionComponent('span'),
  p: createMotionComponent('p'),
  h1: createMotionComponent('h1'),
  h2: createMotionComponent('h2'),
  h3: createMotionComponent('h3'),
  button: createMotionComponent('button'),
  section: createMotionComponent('section'),
  a: createMotionComponent('a'),
};

export const AnimatePresence: React.FC<{ children: React.ReactNode }> = ({ children }) => <>{children}</>;
