import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import { ThemeProvider } from './context/ThemeContext';
import { LanguageProvider } from './i18n';
// SpaceLoop Enterprise Core Engine v2.5.3-release
import './styles/index.css';

// Handle dynamic import chunk failures gracefully during active deployments
window.addEventListener('vite:preloadError', (event) => {
  const lastReload = sessionStorage.getItem('spaceloop_vite_reload');
  const now = Date.now();
  if (!lastReload || now - parseInt(lastReload, 10) > 10000) {
    sessionStorage.setItem('spaceloop_vite_reload', now.toString());
    window.location.reload();
  }
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <LanguageProvider>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </LanguageProvider>
  </React.StrictMode>
);

