import React, { useState } from 'react';
import { View, Text, Pressable } from 'react-native';
import { useNavigate } from 'react-router-dom';
import { ThemeToggle } from './ThemeToggle';

interface FooterProps {
  onOpenDemoModal: () => void;
}

export const Footer: React.FC<FooterProps> = ({ onOpenDemoModal }) => {
  const navigate = useNavigate();
  const [legalModalType, setLegalModalType] = useState<'privacy' | 'terms' | 'easements' | null>(null);

  const legalContent = {
    privacy: {
      title: 'Privacy Policy & DPDP Act (2023) Compliance',
      body: 'SpaceLoop processes user data in strict adherence to the Digital Personal Data Protection (DPDP) Act, 2023. User identity verification through DigiLocker utilizes ephemeral tokenization—zero plaintext Aadhaar or government ID numbers are stored in platform databases. Geolocation telemetry is utilized exclusively at the instant of access validation (50m geofence handshake) and checkout verification, with zero background tracking outside active micro-lease windows.',
    },
    terms: {
      title: 'Terms of Service & Platform Governance',
      body: 'All platform transactions constitute short-duration revocable micro-leases. Seekers and Hosts agree to punctuality benchmarks (on-time checkout) and premises condition preservation. A mandatory ₹100 UPI escrow deposit is reserved at booking creation and released automatically upon verified checkout handshake without property damage or overstay violations.',
    },
    easements: {
      title: 'Indian Easements Act, 1882 (Section 52)',
      body: 'Every booking generated on SpaceLoop operates strictly as a revocable license under Section 52 of the Indian Easements Act, 1882. The booking does NOT create a tenancy, sub-tenancy, or leasehold interest. The host retains full legal possession, control, and dominion over the licensed premises at all times. The guest is deemed a temporary licensee permitted to occupy the specific space exclusively for the booked hourly slot.',
    },
  };

  return (
    <>
      <footer className="bg-slate-950 border-t border-slate-800/80 mt-20 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 mb-10">
            {/* Brand (5 cols) */}
            <div className="md:col-span-5 space-y-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-indigo-600 flex items-center justify-center text-white text-sm shadow-md shadow-indigo-600/30">
                  <i className="fa-solid fa-infinity" />
                </div>
                <span className="text-xl font-extrabold text-white tracking-tight">SpaceLoop</span>
              </div>
              <p className="text-sm text-slate-200 font-semibold italic">
                &ldquo;Turning idle spaces into opportunities.&rdquo;
              </p>
              <p className="text-xs text-slate-400 max-w-sm leading-relaxed">
                India's premier AI-powered micro-leasing platform connecting students and creators with verified study rooms, workspaces, and creative studios.
              </p>
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
                <i className="fa-solid fa-shield-halved text-[11px]" />
                <span>SpaceLoop Verified &bull; Zero-Hardware India Stack Protocol</span>
              </div>
            </div>

            {/* Navigation (4 cols) */}
            <div className="md:col-span-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3.5">Navigation</h4>
              <ul className="grid grid-cols-2 gap-2 text-xs font-medium text-slate-400">
                <li>
                  <button
                    type="button"
                    onClick={() => navigate('/explore')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-compass text-slate-500 text-[10px]" /> Explore
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => navigate('/list-space')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-plus text-slate-500 text-[10px]" /> Host
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => navigate('/how-it-works')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-circle-question text-slate-500 text-[10px]" /> How It Works
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => navigate('/verify')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-shield-check text-slate-500 text-[10px]" /> Safety
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => navigate('/how-it-works')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-comments text-slate-500 text-[10px]" /> Help
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => navigate('/calculator')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-calculator text-slate-500 text-[10px]" /> Calculator
                  </button>
                </li>
              </ul>
            </div>

            {/* Legal (3 cols) */}
            <div className="md:col-span-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3.5">Legal</h4>
              <ul className="space-y-2 text-xs font-medium text-slate-400">
                <li>
                  <button
                    type="button"
                    onClick={() => setLegalModalType('privacy')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-user-shield text-slate-500 text-[10px]" /> Privacy Policy
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => setLegalModalType('terms')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-file-contract text-slate-500 text-[10px]" /> Terms of Service
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => setLegalModalType('easements')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-scale-balanced text-slate-500 text-[10px]" /> Indian Easements Act, 1882
                  </button>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="pt-8 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
            <div className="flex items-center gap-3">
              <p>&copy; 2026 SpaceLoop. All rights reserved.</p>
              <ThemeToggle variant="compact" />
            </div>
            <div className="flex items-center gap-3 text-slate-400 flex-wrap justify-center">
              <span className="flex items-center gap-1">
                <i className="fa-solid fa-shield-halved text-emerald-400" /> ₹100 UPI Escrow
              </span>
              <span>&bull;</span>
              <span className="flex items-center gap-1">
                <i className="fa-solid fa-robot text-indigo-400" /> AI Condition Delta
              </span>
              <span>&bull;</span>
              <span className="flex items-center gap-1">
                <i className="fa-solid fa-location-crosshairs text-amber-400" /> 50m Geofence Gate
              </span>
              <span>&bull;</span>
              <button
                type="button"
                onClick={onOpenDemoModal}
                className="text-indigo-400 hover:text-indigo-300 font-semibold underline"
              >
                ⚡ Judge / Demo Console
              </button>
            </div>
          </div>
        </div>
      </footer>

      {/* Legal Info Modal */}
      {legalModalType && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-xl rounded-2xl shadow-2xl overflow-hidden flex flex-col">
            <div className="p-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <i className="fa-solid fa-scale-balanced text-indigo-400" />
                <span>{legalContent[legalModalType].title}</span>
              </h3>
              <button
                type="button"
                onClick={() => setLegalModalType(null)}
                className="text-slate-400 hover:text-white p-1"
              >
                <i className="fa-solid fa-xmark text-lg" />
              </button>
            </div>
            <div className="p-6 text-xs text-slate-300 space-y-3 leading-relaxed max-h-[60vh] overflow-y-auto">
              <p>{legalContent[legalModalType].body}</p>
            </div>
            <div className="p-4 bg-slate-950 border-t border-slate-800 flex justify-end">
              <button
                type="button"
                onClick={() => setLegalModalType(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
