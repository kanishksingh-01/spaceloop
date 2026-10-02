import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { User } from '../../types';
import { useTranslation } from '../../i18n';

interface MobileNavProps {
  currentUser: User | null;
  onOpenAuthModal: () => void;
}

export const MobileNav: React.FC<MobileNavProps> = ({ currentUser, onOpenAuthModal }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();

  const isHostContext =
    currentUser?.role === 'host' ||
    currentUser?.role === 'owner' ||
    Boolean(currentUser?.is_host) ||
    location.pathname.startsWith('/host');

  const handleNav = (targetPath: string) => {
    if (location.pathname === targetPath) {
      window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
    } else {
      navigate(targetPath);
    }
  };

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-950/95 backdrop-blur-lg border-t border-slate-800/80 px-2 py-2 flex items-center justify-around text-[10px] font-medium text-slate-400">
      {currentUser ? (
        isHostContext ? (
          <>
            <button
              onClick={() => handleNav('/host')}
              className={`flex flex-col items-center gap-1 ${
                location.pathname === '/host' || location.pathname === '/host/' || location.pathname === '/host/overview'
                  ? 'text-amber-400 font-bold'
                  : 'hover:text-amber-400'
              }`}
            >
              <i className="fa-solid fa-chart-pie text-base" />
              <span>{t('host.overview')}</span>
            </button>
            <button
              onClick={() => handleNav('/host/spaces')}
              className={`flex flex-col items-center gap-1 ${
                location.pathname.startsWith('/host/spaces') && !location.pathname.includes('/create')
                  ? 'text-amber-400 font-bold'
                  : 'hover:text-amber-400'
              }`}
            >
              <i className="fa-solid fa-warehouse text-base" />
              <span>{t('host.mySpaces')}</span>
            </button>
            <button
              onClick={() => handleNav('/host/spaces/create')}
              className="flex flex-col items-center gap-1 text-white"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 flex items-center justify-center -mt-3 shadow-lg shadow-amber-500/40">
                <i className="fa-solid fa-plus text-xs text-slate-950 font-black" />
              </div>
              <span className="font-bold text-amber-300">{t('nav.listSpace')}</span>
            </button>
            <button
              onClick={() => handleNav('/host/bookings')}
              className={`flex flex-col items-center gap-1 ${
                location.pathname.startsWith('/host/bookings')
                  ? 'text-amber-400 font-bold'
                  : 'hover:text-amber-400'
              }`}
            >
              <i className="fa-solid fa-calendar-check text-base" />
              <span>{t('host.bookings')}</span>
            </button>
            <button
              onClick={() => handleNav('/host/live-sessions')}
              className={`flex flex-col items-center gap-1 ${
                location.pathname.startsWith('/host/live')
                  ? 'text-amber-400 font-bold'
                  : 'hover:text-amber-400'
              }`}
            >
              <i className="fa-solid fa-tower-broadcast text-base" />
              <span>{t('host.liveSessions')}</span>
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => handleNav('/explore')}
              className={`flex flex-col items-center gap-1 ${
                location.pathname === '/explore' ? 'text-indigo-400 font-semibold' : 'hover:text-indigo-400'
              }`}
            >
              <i className="fa-solid fa-compass text-base" />
              <span>{t('nav.explore')}</span>
            </button>
            <button
              onClick={() => handleNav('/dashboard')}
              className={`flex flex-col items-center gap-1 ${
                location.pathname === '/dashboard' ? 'text-indigo-400 font-semibold' : 'hover:text-indigo-400'
              }`}
            >
              <i className="fa-solid fa-calendar-check text-base" />
              <span>{t('nav.myBookings')}</span>
            </button>
            <button
              onClick={() => handleNav('/host')}
              className="flex flex-col items-center gap-1 text-amber-400 font-semibold"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 flex items-center justify-center -mt-3 shadow-lg shadow-amber-500/40">
                <i className="fa-solid fa-house-chimney-user text-xs text-slate-950 font-black" />
              </div>
              <span className="text-amber-300 font-bold">{t('nav.hostPortal')}</span>
            </button>
            <button
              onClick={() => handleNav('/how-it-works')}
              className="flex flex-col items-center gap-1 hover:text-indigo-400"
            >
              <i className="fa-solid fa-comments text-base" />
              <span>{t('nav.help')}</span>
            </button>
            <button
              onClick={() => handleNav('/dashboard')}
              className="flex flex-col items-center gap-1 hover:text-indigo-400"
            >
              <i className="fa-solid fa-user text-base" />
              <span>{t('nav.profile')}</span>
            </button>
          </>
        )
      ) : (
        <>
          <button
            onClick={() => handleNav('/')}
            className={`flex flex-col items-center gap-1 ${
              location.pathname === '/' ? 'text-indigo-400 font-semibold' : 'hover:text-indigo-400'
            }`}
          >
            <i className="fa-solid fa-house text-base" />
            <span>{t('common.brand')}</span>
          </button>
          <button
            onClick={() => handleNav('/explore')}
            className={`flex flex-col items-center gap-1 ${
              location.pathname === '/explore' ? 'text-indigo-400 font-semibold' : 'hover:text-indigo-400'
            }`}
          >
            <i className="fa-solid fa-compass text-base" />
            <span>{t('nav.explore')}</span>
          </button>
          <button
            onClick={() => handleNav('/host')}
            className={`flex flex-col items-center gap-1 ${
              location.pathname.startsWith('/host') ? 'text-amber-400 font-bold' : 'text-amber-300/80 hover:text-amber-300'
            }`}
          >
            <div className="w-8 h-8 rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center -mt-2">
              <i className="fa-solid fa-house-laptop text-xs text-amber-400" />
            </div>
            <span className="font-bold text-amber-300">{t('nav.hostPortal')}</span>
          </button>
          <button
            onClick={() => handleNav('/architecture')}
            className={`flex flex-col items-center gap-1 ${
              location.pathname === '/architecture' ? 'text-indigo-400 font-semibold' : 'hover:text-indigo-400'
            }`}
          >
            <i className="fa-solid fa-cubes text-base" />
            <span>{t('nav.architecture')}</span>
          </button>
          <button
            onClick={onOpenAuthModal}
            className="flex flex-col items-center gap-1 hover:text-indigo-400"
          >
            <i className="fa-solid fa-lock text-base" />
            <span>{t('nav.signIn')}</span>
          </button>
        </>
      )}
    </nav>
  );
};
