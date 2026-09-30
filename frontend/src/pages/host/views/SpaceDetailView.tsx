import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { Space, Booking } from '../../../types';
import { getHostSpaceDetail, editSpace, toggleSpaceStatus, assistListing } from '../../../services/spaces';
import { estimateRevenue } from '../../../services/calculator';
import { ResourceHeader } from '../components/ResourceHeader';
import { ContextTabs, TabItem } from '../components/ContextTabs';
import { StatusBadge } from '../components/StatusBadge';

export const SpaceDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const spaceId = Number(id);
  const activeTab = searchParams.get('tab') || 'overview';

  const [space, setSpace] = useState<Space | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [activity, setActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states for Listing, Pricing, Access, Verification
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [hourlyRate, setHourlyRate] = useState<number | string>(50);
  const [dailyRate, setDailyRate] = useState<number | string>('');
  const [address, setAddress] = useState('');
  const [location, setLocation] = useState('');
  const [sqft, setSqft] = useState<number | string>('');
  const [capacity, setCapacity] = useState<number | string>('');
  const [amenities, setAmenities] = useState<string[]>([]);
  const [newAmenityInput, setNewAmenityInput] = useState('');

  // Access & Security state
  const [accessType, setAccessType] = useState('room_qr');
  const [keyboxCode, setKeyboxCode] = useState('');
  const [geofenceRadius, setGeofenceRadius] = useState<number>(50);
  const [roomQrToken, setRoomQrToken] = useState('');

  // Verification state
  const [discomCaNumber, setDiscomCaNumber] = useState('');
  const [discomConsumerName, setDiscomConsumerName] = useState('');

  // AI Assist state
  const [optimizingAi, setOptimizingAi] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<string | null>(null);

  // Pricing calculator estimate state
  const [calculatorEstimate, setCalculatorEstimate] = useState<any>(null);
  const [estimatingPrice, setEstimatingPrice] = useState(false);

  useEffect(() => {
    if (spaceId) {
      loadSpace();
    }
  }, [spaceId]);

  const loadSpace = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getHostSpaceDetail(spaceId);
      if (res && res.space) {
        const s = res.space;
        setSpace(s);
        setBookings(res.bookings || []);
        setActivity(res.activity || []);

        // Populate form fields
        setTitle(s.title || '');
        setDescription(s.description || '');
        setCategory(s.category || 'Workspace');
        setHourlyRate(s.hourly_rate || 50);
        setDailyRate(s.daily_rate || '');
        setAddress(s.address || s.location || '');
        setLocation(s.location || s.city || '');
        setSqft(s.square_feet || s.sqft || 150);
        setCapacity(s.capacity || s.max_capacity || 4);
        setAmenities(Array.isArray(s.amenities) ? s.amenities : []);
        setAccessType(s.physical_access_type || 'room_qr');
        setKeyboxCode(s.keybox_code || '');
        setGeofenceRadius(s.geofence_radius_meters || 50);
        setRoomQrToken(s.room_qr_token || `SL-ROOM-${s.id}-${Math.floor(1000 + Math.random() * 9000)}`);
        setDiscomCaNumber(s.discom_ca_number || '');
        setDiscomConsumerName(s.discom_consumer_name || '');
      } else {
        setError('Space not found or unauthorized.');
      }
    } catch (err: any) {
      console.error('Failed to load space detail:', err);
      setError(err.message || 'Failed to load space detail.');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (tabId: string) => {
    setSearchParams({ tab: tabId });
  };

  const handleSave = async () => {
    if (!space) return;
    try {
      setSaving(true);
      setError(null);
      setSaveSuccess(false);

      const payload = {
        title,
        description,
        category,
        hourly_rate: Number(hourlyRate),
        daily_rate: dailyRate ? Number(dailyRate) : undefined,
        address,
        location,
        square_feet: Number(sqft) || undefined,
        capacity: Number(capacity) || undefined,
        amenities,
        physical_access_type: accessType,
        keybox_code: keyboxCode,
        geofence_radius_meters: Number(geofenceRadius),
        room_qr_token: roomQrToken,
        discom_ca_number: discomCaNumber,
        discom_consumer_name: discomConsumerName,
      };

      const updated = await editSpace(space.id, payload);
      setSpace((updated as any).space || updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to save space changes.');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleStatus = async () => {
    if (!space) return;
    try {
      await toggleSpaceStatus(space.id);
      setSpace({ ...space, is_active: !space.is_active });
    } catch (err: any) {
      setError(err.message || 'Failed to toggle status.');
    }
  };

  const handleRegenerateQrToken = () => {
    const newToken = `SL-ROOM-${space?.id || 1}-${Math.floor(100000 + Math.random() * 900000)}`;
    setRoomQrToken(newToken);
  };

  const handleAiOptimize = async () => {
    if (!description && !title) return;
    try {
      setOptimizingAi(true);
      const textToAnalyze = `Space Title: ${title}. Category: ${category}. Current description: ${description}. Amenities: ${amenities.join(', ')}.`;
      const res = await assistListing(textToAnalyze);
      if (res && res.generated_description) {
        setDescription(res.generated_description);
        setAiSuggestions(`AI Enhanced successfully via ${res.ai_provider || 'Gemini'}!`);
      }
    } catch (err: any) {
      console.warn('AI assist fallback:', err);
    } finally {
      setOptimizingAi(false);
    }
  };

  const handleCalculateAiPricing = async () => {
    try {
      setEstimatingPrice(true);
      const est = await estimateRevenue({
        space_type: category || 'Workspace',
        square_feet: Number(sqft) || 200,
        city: location || 'Bangalore',
        amenities,
      });
      setCalculatorEstimate(est);
    } catch (err) {
      console.warn('Pricing calculator failed:', err);
    } finally {
      setEstimatingPrice(false);
    }
  };

  const handleAddAmenity = () => {
    if (newAmenityInput.trim() && !amenities.includes(newAmenityInput.trim())) {
      setAmenities([...amenities, newAmenityInput.trim()]);
      setNewAmenityInput('');
    }
  };

  const handleRemoveAmenity = (name: string) => {
    setAmenities(amenities.filter(a => a !== name));
  };

  const tabs: TabItem[] = [
    { id: 'overview', label: 'Overview', icon: 'fa-solid fa-chart-pie' },
    { id: 'listing', label: 'Listing', icon: 'fa-solid fa-pen-to-square' },
    { id: 'availability', label: 'Availability', icon: 'fa-regular fa-calendar-check' },
    { id: 'pricing', label: 'Pricing', icon: 'fa-solid fa-indian-rupee-sign' },
    { id: 'verification', label: 'Verification', icon: 'fa-solid fa-shield-halved' },
    { id: 'access', label: 'Access & Security', icon: 'fa-solid fa-key' },
    { id: 'bookings', label: 'Bookings', count: bookings.length, icon: 'fa-solid fa-users' },
    { id: 'activity', label: 'Activity', icon: 'fa-solid fa-clock-rotate-left' },
  ];

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center py-24">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-mono text-slate-400">LOADING SPACE PROFILE...</span>
        </div>
      </div>
    );
  }

  if (error && !space) {
    return (
      <div className="p-8 max-w-xl mx-auto text-center py-20">
        <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center text-xl mx-auto mb-4">
          <i className="fa-solid fa-triangle-exclamation" />
        </div>
        <h2 className="text-lg font-bold text-white mb-2">Space Not Found</h2>
        <p className="text-xs text-slate-400 mb-6">{error}</p>
        <button
          onClick={() => navigate('/host/spaces')}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
        >
          Return to Spaces
        </button>
      </div>
    );
  }

  if (!space) return null;

  return (
    <div className="flex-1 flex flex-col">
      {/* Level-2 Resource Header */}
      <ResourceHeader
        breadcrumbs={[
          { label: 'My Spaces', path: '/host/spaces' },
          { label: space.title },
        ]}
        title={space.title}
        subtitle={`${space.category} • ${space.location || space.address || 'Location registered'}`}
        statusBadge={<StatusBadge status={space.is_active ? 'published' : 'draft'} type="space" />}
        metrics={[
          { label: 'Hourly Rate', value: `₹${space.hourly_rate}/hr` },
          { label: 'Bookings', value: bookings.length },
          { label: 'Revenue', value: `₹${space.total_revenue || 0}` },
          { label: 'OTI Score', value: `${space.oti_score || 94}/100` },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate(`/space/${space.id}`)}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs border border-slate-700 transition flex items-center gap-1.5"
            >
              <i className="fa-solid fa-arrow-up-right-from-square text-[10px]" />
              <span>Public Preview</span>
            </button>
            <button
              onClick={handleToggleStatus}
              className={`px-3 py-1.5 rounded-xl font-semibold text-xs transition border ${
                space.is_active
                  ? 'border-slate-700 text-slate-400 hover:text-rose-400 hover:border-rose-500/40'
                  : 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/25'
              }`}
            >
              {space.is_active ? 'Deactivate' : 'Publish Space'}
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-md shadow-amber-500/20 transition flex items-center gap-1.5 disabled:opacity-50"
            >
              <i className={`fa-solid ${saving ? 'fa-spinner animate-spin' : 'fa-check'} text-xs`} />
              <span>{saving ? 'Saving...' : saveSuccess ? 'Saved!' : 'Save Changes'}</span>
            </button>
          </div>
        }
      />

      {/* Save Success Banner */}
      {saveSuccess && (
        <div className="bg-emerald-500/10 border-b border-emerald-500/30 px-6 py-2 text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <i className="fa-solid fa-circle-check text-emerald-400" />
            <span>Space configuration changes saved successfully to physical registry.</span>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-rose-500/10 border-b border-rose-500/30 px-6 py-2 text-xs text-rose-300 flex items-center gap-2">
          <i className="fa-solid fa-triangle-exclamation" />
          <span>{error}</span>
        </div>
      )}

      {/* Level-2 Context Tabs */}
      <ContextTabs tabs={tabs} activeTab={activeTab} onTabChange={handleTabChange} />

      {/* Tab Panels */}
      <div className="p-6 md:p-8 max-w-6xl mx-auto w-full">
        {/* TAB 1: OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Photo & Quick Badges */}
              <div className="md:col-span-1 space-y-4">
                <div className="rounded-2xl overflow-hidden border border-slate-800 bg-slate-900 aspect-video md:aspect-square relative">
                  <img
                    src={space.image_url || 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80'}
                    alt={space.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute bottom-3 left-3 bg-slate-950/80 backdrop-blur-sm px-3 py-1 rounded-xl border border-slate-800 text-xs font-mono font-bold text-white">
                    ₹{space.hourly_rate}/hr
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Physical Access:</span>
                    <span className="font-mono font-semibold text-amber-400">{space.physical_access_type || 'room_qr'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Geofence Perimeter:</span>
                    <span className="font-mono text-slate-200">{space.geofence_radius_meters || 50}m</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Discom CA:</span>
                    <span className="font-mono text-slate-200">{space.discom_ca_number || 'Pending'}</span>
                  </div>
                </div>
              </div>

              {/* Space Health & Quick Details */}
              <div className="md:col-span-2 space-y-6">
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                  <h3 className="text-sm font-bold text-white">Space Health & Performance</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-center">
                      <div className="text-[10px] text-slate-500 uppercase font-mono">Total Bookings</div>
                      <div className="text-lg font-black text-white mt-0.5">{bookings.length}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-center">
                      <div className="text-[10px] text-slate-500 uppercase font-mono">Gross Earnings</div>
                      <div className="text-lg font-black text-emerald-400 mt-0.5">₹{space.total_revenue || 0}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-center">
                      <div className="text-[10px] text-slate-500 uppercase font-mono">OTI Trust Index</div>
                      <div className="text-lg font-black text-amber-400 mt-0.5">{space.oti_score || 94}%</div>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-center">
                      <div className="text-[10px] text-slate-500 uppercase font-mono">Condition Delta</div>
                      <div className="text-lg font-black text-sky-400 mt-0.5">98.4%</div>
                    </div>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
                  <h3 className="text-sm font-bold text-white">About This Space</h3>
                  <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                    {space.description || 'No description added yet. Configure your space in the Listing tab.'}
                  </p>

                  <div className="pt-3 border-t border-slate-800/80">
                    <span className="text-xs text-slate-400 font-semibold block mb-2">Amenities Included:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {amenities.map(a => (
                        <span key={a} className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 text-xs border border-slate-700">
                          {a}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: LISTING FORM */}
        {activeTab === 'listing' && (
          <div className="space-y-6 bg-slate-900/60 border border-slate-800 p-6 rounded-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold text-white">Listing Metadata</h3>
                <p className="text-xs text-slate-400">Specify details seekers see during search and discovery.</p>
              </div>
              <button
                type="button"
                onClick={handleAiOptimize}
                disabled={optimizingAi}
                className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-indigo-600 hover:from-amber-400 hover:to-indigo-500 text-white font-bold text-xs shadow-md transition flex items-center gap-1.5"
              >
                <i className={`fa-solid ${optimizingAi ? 'fa-spinner animate-spin' : 'fa-wand-magic-sparkles'} text-xs`} />
                <span>{optimizingAi ? 'Optimizing...' : 'AI Enhance Copy'}</span>
              </button>
            </div>

            {aiSuggestions && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs text-amber-300">
                ✨ {aiSuggestions}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Space Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none"
                  placeholder="e.g. Quiet High-Speed Tech Pod"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Category</label>
                <select
                  value={category}
                  onChange={e => setCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none"
                >
                  <option value="Workspace">Workspace / Desk</option>
                  <option value="Studio">Studio / Production</option>
                  <option value="Storage">Micro-Storage</option>
                  <option value="Meeting">Meeting Room</option>
                  <option value="Event">Event Space</option>
                  <option value="Creative">Creative / Maker</option>
                  <option value="Parking">EV / Secure Parking</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="text-xs font-semibold text-slate-300 block mb-1">Detailed Description</label>
                <textarea
                  rows={4}
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl p-3.5 text-xs text-white focus:outline-none leading-relaxed"
                  placeholder="Describe your space, atmosphere, best uses, and quiet hours..."
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Area (Square Feet)</label>
                <input
                  type="number"
                  value={sqft}
                  onChange={e => setSqft(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Max Occupancy</label>
                <input
                  type="number"
                  value={capacity}
                  onChange={e => setCapacity(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none"
                />
              </div>

              <div className="md:col-span-2">
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Amenities & Equipment</label>
                <div className="flex flex-wrap gap-2 mb-3">
                  {amenities.map(a => (
                    <span
                      key={a}
                      className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 text-xs border border-slate-700 flex items-center gap-1.5"
                    >
                      <span>{a}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveAmenity(a)}
                        className="text-slate-500 hover:text-rose-400 text-xs"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={newAmenityInput}
                    onChange={e => setNewAmenityInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), handleAddAmenity())}
                    placeholder="Add amenity (e.g. 500Mbps Fiber, Ergonomic Chair, 4K Monitor)..."
                    className="flex-1 bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={handleAddAmenity}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: AVAILABILITY */}
        {activeTab === 'availability' && (
          <div className="space-y-6 bg-slate-900/60 border border-slate-800 p-6 rounded-2xl">
            <div>
              <h3 className="text-base font-bold text-white">Operational Hours & Buffers</h3>
              <p className="text-xs text-slate-400">Control when renters can book and physical turnaround cleaning times.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                <label className="text-xs font-semibold text-slate-300 block mb-1">Standard Opening</label>
                <input
                  type="time"
                  defaultValue="08:00"
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white"
                />
              </div>
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                <label className="text-xs font-semibold text-slate-300 block mb-1">Standard Closing</label>
                <input
                  type="time"
                  defaultValue="22:00"
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white"
                />
              </div>
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                <label className="text-xs font-semibold text-slate-300 block mb-1">Session Buffer</label>
                <select className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-white">
                  <option value="15">15 minutes turnaround</option>
                  <option value="30">30 minutes turnaround</option>
                  <option value="60">1 hour sanitization</option>
                </select>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
              <div>
                <div className="text-xs font-bold text-white">Instant Booking Protocol</div>
                <div className="text-[11px] text-slate-400">
                  Allow verified seekers to automatically confirm without manual host approval.
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                ENABLED (OTI &gt; 80)
              </span>
            </div>
          </div>
        )}

        {/* TAB 4: PRICING */}
        {activeTab === 'pricing' && (
          <div className="space-y-6">
            <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-4">
              <div>
                <h3 className="text-base font-bold text-white">Hourly & Micro-Lease Rates</h3>
                <p className="text-xs text-slate-400">All rentals calculate rental subtotal + 5% platform fee + ₹100 UPI escrow deposit.</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Hourly Base Rate (₹)</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-slate-500">₹</span>
                    <input
                      type="number"
                      value={hourlyRate}
                      onChange={e => setHourlyRate(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl pl-7 pr-3 py-2 text-xs text-white focus:outline-none"
                    />
                  </div>
                  <span className="text-[10px] text-slate-500 mt-1 block">Min ₹20/hr • Recommended ₹50 - ₹200/hr</span>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Daily Cap Rate (₹ optional)</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-slate-500">₹</span>
                    <input
                      type="number"
                      value={dailyRate}
                      onChange={e => setDailyRate(e.target.value)}
                      placeholder="e.g. 450"
                      className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl pl-7 pr-3 py-2 text-xs text-white focus:outline-none"
                    />
                  </div>
                  <span className="text-[10px] text-slate-500 mt-1 block">Full 8+ hour day maximum discount cap</span>
                </div>
              </div>
            </div>

            {/* Smart Pricing Suggestion Tool */}
            <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-950/40 to-slate-900 border border-indigo-500/30 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs">
                    <i className="fa-solid fa-calculator" />
                  </div>
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">AI Neighborhood Pricing Engine</h4>
                </div>
                <button
                  type="button"
                  onClick={handleCalculateAiPricing}
                  disabled={estimatingPrice}
                  className="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition"
                >
                  {estimatingPrice ? 'Calculating...' : 'Run Yield Estimate'}
                </button>
              </div>

              {calculatorEstimate ? (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-indigo-500/20 text-center">
                    <div className="text-[10px] text-slate-400 font-mono">Suggested Rate</div>
                    <div className="text-base font-black text-amber-400">₹{calculatorEstimate.suggested_hourly_rate || 75}/hr</div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-indigo-500/20 text-center">
                    <div className="text-[10px] text-slate-400 font-mono">Estimated Monthly</div>
                    <div className="text-base font-black text-emerald-400">₹{calculatorEstimate.estimated_monthly_earnings?.toLocaleString('en-IN') || '14,500'}</div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-indigo-500/20 text-center">
                    <div className="text-[10px] text-slate-400 font-mono">Est. Occupancy</div>
                    <div className="text-base font-black text-sky-400">{calculatorEstimate.estimated_occupancy_rate || 65}%</div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950/70 border border-indigo-500/20 text-center">
                    <div className="text-[10px] text-slate-400 font-mono">Demand Index</div>
                    <div className="text-base font-black text-indigo-300">High (Urban)</div>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-400">
                  Run the neighborhood yield estimate to analyze real micro-space pricing across {location || 'your area'}.
                </p>
              )}
            </div>
          </div>
        )}

        {/* TAB 5: VERIFICATION */}
        {activeTab === 'verification' && (
          <div className="space-y-6 bg-slate-900/60 border border-slate-800 p-6 rounded-2xl">
            <div>
              <h3 className="text-base font-bold text-white">Discom Utility & Address Verification</h3>
              <p className="text-xs text-slate-400">
                Electricity connection verifies legitimate host ownership of the physical premises.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Discom Consumer Account (CA) Number</label>
                <input
                  type="text"
                  value={discomCaNumber}
                  onChange={e => setDiscomCaNumber(e.target.value)}
                  placeholder="e.g. 100294819"
                  className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none font-mono"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Consumer Name on Utility Bill</label>
                <input
                  type="text"
                  value={discomConsumerName}
                  onChange={e => setDiscomConsumerName(e.target.value)}
                  placeholder="e.g. Rajesh Sharma"
                  className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none"
                />
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-sm ${
                  space.is_verified ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                }`}>
                  <i className={space.is_verified ? 'fa-solid fa-shield-check' : 'fa-solid fa-clock'} />
                </div>
                <div>
                  <div className="text-xs font-bold text-white">
                    {space.is_verified ? 'Premises Verified by Discom' : 'Pending Verification Check'}
                  </div>
                  <div className="text-[11px] text-slate-400">
                    {space.is_verified
                      ? 'CA bill name matches host Aadhaar identity.'
                      : 'Save the CA number above and click Verify in Space Verification.'}
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => navigate('/host/verification')}
                className="px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 text-xs font-semibold border border-amber-500/30"
              >
                Verification Hub →
              </button>
            </div>
          </div>
        )}

        {/* TAB 6: ACCESS & SECURITY */}
        {activeTab === 'access' && (
          <div className="space-y-6 bg-slate-900/60 border border-slate-800 p-6 rounded-2xl">
            <div>
              <h3 className="text-base font-bold text-white">Physical Access Controls & 50m Perimeter</h3>
              <p className="text-xs text-slate-400">
                Configure how renters enter physical doors and enforce automated 50-meter GPS proximity.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Physical Access Mechanism</label>
                <select
                  value={accessType}
                  onChange={e => setAccessType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none"
                >
                  <option value="room_qr">Room Dynamic QR Code (Scanned on Wall)</option>
                  <option value="keybox">Physical Keybox / Lockbox PIN</option>
                  <option value="smart_lock">Smart Door Lock (BLE / WiFi)</option>
                  <option value="host_greeter">Host In-Person Greeting</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Geofence Radius (Meters)</label>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min={20}
                    max={150}
                    step={5}
                    value={geofenceRadius}
                    onChange={e => setGeofenceRadius(Number(e.target.value))}
                    className="flex-1 accent-amber-500 cursor-pointer"
                  />
                  <span className="font-mono text-xs font-bold text-amber-400 bg-slate-950 px-2 py-1 rounded border border-slate-800">
                    {geofenceRadius}m
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 mt-1 block">50m is the default zero-spoofing threshold.</span>
              </div>

              {accessType === 'keybox' && (
                <div className="md:col-span-2">
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Keybox Lock Code</label>
                  <input
                    type="text"
                    value={keyboxCode}
                    onChange={e => setKeyboxCode(e.target.value)}
                    placeholder="e.g. 4819"
                    className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none font-mono"
                  />
                  <span className="text-[10px] text-slate-500 mt-1 block">Revealed to seeker ONLY after GPS arrival verification within 50m.</span>
                </div>
              )}

              {accessType === 'room_qr' && (
                <div className="md:col-span-2 p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-xs font-bold text-white">Dynamic Room QR Token</div>
                      <div className="text-[10px] text-slate-400">Print this QR code to place on the space entrance door.</div>
                    </div>
                    <button
                      type="button"
                      onClick={handleRegenerateQrToken}
                      className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
                    >
                      Regenerate
                    </button>
                  </div>
                  <div className="font-mono text-xs text-amber-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800 select-all">
                    {roomQrToken}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 7: BOOKINGS */}
        {activeTab === 'bookings' && (
          <div className="space-y-4 bg-slate-900/60 border border-slate-800 p-6 rounded-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">Space Booking Ledger</h3>
              <span className="text-xs text-slate-400 font-mono">{bookings.length} Total Bookings</span>
            </div>

            {bookings.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-xs">
                No bookings yet recorded for this space.
              </div>
            ) : (
              <div className="divide-y divide-slate-800">
                {bookings.map(b => (
                  <div
                    key={b.id}
                    onClick={() => navigate(`/host/bookings/${b.id}`)}
                    className="py-3.5 flex items-center justify-between gap-3 cursor-pointer group hover:bg-slate-800/30 px-3 rounded-xl transition"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-white text-xs group-hover:text-amber-400 transition">
                          Booking #{b.id}
                        </span>
                        <StatusBadge status={b.status} type="booking" />
                      </div>
                      <div className="text-[11px] text-slate-400">
                        Seeker: <strong className="text-slate-300">{b.renter?.name || b.user_name || 'Guest'}</strong> •{' '}
                        {new Date(b.start_time).toLocaleDateString()} ({b.total_hours} hrs)
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-mono font-bold text-emerald-400">₹{b.total_price}</div>
                      <div className="text-[10px] text-slate-500">₹100 Escrow Held</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 8: ACTIVITY */}
        {activeTab === 'activity' && (
          <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-4">
            <h3 className="text-base font-bold text-white">Space Audit & Access Trail</h3>
            {activity.length === 0 ? (
              <div className="py-10 text-center text-slate-500 text-xs">
                No telemetry activity logged for this space yet.
              </div>
            ) : (
              <div className="space-y-3">
                {activity.map((ev, i) => (
                  <div key={i} className="flex items-start gap-3 text-xs border-b border-slate-800/80 pb-3 last:border-0">
                    <div className="w-6 h-6 rounded-lg bg-slate-800 text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
                      <i className="fa-solid fa-circle-dot text-[10px]" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-slate-200 font-medium">{ev.title || ev.action || 'Audit Event'}</div>
                      <div className="text-[11px] text-slate-500">{ev.timestamp ? new Date(ev.timestamp).toLocaleString() : 'Recent'} • {ev.description || ''}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
