import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useNavigate, useLocation } from 'react-router-dom';
import { User } from '../../types';

interface MobileNavProps {
  currentUser: User | null;
  onOpenAuthModal: () => void;
}

export const MobileNav: React.FC<MobileNavProps> = ({ currentUser, onOpenAuthModal }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const isHostContext =
    currentUser?.role === 'host' ||
    currentUser?.role === 'owner' ||
    Boolean(currentUser?.is_host) ||
    location.pathname.startsWith('/host');

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-950/95 backdrop-blur-lg border-t border-slate-800/80 px-2 py-2 flex items-center justify-around text-[10px] font-medium text-slate-400">
      {currentUser ? (
        isHostContext ? (
          <>
            <button
              onClick={() => navigate('/host')}
              className={`flex flex-col items-center gap-1 ${
                location.pathname === '/host' || location.pathname === '/host/' || location.pathname === '/host/overview'
                  ? 'text-amber-400 font-bold'
                  : 'hover:text-amber-400'
              }`}
            >
              <i className="fa-solid fa-chart-pie text-base" />
              <span>Overview</span>
            </button>
            <button
              onClick={() => navigate('/host/spaces')}
              className={`flex flex-col items-center gap-1 ${
                location.pathname.startsWith('/host/spaces') && !location.pathname.includes('/create')
                  ? 'text-amber-400 font-bold'
                  : 'hover:text-amber-400'
              }`}
            >
              <i className="fa-solid fa-warehouse text-base" />
              <span>Spaces</span>
            </button>
            <button
              onClick={() => navigate('/host/spaces/create')}
              className="flex flex-col items-center gap-1 text-white"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 flex items-center justify-center -mt-3 shadow-lg shadow-amber-500/40">
                <i className="fa-solid fa-plus text-xs text-slate-950 font-black" />
              </div>
              <span className="font-bold text-amber-300">List Space</span>
            </button>
            <button
              onClick={() => navigate('/host/bookings')}
              className={`flex flex-col items-center gap-1 ${
                location.pathname.startsWith('/host/bookings')
                  ? 'text-amber-400 font-bold'
                  : 'hover:text-amber-400'
              }`}
            >
              <i className="fa-solid fa-calendar-check text-base" />
              <span>Bookings</span>
            </button>
            <button
              onClick={() => navigate('/host/live-sessions')}
              className={`flex flex-col items-center gap-1 ${
                location.pathname.startsWith('/host/live')
                  ? 'text-amber-400 font-bold'
                  : 'hover:text-amber-400'
              }`}
            >
              <i className="fa-solid fa-tower-broadcast text-base" />
              <span>Live Hub</span>
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => navigate('/explore')}
              className={`flex flex-col items-center gap-1 ${
                location.pathname === '/explore' ? 'text-indigo-400 font-semibold' : 'hover:text-indigo-400'
              }`}
            >
              <i className="fa-solid fa-compass text-base" />
              <span>Explore</span>
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className={`flex flex-col items-center gap-1 ${
                location.pathname === '/dashboard' ? 'text-indigo-400 font-semibold' : 'hover:text-indigo-400'
              }`}
            >
              <i className="fa-solid fa-calendar-check text-base" />
              <span>Bookings</span>
            </button>
            <button
              onClick={() => navigate('/host')}
              className="flex flex-col items-center gap-1 text-amber-400 font-semibold"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 flex items-center justify-center -mt-3 shadow-lg shadow-amber-500/40">
                <i className="fa-solid fa-house-chimney-user text-xs text-slate-950 font-black" />
              </div>
              <span className="text-amber-300 font-bold">Host OS</span>
            </button>
            <button
              onClick={() => navigate('/how-it-works')}
              className="flex flex-col items-center gap-1 hover:text-indigo-400"
            >
              <i className="fa-solid fa-comments text-base" />
              <span>Help</span>
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="flex flex-col items-center gap-1 hover:text-indigo-400"
            >
              <i className="fa-solid fa-user text-base" />
              <span>Profile</span>
            </button>
          </>
        )
      ) : (
        <>
          <button
            onClick={() => navigate('/')}
            className={`flex flex-col items-center gap-1 ${
              location.pathname === '/' ? 'text-indigo-400 font-semibold' : 'hover:text-indigo-400'
            }`}
          >
            <i className="fa-solid fa-house text-base" />
            <span>Home</span>
          </button>
          <button
            onClick={() => navigate('/explore')}
            className={`flex flex-col items-center gap-1 ${
              location.pathname === '/explore' ? 'text-indigo-400 font-semibold' : 'hover:text-indigo-400'
            }`}
          >
            <i className="fa-solid fa-compass text-base" />
            <span>Explore</span>
          </button>
          <button
            onClick={() => navigate('/host')}
            className={`flex flex-col items-center gap-1 ${
              location.pathname.startsWith('/host') ? 'text-amber-400 font-bold' : 'text-amber-300/80 hover:text-amber-300'
            }`}
          >
            <div className="w-8 h-8 rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center -mt-2">
              <i className="fa-solid fa-house-laptop text-xs text-amber-400" />
            </div>
            <span className="font-bold text-amber-300">Host OS</span>
          </button>
          <button
            onClick={() => navigate('/architecture')}
            className={`flex flex-col items-center gap-1 ${
              location.pathname === '/architecture' ? 'text-indigo-400 font-semibold' : 'hover:text-indigo-400'
            }`}
          >
            <i className="fa-solid fa-cubes text-base" />
            <span>Arch</span>
          </button>
          <button
            onClick={onOpenAuthModal}
            className="flex flex-col items-center gap-1 hover:text-indigo-400"
          >
            <i className="fa-solid fa-lock text-base" />
            <span>Sign In</span>
          </button>
        </>
      )}
    </nav>
  );
};
