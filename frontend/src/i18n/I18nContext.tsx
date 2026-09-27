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
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

// Helper to resolve dot-notated nested keys like 'nav.explore' or 'loopbot.quickPrompts.findDesk'
function resolveKey(dict: any, path: string): string | undefined {
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

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<SupportedLanguage>(() => {
    try {
      const saved = localStorage.getItem(UI_LANG_STORAGE_KEY);
      if (saved && saved in DICTIONARIES) {
        return saved as SupportedLanguage;
      }
    } catch {
      // localStorage may fail in restricted sandbox/iframe
    }
    return 'en';
  });

  const [loopbotLanguage, setLoopbotLanguageState] = useState<string>(() => {
    try {
      return localStorage.getItem(LOOPBOT_LANG_STORAGE_KEY) || 'auto';
    } catch {
      return 'auto';
    }
  });

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
      let text = resolveKey(currentDict, key);
      // Fallback to English if key missing or blank
      if (!text) {
        text = resolveKey(fallbackDict, key) || key;
      }

      if (params) {
        Object.entries(params).forEach(([paramKey, val]) => {
          text = text!.replace(new RegExp(`{${paramKey}}`, 'g'), String(val));
        });
      }

      return text;
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
    }),
    [language, loopbotLanguage, currentLanguageOption, t]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};

export const useTranslation = (): I18nContextType => {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useTranslation must be used within a LanguageProvider');
  }
  return context;
};
