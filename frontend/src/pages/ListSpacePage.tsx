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
  const [error, setError] = useState<string | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);

  const presets = [
    {
      label: 'Wagholi Study Pod (Pune)',
      photo: 'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=800&q=80',
      category: 'Study Pod',
      title: 'Acoustic Study Pod near JSPM',
      location: 'Wagholi',
      address: 'Gate 2, JSPM Imperial College Road, Wagholi, Pune',
      city: 'Pune',
      rate: '45',
      notes: 'Calm study nook with ergonomic chair, high-speed fiber Wi-Fi, and 20A grounded plug.',
    },
    {
      label: 'Koramangala Storage (Bengaluru)',
      photo: 'https://images.unsplash.com/photo-1588854337236-6889d631faa8?auto=format&fit=crop&w=800&q=80',
      category: 'Storage',
      title: 'Clean Ground Floor Garage Storage',
      location: 'Koramangala',
      address: '80 Feet Road, 4th Block, Bengaluru',
      city: 'Bengaluru',
      rate: '65',
      notes: 'Dry, CCTV-monitored ground floor space with roll-up metal shutter for inventory.',
    },
    {
      label: 'Hauz Khas Studio (Delhi)',
      photo: 'https://images.unsplash.com/photo-1590674899484-d5640e854abe?auto=format&fit=crop&w=800&q=80',
      category: 'Studio',
      title: 'Sound-Treated Creator Studio',
      location: 'Hauz Khas',
      address: 'C-14 Hauz Khas Enclave, New Delhi',
      city: 'Delhi',
      rate: '95',
      notes: 'Acoustic foam wall panelling, ring light, dedicated high-amperage audio circuit.',
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
    setNotes(p.notes);
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
      if (res.scan) {
        if (res.scan.title) setTitle(res.scan.title);
        if (res.scan.description) setDescription(res.scan.description);
        if (res.scan.suggested_price) setHourlyRate(String(res.scan.suggested_price));
        if (res.scan.amenities) setAmenities(res.scan.amenities.join(', '));
        setScanMessage('✨ AI Multimodal analysis complete! Title, specs, and price suggested.');
      } else {
        setScanMessage('✨ AI analysis applied based on photo and notes.');
      }
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

      const res = await createSpace({
        title,
        description: description || notes,
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
          <View className="grid grid-cols-1 sm:grid-cols-3 gap-3">
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
              <TextInput
                value={category}
                onChangeText={setCategory}
                placeholder="Study Pod / Storage / Studio / Parking"
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
