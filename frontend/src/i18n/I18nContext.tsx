import React, { createContext, useContext, useState, useEffect, useMemo, ReactNode } from 'react';
import { SupportedLanguage, TranslationDictionary, SUPPORTED_LANGUAGES, LanguageOption } from './types';
import { en } from './locales/en';
import { hi } from './locales/hi';
import { mr } from './locales/mr';
import { gar } from './locales/gar';
import { kfy } from './locales/kfy';
import { jns } from './locales/jns';

const DICTIONARIES: Record<SupportedLanguage, TranslationDictionary> = {
  en,
  hi,
  mr,
  gar,
  kfy,
  jns,
};

const UI_LANG_STORAGE_KEY = 'spaceloop_ui_lang';
const LOOPBOT_LANG_STORAGE_KEY = 'spaceloop_loopbot_lang';

export interface I18nContextType {
  language: SupportedLanguage;
  setLanguage: (lang: SupportedLanguage) => void;
  loopbotLanguage: string; // 'auto' or SupportedLanguage
  setLoopbotLanguage: (lang: string) => void;
  languages: LanguageOption[];
  currentLanguageOption: LanguageOption;
  t: (key: string, params?: Record<string, string | number>) => string;
  formatCurrency: (amount: number) => string;
  formatNumber: (num: number) => string;
  formatDate: (dateInput: string | Date | number, options?: Intl.DateTimeFormatOptions) => string;
  formatTime: (dateInput: string | Date | number, options?: Intl.DateTimeFormatOptions) => string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

// Helper to resolve dot-notated nested keys like 'nav.explore' or 'loopbot.quickPrompts.findDesk'
function resolveKey(dict: any, path: string): string | undefined {
  if (!dict || typeof dict !== 'object') return undefined;
  const parts = path.split('.');
  let current = dict;
  for (const part of parts) {
    if (current && typeof current === 'object' && part in current) {
      current = current[part];
    } else {
      return undefined;
    }
  }
  return typeof current === 'string' ? current : undefined;
}

// Browser language auto-detection
function detectBrowserLanguage(): SupportedLanguage {
  try {
    const navLangs = navigator.languages || [navigator.language];
    for (const raw of navLangs) {
      if (!raw) continue;
      const lower = raw.toLowerCase();
      if (lower.startsWith('hi')) return 'hi';
      if (lower.startsWith('mr')) return 'mr';
      if (lower.startsWith('gar') || lower.startsWith('gbm')) return 'gar';
      if (lower.startsWith('kfy')) return 'kfy';
      if (lower.startsWith('jns')) return 'jns';
    }
  } catch {
    // ignore
  }
  return 'en';
}

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<SupportedLanguage>(() => {
    try {
      const saved = localStorage.getItem(UI_LANG_STORAGE_KEY);
      if (saved && saved in DICTIONARIES) {
        return saved as SupportedLanguage;
      }
    } catch {
      // localStorage may fail in restricted sandbox
    }
    return detectBrowserLanguage();
  });

  const [loopbotLanguage, setLoopbotLanguageState] = useState<string>(() => {
    try {
      return localStorage.getItem(LOOPBOT_LANG_STORAGE_KEY) || 'auto';
    } catch {
      return 'auto';
    }
  });

