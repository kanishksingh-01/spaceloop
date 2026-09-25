import React, { useState } from 'react';
import { loginUser, registerUser, digilockerAuth, studentSsoAuth } from '../../services/auth';
import { User } from '../../types';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (user?: User) => void;
  initialMode?: 'login' | 'register';
  onSwitchToHost?: () => void;
}

type AuthMethod = 'credentials' | 'sso' | 'digilocker';

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialMode = 'login',
  onSwitchToHost,
}) => {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);
  const [method, setMethod] = useState<AuthMethod>('credentials');

  // Form fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<'seeker' | 'host'>('seeker');

  // Academic SSO fields - clean empty defaults
  const [collegeName, setCollegeName] = useState('');
  const [studentId, setStudentId] = useState('');
  const [collegeEmail, setCollegeEmail] = useState('');

  // DigiLocker fields - clean empty defaults
  const [aadhaarNumber, setAadhaarNumber] = useState('');
  const [otp, setOtp] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }

    setLoading(true);
    try {
      let authedUser: User | undefined;
      if (mode === 'login') {
        const res = await loginUser(email, password);
        authedUser = res?.user;
        setSuccessMsg('Signed in successfully!');
      } else {
        if (password !== confirmPassword) {
          setError('Passwords do not match.');
          setLoading(false);
          return;
        }
        const nameParts = name.trim().split(' ');
        const firstName = nameParts[0] || 'User';
        const lastName = nameParts.slice(1).join(' ') || '';

        const res = await registerUser({
          first_name: firstName,
          last_name: lastName,
          email,
          password,
          confirm_password: confirmPassword,
          role,
        });
        authedUser = res?.user;
        setSuccessMsg('Account registered and verified!');
      }

      setLoading(false);
      if (onSuccess) onSuccess(authedUser);
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
      setLoading(false);
    }
  };

  const handleSsoSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!collegeEmail || !studentId) {
      setError('Please provide academic email and student ID.');
      return;
    }

    setLoading(true);
    try {
      const res = await studentSsoAuth({
        name: name || 'Academic Scholar',
        college_email: collegeEmail,
        college_name: collegeName || 'University',
        student_id: studentId,
      });
      setSuccessMsg('University Student SSO verified!');
      setLoading(false);
      if (onSuccess) onSuccess(res?.user);
    } catch (err: any) {
      setError(err.message || 'SSO verification failed.');
      setLoading(false);
    }
  };

  const handleDigiLockerSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!aadhaarNumber || !otp) {
      setError('Please provide Aadhaar number and OTP.');
      return;
    }

    setLoading(true);
    try {
      const res = await digilockerAuth({
        name: name || 'DigiLocker Verified User',
        aadhaar_number: aadhaarNumber,
        otp,
        role,
      });
      setSuccessMsg('DigiLocker Aadhaar authentication verified!');
      setLoading(false);
      if (onSuccess) onSuccess(res?.user);
    } catch (err: any) {
      setError(err.message || 'DigiLocker verification failed.');
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white w-full max-w-lg rounded-3xl floating-panel overflow-hidden my-6 transition-all">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30">
                🚀 Space Seeker Authentication
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              {mode === 'login' ? 'Seeker Sign In' : 'Join SpaceLoop'}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {mode === 'login'
                ? 'Sign in to reserve workspaces, studios, micro-pods, and manage your bookings.'
                : 'Create your Seeker account with verified credentials.'}
            </p>
          </div>
          <button
            onClick={onClose}
            type="button"
            className="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            ✕
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* Switch to Host Auth Banner */}
          {onSwitchToHost && (
            <div className="p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <span className="text-xl">🏡</span>
                <div>
                  <div className="text-xs font-bold text-amber-300">Looking to Host or List Spaces?</div>
                  <div className="text-[10px] text-slate-400">Hosts require State Electricity Discom & UPI Bank KYC.</div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  onClose();
                  onSwitchToHost();
                }}
                className="px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shrink-0 transition"
              >
                Host Portal →
              </button>
            </div>
          )}
          {/* Status Banners */}
          {error && (
            <div className="p-3.5 bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/30 rounded-2xl flex items-start gap-2">
              <span className="text-rose-500 text-sm">⚠️</span>
              <p className="text-xs text-rose-700 dark:text-rose-300 font-medium">{error}</p>
            </div>
          )}
          {successMsg && (
            <div className="p-3.5 bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/30 rounded-2xl flex items-start gap-2">
              <span className="text-emerald-500 text-sm">✓</span>
              <p className="text-xs text-emerald-700 dark:text-emerald-300 font-medium">{successMsg}</p>
            </div>
          )}


          {/* Authentication Method Selector */}
          <div className="flex rounded-xl bg-slate-100 dark:bg-slate-950 p-1 border border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={() => setMethod('credentials')}
              className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition ${
                method === 'credentials'
                  ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
              }`}
            >
              Email & Password
            </button>
            <button
              type="button"
              onClick={() => setMethod('sso')}
              className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition ${
                method === 'sso'
                  ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
              }`}
            >
              University SSO
            </button>
            <button
              type="button"
              onClick={() => setMethod('digilocker')}
              className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition ${
                method === 'digilocker'
                  ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-300'
              }`}
            >
              DigiLocker / Aadhaar
            </button>
          </div>

          {/* METHOD 1: Credentials (Standard Login / Register) */}
          {method === 'credentials' && (
            <form onSubmit={handleCredentialsSubmit} className="space-y-3.5">
              {mode === 'register' && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Full Name
                    </label>
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. Full Name"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Account Type / Role
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        type="button"
                        onClick={() => setRole('seeker')}
                        className={`p-2.5 rounded-xl border text-left text-xs font-bold transition ${
                          role === 'seeker'
                            ? 'bg-indigo-50 dark:bg-indigo-950/40 border-indigo-500 text-indigo-700 dark:text-indigo-300'
                            : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                        }`}
                      >
                        <div>🎟️ Space Seeker</div>
                        <div className="text-[10px] font-normal text-slate-400">Book desks, studios & spaces</div>
                      </button>
                      <button
                        type="button"
                        onClick={() => setRole('host')}
                        className={`p-2.5 rounded-xl border text-left text-xs font-bold transition ${
                          role === 'host'
                            ? 'bg-indigo-50 dark:bg-indigo-950/40 border-indigo-500 text-indigo-700 dark:text-indigo-300'
                            : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                        }`}
                      >
                        <div>🏠 Host / Owner</div>
                        <div className="text-[10px] font-normal text-slate-400">List spaces & earn hourly</div>
                      </button>
                    </div>
                  </div>
                </>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. name@domain.com"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {mode === 'register' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm transition shadow-lg shadow-indigo-600/25 disabled:opacity-50"
              >
                {loading
                  ? 'Authenticating...'
                  : mode === 'login'
                  ? 'Sign In to Account'
                  : 'Complete Registration'}
              </button>
            </form>
          )}

          {/* METHOD 2: University SSO */}
          {method === 'sso' && (
            <form onSubmit={handleSsoSubmit} className="space-y-3.5">
              <div className="p-3 bg-indigo-50/70 dark:bg-indigo-950/40 rounded-xl border border-indigo-200 dark:border-indigo-800 text-xs text-indigo-800 dark:text-indigo-300">
                🎓 <strong>Verified Academic Access:</strong> Grants immediate student discount tier and verified trust badge on your door passes.
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your full name"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  College / University
                </label>
                <input
                  type="text"
                  required
                  value={collegeName}
                  onChange={(e) => setCollegeName(e.target.value)}
                  placeholder="e.g. IIT Delhi / BITS Pilani / COEP"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Student ID / Roll No
                  </label>
                  <input
                    type="text"
                    required
                    value={studentId}
                    onChange={(e) => setStudentId(e.target.value)}
                    placeholder="e.g. 2023CSB108"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Academic Email
                  </label>
                  <input
                    type="email"
                    required
                    value={collegeEmail}
                    onChange={(e) => setCollegeEmail(e.target.value)}
                    placeholder="name@college.edu.in"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm transition shadow-lg shadow-indigo-600/25 disabled:opacity-50"
              >
                {loading ? 'Authenticating SSO...' : 'Verify & Continue with College SSO'}
              </button>
            </form>
          )}

          {/* METHOD 3: DigiLocker Aadhaar */}
          {method === 'digilocker' && (
            <form onSubmit={handleDigiLockerSubmit} className="space-y-3.5">
              <div className="p-3 bg-emerald-50/70 dark:bg-emerald-950/40 rounded-xl border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300">
                🛡️ <strong>DigiLocker National Stack:</strong> Instantly issues verified host or seeker credentials with objective 920+ trust rating.
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Full Name (as registered on Aadhaar)
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter full legal name"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Aadhaar Number (12 digits)
                  </label>
                  <input
                    type="text"
                    required
                    value={aadhaarNumber}
                    onChange={(e) => setAadhaarNumber(e.target.value)}
                    placeholder="Enter 12-digit Aadhaar number"
                    maxLength={14}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    DigiLocker OTP
                  </label>
                  <input
                    type="password"
                    required
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    placeholder="6-digit OTP"
                    maxLength={6}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Authenticate As
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setRole('seeker')}
                    className={`p-2.5 rounded-xl border text-center text-xs font-bold transition ${
                      role === 'seeker'
                        ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 text-emerald-700 dark:text-emerald-300'
                        : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    Verified Seeker
                  </button>
                  <button
                    type="button"
                    onClick={() => setRole('host')}
                    className={`p-2.5 rounded-xl border text-center text-xs font-bold transition ${
                      role === 'host'
                        ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 text-emerald-700 dark:text-emerald-300'
                        : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    Verified Host
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm transition shadow-lg shadow-emerald-600/25 disabled:opacity-50"
              >
                {loading ? 'Verifying OTP...' : 'Authenticate via DigiLocker OTP'}
              </button>
            </form>
          )}

          {/* Toggle between Login and Sign Up */}
          <div className="pt-3 border-t border-slate-200 dark:border-slate-800 text-center">
            {mode === 'login' ? (
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => {
                    setMode('register');
                    setError(null);
                    setSuccessMsg(null);
                  }}
                  className="font-bold text-indigo-600 dark:text-indigo-400 hover:underline ml-1"
                >
                  Sign up
                </button>
              </p>
            ) : (
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => {
                    setMode('login');
                    setError(null);
                    setSuccessMsg(null);
                  }}
                  className="font-bold text-indigo-600 dark:text-indigo-400 hover:underline ml-1"
                >
                  Log in
                </button>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
