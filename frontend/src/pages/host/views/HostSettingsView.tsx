import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { User } from '../../../types';
import { getHostSettings, updateHostSettings } from '../../../services/host';

type SettingsTab =
  | 'profile'
  | 'security'
  | 'identity'
  | 'notifications'
  | 'payout'
  | 'defaults'
  | 'privacy'
  | 'help';

export const HostSettingsView: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const isHelpRoute = location.pathname.includes('/help');

  const [activeTab, setActiveTab] = useState<SettingsTab>(isHelpRoute ? 'help' : 'profile');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [name, setName] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phone, setPhone] = useState('');
  const [bio, setBio] = useState('');
  const [payoutVpa, setPayoutVpa] = useState('');
  const [bankBeneficiaryName, setBankBeneficiaryName] = useState('');
  const [defaultBufferMinutes, setDefaultBufferMinutes] = useState(15);
  const [instantBookingEnabled, setInstantBookingEnabled] = useState(true);
  const [defaultGeofenceRadius, setDefaultGeofenceRadius] = useState(30);

  // Preferences
  const [smsAlerts, setSmsAlerts] = useState(true);
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [pushAlerts, setPushAlerts] = useState(true);
  const [arrivalChime, setArrivalChime] = useState(true);
  const [maskAddressUntilBooking, setMaskAddressUntilBooking] = useState(true);
  const [maskPhoneUntilBooking, setMaskPhoneUntilBooking] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const data = await getHostSettings();
      if (data && data.success) {
        if (data.user) {
          setCurrentUser(data.user);
          setName(data.user.name || '');
          setFirstName(data.user.first_name || '');
          setLastName(data.user.last_name || '');
          setPhone(data.user.phone || '');
          setBio(data.user.bio || '');
          setPayoutVpa(data.user.upi_vpa_masked || data.user.upi_vpa || 'host@oksbi');
          setBankBeneficiaryName(data.user.bank_beneficiary_name || data.user.name || '');
        }
        if (data.settings) {
          const s = data.settings;
          if (s.defaults) {
            setDefaultBufferMinutes(s.defaults.default_buffer_minutes ?? 15);
            setInstantBookingEnabled(s.defaults.instant_booking_enabled ?? true);
            setDefaultGeofenceRadius(s.defaults.geofence_radius_meters ?? 30);
          }
          if (s.notifications) {
            setSmsAlerts(s.notifications.sms_alerts ?? true);
            setEmailAlerts(s.notifications.email_alerts ?? true);
            setPushAlerts(s.notifications.push_alerts ?? true);
            setArrivalChime(s.notifications.arrival_chime ?? true);
          }
        }
      }
    } catch (err: any) {
      console.warn('Failed to load host settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      setSuccessMsg(null);

      const res = await updateHostSettings({
        name,
        first_name: firstName,
        last_name: lastName,
        phone,
        bio,
        upi_vpa: payoutVpa,
        bank_beneficiary_name: bankBeneficiaryName,
        default_buffer_minutes: defaultBufferMinutes,
        instant_booking_enabled: instantBookingEnabled,
        geofence_radius_meters: defaultGeofenceRadius,
        sms_alerts: smsAlerts,
        email_alerts: emailAlerts,
        push_alerts: pushAlerts,
        arrival_chime: arrivalChime,
        mask_address: maskAddressUntilBooking,
        mask_phone: maskPhoneUntilBooking,
      });

      if (res && res.success) {
        setSuccessMsg(res.message || 'Host settings saved successfully!');
        if (res.user) {
          setCurrentUser(res.user);
        }
        setTimeout(() => setSuccessMsg(null), 3500);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save host settings.');
    } finally {
      setSaving(false);
    }
  };

  const tabs: Array<{ id: SettingsTab; label: string; icon: string }> = [
    { id: 'profile', label: 'Profile', icon: 'fa-solid fa-user' },
    { id: 'security', label: 'Account & Security', icon: 'fa-solid fa-lock' },
    { id: 'identity', label: 'Identity Verification', icon: 'fa-solid fa-id-card' },
    { id: 'notifications', label: 'Notification Preferences', icon: 'fa-solid fa-bell' },
    { id: 'payout', label: 'Payment & Settlement', icon: 'fa-solid fa-indian-rupee-sign' },
    { id: 'defaults', label: 'Default Space Settings', icon: 'fa-solid fa-sliders' },
    { id: 'privacy', label: 'Privacy', icon: 'fa-solid fa-shield-halved' },
    { id: 'help', label: 'Help & Support', icon: 'fa-solid fa-circle-question' },
  ];

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
    {
      q: 'What legal framework governs peer-to-peer micro-leasing?',
      a: 'SpaceLoop leases physical space on an hourly micro-easement basis governed by Section 52 of the Indian Easements Act, 1882. Each reservation produces an automated tamper-proof revocable micro-license agreement.',
    },
  ];

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 uppercase tracking-wider">
            Host Configuration
          </span>
          <span className="text-slate-500 text-xs font-mono">SpaceLoop Operating System</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
          Host Account & Operating Settings
        </h1>
        <p className="text-slate-400 text-xs md:text-sm mt-0.5">
          Manage your verified identity, UPI settlement account, default space operating protocols, and privacy boundaries.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar border-b border-slate-800 pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition flex items-center gap-2 ${
              activeTab === tab.id
                ? 'bg-amber-500 text-slate-950 font-bold shadow-md shadow-amber-500/10'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <i className={`${tab.icon} text-xs`} />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2.5 animate-fadeIn">
          <i className="fa-solid fa-circle-check text-emerald-400 text-sm" />
          <span className="font-semibold">{successMsg}</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2.5">
          <i className="fa-solid fa-triangle-exclamation text-rose-400 text-sm" />
          <span className="font-semibold">{error}</span>
        </div>
      )}

      {/* TAB 1: PROFILE */}
      {activeTab === 'profile' && (
        <form onSubmit={handleSave} className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-white">Public Host Profile</h3>
              <p className="text-xs text-slate-400">Information displayed on your space listings to verified seekers.</p>
            </div>
            <div className="p-2.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-right shrink-0">
              <span className="text-[10px] uppercase font-bold text-amber-400 tracking-wider block">Objective Trust Score</span>
              <span className="text-sm font-black text-white font-mono">
                {(currentUser as any)?.objective_trust_score ?? 99.2} / 100
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="text-slate-300 font-semibold block mb-1">Display Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/50 rounded-xl px-3.5 py-2.5 text-white"
              />
            </div>

            <div>
              <label className="text-slate-300 font-semibold block mb-1">Contact Phone</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 98000 00000"
                className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/50 rounded-xl px-3.5 py-2.5 text-white"
              />
            </div>

            <div>
              <label className="text-slate-300 font-semibold block mb-1">First Name</label>
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/50 rounded-xl px-3.5 py-2.5 text-white"
              />
            </div>

            <div>
              <label className="text-slate-300 font-semibold block mb-1">Last Name</label>
              <input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/50 rounded-xl px-3.5 py-2.5 text-white"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="text-slate-300 font-semibold block mb-1">Host Bio & Premise Caretaker Note</label>
              <textarea
                rows={4}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Share your hosting specialty, building accessibility, or house preferences..."
                className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/50 rounded-xl p-3 text-white leading-relaxed"
              />
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-800">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 transition disabled:opacity-50"
            >
              {saving ? 'Saving Profile...' : 'Save Profile Changes'}
            </button>
          </div>
        </form>
      )}

      {/* TAB 2: ACCOUNT & SECURITY */}
      {activeTab === 'security' && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
          <div>
            <h3 className="text-base font-bold text-white">Account Security & Access Control</h3>
            <p className="text-xs text-slate-400">Authentication safeguards and active host login sessions.</p>
          </div>

          <div className="space-y-4 text-xs">
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <div className="font-bold text-white">Two-Factor Authentication (TOTP / MFA)</div>
                <div className="text-slate-400 text-[11px] mt-0.5">
                  Protect payouts and space configuration with authenticator apps.
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                {(currentUser as any)?.mfa_enabled ? 'Active' : 'Optional / Active'}
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <div className="font-bold text-white">Account Login Email</div>
                <div className="text-slate-400 text-[11px] font-mono mt-0.5">{currentUser?.email || 'host@spaceloop.in'}</div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Verified
              </span>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <div className="font-bold text-white">Session Security & IP Anomaly Defense</div>
                <div className="text-slate-400 text-[11px] mt-0.5">
                  Monitored by SpaceLoop Trust & Safety with sliding window rate limiting.
                </div>
              </div>
              <span className="text-[11px] font-mono text-slate-400">Active Shield</span>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: IDENTITY VERIFICATION */}
      {activeTab === 'identity' && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-white">India Stack Identity Verification</h3>
              <p className="text-xs text-slate-400">Digital verification of personal identity and physical property ownership.</p>
            </div>
            <button
              type="button"
              onClick={() => navigate('/host/verification')}
              className="px-4 py-2 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-400 text-xs font-bold transition flex items-center gap-1.5"
            >
              <span>Manage Documents</span>
              <i className="fa-solid fa-arrow-right text-[10px]" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white flex items-center gap-2">
                  <i className="fa-solid fa-bolt text-amber-400" />
                  <span>State Electricity Board (Discom)</span>
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Verified
                </span>
              </div>
              <p className="text-slate-400 text-[11px]">
                Linked Consumer Account: <span className="font-mono text-slate-300">{currentUser?.discom_ca_masked || 'CA-***9842'}</span>
              </p>
              <div className="text-[10px] text-slate-500">Provider: {currentUser?.discom_provider || 'TPDDL (Tata Power)'}</div>
            </div>

            <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white flex items-center gap-2">
                  <i className="fa-solid fa-address-card text-sky-400" />
                  <span>DigiLocker Aadhaar KYC</span>
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {(currentUser as any)?.is_aadhaar_verified ? 'Verified' : 'Active'}
                </span>
              </div>
              <p className="text-slate-400 text-[11px]">
                Masked UID: <span className="font-mono text-slate-300">{(currentUser as any)?.aadhaar_masked || 'XXXX-XXXX-8921'}</span>
              </p>
              <div className="text-[10px] text-slate-500">DPDP Act 2023 Compliant SHA-256 Hash persistence</div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: NOTIFICATION PREFERENCES */}
      {activeTab === 'notifications' && (
        <form onSubmit={handleSave} className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
          <div>
            <h3 className="text-base font-bold text-white">Operational Notification Preferences</h3>
            <p className="text-xs text-slate-400">Configure how and when you receive real-time alerts.</p>
          </div>

          <div className="space-y-4 text-xs">
            <label className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-between cursor-pointer">
              <div>
                <div className="font-bold text-white">Instant Booking & Arrival Push Notifications</div>
                <div className="text-slate-400 text-[11px]">Receive web notifications when a guest arrives within the 50m perimeter.</div>
              </div>
              <input
                type="checkbox"
                checked={pushAlerts}
                onChange={(e) => setPushAlerts(e.target.checked)}
                className="w-4 h-4 accent-amber-500 rounded"
              />
            </label>

            <label className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-between cursor-pointer">
              <div>
                <div className="font-bold text-white">SMS Booking & Emergency Alerts</div>
                <div className="text-slate-400 text-[11px]">Send critical door access PIN verification events via transactional SMS.</div>
              </div>
              <input
                type="checkbox"
                checked={smsAlerts}
                onChange={(e) => setSmsAlerts(e.target.checked)}
                className="w-4 h-4 accent-amber-500 rounded"
              />
            </label>

            <label className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-between cursor-pointer">
              <div>
                <div className="font-bold text-white">Daily Settlement & Payout Summaries</div>
                <div className="text-slate-400 text-[11px]">Daily digest email detailing net 95% UPI transfers and completed bookings.</div>
              </div>
              <input
                type="checkbox"
                checked={emailAlerts}
                onChange={(e) => setEmailAlerts(e.target.checked)}
                className="w-4 h-4 accent-amber-500 rounded"
              />
            </label>

            <label className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-between cursor-pointer">
              <div>
                <div className="font-bold text-white">Cockpit Live Arrival Chime</div>
                <div className="text-slate-400 text-[11px]">Play audio ping in Host Live Sessions cockpit when guest checks in.</div>
              </div>
              <input
                type="checkbox"
                checked={arrivalChime}
                onChange={(e) => setArrivalChime(e.target.checked)}
                className="w-4 h-4 accent-amber-500 rounded"
              />
            </label>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-800">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-md transition disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Notification Preferences'}
            </button>
          </div>
        </form>
      )}

      {/* TAB 5: PAYMENT & SETTLEMENT */}
      {activeTab === 'payout' && (
        <form onSubmit={handleSave} className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
          <div>
            <h3 className="text-base font-bold text-white">UPI Payout VPA & Settlement Ledger</h3>
            <p className="text-xs text-slate-400">
              Net earnings (95%) are deposited automatically to this UPI ID upon exit inspection verification.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="text-slate-300 font-semibold block mb-1">Virtual Payment Address (UPI VPA)</label>
              <input
                type="text"
                value={payoutVpa}
                onChange={(e) => setPayoutVpa(e.target.value)}
                placeholder="e.g. yourname@okhdfcbank"
                className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/50 rounded-xl px-3.5 py-2.5 text-white font-mono"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                Verified with NPCI penny-drop protocol.
              </span>
            </div>

            <div>
              <label className="text-slate-300 font-semibold block mb-1">Bank Account Beneficiary Name</label>
              <input
                type="text"
                value={bankBeneficiaryName}
                onChange={(e) => setBankBeneficiaryName(e.target.value)}
                placeholder="Name as registered on bank account"
                className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/50 rounded-xl px-3.5 py-2.5 text-white"
              />
            </div>
          </div>

          {/* Fee Breakdown Card */}
          <div className="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
            <span className="text-xs font-bold text-white block">Fee Structure & Settlement Schedule</span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] block">Host Net Share</span>
                <span className="text-lg font-black text-emerald-400 font-mono">95.0%</span>
                <span className="text-[10px] text-slate-500 block">Instant auto-deposit</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] block">Platform Infrastructure</span>
                <span className="text-lg font-black text-slate-300 font-mono">5.0%</span>
                <span className="text-[10px] text-slate-500 block">Includes GST & payment gateway</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-slate-400 text-[10px] block">Micro-Escrow Deposit</span>
                <span className="text-lg font-black text-amber-400 font-mono">₹100 Flat</span>
                <span className="text-[10px] text-slate-500 block">Released or held on exit inspection</span>
              </div>
            </div>
          </div>

          <div className="flex justify-between items-center pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => navigate('/host/escrow')}
              className="text-xs text-amber-400 hover:text-amber-300 font-semibold flex items-center gap-1.5"
            >
              <span>View Escrow Ledger</span>
              <i className="fa-solid fa-arrow-right text-[10px]" />
            </button>

            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md transition disabled:opacity-50"
            >
              {saving ? 'Updating...' : 'Save Payout Configuration'}
            </button>
          </div>
        </form>
      )}

      {/* TAB 6: DEFAULT SPACE SETTINGS */}
      {activeTab === 'defaults' && (
        <form onSubmit={handleSave} className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
          <div>
            <h3 className="text-base font-bold text-white">Default Space Operating Protocols</h3>
            <p className="text-xs text-slate-400">Settings automatically applied to all newly created listings.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
              <label className="font-bold text-white block">Default Buffer Minutes Between Bookings</label>
              <p className="text-slate-400 text-[11px]">
                Cooling period reserved for premise ventilation, caretaker turnaround, and electrical appliance cool-off.
              </p>
              <select
                value={defaultBufferMinutes}
                onChange={(e) => setDefaultBufferMinutes(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-white"
              >
                <option value={0}>0 Minutes (Back-to-back)</option>
                <option value={15}>15 Minutes (Recommended)</option>
                <option value={30}>30 Minutes</option>
                <option value={60}>60 Minutes</option>
              </select>
            </div>

            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
              <label className="font-bold text-white block">Standard Geofence Perimeter Radius</label>
              <p className="text-slate-400 text-[11px]">
                GPS distance within which physical access credentials and door PINs are unlocked.
              </p>
              <select
                value={defaultGeofenceRadius}
                onChange={(e) => setDefaultGeofenceRadius(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-white"
              >
                <option value={30}>30 Meters (High Precision)</option>
                <option value={50}>50 Meters (Standard)</option>
                <option value={100}>100 Meters (Large Campus)</option>
              </select>
            </div>

            <div className="sm:col-span-2 p-4 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <div className="font-bold text-white">Instant Booking Approval Mode</div>
                <div className="text-slate-400 text-[11px] mt-0.5">
                  Automatically confirm bookings from verified seekers with OTI trust scores above 85.
                </div>
              </div>
              <input
                type="checkbox"
                checked={instantBookingEnabled}
                onChange={(e) => setInstantBookingEnabled(e.target.checked)}
                className="w-4 h-4 accent-amber-500 rounded"
              />
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-800">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-md transition disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Default Space Settings'}
            </button>
          </div>
        </form>
      )}

      {/* TAB 7: PRIVACY */}
      {activeTab === 'privacy' && (
        <form onSubmit={handleSave} className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6">
          <div>
            <h3 className="text-base font-bold text-white">Privacy & Address Disclosure Controls</h3>
            <p className="text-xs text-slate-400">Control what physical details seekers can see before and after booking.</p>
          </div>

          <div className="space-y-4 text-xs">
            <label className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-between cursor-pointer">
              <div>
                <div className="font-bold text-white">Mask Precise Street Address Until Confirmed Booking</div>
                <div className="text-slate-400 text-[11px]">
                  Seekers see only neighborhood / landmark on public search until micro-lease is signed.
                </div>
              </div>
              <input
                type="checkbox"
                checked={maskAddressUntilBooking}
                onChange={(e) => setMaskAddressUntilBooking(e.target.checked)}
                className="w-4 h-4 accent-amber-500 rounded"
              />
            </label>

            <label className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex items-center justify-between cursor-pointer">
              <div>
                <div className="font-bold text-white">Mask Host Phone Number (In-App Relay Only)</div>
                <div className="text-slate-400 text-[11px]">
                  Routes seeker inquiries through SpaceLoop verified in-app chat rather than exposing personal mobile number.
                </div>
              </div>
              <input
                type="checkbox"
                checked={maskPhoneUntilBooking}
                onChange={(e) => setMaskPhoneUntilBooking(e.target.checked)}
                className="w-4 h-4 accent-amber-500 rounded"
              />
            </label>

            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800">
              <span className="font-bold text-white block mb-1">Digital Personal Data Protection (DPDP) Act 2023 Compliance</span>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                All host and seeker documents are cryptographically tokenized. Raw Aadhaar numbers are never stored in plaintext,
                and electricity meter numbers are verified ephemerally against State Power Board endpoints.
              </p>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-800">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-md transition disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Privacy Controls'}
            </button>
          </div>
        </form>
      )}

      {/* TAB 8: HELP & SUPPORT */}
      {activeTab === 'help' && (
        <div className="space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-4">
            <h3 className="text-base font-bold text-white">Host Knowledge Base & Legal Protocol</h3>
            <div className="space-y-4">
              {faqs.map((faq, i) => (
                <div key={i} className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80 space-y-1.5">
                  <div className="text-xs font-bold text-amber-300">{faq.q}</div>
                  <p className="text-xs text-slate-400 leading-relaxed">{faq.a}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="p-6 rounded-3xl bg-gradient-to-r from-amber-500/10 via-slate-900 to-indigo-500/10 border border-amber-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h4 className="text-sm font-bold text-white">SpaceLoop Operations & Dispute Desk</h4>
              <p className="text-xs text-slate-400 mt-0.5">
                Have an urgent condition dispute or electrical meter verification query? Our team is on standby 24/7.
              </p>
            </div>
            <a
              href="mailto:operations@spaceloop.in"
              className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-300 font-bold text-xs border border-slate-700 transition flex items-center gap-2 self-start sm:self-auto shrink-0"
            >
              <i className="fa-solid fa-headset text-xs" />
              <span>Contact Host Desk</span>
            </a>
          </div>
        </div>
      )}
    </div>
  );
};
