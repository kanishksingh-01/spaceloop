import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { verifyEmailToken, resendEmailVerification } from '../services/auth';
import { User } from '../types';
import { useTranslation } from '../i18n';

interface VerifyEmailPageProps {
  onUserVerified?: (user: User) => void;
}

export const VerifyEmailPage: React.FC<VerifyEmailPageProps> = ({ onUserVerified }) => {
  const { token: paramToken } = useParams<{ token?: string }>();
  const [searchParams] = useSearchParams();
  const token = paramToken || searchParams.get('token') || '';
  const navigate = useNavigate();
  const { t } = useTranslation();

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
          setMessage(res.message || t('verifyEmail.verifiedSuccessDesc'));
          if (res.user) {
            setVerifiedUser(res.user);
            localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
            if (onUserVerified) {
              onUserVerified(res.user);
            }
          }
        } else {
          setSuccess(false);
          setMessage(res.message || t('verifyEmail.invalidLinkDesc'));
        }
      } catch (err: any) {
        if (!isMounted) return;
        setSuccess(false);
        setMessage(err.message || t('verifyEmail.invalidLinkDesc'));
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    performVerification();
    return () => {
      isMounted = false;
    };
  }, [token, t]);

  const handleResend = async (e: React.FormEvent) => {
    e.preventDefault();
    setResendStatus(null);
    setResendError(null);

    const emailToUse = resendEmail.trim();
    if (!emailToUse) {
      setResendError(t('auth.emailPlaceholder'));
      return;
    }

    setResending(true);
    try {
      const res = await resendEmailVerification(emailToUse);
      setResendStatus(res.message || t('auth.verificationSent'));
    } catch (err: any) {
      setResendError(err.message || t('common.error'));
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-16 bg-background">
      <div className="w-full max-w-md">
        <div className="bg-surface border border-border rounded-3xl p-8 shadow-2xl backdrop-blur-xl text-center">
          {loading ? (
            <div className="py-8 space-y-4">
              <div className="w-12 h-12 border-3 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
              <h2 className="text-xl font-heading font-bold text-text-primary">{t('verifyEmail.checkingStatus')}</h2>
              <p className="text-xs text-text-secondary">
                {t('verifyEmail.subtitle')}
              </p>
            </div>
          ) : success ? (
            <div className="space-y-6">
              <div className="w-16 h-16 rounded-3xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-500 flex items-center justify-center mx-auto text-3xl shadow-lg shadow-emerald-500/20">
                <i className="fa-solid fa-check-double" />
              </div>

              <div>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-xs font-bold mb-3">
                  {t('verify.verifiedSuccessBadge')}
                </span>
                <h1 className="text-2xl font-heading font-black text-text-primary">{t('verifyEmail.verifiedSuccessTitle')}</h1>
                <p className="text-xs text-text-secondary mt-2 leading-relaxed">
                  {message || t('verifyEmail.verifiedSuccessDesc')}
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-surface-elevated border border-border text-left text-xs text-text-secondary space-y-1.5">
                <div className="flex items-center justify-between text-text-primary font-medium">
                  <span>{t('dashboard.statusLabel')}:</span>
                  <span className="text-emerald-500 font-bold flex items-center gap-1">
                    <i className="fa-solid fa-circle-check text-xs" /> {t('common.verified')}
                  </span>
                </div>
                {verifiedUser?.email && (
                  <div className="flex items-center justify-between">
                    <span>{t('auth.emailLabel')}:</span>
                    <span className="text-text-primary font-mono">{verifiedUser.email}</span>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span>{t('nav.menu')}:</span>
                  <span className="text-primary font-semibold">{t('common.confirmed')}</span>
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
                  className="w-full py-3.5 rounded-xl bg-primary hover:bg-primary-hover text-white font-bold text-sm shadow-xl shadow-primary/25 flex items-center justify-center gap-2 transition cursor-pointer"
                >
                  <span>{t('verifyEmail.continueToLoginBtn')}</span>
                  <i className="fa-solid fa-arrow-right text-xs" />
                </button>

                <button
                  type="button"
                  onClick={() => navigate('/explore')}
                  className="w-full py-2.5 rounded-xl bg-surface-elevated hover:bg-border/60 text-text-primary border border-border font-semibold text-xs transition cursor-pointer"
                >
                  {t('nav.explore')}
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="w-16 h-16 rounded-3xl bg-rose-500/15 border border-rose-500/30 text-rose-500 flex items-center justify-center mx-auto text-3xl shadow-lg shadow-rose-500/20">
                <i className="fa-solid fa-link-slash" />
              </div>

              <div>
                <h1 className="text-2xl font-heading font-black text-text-primary">
                  {token ? t('verifyEmail.invalidLinkTitle') : t('verifyEmail.title')}
                </h1>
                <p className="text-xs text-rose-500 mt-2 leading-relaxed">
                  {message || t('verifyEmail.invalidLinkDesc')}
                </p>
              </div>

              {/* Resend Verification Form */}
              <form onSubmit={handleResend} className="p-4 rounded-2xl bg-surface-elevated border border-border text-left space-y-3">
                <label className="block text-xs font-semibold text-text-secondary">
                  {t('verifyEmail.resendEmailBtn')}
                </label>
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="email"
                    value={resendEmail}
                    onChange={(e) => setResendEmail(e.target.value)}
                    placeholder={t('auth.emailPlaceholder')}
                    className="flex-1 px-3 py-2.5 rounded-xl bg-surface border border-border text-text-primary text-xs focus:outline-none focus:border-primary"
                    required
                  />
                  <button
                    type="submit"
                    disabled={resending}
                    className="px-4 py-2.5 rounded-xl bg-primary hover:bg-primary-hover text-white font-bold text-xs transition disabled:opacity-50 shrink-0 cursor-pointer"
                  >
                    {resending ? t('common.loading') : t('common.submit')}
                  </button>
                </div>

                {resendStatus && (
                  <div className="text-[11px] text-emerald-500 font-medium">
                    ✓ {resendStatus}
                  </div>
                )}
                {resendError && (
                  <div className="text-[11px] text-rose-500 font-medium">
                    ⚠️ {resendError}
                  </div>
                )}
              </form>

              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => navigate('/')}
                  className="w-full py-2.5 rounded-xl bg-surface-elevated hover:bg-border/60 text-text-primary font-semibold text-xs border border-border transition flex items-center justify-center gap-2 cursor-pointer"
                >
                  <i className="fa-solid fa-house text-xs" />
                  <span>{t('common.back')}</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
