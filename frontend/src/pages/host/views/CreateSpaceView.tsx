import React, { useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { createSpace, uploadSpacePhoto, aiScanSpace } from '../../../services/spaces';
import { estimateRevenue } from '../../../services/calculator';
import { User } from '../../../types';
import { HostPageHeader, HostCard } from '../components';

interface CreateSpaceViewProps {
  currentUser?: User | null;
  onOpenHostAuthModal?: () => void;
}

const STEPS = [
  { id: 1, label: 'Basic Info', icon: 'fa-solid fa-circle-info' },
  { id: 2, label: 'Capacity & Size', icon: 'fa-solid fa-ruler-combined' },
  { id: 3, label: 'Amenities', icon: 'fa-solid fa-wifi' },
  { id: 4, label: 'Photos & AI Scan', icon: 'fa-solid fa-camera' },
  { id: 5, label: 'Location & Perimeter', icon: 'fa-solid fa-location-dot' },
  { id: 6, label: 'Operating Hours', icon: 'fa-regular fa-clock' },
  { id: 7, label: 'Pricing Engine', icon: 'fa-solid fa-indian-rupee-sign' },
  { id: 8, label: 'Access & Verification', icon: 'fa-solid fa-shield-halved' },
  { id: 9, label: 'Review & Publish', icon: 'fa-solid fa-paper-plane' },
];

const PRESET_AMENITIES = [
  'High-Speed Wi-Fi',
  'Continuous Power Backup',
  'Ergonomic Desk & Chair',
  'Air Conditioning',
  'Private Restroom',
  'External Monitor / HDMI',
  'Whiteboard & Markers',
  'Coffee / Drinking Water',
  'Sound Isolation',
  'EV Charging Point',
];

export const CreateSpaceView: React.FC<CreateSpaceViewProps> = (props) => {
  const navigate = useNavigate();
  const outletCtx = useOutletContext<{ currentUser?: User | null; onOpenHostAuthModal?: () => void }>() || {};
  const effectiveUser = props.currentUser !== undefined && props.currentUser !== null
    ? props.currentUser
    : (outletCtx.currentUser || (() => {
        try {
          const cached = localStorage.getItem('spaceloop_user');
          if (cached) return JSON.parse(cached) as User;
        } catch {}
        return null;
      })());
  const currentUser = effectiveUser;
  const onOpenHostAuthModal = props.onOpenHostAuthModal || outletCtx.onOpenHostAuthModal;

  const [currentStep, setCurrentStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form Data
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Workspace');
  const [description, setDescription] = useState('');

  const [sqft, setSqft] = useState(150);
  const [capacity, setCapacity] = useState(2);

  const [amenities, setAmenities] = useState<string[]>(['High-Speed Wi-Fi', 'Continuous Power Backup']);
  const [customAmenity, setCustomAmenity] = useState('');

  const [photos, setPhotos] = useState<string[]>([]);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [aiScanning, setAiScanning] = useState(false);
  const [aiScanResult, setAiScanResult] = useState<any>(null);

  const [address, setAddress] = useState('');
  const [city, setCity] = useState('Bangalore');
  const [lat, setLat] = useState('12.9716');
  const [lng, setLng] = useState('77.5946');
  const [geofenceRadius, setGeofenceRadius] = useState(50);

  const [startTime, setStartTime] = useState('08:00');
  const [endTime, setEndTime] = useState('22:00');
  const [bufferMinutes, setBufferMinutes] = useState(15);

  const [hourlyRate, setHourlyRate] = useState(60);
  const [dailyRate, setDailyRate] = useState<string | number>('');
  const [estimatingYield, setEstimatingYield] = useState(false);
  const [yieldEstimate, setYieldEstimate] = useState<any>(null);

  const [accessType, setAccessType] = useState('room_qr');
  const [keyboxCode, setKeyboxCode] = useState('');
  const [discomCaNumber, setDiscomCaNumber] = useState('');
  const [discomConsumerName, setDiscomConsumerName] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);

  const handleNext = () => {
    if (currentStep === 1 && !title.trim()) {
      setError('Please provide a title for your space.');
      return;
    }
    if (currentStep === 5 && !address.trim()) {
      setError('Please provide the physical space address.');
      return;
    }
    setError(null);
    setCurrentStep(prev => Math.min(prev + 1, STEPS.length));
  };

  const handleBack = () => {
    setError(null);
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const toggleAmenity = (item: string) => {
    if (amenities.includes(item)) {
      setAmenities(amenities.filter(a => a !== item));
    } else {
      setAmenities([...amenities, item]);
    }
  };

  const addCustomAmenity = () => {
    if (customAmenity.trim() && !amenities.includes(customAmenity.trim())) {
      setAmenities([...amenities, customAmenity.trim()]);
      setCustomAmenity('');
    }
  };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!currentUser || !currentUser.is_host) {
      setError('Authentication required. Please sign in to your Host account to upload photos.');
      if (onOpenHostAuthModal) {
        onOpenHostAuthModal();
      }
      return;
    }

    try {
      setUploadingPhoto(true);
      setError(null);
      const res = await uploadSpacePhoto(file);
      if (res && res.photo_url) {
        setPhotos(prev => [...prev, res.photo_url]);
      }
    } catch (err: any) {
      const isAuthError = err?.status === 401;

      if (isAuthError) {
        setError('Authentication required. Please sign in to your Host account to upload photos.');
        if (onOpenHostAuthModal) {
          onOpenHostAuthModal();
        }
      } else {
        setError(err?.message || 'Photo upload failed. Using fallback preview.');
        const localUrl = URL.createObjectURL(file);
        setPhotos(prev => [...prev, localUrl]);
      }
    } finally {
      setUploadingPhoto(false);
    }
  };

  const handleRunAiSpatialScan = async () => {
    const photoToScan = photos[0] || 'https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?auto=format&fit=crop&w=1200&q=80';
    try {
      setAiScanning(true);
      const res = await aiScanSpace(photoToScan, `Host noted: ${title} ${category}`);
      setAiScanResult(res);
      if (res.detected_amenities && Array.isArray(res.detected_amenities)) {
        const merged = Array.from(new Set([...amenities, ...res.detected_amenities]));
        setAmenities(merged);
      }
    } catch (err) {
      console.warn('AI scan fallback:', err);
    } finally {
      setAiScanning(false);
    }
  };

  const handleEstimateYield = async () => {
    try {
      setEstimatingYield(true);
      const est = await estimateRevenue({
        space_type: category,
        square_feet: Number(sqft),
        city,
        amenities,
      });
      setYieldEstimate(est);
      if (est.suggested_hourly_rate) {
        setHourlyRate(est.suggested_hourly_rate);
      }
    } catch (err) {
      console.warn('Estimate error:', err);
    } finally {
      setEstimatingYield(false);
    }
  };

  const handlePublish = async (asDraft = false) => {
    try {
      if (!currentUser || !currentUser.is_host) {
        setError('Authentication required. Please sign in to your Host account to publish a space.');
        if (onOpenHostAuthModal) {
          onOpenHostAuthModal();
        }
        return;
      }

      if (!asDraft && !termsAccepted) {
        setError('You must review and agree to the SpaceLoop Terms & Conditions and Section 52 Easements Act compliance before publishing your listing.');
        return;
      }
      setSubmitting(true);
      setError(null);

      const payload = {
        title,
        category,
        description,
        square_feet: Number(sqft),
        capacity: Number(capacity),
        amenities,
        photos: photos.length > 0 ? photos : ['https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80'],
        image_url: photos[0] || 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80',
        address,
        location: `${address}, ${city}`,
        city,
        lat: Number(lat) || 12.9716,
        lng: Number(lng) || 77.5946,
        geofence_radius_meters: Number(geofenceRadius),
        hourly_rate: Number(hourlyRate),
        daily_rate: dailyRate ? Number(dailyRate) : undefined,
        physical_access_type: accessType,
        keybox_code: keyboxCode,
        room_qr_token: `SL-ROOM-${Math.floor(100000 + Math.random() * 900000)}`,
        discom_ca_number: discomCaNumber,
        discom_consumer_name: discomConsumerName,
        is_active: !asDraft,
        terms_accepted: asDraft ? false : termsAccepted,
      };

      const res = await createSpace(payload);
      if (res && (res.space_id || res.id)) {
        const id = res.space_id || res.id;
        navigate(`/host/spaces/${id}?tab=overview`);
      } else {
        navigate('/host/spaces');
      }
    } catch (err: any) {
      const isAuthError = err?.status === 401;

      if (isAuthError) {
        setError('Authentication required. Please sign in to your Host account to publish a space.');
        if (onOpenHostAuthModal) {
          onOpenHostAuthModal();
        }
      } else {
        setError(err?.message || 'Failed to publish space. Please check all required fields.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-6 max-w-5xl mx-auto w-full space-y-6">
      {/* Header */}
      <HostPageHeader
        breadcrumbs={[
          { label: 'My Spaces', onClick: () => navigate('/host/spaces') },
          { label: 'List New Space', active: true },
        ]}
        category="Space Onboarding Wizard"
        title="List a Physical Space"
        subtitle={`Step ${currentStep} of ${STEPS.length}: ${STEPS[currentStep - 1].label}`}
        actions={
          <div className="flex items-center gap-2">
            {currentStep > 1 && (
              <button
                type="button"
                onClick={handleBack}
                className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
              >
                Back
              </button>
            )}

            {currentStep < STEPS.length ? (
              <button
                type="button"
                onClick={handleNext}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-md shadow-amber-500/20 transition flex items-center gap-1.5"
              >
                <span>Continue</span>
                <i className="fa-solid fa-arrow-right text-[10px]" />
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handlePublish(true)}
                  disabled={submitting}
                  className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
                >
                  Save Draft
                </button>
                <button
                  type="button"
                  onClick={() => handlePublish(false)}
                  disabled={submitting || !termsAccepted}
                  title={!termsAccepted ? 'Please accept the Host Terms & Conditions below' : undefined}
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/25 transition flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <i className={`fa-solid ${submitting ? 'fa-spinner animate-spin' : 'fa-check'} text-xs`} />
                  <span>{submitting ? 'Publishing...' : 'Publish Space'}</span>
                </button>
              </div>
            )}
          </div>
        }
      />

      {/* Progress Stepper Bar */}
      <div className="overflow-x-auto pb-1 scrollbar-none">
        <div className="flex items-center gap-1.5 min-w-[760px]">
          {STEPS.map(step => {
            const active = step.id === currentStep;
            const completed = step.id < currentStep;
            return (
              <button
                key={step.id}
                type="button"
                onClick={() => setCurrentStep(step.id)}
                className={`flex-1 flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-medium transition ${
                  active
                    ? 'bg-amber-500/15 border-amber-500/40 text-amber-300 shadow-sm'
                    : completed
                    ? 'bg-slate-900/80 border-slate-700/80 text-emerald-400 hover:border-slate-600'
                    : 'bg-slate-950/40 border-slate-800/80 text-slate-500 hover:text-slate-400'
                }`}
              >
                <i className={`${step.icon} text-xs ${active ? 'text-amber-400' : completed ? 'text-emerald-400' : 'text-slate-600'}`} />
                <span className="truncate">{step.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Unauthenticated Host Warning Banner */}
      {(!currentUser || !currentUser.is_host) && (
        <div className="p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs text-amber-300 flex items-center justify-between flex-wrap gap-2.5">
          <div className="flex items-center gap-2.5">
            <i className="fa-solid fa-shield-halved text-amber-400 text-sm" />
            <span>
              <strong>Host Preview Mode:</strong> You are currently drafting in preview mode. Sign in to your Host account to upload photos and publish your space.
            </span>
          </div>
          {onOpenHostAuthModal && (
            <button
              type="button"
              onClick={onOpenHostAuthModal}
              className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition"
            >
              Sign In to Host
            </button>
          )}
        </div>
      )}

      {/* Error Notice */}
      {error && (
        <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300 flex items-center justify-between flex-wrap gap-2.5">
          <div className="flex items-center gap-2.5">
            <i className="fa-solid fa-triangle-exclamation text-rose-400 text-sm" />
            <span>{error}</span>
          </div>
          {error.toLowerCase().includes('sign in') && onOpenHostAuthModal && (
            <button
              type="button"
              onClick={onOpenHostAuthModal}
              className="px-3 py-1.5 rounded-lg bg-rose-500 hover:bg-rose-400 text-slate-950 font-bold text-xs transition shrink-0"
            >
              Sign In Now
            </button>
          )}
        </div>
      )}

      {/* Step Panels inside HostCard */}
      <HostCard
        title={STEPS[currentStep - 1].label}
        subtitle={`Stage ${currentStep} of ${STEPS.length}`}
        icon={STEPS[currentStep - 1].icon}
      >
        {/* STEP 1: BASIC INFO */}
        {currentStep === 1 && (
          <div className="space-y-5">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Listing Title <span className="text-amber-400">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="e.g. Ergonomic Coding Pod & Ultra High-Speed Fiber"
                className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none transition"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Space Category</label>
              <select
                value={category}
                onChange={e => setCategory(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none transition"
              >
                <option value="Workspace">Workspace / Private Desk</option>
                <option value="Studio">Studio / Podcast Room</option>
                <option value="Storage">Micro-Storage / Luggage</option>
                <option value="Meeting">Meeting / Conference Room</option>
                <option value="Event">Event / Workshop Space</option>
                <option value="Creative">Creative / Maker Lab</option>
                <option value="Parking">Secure Parking / EV Charging</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Detailed Description</label>
              <textarea
                rows={4}
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Describe lighting, noise level, ideal tasks, and access guidelines..."
                className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl p-3.5 text-xs text-white focus:outline-none leading-relaxed transition"
              />
            </div>
          </div>
        )}

        {/* STEP 2: CAPACITY & SIZE */}
        {currentStep === 2 && (
          <div className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Square Feet (Sq. Ft)</label>
                <input
                  type="number"
                  value={sqft}
                  onChange={e => setSqft(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none transition"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Maximum Occupants</label>
                <input
                  type="number"
                  value={capacity}
                  onChange={e => setCapacity(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none transition"
                />
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: AMENITIES */}
        {currentStep === 3 && (
          <div className="space-y-5">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
              {PRESET_AMENITIES.map(item => {
                const checked = amenities.includes(item);
                return (
                  <button
                    key={item}
                    type="button"
                    onClick={() => toggleAmenity(item)}
                    className={`p-3 rounded-xl border text-left text-xs font-medium transition flex items-center justify-between ${
                      checked
                        ? 'bg-amber-500/15 border-amber-500/40 text-amber-300'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <span>{item}</span>
                    <i className={`fa-solid ${checked ? 'fa-circle-check text-amber-400' : 'fa-circle text-slate-700'} text-xs`} />
                  </button>
                );
              })}
            </div>

            <div className="flex items-center gap-2 pt-2">
              <input
                type="text"
                value={customAmenity}
                onChange={e => setCustomAmenity(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addCustomAmenity())}
                placeholder="Add other amenity (e.g. Ring light, 3D printer)..."
                className="flex-1 bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none transition"
              />
              <button
                type="button"
                onClick={addCustomAmenity}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
              >
                Add
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: PHOTOS & AI SCAN */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400">Upload clear photos of the space entrance, workspace, and seating.</p>
              </div>
              <button
                type="button"
                onClick={handleRunAiSpatialScan}
                disabled={aiScanning}
                className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition flex items-center gap-1.5 shadow-md"
              >
                <i className={`fa-solid ${aiScanning ? 'fa-spinner animate-spin' : 'fa-wand-magic-sparkles'} text-xs`} />
                <span>{aiScanning ? 'Scanning...' : 'AI Spatial Tagging'}</span>
              </button>
            </div>

            {/* Photos Preview */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {photos.map((url, i) => (
                <div key={i} className="aspect-video rounded-xl overflow-hidden border border-slate-800 relative group">
                  <img src={url} alt="Space" className="w-full h-full object-cover" />
                  <button
                    type="button"
                    onClick={() => setPhotos(photos.filter((_, idx) => idx !== i))}
                    className="absolute top-1.5 right-1.5 w-6 h-6 rounded-lg bg-slate-950/80 text-rose-400 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition"
                  >
                    ×
                  </button>
                </div>
              ))}

              <label className="aspect-video rounded-xl border-2 border-dashed border-slate-800 hover:border-amber-500/50 flex flex-col items-center justify-center cursor-pointer transition bg-slate-950/50">
                <i className={`fa-solid ${uploadingPhoto ? 'fa-spinner animate-spin' : 'fa-cloud-arrow-up'} text-amber-400 text-lg mb-1`} />
                <span className="text-[11px] text-slate-400">{uploadingPhoto ? 'Uploading...' : 'Upload Photo'}</span>
                <input type="file" accept="image/*" onChange={handlePhotoUpload} className="hidden" />
              </label>
            </div>

            {aiScanResult && (
              <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/30 space-y-2">
                <div className="text-xs font-bold text-indigo-300 flex items-center gap-2">
                  <i className="fa-solid fa-check-double text-indigo-400" />
                  <span>AI Computer Vision Analysis Verified</span>
                </div>
                <p className="text-[11px] text-slate-300">
                  {aiScanResult.summary || 'Detected well-lit workstation with ergonomic desk setup, power outlets, and clean physical condition.'}
                </p>
              </div>
            )}
          </div>
        )}

        {/* STEP 5: LOCATION & GEOFENCE */}
        {currentStep === 5 && (
          <div className="space-y-5">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Street Address <span className="text-amber-400">*</span>
              </label>
              <input
                type="text"
                value={address}
                onChange={e => setAddress(e.target.value)}
                placeholder="e.g. 42 Indiranagar 100 Feet Road"
                className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none transition"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">City</label>
                <input
                  type="text"
                  value={city}
                  onChange={e => setCity(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white transition"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Latitude</label>
                <input
                  type="text"
                  value={lat}
                  onChange={e => setLat(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white font-mono transition"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Longitude</label>
                <input
                  type="text"
                  value={lng}
                  onChange={e => setLng(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white font-mono transition"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Zero-Spoofing Geofence Radius: <span className="text-amber-400 font-mono">{geofenceRadius} meters</span>
              </label>
              <input
                type="range"
                min={20}
                max={150}
                step={5}
                value={geofenceRadius}
                onChange={e => setGeofenceRadius(Number(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer"
              />
              <span className="text-[10px] text-slate-500 block mt-1">
                Arrival is mathematically confirmed via Haversine calculation within {geofenceRadius}m of this coordinate.
              </span>
            </div>
          </div>
        )}

        {/* STEP 6: OPERATING HOURS */}
        {currentStep === 6 && (
          <div className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Daily Opening Time</label>
                <input
                  type="time"
                  value={startTime}
                  onChange={e => setStartTime(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white transition"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Daily Closing Time</label>
                <input
                  type="time"
                  value={endTime}
                  onChange={e => setEndTime(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white transition"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Buffer Between Sessions</label>
                <select
                  value={bufferMinutes}
                  onChange={e => setBufferMinutes(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white transition"
                >
                  <option value={15}>15 Minutes (Standard)</option>
                  <option value={30}>30 Minutes (Cleaning)</option>
                  <option value={60}>60 Minutes (Sanitization)</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* STEP 7: PRICING ENGINE */}
        {currentStep === 7 && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400">95% net payout released automatically to host UPI upon session checkout.</p>
              </div>
              <button
                type="button"
                onClick={handleEstimateYield}
                disabled={estimatingYield}
                className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-400 font-semibold text-xs border border-slate-700 transition"
              >
                {estimatingYield ? 'Calculating...' : 'Run Yield Estimate'}
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Hourly Rate (₹)</label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 text-xs">₹</span>
                  <input
                    type="number"
                    value={hourlyRate}
                    onChange={e => setHourlyRate(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl pl-8 pr-3 py-2 text-xs text-white focus:outline-none transition"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Daily Cap Rate (₹ optional)</label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 text-xs">₹</span>
                  <input
                    type="number"
                    value={dailyRate}
                    onChange={e => setDailyRate(e.target.value)}
                    placeholder="e.g. 400"
                    className="w-full bg-slate-950 border border-slate-800 focus:border-amber-500/60 rounded-xl pl-8 pr-3 py-2 text-xs text-white focus:outline-none transition"
                  />
                </div>
              </div>
            </div>

            {yieldEstimate && (
              <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-xs text-emerald-300 flex items-center justify-between">
                <span>Estimated Monthly Earnings: <strong className="font-mono">₹{yieldEstimate.estimated_monthly_earnings?.toLocaleString('en-IN') || '12,500'}</strong></span>
                <span className="text-slate-400 font-mono">Suggested: ₹{yieldEstimate.suggested_hourly_rate}/hr</span>
              </div>
            )}
          </div>
        )}

        {/* STEP 8: ACCESS & VERIFICATION */}
        {currentStep === 8 && (
          <div className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Access Method</label>
                <select
                  value={accessType}
                  onChange={e => setAccessType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white transition"
                >
                  <option value="room_qr">Room Dynamic QR Code (Scanned on Door)</option>
                  <option value="keybox">Keybox PIN Code</option>
                  <option value="smart_lock">Smart Door Lock (BLE / WiFi)</option>
                  <option value="host_greeter">Host In-Person Greeting</option>
                </select>
              </div>

              {accessType === 'keybox' && (
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Keybox PIN Code</label>
                  <input
                    type="text"
                    value={keyboxCode}
                    onChange={e => setKeyboxCode(e.target.value)}
                    placeholder="e.g. 4920"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white font-mono transition"
                  />
                </div>
              )}

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Discom CA Number (Electricity Bill)</label>
                <input
                  type="text"
                  value={discomCaNumber}
                  onChange={e => setDiscomCaNumber(e.target.value)}
                  placeholder="e.g. 100293847"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white font-mono transition"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Consumer Name on Utility Bill</label>
                <input
                  type="text"
                  value={discomConsumerName}
                  onChange={e => setDiscomConsumerName(e.target.value)}
                  placeholder="e.g. Rajesh Sharma"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white transition"
                />
              </div>
            </div>
          </div>
        )}

        {/* STEP 9: REVIEW & PUBLISH */}
        {currentStep === 9 && (
          <div className="space-y-6">
            <div className="p-5 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-3 text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Space Title:</span>
                <span className="font-bold text-white">{title || 'Untitled Space'}</span>
              </div>
              <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Category & Size:</span>
                <span className="font-medium text-slate-200">{category} • {sqft} sqft • Max {capacity} occupants</span>
              </div>
              <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Physical Address:</span>
                <span className="font-medium text-slate-200">{address}, {city}</span>
              </div>
              <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Hourly Pricing:</span>
                <span className="font-bold text-emerald-400 font-mono">₹{hourlyRate}/hr</span>
              </div>
              <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                <span className="text-slate-400">Zero-Spoofing Perimeter:</span>
                <span className="font-mono text-amber-400">{geofenceRadius}m Haversine Radius</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Access Mechanism:</span>
                <span className="font-mono text-slate-200">{accessType}</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-start gap-2.5">
              <i className="fa-solid fa-circle-check text-amber-400 mt-0.5" />
              <span>
                By publishing, your space will appear in search results. Renters will submit automated ₹100 micro-escrow deposits on booking, released upon checkout condition match.
              </span>
            </div>

            {/* Terms and Conditions Acceptance */}
            <div className={`p-4 rounded-xl border transition ${termsAccepted ? 'bg-slate-900/90 border-amber-500/40' : 'bg-slate-950/80 border-slate-800'}`}>
              <label className="flex items-start gap-3 cursor-pointer select-none">
                <input
                  type="checkbox"
                  id="create_space_terms_checkbox"
                  checked={termsAccepted}
                  onChange={e => setTermsAccepted(e.target.checked)}
                  className="mt-1 w-4 h-4 rounded border-slate-700 text-amber-500 focus:ring-amber-400 bg-slate-900 cursor-pointer"
                />
                <span className="text-xs text-slate-300 leading-relaxed">
                  I agree to the <strong className="text-amber-400 font-semibold">SpaceLoop Host Terms &amp; Conditions</strong>, including Section 52 Indian Easements Act micro-lease compliance, premises electrical safety standards, and automated ₹100 refundable escrow resolution.
                </span>
              </label>
              {!termsAccepted && (
                <p className="text-[11px] text-amber-400/90 pl-7 mt-1.5 flex items-center gap-1.5">
                  <i className="fa-solid fa-circle-exclamation text-[10px]" />
                  <span>Mandatory: You must accept these terms before publishing your listing.</span>
                </p>
              )}
            </div>
          </div>
        )}
      </HostCard>
    </div>
  );
};
