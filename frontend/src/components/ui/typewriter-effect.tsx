import React, { useEffect, useState } from 'react';

export interface TypewriterWord {
  text: string;
  className?: string;
}

export interface TypewriterEffectSmoothProps {
  words: TypewriterWord[];
  className?: string;
  cursorClassName?: string;
  duration?: number;
  delay?: number;
}

export interface TypewriterEffectProps {
  words: TypewriterWord[];
  className?: string;
  cursorClassName?: string;
  duration?: number;
}

/**
 * Helper to convert a plain string into a typed words array with optional highlight styling
 */
export const stringToWords = (
  str: string,
  highlightWord?: string,
  highlightClass?: string
): TypewriterWord[] => {
  if (!str) return [];
  const parts = str.split(/\s+/).filter(Boolean);
  return parts.map((w) => {
    const isHighlight = highlightWord && w.toLowerCase().includes(highlightWord.toLowerCase());
    return {
      text: w,
      className: isHighlight
        ? highlightClass ||
          'text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-violet-300 to-indigo-300'
        : undefined,
    };
  });
};

/**
 * Aceternity UI: TypewriterEffectSmooth
 * Smoothly reveals words with a sleek typing animation and active blinking cursor.
 */
export const TypewriterEffectSmooth: React.FC<TypewriterEffectSmoothProps> = ({
  words,
  className = '',
  cursorClassName = '',
  duration = 1.4,
  delay = 0.05,
}) => {
  const [isRendered, setIsRendered] = useState(false);
  const fullText = words.map((w) => w.text).join(' ');

  // Reset animation whenever words change (e.g. language toggle)
  useEffect(() => {
    setIsRendered(false);
    const timer = setTimeout(() => {
      setIsRendered(true);
    }, delay * 1000);
    return () => clearTimeout(timer);
  }, [fullText, delay]);

  const wordsArray = words.map((word) => ({
    ...word,
    text: word.text.split(''),
  }));

  return (
    <div
      className={`inline-flex flex-wrap items-center justify-center ${className}`}
      aria-label={fullText}
    >
      <div className="overflow-hidden inline-block align-middle max-w-full">
        <div
          className="text-inherit font-inherit inline-flex flex-wrap items-center justify-center transition-all ease-out"
          style={{
            maxWidth: isRendered ? '100%' : '0%',
            opacity: isRendered ? 1 : 0,
            transitionDuration: `${duration}s`,
            transitionTimingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        >
          {wordsArray.map((word, wIdx) => (
            <div key={`word-${wIdx}`} className="inline-block mr-1 sm:mr-2 my-0.5">
              {word.text.map((char, cIdx) => (
                <span
                  key={`char-${cIdx}`}
                  className={`inline-block ${word.className || ''}`}
                >
                  {char}
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>
      {/* Blinking Vertical Typewriter Cursor */}
      <span
        className={`inline-block w-[3px] sm:w-[4px] h-[0.9em] rounded-full bg-indigo-500 dark:bg-indigo-400 align-middle ml-1 animate-pulse shadow-[0_0_8px_rgba(99,102,241,0.8)] ${cursorClassName}`}
      />
    </div>
  );
};

/**
 * Aceternity UI: TypewriterEffect
 * Staggered character reveal typewriter effect.
 */
export const TypewriterEffect: React.FC<TypewriterEffectProps> = ({
  words,
  className = '',
  cursorClassName = '',
}) => {
  const [displayedCount, setDisplayedCount] = useState(0);
  const fullText = words.map((w) => w.text).join(' ');
  const totalChars = fullText.length;

  useEffect(() => {
    setDisplayedCount(0);
    let count = 0;
    const interval = setInterval(() => {
      count += 1;
      setDisplayedCount(count);
      if (count >= totalChars) {
        clearInterval(interval);
      }
    }, 45);

    return () => clearInterval(interval);
  }, [fullText, totalChars]);

  let accumulated = 0;

  return (
    <div className={`inline-flex flex-wrap items-center justify-center ${className}`} aria-label={fullText}>
      {words.map((word, wIdx) => {
        const wordChars = word.text.split('');
        return (
          <div key={`word-${wIdx}`} className="inline-block mr-1.5 sm:mr-2 my-0.5">
            {wordChars.map((char, cIdx) => {
              accumulated += 1;
              const isVisible = accumulated <= displayedCount;
              return (
                <span
                  key={`char-${cIdx}`}
                  className={`inline-block transition-opacity duration-75 ${
                    isVisible ? 'opacity-100' : 'opacity-0'
                  } ${word.className || ''}`}
                >
                  {char}
                </span>
              );
            })}
          </div>
        );
      })}
      <span
        className={`inline-block w-[3px] sm:w-[4px] h-[0.9em] rounded-full bg-indigo-500 align-middle ml-0.5 animate-pulse ${cursorClassName}`}
      />
    </div>
  );
};
