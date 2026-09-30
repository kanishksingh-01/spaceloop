import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { User } from '../../../types';
import { getCurrentUser } from '../../../services/auth';
import { updateHostSettings } from '../../../services/host';

export const HostSettingsView: React.FC = () => {
  const location = useLocation();
  const isHelpRoute = location.pathname.includes('/help');

  const [activeTab, setActiveTab] = useState<'profile' | 'payout' | 'defaults' | 'help'>(
    isHelpRoute ? 'help' : 'profile'
  );

  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [bio, setBio] = useState('');
  const [payoutVpa, setPayoutVpa] = useState('');
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const u = await getCurrentUser();
      if (u) {
        setCurrentUser(u);
        setName(u.name || '');
        setPhone(u.phone || '');
        setBio((u as any).bio || '');
        setPayoutVpa((u as any).payout_vpa || (u as any).upi_vpa || 'host@oksbi');
      }
    } catch (err) {
      console.error('Failed to load user profile:', err);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      setSuccessMsg(null);

      const res = await updateHostSettings({
        name,
        phone,
        bio,
        upi_vpa: payoutVpa,
      });

      if (res && res.success) {
        setSuccessMsg(res.message || 'Host settings saved successfully!');
        setTimeout(() => setSuccessMsg(null), 3000);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to update host settings.');
    } finally {
      setSaving(false);
    }
  };

  const faqs = [
    {
      q: 'How does the ₹100 micro-escrow guarantee work?',
      a: 'Renters authorize a ₹100 micro-escrow hold when booking. Upon departure, computer vision analyzes the exit photo against baseline entry condition. If no damage is detected and electrical appliances are turned off, the ₹100 is refunded to the renter, and your 95% net payout is released instantly to your UPI VPA.',
    },
    {
      q: 'Why is Discom electricity utility verification required?',
      a: 'Physical space verification through electric utility consumer accounts (CA) proves legal possession of the space. This prevents unauthorized sub-leasing and guarantees a 98%+ Operational Trust Index (OTI) rating for your listings.',
    },
    {
      q: 'How is the 50-meter Zero-Spoofing Perimeter calculated?',
      a: 'SpaceLoop calculates great-circle distance using the Haversine formula from the space’s verified coordinates to the renter’s device GPS. Entry credentials (dynamic QR or keybox PIN) are strictly concealed until the renter arrives within 50 meters.',
    },
    {
      q: 'What is the platform commission fee?',
      a: 'SpaceLoop charges a transparent 5% platform fee on completed bookings. Hosts receive 95% net payout disbursed automatically to their UPI ID.',
    },
  ];

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 uppercase tracking-wider">
            Host Configuration
          </span>
          <span className="text-slate-500 text-xs font-mono">Profile & Settlement Defaults</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          {activeTab === 'help' ? 'Host Help & Support Center' : 'Host Account & Payout Settings'}
        </h1>
        <p className="text-slate-400 text-xs md:text-sm mt-0.5">
          Configure payout destination UPI VPAs, operational guidelines, and find answers to host protocol questions.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        {[
          { id: 'profile', label: 'Host Profile', icon: 'fa-solid fa-user' },
          { id: 'payout', label: 'UPI Payout VPA', icon: 'fa-solid fa-indian-rupee-sign' },
          { id: 'defaults', label: 'Space Defaults', icon: 'fa-solid fa-sliders' },
          { id: 'help', label: 'Help & FAQs', icon: 'fa-solid fa-circle-question' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 ${
              activeTab === tab.id
                ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <i className={`${tab.icon} text-xs`} />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2.5">
          <i className="fa-solid fa-circle-check text-emerald-400" />
          <span>{successMsg}</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2.5">
          <i className="fa-solid fa-triangle-exclamation text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* TAB: PROFILE */}
      {activeTab === 'profile' && (
        <form onSubmit={handleSave} className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-5">
          <h3 className="text-base font-bold text-white">Host Public Profile</h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="text-slate-300 font-semibold block mb-1">Display Name</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white focus:outline-none"
              />
            </div>

            <div>
              <label className="text-slate-300 font-semibold block mb-1">Contact Phone</label>
              <input
                type="text"
                value={phone}
                onChange={e => setPhone(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-white focus:outline-none"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="text-slate-300 font-semibold block mb-1">Host Bio</label>
              <textarea
                rows={3}
                value={bio}
                onChange={e => setBio(e.target.value)}
                placeholder="Share your hosting background and space specialty..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white focus:outline-none"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-md transition disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        </form>
      )}

      {/* TAB: PAYOUT */}
      {activeTab === 'payout' && (
        <form onSubmit={handleSave} className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-5">
          <div>
            <h3 className="text-base font-bold text-white">UPI Payout Configuration</h3>
            <p className="text-xs text-slate-400">
              Space rental earnings (95%) are deposited directly into this Virtual Payment Address (VPA).
            </p>
          </div>

          <div className="max-w-md space-y-2">
            <label className="text-xs font-semibold text-slate-300 block">UPI ID / VPA</label>
            <div className="relative">
              <input
                type="text"
                value={payoutVpa}
                onChange={e => setPayoutVpa(e.target.value)}
                placeholder="e.g. yourname@okhdfcbank"
                className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/50 rounded-xl px-3.5 py-2 text-xs text-white font-mono"
              />
            </div>
            <span className="text-[10px] text-slate-500 block">
              Verified with automated ₹1 penny-drop protocol before live payouts.
            </span>
          </div>

          <div className="flex justify-start">
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-md transition disabled:opacity-50"
            >
              {saving ? 'Updating...' : 'Update Payout VPA'}
            </button>
          </div>
        </form>
      )}

      {/* TAB: DEFAULTS */}
      {activeTab === 'defaults' && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-5">
          <h3 className="text-base font-bold text-white">Global Space Operational Defaults</h3>
          <div className="space-y-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <div className="font-semibold text-white">Standard Arrival Radius</div>
                <div className="text-slate-400 text-[11px]">Enforced on all new listings unless overridden.</div>
              </div>
              <span className="font-mono text-amber-400 font-bold">50 Meters</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <div className="font-semibold text-white">Automated UPI Micro-Escrow</div>
                <div className="text-slate-400 text-[11px]">Hold amount collected from seekers at booking.</div>
              </div>
              <span className="font-mono text-emerald-400 font-bold">₹100 Flat</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <div className="font-semibold text-white">Check-in Grace Period</div>
                <div className="text-slate-400 text-[11px]">Maximum arrival window before auto-cancel alert.</div>
              </div>
              <span className="font-mono text-slate-200">15 Minutes</span>
            </div>
          </div>
        </div>
      )}

      {/* TAB: HELP & SUPPORT */}
      {activeTab === 'help' && (
        <div className="space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white">Frequently Asked Host Questions</h3>
            <div className="space-y-4">
              {faqs.map((faq, i) => (
                <div key={i} className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-1.5">
                  <div className="text-xs font-bold text-amber-300">{faq.q}</div>
                  <p className="text-xs text-slate-400 leading-relaxed">{faq.a}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-gradient-to-r from-amber-500/10 via-slate-900 to-indigo-500/10 border border-amber-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-bold text-white">Need Dedicated Host Support?</h4>
              <p className="text-xs text-slate-400 mt-0.5">SpaceLoop Trust & Operations team is on standby 24/7.</p>
            </div>
            <a
              href="mailto:host-support@spaceloop.in"
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-300 font-semibold text-xs border border-slate-700 transition flex items-center gap-2 self-start sm:self-auto"
            >
              <i className="fa-solid fa-headset text-xs" />
              <span>Contact Operations Desk</span>
            </a>
          </div>
        </div>
      )}
    </div>
  );
};
