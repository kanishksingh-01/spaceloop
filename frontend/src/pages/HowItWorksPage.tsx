import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useNavigate } from 'react-router-dom';

export const HowItWorksPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <View className="min-h-screen bg-slate-950 pb-20">
      <View className="bg-slate-900 border-b border-slate-800 py-12 px-4 text-center">
        <View className="max-w-4xl mx-auto">
          <View className="inline-flex flex-row items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 mb-3 self-center">
            <Text className="text-xs font-bold text-indigo-300">
              ⚡ The SpaceLoop Protocol
            </Text>
          </View>
          <Text className="text-3xl sm:text-4xl font-black text-white mb-2">
            How SpaceLoop Works
          </Text>
          <Text className="text-sm text-slate-400 max-w-xl mx-auto">
            Converting urban dead space into liquid temporary value in 3 simple steps without expensive smart locks or hardware.
          </Text>
        </View>
      </View>

      <View className="max-w-5xl mx-auto px-4 sm:px-6 mt-10 space-y-12">
        {/* For Seekers */}
        <View className="space-y-6">
          <View className="flex-row items-center gap-2">
            <Text className="text-2xl">🎓</Text>
            <Text className="text-xl font-bold text-white">For Students, Creators & Seekers</Text>
          </View>

          <View className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <View className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
              <Text className="text-3xl font-black text-indigo-400 mb-2">01</Text>
              <Text className="text-base font-bold text-white mb-1">Natural Language AI Search</Text>
              <Text className="text-xs text-slate-400 leading-relaxed">
                Describe your exact need, e.g. "quiet study nook in Wagholi with power strips under ₹50". Our LLM matches acoustics, proximity, and amenities.
              </Text>
            </View>

            <View className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
              <Text className="text-3xl font-black text-indigo-400 mb-2">02</Text>
              <Text className="text-base font-bold text-white mb-1">₹100 UPI Micro-Escrow</Text>
              <Text className="text-xs text-slate-400 leading-relaxed">
                Instant booking generates a legal micro-license under the Indian Easements Act, 1882. A flat ₹100 deposit is held safely in escrow.
              </Text>
            </View>

            <View className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
              <Text className="text-3xl font-black text-indigo-400 mb-2">03</Text>
              <Text className="text-base font-bold text-white mb-1">Zero-Hardware Door Pass</Text>
              <Text className="text-xs text-slate-400 leading-relaxed">
                Arrive at the location. Your smartphone GPS confirms the 50m geofence, unlocks the QR door pass, and checks you out automatically.
              </Text>
            </View>
          </View>
        </View>

        {/* For Hosts */}
        <View className="space-y-6">
          <View className="flex-row items-center gap-2">
            <Text className="text-2xl">🏠</Text>
            <Text className="text-xl font-bold text-white">For Property Owners & Hosts</Text>
          </View>

          <View className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <View className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
              <Text className="text-3xl font-black text-emerald-400 mb-2">01</Text>
              <Text className="text-base font-bold text-white mb-1">Multimodal AI Inspection</Text>
              <Text className="text-xs text-slate-400 leading-relaxed">
                Snap one photo of your space. Vision models calculate square footage, ambient decibels, and generate a listing title and amenities.
              </Text>
            </View>

            <View className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
              <Text className="text-3xl font-black text-emerald-400 mb-2">02</Text>
              <Text className="text-base font-bold text-white mb-1">Zero-Hardware Gate Protocol</Text>
              <Text className="text-xs text-slate-400 leading-relaxed">
                No expensive smart locks or IoT hubs. Print our tamper-resistant door sign QR code. Guests authenticate via phone GPS handshakes.
              </Text>
            </View>

            <View className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
              <Text className="text-3xl font-black text-emerald-400 mb-2">03</Text>
              <Text className="text-base font-bold text-white mb-1">Guaranteed Payouts</Text>
              <Text className="text-xs text-slate-400 leading-relaxed">
                Direct UPI transfers directly to your bank upon session conclusion. Zero tenant rights or multi-month holdover risks under Section 52.
              </Text>
            </View>
          </View>
        </View>

        {/* Call to action */}
        <View className="p-8 bg-gradient-to-r from-indigo-900/40 via-purple-900/40 to-slate-900 rounded-3xl border border-indigo-500/30 text-center items-center">
          <Text className="text-2xl font-black text-white mb-2">
            Ready to Turn Dead Space into Living Value?
          </Text>
          <Text className="text-xs text-slate-300 max-w-md mb-6">
            Join thousands of verified students, creators, and property owners across Pune, Delhi, and Bengaluru.
          </Text>
          <View className="flex-row gap-3">
            <Pressable
              onPress={() => navigate('/')}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 rounded-xl"
            >
              <Text className="text-xs font-bold text-white">Find a Space</Text>
            </Pressable>
            <Pressable
              onPress={() => navigate('/list-space')}
              className="px-6 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl"
            >
              <Text className="text-xs font-bold text-slate-200">List Your Space</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </View>
  );
};
