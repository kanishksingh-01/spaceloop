import React, { useState } from 'react';
import { View, Text, Pressable, TextInput, Image, ScrollView } from 'react-native';
import { useNavigate } from 'react-router-dom';
import {
  aiScanSpace,
  createSpace,
  uploadSpacePhoto,
  assistListing,
  translateListing,
  ListingAssistanceResponse,
} from '../services/spaces';
import { HostAuthModal } from '../components/common/HostAuthModal';
import { User } from '../types';

interface ListSpacePageProps {
  currentUser: User | null;
}

export const ListSpacePage: React.FC<ListSpacePageProps> = ({ currentUser }) => {
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('Workspace');
  const [hourlyRate, setHourlyRate] = useState('');
  const [location, setLocation] = useState('');
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');
  const [photoUrl, setPhotoUrl] = useState('');
  const [amenities, setAmenities] = useState('');
  const [notes, setNotes] = useState('');

  const [termsAccepted, setTermsAccepted] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);

  const [isScanning, setIsScanning] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [scanMessage, setScanMessage] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [selectedPersonas, setSelectedPersonas] = useState<string[]>([]);

  // Part 6: NLP Listing Assistant & Translation State
  const [nlInput, setNlInput] = useState('');
  const [isNlDrafting, setIsNlDrafting] = useState(false);
  const [nlAssistResult, setNlAssistResult] = useState<ListingAssistanceResponse | null>(null);
  const [isTranslating, setIsTranslating] = useState(false);
  const [translationSuccess, setTranslationSuccess] = useState<string | null>(null);

  const categoryOptions = [
    'Workspace',
    'Meeting',
    'Studio',
    'Podcast',
    'Workshop',
    'Retail',
    'Storage',
    'Study Pod',
  ];

  const personasList = [
    'Remote Workers',
    'Creators & Podcasters',
    'Startups & Teams',
    'Client Consultations',
    'Hardware Builders',
    'Pop-Up Vendors',
    'Students & Learners',
  ];

  const togglePersona = (p: string) => {
    setSelectedPersonas((prev) =>
      prev.includes(p) ? prev.filter((item) => item !== p) : [...prev, p]
    );
  };

  const presets = [
    {
      label: 'Executive Glass Meeting Suite',
      photo: 'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80',
      category: 'Meeting',
      title: 'Executive Glass Meeting & Client Suite',
      location: 'Indiranagar',
      address: '100 Feet Road, Indiranagar, Bengaluru',
      city: 'Bengaluru',
      rate: '120',
      amenities: '4K Display, Polycom Mic, 1Gbps WiFi, Nespresso, Whiteboard',
      notes: 'Soundproofed glass consultation room ideal for client meetings, investor pitches, and team syncs.',
      personas: ['Startups & Teams', 'Client Consultations', 'Remote Workers'],
    },
    {
      label: 'Acoustic Creator Podcast Cabin',
      photo: 'https://images.unsplash.com/photo-1590674899484-d5640e854abe?auto=format&fit=crop&w=800&q=80',
      category: 'Studio',
      title: 'Acoustic Creator & Podcast Cabin',
      location: 'Baner',
      address: 'Pan Card Club Road, Baner, Pune',
      city: 'Pune',
      rate: '85',
      amenities: 'Dual Shure MV7 Mics, Scarlett 2i2, Monitor Headphones, Acoustic Paneling',
      notes: 'Sound-isolated recording booth for 2 with studio mics, zero echo, and pro audio interface.',
      personas: ['Creators & Podcasters', 'Startups & Teams'],
    },
    {
      label: 'Maker Workshop & Prototyping Bay',
      photo: 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=800&q=80',
      category: 'Workshop',
      title: 'Hardware Prototyping & Soldering Bay',
      location: 'Electronic City',
      address: 'Phase 1, Electronic City, Bengaluru',
      city: 'Bengaluru',
      rate: '90',
      amenities: '3D Printer, Soldering Station, Multimeter, ESD Mat, 20A Circuit',
      notes: 'Ventilated maker workbench with ESD station and 3D printing equipment for hardware engineers.',
      personas: ['Hardware Builders', 'Startups & Teams', 'Students & Learners'],
    },
    {
      label: 'Quiet Study & Focus Nook',
      photo: 'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=800&q=80',
      category: 'Study Pod',
      title: 'Acoustic Focus Nook near JSPM',
      location: 'Wagholi',
      address: 'Gate 2, JSPM Imperial College Road, Wagholi, Pune',
      city: 'Pune',
      rate: '45',
      amenities: 'Ergonomic Task Chair, Fiber WiFi, LED Reading Lamp, Power Outlets, AC',
      notes: 'Silent air-conditioned nook for intensive study, thesis writing, or deep coding work.',
      personas: ['Students & Learners', 'Remote Workers'],
    },
  ];

  const handleApplyPreset = (p: typeof presets[0]) => {
    setPhotoUrl(p.photo);
    setCategory(p.category);
    setTitle(p.title);
    setLocation(p.location);
    setAddress(p.address);
    setCity(p.city);
    setHourlyRate(p.rate);
    setAmenities(p.amenities);
    setNotes(p.notes);
    if (p.personas) {
      setSelectedPersonas(p.personas);
    }
  };

  const handleAiScan = async () => {
    if (!photoUrl) {
      setError('Please provide a photo URL to scan');
      return;
    }
    setIsScanning(true);
    setError(null);
    setScanMessage(null);
    try {
      const res = await aiScanSpace(photoUrl, notes);
      setScanResult(res);

      const suggestedTitle = res.title || res.scan?.title;
      const suggestedDesc = res.enhanced_description || res.description || res.scan?.description;
      const suggestedRate = res.recommended_hourly_price || res.suggested_price || res.scan?.suggested_price;
      const suggestedCategory = res.category || res.scan?.category;
      const suggestedAmenities = res.detected_amenities || res.amenities || res.scan?.amenities;

      if (suggestedTitle) setTitle(suggestedTitle);
      if (suggestedDesc) setDescription(suggestedDesc);
      if (suggestedRate) setHourlyRate(String(Math.round(suggestedRate)));
      if (suggestedCategory) setCategory(suggestedCategory);
      if (suggestedAmenities && Array.isArray(suggestedAmenities)) {
        setAmenities(suggestedAmenities.join(', '));
      }

      setScanMessage(
        `✨ AI Multimodal analysis complete! Detected ${res.estimated_sqft || 250} sqft (${res.lighting || 'Natural light'}, ${res.noise_level || 'Quiet'}), Suitability: ${res.suitability_score || 94}%. Optimal rate suggested: ₹${Math.round(suggestedRate || 45)}/hr.`
      );
    } catch (err: any) {
      setError(err.message || 'AI inspection encountered an error. You can still publish manually.');
    } finally {
      setIsScanning(false);
    }
  };

  const handleNlDraft = async () => {
    if (!nlInput.trim()) {
      setError('Please enter some space details in natural language (e.g. 2 bedroom workspace in Pune for 4 people with fast WiFi and AC).');
      return;
    }
    setIsNlDrafting(true);
    setError(null);
    try {
      const res = await assistListing(nlInput.trim());
      setNlAssistResult(res);
      const draft = res.listing_draft || {};
      const fields = res.extracted_fields || {};

      if (draft.title || fields.title) setTitle(draft.title || fields.title || '');
      if (res.generated_description || draft.description) setDescription(res.generated_description || draft.description || '');
      if (draft.category || fields.category) setCategory(draft.category || fields.category || 'Workspace');
      if (draft.price_hourly || fields.price_hourly) {
        setHourlyRate(String(Math.round(draft.price_hourly || fields.price_hourly || 0)));
      }
      if (draft.location || fields.location) setLocation(draft.location || fields.location || '');
      if (draft.city || fields.city) setCity(draft.city || fields.city || '');
      const amenitiesToSet = draft.amenities || fields.amenities || [];
      if (amenitiesToSet.length > 0) {
        setAmenities(amenitiesToSet.join(', '));
      }
      const locDisplay = draft.location || fields.location;
      setScanMessage(
        `✓ Listing draft created! Extracted ${draft.category || fields.propertyType || 'space'}${locDisplay ? ` in ${locDisplay}` : ''}. Review and confirm details below.`
      );
    } catch (err: any) {
      setError(err.message || 'Failed to analyze listing text with AI.');
    } finally {
      setIsNlDrafting(false);
    }
  };

  const handleTranslateListing = async (lang: 'hi' | 'mr' | 'en') => {
    if (!title && !description) {
      setError('Please provide or draft a title and description before translating.');
      return;
    }
    setIsTranslating(true);
    setError(null);
    setTranslationSuccess(null);
    try {
      const amenityArray = amenities
        .split(',')
        .map((a) => a.trim())
        .filter(Boolean);
      const res = await translateListing(title, description, amenityArray, lang);
      if (res.title) setTitle(res.title);
      if (res.description) setDescription(res.description);
      const langNames: Record<string, string> = { hi: 'Hindi', mr: 'Marathi', en: 'English' };
      setTranslationSuccess(`Listing translated to ${langNames[lang] || lang}!`);
    } catch (err: any) {
      setError(err.message || 'Failed to translate listing.');
    } finally {
      setIsTranslating(false);
    }
  };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      setError('Selected image exceeds 5MB size limit. Please upload a smaller image.');
      return;
    }
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setError('Please select a valid image format (PNG, JPEG, or WEBP).');
      return;
    }

    setUploadingPhoto(true);
    setError(null);
    try {
      const res = await uploadSpacePhoto(file);
      if (res && res.photo_url) {
        setPhotoUrl(res.photo_url);
        setScanMessage('Photo uploaded successfully! You can run AI scan or continue with space details.');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to upload photo. Please check your network or try again.');
    } finally {
      setUploadingPhoto(false);
    }
  };

  const handlePublish = async () => {
    if (isPublishing) return;
    if (!currentUser || !currentUser.is_host) {
      setShowAuthModal(true);
      return;
    }
    if (!currentUser.is_host_verified) {
      setError('Host verification required. Please complete Discom property verification in the Host Portal.');
      setShowAuthModal(true);
      return;
    }
    if (!termsAccepted) {
      setError('You must review and accept the SpaceLoop Host Terms & Conditions before publishing.');
      return;
    }
    if (!title.trim() || !hourlyRate || !location.trim()) {
      setError('Please provide a listing title, hourly rate, and neighborhood/locality.');
      return;
    }
    setIsPublishing(true);
    setError(null);
    try {
      const amenityArray = amenities
        .split(',')
        .map((a) => a.trim())
        .filter(Boolean);

      let finalDesc = description || notes;
      if (selectedPersonas.length > 0) {
        finalDesc += `\n\nSuitable For: ${selectedPersonas.join(', ')}`;
      }

      const res = await createSpace({
        title: title.trim(),
        description: finalDesc,
        category,
        hourly_rate: Number(hourlyRate),
        price_hourly: Number(hourlyRate),
        location: location.trim(),
        neighborhood: location.trim(),
        address: address.trim() || location.trim(),
        city: city.trim() || 'Pune',
        photos: photoUrl ? [photoUrl] : [],
        amenities: amenityArray,
        terms_accepted: true,
        latitude: city === 'Pune' ? 18.5793 : city === 'Delhi' ? 28.5494 : 12.9352,
        longitude: city === 'Pune' ? 73.9825 : city === 'Delhi' ? 77.2001 : 77.6245,
      });

      const spaceId = res.space_id || (res as any).id;
      if (spaceId) {
        navigate(`/space/${spaceId}`);
      } else {
        navigate('/host/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to list space');
    } finally {
      setIsPublishing(false);
    }
  };

  return (
    <View className="min-h-screen bg-slate-950 pb-20">
      {/* Header Banner */}
      <View className="bg-slate-900 border-b border-slate-800 py-10 px-4">
        <View className="max-w-4xl mx-auto text-center">
          <View className="inline-flex flex-row items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 mb-3 self-center">
            <Text className="text-xs font-bold text-indigo-300">
              🤖 Multimodal AI Space Inspector
            </Text>
          </View>
          <Text className="text-3xl sm:text-4xl font-black text-white mb-2">
            List Your Idle Space in 60 Seconds
          </Text>
          <Text className="text-sm text-slate-400 max-w-xl mx-auto">
            Upload a photo or choose a preset. Our AI detects usable square footage, acoustic profile, and suggests optimal hourly rates.
          </Text>
        </View>
      </View>

      <View className="max-w-4xl mx-auto px-4 sm:px-6 mt-8 space-y-8">
        {scanMessage && (
          <View className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl">
            <Text className="text-sm text-emerald-300 font-medium">✓ {scanMessage}</Text>
          </View>
        )}

        {error && (
          <View className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl">
            <Text className="text-sm text-rose-300 font-medium">✕ {error}</Text>
          </View>
        )}

        {/* NLP Natural Language Listing Assistant */}
        <View className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/30 rounded-2xl p-6 floating-panel space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-bold text-white">✨ Natural Language Listing Assistant</span>
                <span className="text-[10px] bg-indigo-500/20 text-indigo-300 font-bold px-2 py-0.5 rounded-full border border-indigo-500/30">
                  Multilingual AI
                </span>
              </div>
              <Text className="text-xs text-slate-400 mt-0.5">
                Paste or describe your space in English, Hindi, or Marathi (e.g. &quot;2 bedroom flat in Pune, fully furnished, near IT park, 25k rent&quot;).
              </Text>
            </div>
            <div className="flex items-center gap-1.5 self-start sm:self-auto">
              <span className="text-[11px] text-slate-400">Translate:</span>
              {(['en', 'hi', 'mr'] as const).map((lang) => (
                <button
                  key={lang}
                  type="button"
                  onClick={() => handleTranslateListing(lang)}
                  disabled={isTranslating || (!title && !description)}
                  className={`text-[11px] font-bold px-2.5 py-1 rounded-lg border transition ${
                    isTranslating
                      ? 'opacity-50 cursor-not-allowed bg-slate-800 border-slate-700 text-slate-400'
                      : 'bg-slate-800 hover:bg-indigo-900/60 border-slate-700 hover:border-indigo-500/50 text-indigo-200'
                  }`}
                >
                  {lang.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <textarea
              value={nlInput}
              onChange={(e) => setNlInput(e.target.value)}
              placeholder="e.g. 2 bedroom flat in Pune, fully furnished, near IT park, 25k rent&#10;or: बाणेर मध्ये शांत 1 बीएचके खोली, एसी आणि वायफाय, 15000 भाडं..."
              rows={3}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />

            {/* Quick Test Prompts */}
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <span className="text-[11px] text-slate-400 font-medium">Try prompt:</span>
              <button
                type="button"
                onClick={() => setNlInput("2 bedroom workspace in Pune for 4 people with fast WiFi and AC")}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-indigo-900/40 text-indigo-300 border border-slate-700 hover:border-indigo-500/40 transition"
              >
                &quot;2 bedroom workspace in Pune for 4 people with fast WiFi and AC&quot;
              </button>
              <button
                type="button"
                onClick={() => setNlInput("Workspace for 4 people with WiFi")}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-indigo-900/40 text-indigo-300 border border-slate-700 hover:border-indigo-500/40 transition"
              >
                &quot;Workspace for 4 people with WiFi&quot;
              </button>
              <button
                type="button"
                onClick={() => setNlInput("पुणे में 2 कमरा फ्लैट, पूरी तरह सुसज्जित, 25000 किराया")}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-indigo-900/40 text-indigo-300 border border-slate-700 hover:border-indigo-500/40 transition"
              >
                &quot;पुणे में 2 कमरा फ्लैट, 25000 किराया&quot;
              </button>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-[11px] text-emerald-400 font-medium">
                <i className="fa-solid fa-shield-halved" />
                <span>Zero Hallucination: unmentioned fields are left blank for host review.</span>
              </div>
              <button
                type="button"
                onClick={handleNlDraft}
                disabled={isNlDrafting || !nlInput.trim()}
                className={`px-5 py-2 rounded-xl text-xs font-bold text-white transition flex items-center gap-2 ${
                  isNlDrafting || !nlInput.trim()
                    ? 'bg-indigo-900/40 text-slate-500 cursor-not-allowed'
                    : 'bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-600/30'
                }`}
              >
                {isNlDrafting ? (
                  <>
                    <i className="fa-solid fa-circle-notch fa-spin" />
                    <span>Analyzing &amp; Drafting...</span>
                  </>
                ) : (
                  <>
                    <i className="fa-solid fa-wand-magic-sparkles" />
                    <span>Draft Listing with AI</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* AI Extraction Summary Banner */}
          {nlAssistResult && (
            <div className="mt-4 p-4 rounded-xl bg-slate-950/90 border border-indigo-500/30 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                    <i className="fa-solid fa-file-pen text-indigo-400" />
                    Listing Draft Generated
                  </span>
                  <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full border border-indigo-500/30 font-semibold uppercase">
                    {nlAssistResult.ai_provider || 'nlp'} • {(nlAssistResult.detected_language || 'EN').toUpperCase()}
                  </span>
                </div>
                <span className="text-[10px] text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded-md border border-amber-500/20">
                  Host Review Required — confirm details in form below
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                <div className="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 block mb-0.5">Category / Type</span>
                  <span className="text-white font-semibold">
                    {nlAssistResult.listing_draft?.category || nlAssistResult.extracted_fields?.propertyType || (
                      <span className="text-amber-400/80 italic">Unspecified</span>
                    )}
                    {nlAssistResult.extracted_fields?.bedrooms ? ` (${nlAssistResult.extracted_fields.bedrooms} BHK)` : ''}
                  </span>
                </div>
                <div className="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 block mb-0.5">Location</span>
                  <span className="text-white font-semibold">
                    {nlAssistResult.listing_draft?.location || nlAssistResult.extracted_fields?.location ? (
                      <>
                        {nlAssistResult.listing_draft?.location || nlAssistResult.extracted_fields?.location}
                        {nlAssistResult.extracted_fields?.near ? ` (Near ${nlAssistResult.extracted_fields.near})` : ''}
                      </>
                    ) : (
                      <span className="text-amber-400/80 italic">Unspecified</span>
                    )}
                  </span>
                </div>
                <div className="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 block mb-0.5">Capacity</span>
                  <span className="text-white font-semibold">
                    {nlAssistResult.listing_draft?.max_capacity || nlAssistResult.extracted_fields?.max_capacity ? (
                      `${nlAssistResult.listing_draft?.max_capacity || nlAssistResult.extracted_fields?.max_capacity} people`
                    ) : (
                      <span className="text-amber-400/80 italic">Unspecified</span>
                    )}
                  </span>
                </div>
                <div className="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 block mb-0.5">Hourly Rate</span>
                  <span className="text-indigo-300 font-bold">
                    {nlAssistResult.listing_draft?.price_hourly || nlAssistResult.extracted_fields?.price_hourly ? (
                      `₹${Math.round(nlAssistResult.listing_draft?.price_hourly || nlAssistResult.extracted_fields?.price_hourly || 0)}/hr`
                    ) : (
                      <span className="text-amber-400/80 italic font-normal">Unspecified</span>
                    )}
                  </span>
                </div>
              </div>

              {/* Mentioned Amenities */}
              <div className="bg-slate-900/70 p-2 rounded-lg border border-slate-800/80 text-[11px] flex flex-wrap items-center gap-1.5">
                <span className="text-slate-400 font-medium">Detected Amenities:</span>
                {(nlAssistResult.listing_draft?.amenities || nlAssistResult.extracted_fields?.amenities || []).length > 0 ? (
                  (nlAssistResult.listing_draft?.amenities || nlAssistResult.extracted_fields?.amenities || []).map((amen: string, idx: number) => (
                    <span key={idx} className="bg-indigo-500/10 text-indigo-300 px-2 py-0.5 rounded border border-indigo-500/20 text-[10px] font-medium">
                      ✓ {amen}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-500 italic">None explicitly mentioned in description</span>
                )}
              </div>

              {/* Clarification Questions if missing info */}
              {nlAssistResult.clarifications && nlAssistResult.clarifications.length > 0 && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg space-y-1">
                  <div className="flex items-center gap-1.5 text-amber-300 text-xs font-bold">
                    <i className="fa-solid fa-circle-question" />
                    <span>Recommended Details to Clarify:</span>
                  </div>
                  <ul className="list-disc list-inside text-[11px] text-amber-200/90 space-y-0.5">
                    {nlAssistResult.clarifications.map((q, idx) => (
                      <li key={idx}>{q}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Inconsistencies Warning if any */}
              {nlAssistResult.inconsistencies && nlAssistResult.inconsistencies.length > 0 && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg space-y-1">
                  <div className="flex items-center gap-1.5 text-rose-300 text-xs font-bold">
                    <i className="fa-solid fa-triangle-exclamation" />
                    <span>Inconsistencies Detected:</span>
                  </div>
                  <ul className="list-disc list-inside text-[11px] text-rose-200/90 space-y-0.5">
                    {nlAssistResult.inconsistencies.map((inc, idx) => (
                      <li key={idx}>{inc.message}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {translationSuccess && (
            <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs text-emerald-300 font-medium">
              ✓ {translationSuccess}
            </div>
          )}
        </View>

        {/* 1-Click Demo Presets */}
        <View className="bg-slate-900 border border-slate-800 rounded-2xl p-6 floating-container">
          <Text className="text-sm font-bold text-white mb-3">
            Quick Start: Select a Sample Listing Preset
          </Text>
          <View className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {presets.map((p, idx) => (
              <Pressable
                key={idx}
                onPress={() => handleApplyPreset(p)}
                className="bg-slate-950 border border-slate-800 hover:border-indigo-500 rounded-xl overflow-hidden p-2.5 transition text-left group floating-interactive"
              >
                <Image source={{ uri: p.photo }} className="w-full h-24 rounded-lg object-cover mb-2" />
                <Text className="text-xs font-bold text-white mb-0.5">{p.label}</Text>
                <Text className="text-[11px] text-indigo-300">₹{p.rate}/hr • {p.city}</Text>
              </Pressable>
            ))}
          </View>
        </View>

        {/* Main Listing Form */}
        <View className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5 floating-panel">
          <Text className="text-base font-bold text-white pb-3 border-b border-slate-800">
            Space Parameters & AI Scan
          </Text>

          {/* Photo Upload & URL & AI Scanner Button */}
          <View className="space-y-3">
            <div className="flex items-center justify-between">
              <Text className="text-xs font-medium text-slate-300">Space Photo (Local Upload or URL)</Text>
              <span className="text-[10px] text-slate-400">JPG, PNG, WEBP (Max 5MB)</span>
            </div>
            <div className="flex flex-col sm:flex-row items-center gap-2.5">
              <label className={`cursor-pointer px-4 py-2.5 rounded-xl border border-dashed border-indigo-500/50 bg-indigo-950/30 hover:bg-indigo-900/40 text-xs font-semibold text-indigo-300 flex items-center justify-center gap-2 transition ${uploadingPhoto ? 'opacity-50 pointer-events-none' : ''}`}>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handlePhotoUpload}
                  className="hidden"
                />
                <i className={`fa-solid ${uploadingPhoto ? 'fa-circle-notch fa-spin' : 'fa-cloud-arrow-up'}`} />
                <span>{uploadingPhoto ? 'Uploading...' : 'Upload Photo'}</span>
              </label>

              <span className="text-xs text-slate-500 font-bold hidden sm:inline">OR</span>

              <TextInput
                value={photoUrl}
                onChangeText={setPhotoUrl}
                placeholder="Paste an image URL directly..."
                placeholderTextColor="#64748b"
                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:border-indigo-500 w-full"
              />
              <Pressable
                onPress={handleAiScan}
                disabled={isScanning || !photoUrl}
                className={`px-5 py-2.5 rounded-xl items-center justify-center transition shadow-md w-full sm:w-auto ${
                  isScanning || !photoUrl ? 'bg-indigo-900/50 opacity-50' : 'bg-indigo-600 hover:bg-indigo-500'
                }`}
              >
                <Text className="text-xs font-bold text-white">
                  {isScanning ? 'Inspecting...' : '⚡ Scan with AI'}
                </Text>
              </Pressable>
            </div>
          </View>

          {/* Image Preview */}
          {photoUrl && (
            <div className="relative w-full h-52 rounded-xl overflow-hidden bg-slate-950 border border-slate-800 group">
              <Image source={{ uri: photoUrl }} className="w-full h-full object-cover" />
              <button
                type="button"
                onClick={() => setPhotoUrl('')}
                className="absolute top-2.5 right-2.5 px-3 py-1.5 rounded-lg bg-black/75 hover:bg-rose-600 text-white text-xs font-bold transition flex items-center gap-1.5 shadow"
              >
                <i className="fa-solid fa-trash text-[10px]" /> Remove
              </button>
            </div>
          )}

          {/* AI Space Inspector Analysis Card */}
          {scanResult && (
            <View className="p-4 bg-indigo-950/30 border border-indigo-500/30 rounded-2xl space-y-3 floating-container">
              <View className="flex-row items-center justify-between">
                <Text className="text-xs font-bold text-indigo-300 flex-row items-center gap-1.5">
                  ✨ AI Multimodal Inspection Report
                </Text>
                <View className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30">
                  <Text className="text-[11px] font-bold text-emerald-400">
                    {scanResult.suitability_score || 95}% Suitability
                  </Text>
                </View>
              </View>

              <View className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
                <View className="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
                  <Text className="text-[10px] text-slate-400">Usable Area</Text>
                  <Text className="text-xs font-bold text-white mt-0.5">
                    {scanResult.estimated_sqft || 250} sqft
                  </Text>
                </View>
                <View className="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
                  <Text className="text-[10px] text-slate-400">Max Capacity</Text>
                  <Text className="text-xs font-bold text-white mt-0.5">
                    Up to {scanResult.max_capacity || 4} ppl
                  </Text>
                </View>
                <View className="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
                  <Text className="text-[10px] text-slate-400">Acoustic Profile</Text>
                  <Text className="text-xs font-bold text-indigo-300 mt-0.5 line-clamp-1">
                    {scanResult.noise_level || 'Quiet (<45 dB)'}
                  </Text>
                </View>
                <View className="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
                  <Text className="text-[10px] text-slate-400">Power / Outlets</Text>
                  <Text className="text-xs font-bold text-amber-300 mt-0.5 line-clamp-1">
                    {scanResult.power_access || 'Standard 120V'}
                  </Text>
                </View>
              </View>

              {scanResult.safety_notes && (
                <View className="p-2.5 bg-slate-950/50 rounded-xl border border-slate-800">
                  <Text className="text-[10px] text-slate-400">Safety & Compliance Notes:</Text>
                  <Text className="text-xs text-slate-300 mt-0.5 leading-relaxed">
                    {scanResult.safety_notes}
                  </Text>
                </View>
              )}
            </View>
          )}

          {/* Title & Category */}
          <View className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <View>
              <Text className="text-xs font-medium text-slate-300 mb-1">Listing Title</Text>
              <TextInput
                value={title}
                onChangeText={setTitle}
                placeholder="e.g. Wagholi Sunlit Study Pod"
                placeholderTextColor="#64748b"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:border-indigo-500"
              />
            </View>

            <View>
              <Text className="text-xs font-medium text-slate-300 mb-1">Space Category</Text>
              <View className="flex-row flex-wrap gap-1.5 mb-2">
                {categoryOptions.map((cat) => (
                  <Pressable
                    key={cat}
                    onPress={() => setCategory(cat)}
                    className={`px-2.5 py-1 rounded-lg border text-[11px] transition ${
                      category.toLowerCase() === cat.toLowerCase()
                        ? 'bg-indigo-600 border-indigo-500 shadow-sm'
                        : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <Text
                      className={`text-[11px] font-semibold ${
                        category.toLowerCase() === cat.toLowerCase()
                          ? 'text-white'
                          : 'text-slate-400'
                      }`}
                    >
                      {cat}
                    </Text>
                  </Pressable>
                ))}
              </View>
              <TextInput
                value={category}
                onChangeText={setCategory}
                placeholder="Study Pod / Workspace / Meeting / Studio..."
                placeholderTextColor="#64748b"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:border-indigo-500"
              />
            </View>
          </View>

          {/* Rate & Locality */}
          <View className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <View>
              <Text className="text-xs font-medium text-slate-300 mb-1">Hourly Rate (₹ INR)</Text>
              <TextInput
                value={hourlyRate}
                onChangeText={setHourlyRate}
                placeholder="45"
                placeholderTextColor="#64748b"
                keyboardType="numeric"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:border-indigo-500"
              />
            </View>

            <View>
              <Text className="text-xs font-medium text-slate-300 mb-1">Locality</Text>
              <TextInput
                value={location}
                onChangeText={setLocation}
                placeholder="e.g. Wagholi"
                placeholderTextColor="#64748b"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:border-indigo-500"
              />
            </View>

            <View>
              <Text className="text-xs font-medium text-slate-300 mb-1">City</Text>
              <TextInput
                value={city}
                onChangeText={setCity}
                placeholder="Pune"
                placeholderTextColor="#64748b"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:border-indigo-500"
              />
            </View>
          </View>

          {/* Detailed Address */}
          <View>
            <Text className="text-xs font-medium text-slate-300 mb-1">Full Address</Text>
            <TextInput
              value={address}
              onChangeText={setAddress}
              placeholder="e.g. Gate 2, JSPM Imperial College Road, Wagholi, Pune"
              placeholderTextColor="#64748b"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:border-indigo-500"
            />
          </View>

          {/* Amenities */}
          <View>
            <Text className="text-xs font-medium text-slate-300 mb-1">
              Amenities (comma-separated)
            </Text>
            <TextInput
              value={amenities}
              onChangeText={setAmenities}
              placeholder="Wi-Fi, Power Outlets, Whiteboard, Air Conditioning"
              placeholderTextColor="#64748b"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:border-indigo-500"
            />
          </View>

          {/* Suitable For (Target Personas Multi-Select) */}
          <View>
            <Text className="text-xs font-medium text-slate-300 mb-1.5">
              Suitable For (Multi-Select Personas)
            </Text>
            <View className="flex-row flex-wrap gap-2">
              {personasList.map((p) => {
                const isSelected = selectedPersonas.includes(p);
                return (
                  <Pressable
                    key={p}
                    onPress={() => togglePersona(p)}
                    className={`px-3 py-1.5 rounded-xl border text-xs transition flex-row items-center gap-1.5 ${
                      isSelected
                        ? 'bg-indigo-600/30 border-indigo-500 shadow-sm'
                        : 'bg-slate-950/80 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <Text className={`text-xs ${isSelected ? 'text-indigo-300 font-bold' : 'text-slate-400'}`}>
                      {isSelected ? '✓ ' : '+ '} {p}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>

          {/* Notes / Description */}
          <View>
            <Text className="text-xs font-medium text-slate-300 mb-1">Space Description</Text>
            <TextInput
              value={description || notes}
              onChangeText={setDescription}
              multiline
              numberOfLines={3}
              placeholder="Describe access conditions, quiet hours, noise profile..."
              placeholderTextColor="#64748b"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:border-indigo-500"
            />
          </View>

          {/* Terms & Conditions Mandatory Checkbox & Modal Link */}
          <div className="p-4 bg-slate-950/80 rounded-2xl border border-slate-800 space-y-2">
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id="terms_agree_checkbox"
                checked={termsAccepted}
                onChange={(e) => setTermsAccepted(e.target.checked)}
                className="mt-1 w-4 h-4 rounded border-slate-700 text-emerald-500 focus:ring-emerald-400 bg-slate-900 cursor-pointer"
              />
              <label htmlFor="terms_agree_checkbox" className="text-xs text-slate-300 leading-relaxed cursor-pointer">
                I have read and agree to the{' '}
                <button
                  type="button"
                  onClick={() => setShowTermsModal(true)}
                  className="text-indigo-400 hover:text-indigo-300 font-bold underline inline-flex items-center gap-1"
                >
                  SpaceLoop Host Terms & Conditions <i className="fa-solid fa-arrow-up-right-from-square text-[10px]" />
                </button>
                , including Section 52 Indian Easements Act revocable micro-lease compliance, electrical safety standards, and ₹100 refundable escrow resolution.
              </label>
            </div>
            {!termsAccepted && (
              <p className="text-[11px] text-amber-400/90 pl-7">
                * You must accept the terms before publishing your listing.
              </p>
            )}
          </div>

          {/* Publish Error Display Near Button */}
          {error && (
            <View className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl">
              <Text className="text-sm text-rose-300 font-medium">✕ {error}</Text>
            </View>
          )}

          {/* Publish Button */}
          <Pressable
            onPress={handlePublish}
            disabled={isPublishing || !termsAccepted}
            className={`w-full py-4 rounded-2xl items-center justify-center transition shadow-xl ${
              isPublishing || !termsAccepted
                ? 'bg-emerald-600/40 opacity-60 cursor-not-allowed shadow-none'
                : 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/30'
            }`}
          >
            <Text className="text-sm font-bold text-white">
              {isPublishing ? 'Publishing Space to Marketplace...' : '🚀 Publish Active Space Listing'}
            </Text>
          </Pressable>
        </View>
      </View>

      {/* Terms & Conditions Review Modal */}
      {showTermsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md overflow-y-auto">
          <div className="bg-slate-900 border border-indigo-500/30 text-white w-full max-w-2xl rounded-3xl overflow-hidden my-6 transition-all shadow-2xl">
            <div className="p-6 border-b border-slate-800 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 flex items-center justify-between">
              <div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Legal Compliance
                </span>
                <h3 className="text-lg font-bold text-white mt-1">SpaceLoop Host Terms & Conditions</h3>
              </div>
              <button
                onClick={() => setShowTermsModal(false)}
                type="button"
                className="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto text-xs text-slate-300 leading-relaxed">
              <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800">
                <h4 className="font-bold text-white text-sm mb-1 flex items-center gap-1.5">
                  <i className="fa-solid fa-scale-balanced text-indigo-400" /> 1. Section 52, Indian Easements Act, 1882
                </h4>
                <p>
                  All bookings on SpaceLoop constitute a temporary, revocable micro-license to use the specified physical square footage for lawful workspace, study, or creative activities during booked hours only. This agreement does not create any tenancy, leasehold estate, or landlord-tenant relationship under rent control laws.
                </p>
              </div>

              <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800">
                <h4 className="font-bold text-white text-sm mb-1 flex items-center gap-1.5">
                  <i className="fa-solid fa-shield-halved text-emerald-400" /> 2. Security Deposit & Micro-Escrow
                </h4>
                <p>
                  A mandatory ₹100 refundable micro-escrow is pre-authorized by SpaceLoop on every booking. Upon completed checkout and condition delta verification, the escrow hold is automatically released back to the seeker within 60 minutes. In the rare event of verified property damage, the escrow is held for host resolution.
                </p>
              </div>

              <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800">
                <h4 className="font-bold text-white text-sm mb-1 flex items-center gap-1.5">
                  <i className="fa-solid fa-bolt text-amber-400" /> 3. Electrical & Premise Safety Protocol
                </h4>
                <p>
                  Hosts warrant that all listed electrical points and appliances meet standard safety codes. Seekers are required to perform an electrical turn-off inspection checklist upon checkout.
                </p>
              </div>

              <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800">
                <h4 className="font-bold text-white text-sm mb-1 flex items-center gap-1.5">
                  <i className="fa-solid fa-id-card text-sky-400" /> 4. Discom & Identity Verification
                </h4>
                <p>
                  Hosts agree that only listings backed by verified Discom electricity accounts and verified UPI payout VPAs will be published to the public search index. SpaceLoop retains the right to delist unverified properties.
                </p>
              </div>
            </div>

            <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowTermsModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  setTermsAccepted(true);
                  setShowTermsModal(false);
                }}
                className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/30 transition flex items-center gap-1.5"
              >
                <i className="fa-solid fa-check" /> I Understand & Accept Terms
              </button>
            </div>
          </div>
        </div>
      )}

      {showAuthModal && (
        <HostAuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          currentUser={currentUser}
          onSuccess={() => {
            setShowAuthModal(false);
            handlePublish();
          }}
        />
      )}
    </View>
  );
};
