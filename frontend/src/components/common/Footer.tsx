import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from '../../i18n';

export const Footer: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const [legalModalType, setLegalModalType] = useState<'privacy' | 'terms' | 'easements' | null>(null);

  const handleNav = (targetPath: string) => {
    if (location.pathname === targetPath) {
      window.scrollTo({ top: 0, left: 0, behavior: 'smooth' });
    } else {
      navigate(targetPath);
    }
  };

  const legalContent = {
    privacy: {
      title: t('trustSafety.title'),
      body: t('trustSafety.subtitle'),
    },
    terms: {
      title: t('footer.terms'),
      body: t('trustSafety.sec52Desc'),
    },
    easements: {
      title: t('trustSafety.sec52Title'),
      body: t('trustSafety.sec52Desc'),
    },
  };

  return (
    <>
      <footer className="bg-surface border-t border-border mt-20 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 mb-10">
            {/* Brand (5 cols) */}
            <div className="md:col-span-5 space-y-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center text-white text-sm shadow-md shadow-primary/25">
                  <i className="fa-solid fa-infinity" />
                </div>
                <span className="text-xl font-extrabold text-text-primary tracking-tight">{t('common.brand')}</span>
              </div>
              <p className="text-sm text-text-secondary font-semibold italic">
                &ldquo;Work &bull; Create &bull; Meet &bull; Build &bull; Learn &bull; Host &bull; Grow&rdquo;
              </p>
              <p className="text-xs text-text-muted max-w-sm leading-relaxed">
                {t('footer.description')}
              </p>
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
                <i className="fa-solid fa-shield-halved text-[11px]" />
                <span>{t('common.verified')} &bull; {t('common.sec52Protected')}</span>
              </div>
            </div>

            {/* Navigation (4 cols) */}
            <div className="md:col-span-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3.5">{t('footer.quickLinks')}</h4>
              <ul className="grid grid-cols-2 gap-2 text-xs font-medium text-slate-400">
                <li>
                  <button
                    type="button"
                    onClick={() => handleNav('/explore')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-compass text-slate-500 text-[10px]" /> {t('nav.explore')}
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => handleNav('/list-space')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-plus text-slate-500 text-[10px]" /> {t('nav.listSpace')}
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => handleNav('/how-it-works')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-circle-question text-slate-500 text-[10px]" /> {t('nav.howItWorks')}
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => handleNav('/verify')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-shield-check text-slate-500 text-[10px]" /> {t('nav.trustSafety')}
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => handleNav('/how-it-works')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-comments text-slate-500 text-[10px]" /> {t('nav.help')}
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => handleNav('/calculator')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-calculator text-slate-500 text-[10px]" /> {t('nav.calculator')}
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => handleNav('/architecture')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5 text-indigo-300 font-semibold"
                  >
                    <i className="fa-solid fa-cubes text-indigo-400 text-[10px]" /> {t('nav.architecture')}
                  </button>
                </li>
              </ul>
            </div>

            {/* Legal (3 cols) */}
            <div className="md:col-span-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3.5">{t('footer.legal')}</h4>
              <ul className="space-y-2 text-xs font-medium text-slate-400">
                <li>
                  <button
                    type="button"
                    onClick={() => setLegalModalType('privacy')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-user-shield text-slate-500 text-[10px]" /> {t('footer.privacy')}
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => setLegalModalType('terms')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-file-contract text-slate-500 text-[10px]" /> {t('footer.terms')}
                  </button>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={() => setLegalModalType('easements')}
                    className="hover:text-white hover:underline transition flex items-center gap-1.5"
                  >
                    <i className="fa-solid fa-scale-balanced text-slate-500 text-[10px]" /> {t('trustSafety.sec52Title')}
                  </button>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="pt-8 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
            <div className="flex items-center gap-3">
              <p>&copy; 2026 {t('common.brand')}. {t('footer.rightsReserved')}</p>
            </div>
            <div className="flex items-center gap-3 text-slate-400 flex-wrap justify-center">
              <span className="flex items-center gap-1">
                <i className="fa-solid fa-shield-halved text-emerald-400" /> {t('hero.instantEscrowBadge')}
              </span>
              <span>&bull;</span>
              <span className="flex items-center gap-1">
                <i className="fa-solid fa-robot text-indigo-400" /> {t('landing.feature4Title')}
              </span>
              <span>&bull;</span>
              <span className="flex items-center gap-1">
                <i className="fa-solid fa-location-crosshairs text-amber-400" /> {t('hero.zeroHardwareBadge')}
              </span>
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
                {t('common.close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
