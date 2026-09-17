import React, { useState } from 'react';
import { hostLogin, hostRegister, hostUpgrade, demoSwitch } from '../../services/auth';
import { User } from '../../types';

interface HostAuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  currentUser?: User | null;
  onSwitchToSeeker?: () => void;
}

export const HostAuthModal: React.FC<HostAuthModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  currentUser,
  onSwitchToSeeker,
}) => {
  const isUpgradingSeeker = Boolean(currentUser && !currentUser.is_host);
  const [activeTab, setActiveTab] = useState<'login' | 'register'>(isUpgradingSeeker ? 'register' : 'login');

  // Credentials
  const [name, setName] = useState(currentUser?.name || '');
  const [email, setEmail] = useState(currentUser?.email || '');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Discom Property KYC
  const [provider, setProvider] = useState('BESCOM');
  const [caNumber, setCaNumber] = useState('CA9874561230');
  const [address, setAddress] = useState('80 Feet Rd, Koramangala 4th Block, Bengaluru, KA');

  // UPI Penny Drop
  const [upiVpa, setUpiVpa] = useState('sunita.spaces@okhdfcbank');
  const [panName, setPanName] = useState(currentUser?.name || 'Sunita Sharma');

  // Legal
  const [easementsAccepted, setEasementsAccepted] = useState(true);

  // States
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const applySpoofedHost = () => {
    setError(null);
    setSuccessMsg(null);
    setName('Sunita Sharma');
    setEmail('sunita@spaceloop.in');
    setPassword('password123');
    setConfirmPassword('password123');
    setProvider('TPDDL (Tata Power Delhi)');
    setCaNumber('10048219034');
    setAddress('Hauz Khas Enclave, New Delhi, DL');
    setUpiVpa('sunita.sharma@okhdfcbank');
    setPanName('Sunita Sharma');
  };

  const handleHostLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!email || !password) {
      setError('Please enter both host email and password.');
      return;
    }

    setLoading(true);
    try {
      await hostLogin(email, password);
      setSuccessMsg('Host session authenticated! Redirecting to Host Portal...');
      if (onSuccess) onSuccess();
      setTimeout(() => {
        window.location.href = '/host/dashboard';
      }, 500);
    } catch (err: any) {
      setError(err.message || 'Host login failed. Ensure your account has verified host privileges.');
      setLoading(false);
    }
  };

  const handleHostRegisterOrUpgrade = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!isUpgradingSeeker && (!email || !password)) {
      setError('Please provide host email and password.');
      return;
    }

    if (!isUpgradingSeeker && password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (!caNumber || caNumber.length < 8) {
      setError('Please enter a valid Consumer Account (CA) number (minimum 8 characters).');
      return;
    }

    if (!upiVpa || !upiVpa.includes('@')) {
      setError('Please enter a valid UPI ID / VPA (e.g. username@bank).');
      return;
    }

    if (!easementsAccepted) {
      setError('You must accept the Section 52 Indian Easements Act license compliance.');
      return;
    }

    setLoading(true);
    try {
      if (isUpgradingSeeker) {
        // Upgrade existing seeker account
        await hostUpgrade({
          ca_number: caNumber,
          provider,
          address,
          upi_vpa: upiVpa,
          pan_name: panName || name,
        });
        setSuccessMsg('Account upgraded to Verified Host! Discom & UPI linked.');
      } else {
        // Full new host registration
        const nameParts = name.trim().split(' ');
        await hostRegister({
          first_name: nameParts[0] || 'Host',
          last_name: nameParts.slice(1).join(' ') || '',
          email,
          password,
          confirm_password: confirmPassword,
          ca_number: caNumber,
          provider,
          address,
          upi_vpa: upiVpa,
          pan_name: panName || name,
        });
        setSuccessMsg('Host account created & verified! Redirecting to Host Portal...');
      }

      if (onSuccess) onSuccess();
      setTimeout(() => {
        window.location.href = '/host/dashboard';
      }, 600);
    } catch (err: any) {
      setError(err.message || 'Host registration / verification failed.');
      setLoading(false);
    }
  };

  const handleQuickDemoHost = async () => {
    setLoading(true);
    try {
      await demoSwitch('host');
      if (onSuccess) onSuccess();
      window.location.href = '/host/dashboard';
    } catch (err: any) {
      setError(err.message || 'Failed to switch to host demo persona');
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
      <div className="bg-slate-900 border border-amber-500/30 text-white w-full max-w-xl rounded-3xl floating-panel overflow-hidden my-6 transition-all">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-800 bg-gradient-to-r from-slate-900 via-amber-950/20 to-slate-900 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1.5">
                <i className="fa-solid fa-house-chimney" /> Host & Property Portal
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Discom & UPI Verified
              </span>
            </div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              {isUpgradingSeeker
                ? 'Unlock Host Privileges & Property KYC'
                : activeTab === 'login'
                ? 'Host Sign In'
                : 'Register as Verified Space Host'}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              {isUpgradingSeeker
                ? 'Link your property electricity bill and UPI VPA to monetize unused square footage.'
                : 'Manage listings, inspect condition delta reports, and receive micro-lease payouts.'}
            </p>
          </div>
          <button
            onClick={onClose}
            type="button"
            className="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            ✕
          </button>
        </div>

        <div className="p-6 space-y-5 max-h-[80vh] overflow-y-auto">
          {/* Status Banners */}
          {error && (
            <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-2xl flex items-start gap-2">
              <span className="text-rose-400 text-sm">⚠️</span>
              <p className="text-xs text-rose-300 font-medium">{error}</p>
            </div>
          )}
          {successMsg && (
            <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl flex items-start gap-2">
              <span className="text-emerald-400 text-sm">✓</span>
              <p className="text-xs text-emerald-300 font-medium">{successMsg}</p>
            </div>
          )}

          {/* Quick-Fill Spoofed Host Persona */}
          <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-2xl flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-400 text-sm">
                🏡
              </div>
              <div>
                <div className="text-xs font-bold text-amber-300">Quick Host Persona (Sunita Sharma)</div>
                <div className="text-[10px] text-slate-400">Autofill verified Discom (TPDDL) & UPI credentials</div>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={applySpoofedHost}
                className="px-2.5 py-1 text-[11px] font-bold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
              >
                Auto-Fill Form
              </button>
              <button
                type="button"
                onClick={handleQuickDemoHost}
                className="px-2.5 py-1 text-[11px] font-bold rounded-lg bg-amber-600 hover:bg-amber-500 text-white shadow-sm transition"
              >
                1-Click Login
              </button>
            </div>
          </div>

          {/* Mode Switch Tabs (if not upgrading seeker) */}
          {!isUpgradingSeeker && (
            <div className="flex p-1 bg-slate-950/80 rounded-2xl border border-slate-800">
              <button
                type="button"
                onClick={() => {
                  setActiveTab('login');
                  setError(null);
                }}
                className={`flex-1 py-2 text-xs font-bold rounded-xl transition ${
                  activeTab === 'login'
                    ? 'bg-amber-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Host Sign In
              </button>
              <button
                type="button"
                onClick={() => {
                  setActiveTab('register');
                  setError(null);
                }}
                className={`flex-1 py-2 text-xs font-bold rounded-xl transition ${
                  activeTab === 'register'
                    ? 'bg-amber-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Host Onboarding & Discom KYC
              </button>
            </div>
          )}

          {/* Form Content */}
          {activeTab === 'login' && !isUpgradingSeeker ? (
            <form onSubmit={handleHostLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">Host Account Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="sunita@spaceloop.in"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-amber-500 transition"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">Host Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-amber-500 transition"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white font-bold text-xs shadow-lg shadow-amber-600/25 transition disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? <i className="fa-solid fa-circle-notch fa-spin text-sm" /> : <i className="fa-solid fa-lock text-xs" />}
                <span>{loading ? 'Authenticating Host...' : 'Sign In to Host Portal'}</span>
              </button>
            </form>
          ) : (
            <form onSubmit={handleHostRegisterOrUpgrade} className="space-y-4">
              {!isUpgradingSeeker && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1">Owner / Host Name</label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => {
                        setName(e.target.value);
                        setPanName(e.target.value);
                      }}
                      placeholder="Sunita Sharma"
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:border-amber-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1">Host Email</label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="host@property.in"
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:border-amber-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1">Password</label>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Min 8 chars, 1 digit, 1 upper"
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:border-amber-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1">Confirm Password</label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Re-enter password"
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs focus:border-amber-500"
                      required
                    />
                  </div>
                </div>
              )}

              {/* Property Utility KYC Section */}
              <div className="p-3.5 bg-slate-950/80 rounded-2xl border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-amber-300 flex items-center gap-1.5">
                    <i className="fa-solid fa-bolt text-amber-400" /> 1. Property Electricity Proof (Discom BBPS)
                  </span>
                  <span className="text-[10px] text-emerald-400 font-semibold">Instant Utility Match</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-400 mb-1">State Electricity Board</label>
                    <select
                      value={provider}
                      onChange={(e) => setProvider(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs"
                    >
                      <option value="BESCOM">BESCOM (Bangalore Electricity Supply)</option>
                      <option value="TPDDL (Tata Power Delhi)">TPDDL (Tata Power Delhi)</option>
                      <option value="BSES Rajdhani">BSES Rajdhani Power Limited</option>
                      <option value="BSES Yamuna">BSES Yamuna Power Limited</option>
                      <option value="MSEDCL">MSEDCL (Maharashtra State Discom)</option>
                      <option value="Adani Electricity">Adani Electricity Mumbai</option>
                      <option value="UPPCL">UPPCL (Uttar Pradesh Power Corp)</option>
                      <option value="TANGEDCO">TANGEDCO (Tamil Nadu)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-400 mb-1">Consumer Account (CA) #</label>
                    <input
                      type="text"
                      value={caNumber}
                      onChange={(e) => setCaNumber(e.target.value)}
                      placeholder="CA9874561230"
                      className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">Property Service Address</label>
                  <input
                    type="text"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    placeholder="Floor, Building, Road, Locality, City, State"
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs"
                    required
                  />
                </div>
              </div>

              {/* UPI Payout & Escrow Account */}
              <div className="p-3.5 bg-slate-950/80 rounded-2xl border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-emerald-300 flex items-center gap-1.5">
                    <i className="fa-solid fa-money-bill-transfer text-emerald-400" /> 2. Payout Account & UPI Penny Drop
                  </span>
                  <span className="text-[10px] text-slate-400">NPCI ₹1 Verification</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-400 mb-1">UPI ID / VPA</label>
                    <input
                      type="text"
                      value={upiVpa}
                      onChange={(e) => setUpiVpa(e.target.value)}
                      placeholder="username@okhdfcbank"
                      className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-400 mb-1">PAN / Bank Beneficiary Name</label>
                    <input
                      type="text"
                      value={panName}
                      onChange={(e) => setPanName(e.target.value)}
                      placeholder="Sunita Sharma"
                      className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Legal Section 52 Declaration */}
              <div className="p-3 bg-slate-950/90 rounded-xl border border-slate-800 flex items-start gap-2.5">
                <input
                  type="checkbox"
                  id="easements_check"
                  checked={easementsAccepted}
                  onChange={(e) => setEasementsAccepted(e.target.checked)}
                  className="mt-0.5 rounded border-slate-700 text-amber-500 focus:ring-amber-400"
                />
                <label htmlFor="easements_check" className="text-[11px] text-slate-400 leading-snug cursor-pointer">
                  I certify that I possess lawful title or lease authority for this premises and agree to grant revocable micro-licenses under <strong className="text-slate-300">Section 52 of the Indian Easements Act, 1882</strong> (no tenancy created).
                </label>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/25 transition disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? <i className="fa-solid fa-circle-notch fa-spin text-sm" /> : <i className="fa-solid fa-shield-check text-xs" />}
                <span>{loading ? 'Verifying Discom & Payout...' : (isUpgradingSeeker ? 'Verify & Upgrade to Host' : 'Complete Host Verification & Register')}</span>
              </button>
            </form>
          )}

          {/* Cross-Link to Seeker Auth */}
          <div className="pt-3 border-t border-slate-800 text-center">
            <p className="text-xs text-slate-400">
              Looking to find and book workspaces as a student or guest?{' '}
              <button
                type="button"
                onClick={() => {
                  onClose();
                  if (onSwitchToSeeker) onSwitchToSeeker();
                }}
                className="text-indigo-400 hover:text-indigo-300 font-bold underline transition"
              >
                Go to Seeker Authentication →
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
