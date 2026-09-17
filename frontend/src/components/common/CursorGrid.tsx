import React, { useRef, useEffect, useCallback } from 'react';

export interface CursorGridProps {
  cellSize?: number;
  color?: string;
  radius?: number;
  falloff?: 'linear' | 'smooth' | 'sharp';
  holdTime?: number;
  fadeDuration?: number;
  lineWidth?: number;
  maxOpacity?: number;
  fillOpacity?: number;
  gridOpacity?: number;
  cellRadius?: number;
  clickPulse?: boolean;
  pulseSpeed?: number;
  className?: string;
  style?: React.CSSProperties;
}

interface Pulse {
  x: number;
  y: number;
  startTime: number;
  maxRadius: number;
}

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  let clean = hex.replace('#', '').trim();
  if (clean.length === 3) {
    clean = clean
      .split('')
      .map((c) => c + c)
      .join('');
  }
  const num = parseInt(clean, 16);
  if (isNaN(num)) {
    return { r: 217, g: 70, b: 239 }; // Fallback to #D946EF
  }
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255,
  };
}

export const CursorGrid: React.FC<CursorGridProps> = ({
  cellSize = 70,
  color = '#D946EF',
  radius = 140,
  falloff = 'smooth',
  holdTime = 400,
  fadeDuration = 800,
  lineWidth = 1.2,
  maxOpacity = 1,
  fillOpacity = 0,
  gridOpacity = 0,
  cellRadius = 0,
  clickPulse = true,
  pulseSpeed = 600,
  className = '',
  style = {},
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Parse color to RGB
  const rgb = hexToRgb(color);

  // State refs to keep animation loop decoupled from React renders
  const mouseRef = useRef<{ x: number; y: number; active: boolean }>({
    x: -9999,
    y: -9999,
    active: false,
  });

  const cellStatesRef = useRef<
    Map<string, { lastLitTime: number; peakAlpha: number; currentAlpha: number }>
  >(new Map());

  const pulsesRef = useRef<Pulse[]>([]);
  const animFrameIdRef = useRef<number | null>(null);

  // Compute falloff factor between 0 and 1
  const getFalloffFactor = useCallback(
    (dist: number, maxDist: number): number => {
      if (dist >= maxDist) return 0;
      const t = dist / maxDist;
      if (falloff === 'linear') {
        return Math.max(0, 1 - t);
      }
      if (falloff === 'sharp') {
        return Math.pow(Math.max(0, 1 - t), 3);
      }
      // Smooth (smoothstep / cosine)
      return 0.5 * (1 + Math.cos(Math.PI * t));
    },
    [falloff]
  );

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    let width = 0;
    let height = 0;

    const resizeCanvas = () => {
      const rect = container.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      const dpr = window.devicePixelRatio || 1;

      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;

      ctx.resetTransform?.();
      ctx.scale(dpr, dpr);
    };

    resizeCanvas();
    const resizeObserver = new ResizeObserver(() => {
      resizeCanvas();
    });
    resizeObserver.observe(container);

    // Render loop
    const render = (now: number) => {
      if (width === 0 || height === 0) {
        animFrameIdRef.current = requestAnimationFrame(render);
        return;
      }

      ctx.clearRect(0, 0, width, height);

      const cols = Math.ceil(width / cellSize);
      const rows = Math.ceil(height / cellSize);
      const cellStates = cellStatesRef.current;
      const mouse = mouseRef.current;
      const pulses = pulsesRef.current;

      // 1. Draw static background grid lines if gridOpacity > 0
      if (gridOpacity > 0) {
        ctx.strokeStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${gridOpacity})`;
        ctx.lineWidth = lineWidth;
        for (let c = 0; c < cols; c++) {
          for (let r = 0; r < rows; r++) {
            const x = c * cellSize;
            const y = r * cellSize;
            if (cellRadius > 0 && typeof ctx.roundRect === 'function') {
              ctx.beginPath();
              ctx.roundRect(x, y, cellSize, cellSize, cellRadius);
              ctx.stroke();
            } else {
              ctx.strokeRect(x, y, cellSize, cellSize);
            }
          }
        }
      }

      // 2. Calculate interaction from cursor
      if (mouse.active) {
        // Calculate bounding box of cells affected by cursor radius
        const minCol = Math.max(0, Math.floor((mouse.x - radius) / cellSize));
        const maxCol = Math.min(cols - 1, Math.floor((mouse.x + radius) / cellSize));
        const minRow = Math.max(0, Math.floor((mouse.y - radius) / cellSize));
        const maxRow = Math.min(rows - 1, Math.floor((mouse.y + radius) / cellSize));

        for (let c = minCol; c <= maxCol; c++) {
          for (let r = minRow; r <= maxRow; r++) {
            const cx = c * cellSize + cellSize / 2;
            const cy = r * cellSize + cellSize / 2;
            const dist = Math.hypot(mouse.x - cx, mouse.y - cy);

            if (dist <= radius) {
              const factor = getFalloffFactor(dist, radius);
              const targetAlpha = factor * maxOpacity;
              const key = `${c},${r}`;
              const state = cellStates.get(key);

              if (!state || targetAlpha > state.currentAlpha) {
                cellStates.set(key, {
                  lastLitTime: now,
                  peakAlpha: targetAlpha,
                  currentAlpha: targetAlpha,
                });
              } else {
                state.lastLitTime = now;
              }
            }
          }
        }
      }

      // 3. Process click pulses
      if (pulses.length > 0) {
        const ringThickness = cellSize * 1.6;
        for (let i = pulses.length - 1; i >= 0; i--) {
          const pulse = pulses[i];
          const elapsed = now - pulse.startTime;
          const currentRadius = (elapsed / 1000) * pulseSpeed;

          if (currentRadius > pulse.maxRadius + ringThickness) {
            pulses.splice(i, 1);
            continue;
          }

          // Light up cells intersecting the expanding pulse wave
          const minCol = Math.max(0, Math.floor((pulse.x - currentRadius - ringThickness) / cellSize));
          const maxCol = Math.min(cols - 1, Math.floor((pulse.x + currentRadius + ringThickness) / cellSize));
          const minRow = Math.max(0, Math.floor((pulse.y - currentRadius - ringThickness) / cellSize));
          const maxRow = Math.min(rows - 1, Math.floor((pulse.y + currentRadius + ringThickness) / cellSize));

          for (let c = minCol; c <= maxCol; c++) {
            for (let r = minRow; r <= maxRow; r++) {
              const cx = c * cellSize + cellSize / 2;
              const cy = r * cellSize + cellSize / 2;
              const dist = Math.hypot(pulse.x - cx, pulse.y - cy);
              const diff = Math.abs(dist - currentRadius);

              if (diff <= ringThickness) {
                const pulseFalloff = Math.max(0, 1 - diff / ringThickness);
                const pulseAlpha = pulseFalloff * maxOpacity * Math.max(0, 1 - currentRadius / pulse.maxRadius);

                const key = `${c},${r}`;
                const state = cellStates.get(key);
                if (!state || pulseAlpha > state.currentAlpha) {
                  cellStates.set(key, {
                    lastLitTime: now,
                    peakAlpha: pulseAlpha,
                    currentAlpha: pulseAlpha,
                  });
                }
              }
            }
          }
        }
      }

      // 4. Update fading states & draw illuminated cells
      cellStates.forEach((state, key) => {
        const [cStr, rStr] = key.split(',');
        const c = parseInt(cStr, 10);
        const r = parseInt(rStr, 10);
        const x = c * cellSize;
        const y = r * cellSize;

        // Calculate opacity based on holdTime and fadeDuration
        const timeSinceLit = now - state.lastLitTime;
        let alpha = state.peakAlpha;

        if (timeSinceLit > holdTime) {
          const fadeElapsed = timeSinceLit - holdTime;
          const fadeProgress = Math.min(1, fadeElapsed / Math.max(1, fadeDuration));
          alpha = state.peakAlpha * (1 - fadeProgress);
          state.currentAlpha = alpha;
        }

        if (alpha <= 0.005) {
          cellStates.delete(key);
          return;
        }

        // Draw filled cell background if fillOpacity > 0
        if (fillOpacity > 0) {
          ctx.fillStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha * fillOpacity})`;
          if (cellRadius > 0 && typeof ctx.roundRect === 'function') {
            ctx.beginPath();
            ctx.roundRect(x, y, cellSize, cellSize, cellRadius);
            ctx.fill();
          } else {
            ctx.fillRect(x, y, cellSize, cellSize);
          }
        }

        // Draw illuminated cell borders
        ctx.strokeStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
        ctx.lineWidth = lineWidth;
        if (cellRadius > 0 && typeof ctx.roundRect === 'function') {
          ctx.beginPath();
          ctx.roundRect(x, y, cellSize, cellSize, cellRadius);
          ctx.stroke();
        } else {
          ctx.strokeRect(x, y, cellSize, cellSize);
        }
      });

      animFrameIdRef.current = requestAnimationFrame(render);
    };

    animFrameIdRef.current = requestAnimationFrame(render);

    // Mouse & Touch interaction handlers with container bounds check
    const handleWindowMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      if (
        e.clientX >= rect.left &&
        e.clientX <= rect.right &&
        e.clientY >= rect.top &&
        e.clientY <= rect.bottom
      ) {
        mouseRef.current.x = e.clientX - rect.left;
        mouseRef.current.y = e.clientY - rect.top;
        mouseRef.current.active = true;
      } else {
        mouseRef.current.active = false;
      }
    };

    const handleWindowClick = (e: MouseEvent) => {
      if (!clickPulse) return;
      const rect = container.getBoundingClientRect();
      if (
        e.clientX >= rect.left &&
        e.clientX <= rect.right &&
        e.clientY >= rect.top &&
        e.clientY <= rect.bottom
      ) {
        const clickX = e.clientX - rect.left;
        const clickY = e.clientY - rect.top;
        const maxRadius = Math.hypot(
          Math.max(clickX, width - clickX),
          Math.max(clickY, height - clickY)
        );

        pulsesRef.current.push({
          x: clickX,
          y: clickY,
          startTime: performance.now(),
          maxRadius,
        });
      }
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length > 0) {
        const touch = e.touches[0];
        const rect = container.getBoundingClientRect();
        if (
          touch.clientX >= rect.left &&
          touch.clientX <= rect.right &&
          touch.clientY >= rect.top &&
          touch.clientY <= rect.bottom
        ) {
          mouseRef.current.x = touch.clientX - rect.left;
          mouseRef.current.y = touch.clientY - rect.top;
          mouseRef.current.active = true;
        } else {
          mouseRef.current.active = false;
        }
      }
    };

    const handleTouchStart = (e: TouchEvent) => {
      handleTouchMove(e);
      if (clickPulse && e.touches.length > 0) {
        const touch = e.touches[0];
        const rect = container.getBoundingClientRect();
        const clickX = touch.clientX - rect.left;
        const clickY = touch.clientY - rect.top;
        const maxRadius = Math.hypot(
          Math.max(clickX, width - clickX),
          Math.max(clickY, height - clickY)
        );
        pulsesRef.current.push({
          x: clickX,
          y: clickY,
          startTime: performance.now(),
          maxRadius,
        });
      }
    };

    const handleTouchEnd = () => {
      mouseRef.current.active = false;
    };

    window.addEventListener('mousemove', handleWindowMouseMove);
    window.addEventListener('click', handleWindowClick);
    window.addEventListener('touchmove', handleTouchMove, { passive: true });
    window.addEventListener('touchstart', handleTouchStart, { passive: true });
    window.addEventListener('touchend', handleTouchEnd, { passive: true });

    return () => {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
      resizeObserver.disconnect();
      window.removeEventListener('mousemove', handleWindowMouseMove);
      window.removeEventListener('click', handleWindowClick);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('touchstart', handleTouchStart);
      window.removeEventListener('touchend', handleTouchEnd);
    };
  }, [
    cellSize,
    color,
    radius,
    falloff,
    holdTime,
    fadeDuration,
    lineWidth,
    maxOpacity,
    fillOpacity,
    gridOpacity,
    cellRadius,
    clickPulse,
    pulseSpeed,
    getFalloffFactor,
    rgb.r,
    rgb.g,
    rgb.b,
  ]);

  return (
    <div
      ref={containerRef}
      className={`relative w-full h-full overflow-hidden ${className}`}
      style={{
        pointerEvents: 'auto',
        ...style,
      }}
    >
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none block"
      />
    </div>
  );
};

export default CursorGrid;
