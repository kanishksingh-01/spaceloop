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

  const isHostContext = currentUser?.role === 'host' || currentUser?.role === 'owner';

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-950/95 backdrop-blur-lg border-t border-slate-800/80 px-2 py-2 flex items-center justify-around text-[10px] font-medium text-slate-400">
      {currentUser ? (
        isHostContext ? (
          <>
            <button
              onClick={() => navigate('/dashboard')}
              className={`flex flex-col items-center gap-1 ${
                location.pathname === '/dashboard' ? 'text-indigo-400 font-semibold' : 'hover:text-indigo-400'
              }`}
            >
              <i className="fa-solid fa-chart-pie text-base" />
              <span>Dashboard</span>
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="flex flex-col items-center gap-1 hover:text-indigo-400"
            >
              <i className="fa-solid fa-warehouse text-base" />
              <span>Spaces</span>
            </button>
            <button
              onClick={() => navigate('/list-space')}
              className="flex flex-col items-center gap-1 text-white"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-indigo-600 to-violet-600 flex items-center justify-center -mt-3 shadow-lg shadow-indigo-600/40">
                <i className="fa-solid fa-plus text-xs" />
              </div>
              <span>List</span>
            </button>
            <button
              onClick={() => navigate('/calculator')}
              className={`flex flex-col items-center gap-1 ${
                location.pathname === '/calculator' ? 'text-indigo-400 font-semibold' : 'hover:text-indigo-400'
              }`}
            >
              <i className="fa-solid fa-calculator text-base" />
              <span>Earnings</span>
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="flex flex-col items-center gap-1 hover:text-indigo-400"
            >
              <i className="fa-solid fa-user text-base" />
              <span>Profile</span>
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
              onClick={() => navigate('/dashboard')}
              className="flex flex-col items-center gap-1 text-emerald-400 font-semibold"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-emerald-600 to-teal-600 flex items-center justify-center -mt-3 shadow-lg shadow-emerald-600/40">
                <i className="fa-solid fa-door-open text-xs text-white" />
              </div>
              <span>Session</span>
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
            onClick={() => navigate('/how-it-works')}
            className={`flex flex-col items-center gap-1 ${
              location.pathname === '/how-it-works' ? 'text-indigo-400 font-semibold' : 'hover:text-indigo-400'
            }`}
          >
            <i className="fa-solid fa-circle-question text-base" />
            <span>How It Works</span>
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
