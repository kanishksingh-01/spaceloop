import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { User } from '../../types';
import { demoSwitch } from '../../services/auth';

interface DemoBarProps {
  currentUser: User | null;
  onUserChange: (user: User | null) => void;
}

export const DemoBar: React.FC<DemoBarProps> = ({ currentUser, onUserChange }) => {
  const handleSwitch = async (role: 'seeker' | 'host' | 'admin' | 'guest') => {
    try {
      await demoSwitch(role);
      // Trigger full page re-sync or callback
      window.location.reload();
    } catch (err) {
      console.error('Failed to switch persona:', err);
    }
  };

  const currentRole = currentUser?.role || 'guest';

  return (
    <View className="bg-slate-900/95 border-b border-indigo-500/20 py-1.5 px-4">
      <View className="max-w-7xl mx-auto flex-row items-center justify-between flex-wrap gap-2">
        <View className="flex-row items-center gap-2">
          <View className="w-2 h-2 rounded-full bg-emerald-400" />
          <Text className="text-xs font-semibold text-indigo-300">
            Hackathon Demo Switcher:
          </Text>
          <View className="bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/30">
            <Text className="text-[11px] font-bold text-indigo-200 uppercase">
              Current: {currentUser ? `${currentUser.name} (${currentUser.role})` : 'Guest (Unauthenticated)'}
            </Text>
          </View>
        </View>

        <View className="flex-row items-center gap-1.5 flex-wrap">
          <Pressable
            onPress={() => handleSwitch('seeker')}
            className={`px-2.5 py-1 rounded-lg border text-xs font-medium transition ${
              currentRole === 'seeker'
                ? 'bg-indigo-600 border-indigo-400 text-white'
                : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <Text className="text-xs font-medium text-slate-200">
              👤 Aarav (Seeker)
            </Text>
          </Pressable>

          <Pressable
            onPress={() => handleSwitch('host')}
            className={`px-2.5 py-1 rounded-lg border text-xs font-medium transition ${
              currentRole === 'host'
                ? 'bg-indigo-600 border-indigo-400 text-white'
                : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <Text className="text-xs font-medium text-slate-200">
              🏠 Sunita (Host)
            </Text>
          </Pressable>

          <Pressable
            onPress={() => handleSwitch('admin')}
            className={`px-2.5 py-1 rounded-lg border text-xs font-medium transition ${
              currentRole === 'admin'
                ? 'bg-indigo-600 border-indigo-400 text-white'
                : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <Text className="text-xs font-medium text-slate-200">
              👑 Admin
            </Text>
          </Pressable>

          <Pressable
            onPress={() => handleSwitch('guest')}
            className={`px-2.5 py-1 rounded-lg border text-xs font-medium transition ${
              currentRole === 'guest'
                ? 'bg-rose-600/30 border-rose-500 text-rose-200'
                : 'bg-slate-800/80 border-slate-700 text-slate-400 hover:bg-slate-700'
            }`}
          >
            <Text className="text-xs font-medium text-slate-300">
              🚪 Guest
            </Text>
          </Pressable>
        </View>
      </View>
    </View>
  );
};
