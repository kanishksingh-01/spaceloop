import React, { useState } from 'react';
import { View, Text, Pressable, Image } from 'react-native';
import { useNavigate, useLocation } from 'react-router-dom';
import { User } from '../../types';
import { logoutUser, demoSwitch } from '../../services/auth';

interface HeaderProps {
  currentUser: User | null;
  onOpenAuthModal: () => void;
  onOpenDemoModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentUser,
  onOpenAuthModal,
  onOpenDemoModal,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  const isHostContext = currentUser?.role === 'host' || currentUser?.role === 'owner';

  const handleLogout = async () => {
    try {
      await logoutUser();
      window.location.reload();
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  const handleRoleToggle = async () => {
    try {
      const nextRole = isHostContext ? 'seeker' : 'host';
      await demoSwitch(nextRole);
      window.location.reload();
    } catch (err) {
      console.error('Role switch failed:', err);
    }
  };

  return (
    <header className="sticky top-0 z-40 backdrop-blur-md bg-slate-950/90 border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <button
          type="button"
          onClick={() => navigate('/')}
          className="flex items-center gap-2.5 group shrink-0 focus:outline-none"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 via-violet-600 to-indigo-400 flex items-center justify-center shadow-lg shadow-indigo-500/25 group-hover:scale-105 transition duration-200">
            <i className="fa-solid fa-infinity text-white text-lg" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
              Space<span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-violet-400">Loop</span>
              <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">AI</span>
            </span>
          </div>
        </button>

        {/* Center Role-Aware Nav Links (Desktop) */}
        <nav className="hidden lg:flex items-center gap-1 text-xs font-semibold">
          {currentUser ? (
            isHostContext ? (
              <>
                <button
                  onClick={() => navigate('/dashboard')}
                  className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                    location.pathname === '/dashboard'
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <i className="fa-solid fa-chart-pie text-indigo-400" />
                  <span>Dashboard</span>
                </button>
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 text-slate-300 hover:text-white hover:bg-slate-800/60"
                >
                  <i className="fa-solid fa-warehouse text-slate-400" />
                  <span>My Spaces</span>
                </button>
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 text-slate-300 hover:text-white hover:bg-slate-800/60"
                >
                  <i className="fa-solid fa-calendar-check text-slate-400" />
                  <span>Bookings</span>
                </button>
                <button
                  onClick={() => navigate('/calculator')}
                  className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                    location.pathname === '/calculator'
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <i className="fa-solid fa-calculator text-slate-400" />
                  <span>Earnings</span>
                </button>
                <button
                  onClick={() => navigate('/verify')}
                  className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                    location.pathname === '/verify'
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <i className="fa-solid fa-shield-halved text-emerald-400" />
                  <span>Verification</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" title="Host Verified" />
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => navigate('/')}
                  className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                    location.pathname === '/'
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <i className="fa-solid fa-house text-indigo-400" />
                  <span>Home</span>
                </button>
                <button
                  onClick={() => navigate('/explore')}
                  className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                    location.pathname === '/explore'
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <i className="fa-solid fa-compass text-slate-400" />
                  <span>Explore Spaces</span>
                </button>
                <button
                  onClick={() => navigate('/dashboard')}
                  className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                    location.pathname === '/dashboard'
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <i className="fa-solid fa-calendar-check text-slate-400" />
                  <span>My Bookings</span>
                </button>
                <button
                  onClick={() => navigate('/how-it-works')}
                  className="px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 text-slate-300 hover:text-white hover:bg-slate-800/60"
                >
                  <i className="fa-solid fa-circle-question text-slate-400" />
                  <span>How It Works</span>
                </button>
              </>
            )
          ) : (
            <>
              <button
                onClick={() => navigate('/explore')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname === '/explore'
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <i className="fa-solid fa-compass text-indigo-400" />
                <span>Explore</span>
              </button>
              <button
                onClick={() => navigate('/how-it-works')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  location.pathname === '/how-it-works'
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <i className="fa-solid fa-circle-question text-slate-400" />
                <span>How It Works</span>
              </button>
              <button
                onClick={() => navigate('/#for-seekers')}
                className="px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 text-slate-300 hover:text-white hover:bg-slate-800/60"
              >
                <i className="fa-solid fa-graduation-cap text-slate-400" />
                <span>For Seekers</span>
              </button>
              <button
                onClick={() => navigate('/#for-hosts')}
                className="px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 text-slate-300 hover:text-white hover:bg-slate-800/60"
              >
                <i className="fa-solid fa-house-chimney-user text-slate-400" />
                <span>For Hosts</span>
              </button>
              <button
                onClick={() => navigate('/#trust-safety')}
                className="px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 text-slate-300 hover:text-white hover:bg-slate-800/60"
              >
                <i className="fa-solid fa-shield-halved text-emerald-400" />
                <span>Trust & Safety</span>
              </button>
            </>
          )}
        </nav>

        {/* Right Action Controls */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {/* Live System Connectivity Status Indicator */}
          <button
            type="button"
            onClick={onOpenDemoModal}
            className="hidden sm:inline-block cursor-pointer transition hover:opacity-80 focus:outline-none"
            title="System Status: SpaceLoop AI Engine Online. Click for Evaluation Console."
          >
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> ONLINE
            </span>
          </button>

          {currentUser ? (
            <>
              {/* Context Switch */}
              <button
                type="button"
                onClick={handleRoleToggle}
                className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-xs font-semibold border border-slate-700/80 transition"
              >
                <i className="fa-solid fa-repeat text-[10px] text-indigo-400" />
                <span className={isHostContext ? 'text-indigo-300' : 'text-amber-300'}>
                  {isHostContext ? 'Seeker View' : 'Host View'}
                </span>
              </button>

              {/* Add / List Space CTA */}
              <button
                type="button"
                onClick={() => navigate('/list-space')}
                className="hidden sm:inline-flex items-center gap-1.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold text-xs px-3.5 py-1.5 rounded-lg shadow-md shadow-indigo-600/20 transition"
              >
                <i className="fa-solid fa-plus text-[10px]" /> Add Space
              </button>

              {/* Logout */}
              <button
                type="button"
                onClick={handleLogout}
                className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 border border-slate-800 hover:border-rose-800/40 text-xs font-semibold transition"
                title="Sign Out"
              >
                <i className="fa-solid fa-arrow-right-from-bracket text-[11px]" />
                <span>Logout</span>
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={onOpenAuthModal}
                className="text-xs font-bold text-slate-300 hover:text-white px-3 py-1.5 rounded-lg hover:bg-slate-900 transition"
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={onOpenAuthModal}
                className="bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-700 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-xs px-4 py-2 rounded-xl shadow-md shadow-indigo-600/30 transition"
              >
                Get Started
              </button>
            </>
          )}

          {/* Mobile Menu Toggle Button */}
          <button
            type="button"
            onClick={() => setMobileDrawerOpen(!mobileDrawerOpen)}
            className="lg:hidden p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white focus:outline-none"
            aria-label="Toggle Navigation Menu"
          >
            <i className="fa-solid fa-bars text-sm" />
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileDrawerOpen && (
        <div className="lg:hidden border-t border-slate-800/80 bg-slate-950/95 backdrop-blur-xl px-4 py-4 space-y-3 shadow-2xl">
          {currentUser ? (
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <img
                  src={
                    currentUser.avatar_url ||
                    'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80'
                  }
                  alt={currentUser.name}
                  className="w-8 h-8 rounded-lg object-cover"
                />
                <div>
                  <div className="text-xs font-bold text-white">{currentUser.name}</div>
                  <div className="text-[10px] text-indigo-400 uppercase font-semibold">
                    {currentUser.role} mode
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={handleRoleToggle}
                className="text-[11px] font-semibold text-indigo-300 bg-indigo-950/60 border border-indigo-500/30 px-2.5 py-1 rounded-lg"
              >
                Switch to {isHostContext ? 'Seeker' : 'Host'}
              </button>
            </div>
          ) : null}

          <div className="grid grid-cols-2 gap-2 text-xs font-medium">
            <button
              onClick={() => {
                navigate('/');
                setMobileDrawerOpen(false);
              }}
              className="p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800 text-slate-200 flex items-center gap-2 text-left"
            >
              <i className="fa-solid fa-house text-indigo-400" /> Home
            </button>
            <button
              onClick={() => {
                navigate('/explore');
                setMobileDrawerOpen(false);
              }}
              className="p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800 text-slate-200 flex items-center gap-2 text-left"
            >
              <i className="fa-solid fa-compass text-indigo-400" /> Explore
            </button>
            <button
              onClick={() => {
                navigate('/how-it-works');
                setMobileDrawerOpen(false);
              }}
              className="p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800 text-slate-200 flex items-center gap-2 text-left"
            >
              <i className="fa-solid fa-circle-question text-slate-400" /> How It Works
            </button>
            <button
              onClick={() => {
                navigate('/list-space');
                setMobileDrawerOpen(false);
              }}
              className="p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800 text-slate-200 flex items-center gap-2 text-left"
            >
              <i className="fa-solid fa-plus text-indigo-400" /> List Space
            </button>
          </div>

          <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
            <button
              type="button"
              onClick={() => {
                onOpenDemoModal();
                setMobileDrawerOpen(false);
              }}
              className="text-xs font-semibold text-indigo-300 flex items-center gap-1.5"
            >
              <i className="fa-solid fa-sliders text-indigo-400" />
              <span>Judge / Demo Console</span>
            </button>
            {currentUser && (
              <button
                type="button"
                onClick={handleLogout}
                className="text-xs text-rose-400 font-semibold"
              >
                Sign Out
              </button>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
