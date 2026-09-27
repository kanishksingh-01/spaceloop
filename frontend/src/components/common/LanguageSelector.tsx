import React, { useState, useRef, useEffect } from 'react';
import { useTranslation, SupportedLanguage } from '../../i18n';

interface LanguageSelectorProps {
  className?: string;
  dropUp?: boolean;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({ className = '', dropUp = false }) => {
  const { language, setLanguage, languages, currentLanguageOption } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleOutsideClick);
    }
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
    };
  }, [isOpen]);

  const handleSelect = (code: SupportedLanguage) => {
    setLanguage(code);
    setIsOpen(false);
  };

  return (
    <div className={`relative inline-block text-left ${className}`} ref={containerRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700/60 text-xs font-semibold transition shadow-sm focus:outline-none focus:ring-1 focus:ring-indigo-500/50"
        title="Select Language / भाषा निवडा"
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        <span className="text-sm">🌐</span>
        <span className="font-medium">{currentLanguageOption.name}</span>
        {currentLanguageOption.badge && (
          <span className="text-[9px] px-1 py-0.2 rounded bg-indigo-500/20 text-indigo-300 font-mono font-bold">
            {currentLanguageOption.badge}
          </span>
        )}
        <i className={`fa-solid fa-chevron-${isOpen ? 'up' : 'down'} text-[10px] text-slate-400 ml-0.5 transition-transform duration-150`} />
      </button>

      {isOpen && (
        <div
          className={`absolute right-0 w-56 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-1.5 z-50 animate-in fade-in zoom-in-95 duration-100 ${
            dropUp ? 'bottom-full mb-2' : 'top-full mt-2'
          }`}
        >
          <div className="px-3 py-1.5 border-b border-slate-800/80 mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Select Language / भाषा निवडा
            </span>
          </div>
          <div className="space-y-0.5">
            {languages.map((item) => {
              const isSelected = item.code === language;
              return (
                <button
                  key={item.code}
                  type="button"
                  onClick={() => handleSelect(item.code)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-left text-xs transition ${
                    isSelected
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 font-bold'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80 border border-transparent'
                  }`}
                >
                  <div className="flex flex-col">
                    <span className="text-sm leading-tight">{item.name}</span>
                    <span className="text-[10px] text-slate-400 leading-tight">
                      {item.englishName} • {item.region}
                    </span>
                  </div>
                  {isSelected && <i className="fa-solid fa-check text-indigo-400 text-xs" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
