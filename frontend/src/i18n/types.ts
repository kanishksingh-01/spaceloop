/**
 * SpaceLoop i18n Type Definitions & Schemas
 * Supports: English (en), Hindi (hi), Marathi (mr), Garhwali (gar), Kumaoni (kfy), Jaunsari (jns)
 */

export type SupportedLanguage = 'en' | 'hi' | 'mr' | 'gar' | 'kfy' | 'jns';

export interface LanguageOption {
  code: SupportedLanguage;
  name: string;        // Native display name (e.g., "हिन्दी", "मराठी")
  englishName: string; // English name
  region: string;      // Geographic association
  badge?: string;
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: 'en', name: 'English', englishName: 'English', region: 'Global' },
  { code: 'hi', name: 'हिन्दी', englishName: 'Hindi', region: 'North & Central India' },
  { code: 'mr', name: 'मराठी', englishName: 'Marathi', region: 'Maharashtra' },
  { code: 'gar', name: 'गढ़वाली', englishName: 'Garhwali', region: 'Garhwal, Uttarakhand', badge: 'UK' },
  { code: 'kfy', name: 'कुमाऊँनी', englishName: 'Kumaoni', region: 'Kumaon, Uttarakhand', badge: 'UK' },
  { code: 'jns', name: 'जौनसारी', englishName: 'Jaunsari', region: 'Jaunsar-Bawar, Uttarakhand', badge: 'UK' },
];

export interface TranslationDictionary {
  common: {
    brand: string;
    tagline: string;
    loading: string;
    error: string;
    retry: string;
    close: string;
    cancel: string;
    save: string;
    apply: string;
    search: string;
    viewAll: string;
    perHour: string;
    verified: string;
    freeCancellation: string;
    instantAccess: string;
    sec52Protected: string;
  };
  nav: {
    explore: string;
    howItWorks: string;
    calculator: string;
    listSpace: string;
    trustSafety: string;
    architecture: string;
    myBookings: string;
    hostDashboard: string;
    seekerPortal: string;
    hostPortal: string;
    switchToSeeker: string;
    switchToHost: string;
    signIn: string;
    signOut: string;
    profile: string;
    language: string;
  };
  hero: {
    headline: string;
    highlight: string;
    subtitle: string;
    searchPlaceholder: string;
    findSpaceBtn: string;
    listSpaceBtn: string;
    popularTags: string;
  };
  explore: {
    title: string;
    subtitle: string;
    filterAll: string;
    filterDesk: string;
    filterMeeting: string;
    filterStudio: string;
    filterStorage: string;
    filterEvent: string;
    filterStudy: string;
    priceRange: string;
    capacity: string;
    noResults: string;
    resetFilters: string;
    foundSpaces: string;
  };
  loopbot: {
    title: string;
    status: string;
    initialGreeting: string;
    placeholder: string;
    send: string;
    languageSelect: string;
    autoDetect: string;
    detectedLanguage: string;
    quickPrompts: {
      findDesk: string;
      howMuch: string;
      section52: string;
      earnMoney: string;
    };
  };
  footer: {
    description: string;
    quickLinks: string;
    legal: string;
    terms: string;
    privacy: string;
    escrowPolicy: string;
    rightsReserved: string;
  };
}
