import React, { useState } from 'react';
import { View, Text, Pressable, TextInput, Image, ScrollView } from 'react-native';
import { useNavigate } from 'react-router-dom';
import { aiScanSpace, createSpace } from '../services/spaces';
import { HostAuthModal } from '../components/common/HostAuthModal';
import { User } from '../types';

interface ListSpacePageProps {
  currentUser: User | null;
}

export const ListSpacePage: React.FC<ListSpacePageProps> = ({ currentUser }) => {
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('Study Pod');
  const [hourlyRate, setHourlyRate] = useState('45');
  const [location, setLocation] = useState('Wagholi');
  const [address, setAddress] = useState('Near JSPM Imperial College, Wagholi, Pune');
  const [city, setCity] = useState('Pune');
  const [photoUrl, setPhotoUrl] = useState(
    'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=800&q=80'
  );
  const [amenities, setAmenities] = useState('Wi-Fi, Power Outlets, Whiteboard, Quiet Zone');
  const [notes, setNotes] = useState('Sunlit room with good air ventilation, ideal for exam prep or focused coding.');

  const [isScanning, setIsScanning] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [scanMessage, setScanMessage] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [selectedPersonas, setSelectedPersonas] = useState<string[]>([]);

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

  const handlePublish = async () => {
    if (isPublishing) return;
    if (!currentUser || !currentUser.is_host) {
      setShowAuthModal(true);
      return;
    }
    if (!title || !hourlyRate || !location) {
      setError('Please fill in title, rate, and locality');
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
        title,
        description: finalDesc,
        category,
        hourly_rate: Number(hourlyRate),
        price_hourly: Number(hourlyRate),
        location,
        neighborhood: location,
        address,
        city,
        photos: [photoUrl],
        amenities: amenityArray,
        latitude: city === 'Pune' ? 18.5793 : city === 'Delhi' ? 28.5494 : 12.9352,
        longitude: city === 'Pune' ? 73.9825 : city === 'Delhi' ? 77.2001 : 77.6245,
      });

      const spaceId = res.space_id || (res as any).id;
      if (spaceId) {
        navigate(`/space/${spaceId}`);
      } else {
        navigate('/dashboard');
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

          {/* Photo URL & AI Scanner Button */}
          <View className="space-y-2">
            <Text className="text-xs font-medium text-slate-300">Space Photo URL</Text>
            <View className="flex-col sm:flex-row gap-2">
              <TextInput
                value={photoUrl}
                onChangeText={setPhotoUrl}
                placeholder="Paste an image URL..."
                placeholderTextColor="#64748b"
                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:border-indigo-500"
              />
              <Pressable
                onPress={handleAiScan}
                disabled={isScanning}
                className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl items-center justify-center transition shadow-md"
              >
                <Text className="text-xs font-bold text-white">
                  {isScanning ? 'Inspecting...' : '⚡ Scan with AI'}
                </Text>
              </Pressable>
            </View>
          </View>

          {/* Image Preview */}
          {photoUrl && (
            <View className="w-full h-48 rounded-xl overflow-hidden bg-slate-950 border border-slate-800">
              <Image source={{ uri: photoUrl }} className="w-full h-full object-cover" />
            </View>
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

          {/* Publish Error Display Near Button */}
          {error && (
            <View className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl">
              <Text className="text-sm text-rose-300 font-medium">✕ {error}</Text>
            </View>
          )}

          {/* Publish Button */}
          <Pressable
            onPress={handlePublish}
            disabled={isPublishing}
            className={`w-full py-4 rounded-2xl items-center justify-center transition shadow-xl ${
              isPublishing
                ? 'bg-emerald-600/60 cursor-not-allowed shadow-none'
                : 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/30'
            }`}
          >
            <Text className="text-sm font-bold text-white">
              {isPublishing ? 'Publishing Space to Marketplace...' : '🚀 Publish Active Space Listing'}
            </Text>
          </Pressable>
        </View>
      </View>

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
