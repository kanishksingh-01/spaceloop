import React, { createContext, useContext, useState, useEffect } from 'react';

export type Theme = 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: any) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const theme: Theme = 'dark';

  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem('spaceloop-theme');
        sessionStorage.removeItem('spaceloop-theme');
      } catch (e) {}

      const root = document.documentElement;
      root.classList.remove('light');
      root.classList.add('dark');
      root.style.colorScheme = 'dark';
    }
  }, []);

  const toggleTheme = () => {
    // Permanent dark theme: light theme is disabled
  };

  const setTheme = () => {
    // Permanent dark theme: light theme is disabled
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
