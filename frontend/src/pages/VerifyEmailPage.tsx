import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { verifyEmailToken, resendEmailVerification } from '../services/auth';
import { User } from '../types';

interface VerifyEmailPageProps {
  onUserVerified?: (user: User) => void;
}

export const VerifyEmailPage: React.FC<VerifyEmailPageProps> = ({ onUserVerified }) => {
  const { token: paramToken } = useParams<{ token?: string }>();
  const [searchParams] = useSearchParams();
  const token = paramToken || searchParams.get('token') || '';
  const navigate = useNavigate();

  const [loading, setLoading] = useState(Boolean(token));
  const [success, setSuccess] = useState(false);
  const [verifiedUser, setVerifiedUser] = useState<User | null>(null);
  const [message, setMessage] = useState('');
  const [resendEmail, setResendEmail] = useState('');
  const [resending, setResending] = useState(false);
  const [resendStatus, setResendStatus] = useState<string | null>(null);
  const [resendError, setResendError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    let isMounted = true;
    const performVerification = async () => {
      setLoading(true);
      try {
        const res = await verifyEmailToken(token);
        if (!isMounted) return;

        if (res.success) {
          setSuccess(true);
          setMessage(res.message || 'Your email address has been successfully verified.');
          if (res.user) {
            setVerifiedUser(res.user);
            localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
            if (onUserVerified) {
              onUserVerified(res.user);
            }
          }
        } else {
          setSuccess(false);
          setMessage(res.message || 'This verification link is invalid or has expired.');
        }
      } catch (err: any) {
        if (!isMounted) return;
        setSuccess(false);
        setMessage(err.message || 'This verification link is invalid or has expired.');
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    performVerification();
    return () => {
      isMounted = false;
    };
  }, [token]);

  const handleResend = async (e: React.FormEvent) => {
    e.preventDefault();
    setResendStatus(null);
    setResendError(null);

    const emailToUse = resendEmail.trim();
    if (!emailToUse) {
      setResendError('Please enter your registered email address.');
      return;
    }

    setResending(true);
    try {
      const res = await resendEmailVerification(emailToUse);
      setResendStatus(res.message || 'Verification link sent! Check your inbox.');
    } catch (err: any) {
      setResendError(err.message || 'Failed to send verification email. Please try again.');
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-16 bg-slate-950">
      <div className="w-full max-w-md">
        <div className="bg-slate-900/90 border border-slate-800/80 rounded-3xl p-8 shadow-2xl backdrop-blur-xl text-center">
          {loading ? (
            <div className="py-8 space-y-4">
              <div className="w-12 h-12 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <h2 className="text-xl font-bold text-white">Verifying Email...</h2>
              <p className="text-xs text-slate-400">
                Confirming cryptographic security token with SpaceLoop authentication service.
              </p>
            </div>
          ) : success ? (
            <div className="space-y-6">
              <div className="w-16 h-16 rounded-3xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto text-3xl shadow-lg shadow-emerald-500/20">
                <i className="fa-solid fa-check-double" />
              </div>

              <div>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold mb-3">
                  Account Verified & Active
                </span>
                <h1 className="text-2xl font-black text-white">Email Verified!</h1>
                <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                  {message || 'Your email address has been successfully verified. You now have full access to the SpaceLoop portal.'}
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 text-left text-xs text-slate-400 space-y-1.5">
                <div className="flex items-center justify-between text-white font-medium">
                  <span>Status:</span>
                  <span className="text-emerald-400 font-bold flex items-center gap-1">
                    <i className="fa-solid fa-circle-check text-xs" /> Verified
                  </span>
                </div>
                {verifiedUser?.email && (
                  <div className="flex items-center justify-between">
                    <span>Email:</span>
                    <span className="text-slate-200">{verifiedUser.email}</span>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span>Portal Access:</span>
                  <span className="text-indigo-400">Unlocked</span>
                </div>
              </div>

              <div className="flex flex-col gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    if (verifiedUser?.role === 'host') {
                      navigate('/host/dashboard');
                    } else {
                      navigate('/dashboard');
                    }
                  }}
                  className="w-full py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-700 hover:from-indigo-500 hover:to-violet-500 text-white font-bold text-sm shadow-xl shadow-indigo-600/30 flex items-center justify-center gap-2 transition"
                >
                  <span>Enter SpaceLoop Portal</span>
                  <i className="fa-solid fa-arrow-right text-xs" />
                </button>

                <button
                  type="button"
                  onClick={() => navigate('/explore')}
                  className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition"
                >
                  Explore Verified Spaces
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="w-16 h-16 rounded-3xl bg-rose-500/15 border border-rose-500/30 text-rose-400 flex items-center justify-center mx-auto text-3xl shadow-lg shadow-rose-500/20">
                <i className="fa-solid fa-link-slash" />
              </div>

              <div>
                <h1 className="text-2xl font-black text-white">
                  {token ? 'Verification Failed' : 'Verify Your Email'}
                </h1>
                <p className="text-xs text-rose-300 mt-2 leading-relaxed">
                  {message || 'Please verify your email address to unlock portal bookings and space management.'}
                </p>
              </div>

              {/* Resend Verification Form */}
              <form onSubmit={handleResend} className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 text-left space-y-3">
                <label className="block text-xs font-semibold text-slate-300">
                  Request New Verification Link
                </label>
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="email"
                    value={resendEmail}
                    onChange={(e) => setResendEmail(e.target.value)}
                    placeholder="Enter registered email"
                    className="flex-1 px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs focus:outline-none focus:border-indigo-500"
                    required
                  />
                  <button
                    type="submit"
                    disabled={resending}
                    className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition disabled:opacity-50 shrink-0"
                  >
                    {resending ? 'Sending...' : 'Send Link'}
                  </button>
                </div>

                {resendStatus && (
                  <div className="text-[11px] text-emerald-400 font-medium">
                    ✓ {resendStatus}
                  </div>
                )}
                {resendError && (
                  <div className="text-[11px] text-rose-400 font-medium">
                    ⚠️ {resendError}
                  </div>
                )}
              </form>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => navigate('/')}
                  className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs border border-slate-700 transition flex items-center justify-center gap-2"
                >
                  <i className="fa-solid fa-house text-xs" />
                  <span>Return to Home</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
