import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { demoSwitch } from '../../services/auth';
import { useNavigate } from 'react-router-dom';

interface DemoModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentRole?: string;
}

export const DemoModal: React.FC<DemoModalProps> = ({ isOpen, onClose, currentRole }) => {
  const navigate = useNavigate();

  if (!isOpen) return null;

  const handleSelectRole = async (role: 'seeker' | 'host' | 'admin' | 'guest') => {
    try {
      await demoSwitch(role);
      onClose();
      window.location.reload();
    } catch (err) {
      console.error('Failed to switch demo persona:', err);
    }
  };

  const scenarios = [
    {
      title: '📍 Wagholi Pune Study Pod Discovery',
      desc: 'Matches quiet study pods within 1.2km of JSPM Imperial College Wagholi.',
      action: () => {
        onClose();
        navigate('/?q=quiet+study+space+in+Wagholi+Pune+under+50');
      },
    },
    {
      title: '🛡️ Active Session & QR Door Pass',
      desc: 'Tests 50m GPS geofence handshake and ₹100 UPI escrow refund.',
      action: () => {
        onClose();
        navigate('/session/12');
      },
    },
    {
      title: '🤖 Multimodal AI Space Inspector',
      desc: 'Auto-detects room dimensions, acoustics dB, and smart price recommendation.',
      action: () => {
        onClose();
        navigate('/list-space');
      },
    },
  ];

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 w-full max-w-xl rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Hackathon Evaluation & Demo Console
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 text-sm font-bold"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          {/* Persona Switchers */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-300">
              Select Demo Persona (1-Click Authentication)
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => handleSelectRole('seeker')}
                className={`p-3.5 rounded-xl border text-left transition flex items-start gap-3 ${
                  currentRole === 'seeker'
                    ? 'bg-indigo-600/20 border-indigo-500 text-white'
                    : 'bg-slate-950/80 border-slate-800 hover:border-slate-700 text-slate-300'
                }`}
              >
                <span className="text-2xl">🎓</span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-white">Aarav Sharma</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 font-bold">
                      Seeker
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    IIT Delhi Student • 840 Trust Score
                  </p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleSelectRole('host')}
                className={`p-3.5 rounded-xl border text-left transition flex items-start gap-3 ${
                  currentRole === 'host'
                    ? 'bg-indigo-600/20 border-indigo-500 text-white'
                    : 'bg-slate-950/80 border-slate-800 hover:border-slate-700 text-slate-300'
                }`}
              >
                <span className="text-2xl">🏠</span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-white">Sunita Deshmukh</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                      Host
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Wagholi Property Owner • ₹18.4k Earned
                  </p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleSelectRole('admin')}
                className={`p-3.5 rounded-xl border text-left transition flex items-start gap-3 ${
                  currentRole === 'admin'
                    ? 'bg-indigo-600/20 border-indigo-500 text-white'
                    : 'bg-slate-950/80 border-slate-800 hover:border-slate-700 text-slate-300'
                }`}
              >
                <span className="text-2xl">👑</span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-white">Platform Admin</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Full verification & dispute escalation
                  </p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleSelectRole('guest')}
                className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/80 hover:border-rose-500/40 text-left transition flex items-start gap-3"
              >
                <span className="text-2xl">🚪</span>
                <div>
                  <span className="text-xs font-bold text-rose-300">Reset to Guest</span>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Test unauthenticated booking flow
                  </p>
                </div>
              </button>
            </div>
          </div>

          {/* Quick Evaluation Scenarios */}
          <div className="space-y-3 pt-4 border-t border-slate-800">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Jump to Core Evaluation Scenarios
            </h4>
            <div className="space-y-2">
              {scenarios.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={s.action}
                  className="w-full p-3 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/40 text-left transition flex items-center justify-between group"
                >
                  <div>
                    <span className="text-xs font-bold text-slate-200 group-hover:text-indigo-300 transition">
                      {s.title}
                    </span>
                    <p className="text-[11px] text-slate-400">{s.desc}</p>
                  </div>
                  <span className="text-xs text-indigo-400 font-bold ml-2">Open →</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition"
          >
            Close Console
          </button>
        </div>
      </div>
    </div>
  );
};
