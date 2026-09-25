import React, { useState } from 'react';
import { hostLogin, hostRegister, hostUpgrade, verifyMfaLogin, resendEmailVerification } from '../../services/auth';
import { User } from '../../types';

interface HostAuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (user?: User) => void;
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

  // MFA State
  const [mfaRequired, setMfaRequired] = useState(false);
  const [mfaToken, setMfaToken] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [mfaRecoveryCode, setMfaRecoveryCode] = useState('');
  const [useRecoveryCode, setUseRecoveryCode] = useState(false);

  // Email Verification State
  const [verificationSent, setVerificationSent] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState('');
  const [unverifiedEmail, setUnverifiedEmail] = useState<string | null>(null);
  const [resending, setResending] = useState(false);
  const [resendStatus, setResendStatus] = useState<string | null>(null);

  // Credentials
  const [name, setName] = useState(currentUser?.name || '');
  const [email, setEmail] = useState(currentUser?.email || '');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Discom Property KYC
  const [provider, setProvider] = useState('BESCOM');
  const [caNumber, setCaNumber] = useState('');
  const [address, setAddress] = useState('');

  // UPI Penny Drop
  const [upiVpa, setUpiVpa] = useState('');
  const [panName, setPanName] = useState(currentUser?.name || '');

  // Legal
  const [easementsAccepted, setEasementsAccepted] = useState(false);

  // States
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;


  const handleResendEmail = async (targetEmail: string) => {
    if (!targetEmail) return;
    setResending(true);
    setResendStatus(null);
    try {
      const res = await resendEmailVerification(targetEmail);
      setResendStatus(res.message || 'Verification link sent! Check your inbox.');
    } catch (e: any) {
      setResendStatus(e.message || 'Failed to resend verification link.');
    } finally {
      setResending(false);
    }
  };

  const handleHostLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setUnverifiedEmail(null);
    setResendStatus(null);

    if (!email || !password) {
      setError('Please enter both host email and password.');
      return;
    }

    setLoading(true);
    try {
      const res = await hostLogin(email, password);
      if (res?.mfa_required && res?.mfa_token) {
        setMfaRequired(true);
        setMfaToken(res.mfa_token);
        setLoading(false);
        return;
      }
      setSuccessMsg('Host session authenticated! Redirecting to Host Portal...');
      if (onSuccess) onSuccess(res?.user);
      setTimeout(() => {
        window.location.href = '/host/dashboard';
      }, 500);
    } catch (err: any) {
      if (err?.data?.email_verification_required || (err?.status === 403 && err.message?.toLowerCase().includes('verify your email'))) {
        setUnverifiedEmail(err?.data?.email || email);
        setError('Please verify your email address before logging in.');
      } else {
        setError(err.message || 'Host login failed. Ensure your account has verified host privileges.');
      }
      setLoading(false);
    }
  };

  const handleHostMfaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (!useRecoveryCode && (!mfaCode.trim() || mfaCode.trim().length !== 6)) {
      setError('Please enter the 6-digit verification code from your authenticator app.');
      return;
    }

    if (useRecoveryCode && !mfaRecoveryCode.trim()) {
      setError('Please enter your backup recovery code.');
      return;
    }

    setLoading(true);
    try {
      const res = await verifyMfaLogin({
        mfa_token: mfaToken,
        code: !useRecoveryCode ? mfaCode.trim() : undefined,
        recovery_code: useRecoveryCode ? mfaRecoveryCode.trim() : undefined,
        portal: 'host',
      });
      setSuccessMsg('Host Two-Factor Authentication verified! Redirecting to Host Portal...');
      if (onSuccess) onSuccess(res?.user);
      setTimeout(() => {
        window.location.href = '/host/dashboard';
      }, 500);
    } catch (err: any) {
      setError(err.message || 'MFA verification failed. Please check your code and try again.');
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
      let resUser: User | undefined;
      if (isUpgradingSeeker) {
        // Upgrade existing seeker account
        const res = await hostUpgrade({
          ca_number: caNumber,
          provider,
          address,
          upi_vpa: upiVpa,
          pan_name: panName || name,
        });
        resUser = res?.user;
        setSuccessMsg('Account upgraded to Verified Host! Discom & UPI linked.');
      } else {
        // Full new host registration
        const nameParts = name.trim().split(' ');
        const res = await hostRegister({
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

        if (res?.email_verification_required) {
          setVerificationSent(true);
          setRegisteredEmail(email);
          setSuccessMsg('Host account created! Please verify your email before logging in.');
          setLoading(false);
          return;
        }
        resUser = res?.user;
        setSuccessMsg('Host account created & verified! Redirecting to Host Portal...');
      }

      if (onSuccess) onSuccess(resUser);
      setTimeout(() => {
        window.location.href = '/host/dashboard';
      }, 600);
    } catch (err: any) {
      setError(err.message || 'Host registration / verification failed.');
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
          {unverifiedEmail && (
            <div className="p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex flex-col gap-2">
              <div className="flex items-start gap-2">
                <span className="text-amber-400 text-sm">✉️</span>
                <div>
                  <p className="text-xs text-amber-300 font-medium">
                    Please verify your email address before logging into the Host Portal.
                  </p>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    We sent a verification link to <strong className="text-white">{unverifiedEmail}</strong>.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 pt-1">
                <button
                  type="button"
                  disabled={resending}
                  onClick={() => handleResendEmail(unverifiedEmail)}
                  className="px-3 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 text-[11px] font-bold transition disabled:opacity-50"
                >
                  {resending ? 'Sending link...' : 'Resend verification link'}
                </button>
                {resendStatus && (
                  <span className="text-[11px] text-emerald-400 font-medium">{resendStatus}</span>
                )}
              </div>
            </div>
          )}
          {error && !unverifiedEmail && (
            <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-2xl flex items-start gap-2">
              <span className="text-rose-400 text-sm">⚠️</span>
              <p className="text-xs text-rose-300 font-medium">{error}</p>
            </div>
          )}
          {successMsg && !verificationSent && (
            <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl flex items-start gap-2">
              <span className="text-emerald-400 text-sm">✓</span>
              <p className="text-xs text-emerald-300 font-medium">{successMsg}</p>
            </div>
          )}


          {verificationSent ? (
            <div className="space-y-5 text-center py-4">
              <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 text-3xl mx-auto shadow-inner">
                ✉️
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">Check Your Host Email</h3>
                <p className="text-xs text-slate-300 mt-2 max-w-sm mx-auto leading-relaxed">
                  We've sent a verification link to <strong className="text-amber-400 font-semibold">{registeredEmail}</strong>. Please click the link to verify your host account.
                </p>
              </div>

              {resendStatus && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs text-amber-300">
                  {resendStatus}
                </div>
              )}

              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-left text-xs text-slate-400 space-y-1.5">
                <p className="font-semibold text-slate-300">Important:</p>
                <p>• Your property KYC credentials are saved and will activate upon verification.</p>
                <p>• The verification link expires in 24 hours.</p>
              </div>

              <div className="space-y-2 pt-2">
                <button
                  type="button"
                  disabled={resending}
                  onClick={() => handleResendEmail(registeredEmail)}
                  className="w-full py-2.5 rounded-xl border border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 font-bold text-xs transition disabled:opacity-50"
                >
                  {resending ? 'Sending...' : 'Resend Verification Email'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setVerificationSent(false);
                    setActiveTab('login');
                    setError(null);
                    setSuccessMsg(null);
                    setResendStatus(null);
                  }}
                  className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs transition"
                >
                  Back to Host Sign In
                </button>
              </div>
            </div>
          ) : mfaRequired ? (
            <form onSubmit={handleHostMfaSubmit} className="space-y-4">
              <div className="text-center py-2">
                <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 text-2xl mx-auto mb-3 shadow-inner">
                  🔐
                </div>
                <h3 className="text-lg font-bold text-white">
                  Host Two-Factor Authentication
                </h3>
                <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                  {useRecoveryCode
                    ? 'Enter one of your single-use backup recovery codes to access the Host Portal.'
                    : 'Enter the 6-digit verification code generated by your authenticator app to access the Host Portal.'}
                </p>
              </div>

              {!useRecoveryCode ? (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5 text-center">
                    6-Digit Security Code
                  </label>
                  <input
                    type="text"
                    maxLength={6}
                    autoFocus
                    value={mfaCode}
                    onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="000000"
                    className="w-full text-center tracking-[0.4em] text-2xl font-mono px-4 py-3 rounded-xl border border-slate-700 bg-slate-950 text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5 text-center">
                    Single-Use Recovery Code (e.g. A1B2-C3D4)
                  </label>
                  <input
                    type="text"
                    autoFocus
                    value={mfaRecoveryCode}
                    onChange={(e) => setMfaRecoveryCode(e.target.value.toUpperCase())}
                    placeholder="XXXX-XXXX"
                    className="w-full text-center font-mono text-base uppercase px-4 py-3 rounded-xl border border-slate-700 bg-slate-950 text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>
              )}

              <div className="flex items-center justify-between text-xs pt-1">
                <button
                  type="button"
                  onClick={() => {
                    setUseRecoveryCode(!useRecoveryCode);
                    setError(null);
                  }}
                  className="text-amber-400 hover:underline font-medium"
                >
                  {useRecoveryCode
                    ? '← Use 6-digit authenticator code'
                    : '🔑 Use a backup recovery code instead'}
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setMfaRequired(false);
                    setMfaToken('');
                    setMfaCode('');
                    setMfaRecoveryCode('');
                    setError(null);
                  }}
                  className="text-slate-400 hover:text-white font-medium"
                >
                  Cancel
                </button>
              </div>

              <button
                type="submit"
                disabled={loading || (!useRecoveryCode ? mfaCode.length !== 6 : !mfaRecoveryCode.trim())}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 disabled:opacity-50 text-white font-bold text-sm transition shadow-lg shadow-amber-600/25"
              >
                {loading ? 'Verifying Code...' : 'Verify & Enter Host Portal →'}
              </button>
            </form>
          ) : (
            <>
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
                  placeholder="e.g. name@domain.com"
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
                      placeholder="e.g. Host Full Name"
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
                      placeholder="e.g. name@domain.com"
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
                      placeholder="Enter your password"
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
                      placeholder="e.g. CA1002345678"
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
                      placeholder="e.g. Account Holder Name"
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
        </>
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
