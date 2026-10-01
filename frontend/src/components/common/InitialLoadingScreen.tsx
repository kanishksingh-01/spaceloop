import React from 'react';

interface InitialLoadingScreenProps {
  isFading: boolean;
}

export const InitialLoadingScreen: React.FC<InitialLoadingScreenProps> = ({ isFading }) => {
  return (
    <div
      id="spaceloop-initial-loader"
      role="status"
      aria-label="Loading SpaceLoop"
      className={`fixed inset-0 z-[999999] flex flex-col items-center justify-center spaceloop-loading-screen overflow-hidden select-none transition-opacity duration-700 ease-out ${
        isFading ? 'opacity-0 pointer-events-none' : 'opacity-100'
      }`}
      style={{
        backgroundColor: '#020617',
        color: '#ffffff',
      }}
    >
      {/* Understated Technical Grid Background */}
      <div className="absolute inset-0 spaceloop-loading-grid pointer-events-none" />

      {/* Subtle Luminous Ambient Glow Behind Branding */}
      <div
        className="absolute w-[320px] sm:w-[480px] h-[320px] sm:h-[480px] rounded-full bg-gradient-to-tr from-indigo-600/15 via-violet-600/10 to-sky-500/10 blur-[80px] sm:blur-[100px] pointer-events-none"
        aria-hidden="true"
      />

      {/* Central Minimal Branding */}
      <div className="relative z-10 flex flex-col items-center justify-center px-4 animate-spaceloop-entrance">
        <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-[0.28em] font-display flex items-center justify-center transition-transform">
          <span className="text-white/95 drop-shadow-[0_0_20px_rgba(255,255,255,0.2)]">
            SPACE
          </span>
          <span className="ml-3 sm:ml-4 text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-indigo-400 to-violet-400 animate-spaceloop-glow">
            LOOP
          </span>
        </h1>

        {/* Minimal Futuristic Accent Indicator */}
        <div className="mt-5 w-24 sm:w-28 h-[1.5px] bg-indigo-950/60 relative overflow-hidden rounded-full">
          <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-indigo-400 to-transparent animate-spaceloop-scan" />
        </div>
      </div>
    </div>
  );
};