  // Sync html lang attribute
  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = language;
    }
  }, [language]);

  const setLanguage = (newLang: SupportedLanguage) => {
    if (newLang in DICTIONARIES) {
      setLanguageState(newLang);
      try {
        localStorage.setItem(UI_LANG_STORAGE_KEY, newLang);
      } catch {
        // ignore
      }
    }
  };

  const setLoopbotLanguage = (newLang: string) => {
    setLoopbotLanguageState(newLang);
    try {
      localStorage.setItem(LOOPBOT_LANG_STORAGE_KEY, newLang);
    } catch {
      // ignore
    }
  };

  const currentLanguageOption = useMemo(() => {
    return SUPPORTED_LANGUAGES.find((l) => l.code === language) || SUPPORTED_LANGUAGES[0];
  }, [language]);

  const t = useMemo(() => {
    const currentDict = DICTIONARIES[language] || DICTIONARIES.en;
    const fallbackDict = DICTIONARIES.en;

    return (key: string, params?: Record<string, string | number>): string => {
      let text: string | undefined;

      // Check pluralization if count param is provided
      if (params && typeof params.count === 'number') {
        const pluralKey = params.count === 1 ? `${key}_one` : `${key}_other`;
        text = resolveKey(currentDict, pluralKey);
        if (!text) {
          text = resolveKey(fallbackDict, pluralKey);
        }
      }

      if (!text) {
        text = resolveKey(currentDict, key);
      }
      // Fallback to English if key missing or blank
      if (!text) {
        text = resolveKey(fallbackDict, key);
      }
      if (!text) {
        return key;
      }

      // Variable interpolation: replaces {varName} with param value
      if (params) {
        return text.replace(/\{(\w+)\}/g, (_, varName) => {
          if (varName in params) {
            return String(params[varName]);
          }
          return `{${varName}}`;
        });
      }

      return text;
    };
  }, [language]);

  // Locale-aware currency formatting (INR ₹ standard across India)
  const formatCurrency = useMemo(() => {
    return (amount: number): string => {
      try {
        const localeTag = language === 'en' ? 'en-IN' : (language === 'mr' ? 'mr-IN' : 'hi-IN');
        return new Intl.NumberFormat(localeTag, {
          style: 'currency',
          currency: 'INR',
          maximumFractionDigits: amount % 1 === 0 ? 0 : 2,
        }).format(amount);
      } catch {
        return `₹${amount}`;
      }
    };
  }, [language]);

  // Locale-aware number formatting
  const formatNumber = useMemo(() => {
    return (num: number): string => {
      try {
        const localeTag = language === 'en' ? 'en-IN' : (language === 'mr' ? 'mr-IN' : 'hi-IN');
        return new Intl.NumberFormat(localeTag).format(num);
      } catch {
        return String(num);
      }
    };
  }, [language]);

  // Locale-aware date formatting
  const formatDate = useMemo(() => {
    return (dateInput: string | Date | number, options?: Intl.DateTimeFormatOptions): string => {
      try {
        const d = typeof dateInput === 'string' || typeof dateInput === 'number' ? new Date(dateInput) : dateInput;
        if (isNaN(d.getTime())) return String(dateInput);
        const localeTag = language === 'en' ? 'en-IN' : (language === 'mr' ? 'mr-IN' : 'hi-IN');
        const defaultOptions: Intl.DateTimeFormatOptions = options || {
          day: 'numeric',
          month: 'short',
          year: 'numeric',
        };
        return new Intl.DateTimeFormat(localeTag, defaultOptions).format(d);
      } catch {
        return String(dateInput);
      }
    };
  }, [language]);

  // Locale-aware time formatting
  const formatTime = useMemo(() => {
    return (dateInput: string | Date | number, options?: Intl.DateTimeFormatOptions): string => {
      try {
        const d = typeof dateInput === 'string' || typeof dateInput === 'number' ? new Date(dateInput) : dateInput;
        if (isNaN(d.getTime())) return String(dateInput);
        const localeTag = language === 'en' ? 'en-IN' : (language === 'mr' ? 'mr-IN' : 'hi-IN');
        const defaultOptions: Intl.DateTimeFormatOptions = options || {
          hour: 'numeric',
          minute: '2-digit',
          hour12: true,
        };
        return new Intl.DateTimeFormat(localeTag, defaultOptions).format(d);
      } catch {
        return String(dateInput);
      }
    };
  }, [language]);

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      loopbotLanguage,
      setLoopbotLanguage,
      languages: SUPPORTED_LANGUAGES,
      currentLanguageOption,
      t,
      formatCurrency,
      formatNumber,
      formatDate,
      formatTime,
    }),
    [language, loopbotLanguage, currentLanguageOption, t, formatCurrency, formatNumber, formatDate, formatTime]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};

export const useI18n = (): I18nContextType => {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within a LanguageProvider');
  }
  return context;
};

export const useTranslation = (): I18nContextType => {
  return useI18n();
};
