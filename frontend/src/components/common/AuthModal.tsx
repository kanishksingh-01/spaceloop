import React, { useState } from 'react';
import { View, Text, Pressable, TextInput } from 'react-native';
import { demoSwitch, loginUser } from '../../services/auth';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleDemoLogin = async (role: 'seeker' | 'host' | 'admin') => {
    setLoading(true);
    setError(null);
    try {
      await demoSwitch(role);
      if (onSuccess) onSuccess();
      window.location.reload();
    } catch (err: any) {
      setError(err.message || 'Failed to authenticate demo persona');
      setLoading(false);
    }
  };

  const handleStandardLogin = async () => {
    if (!email || !password) {
      setError('Please enter both email and password');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await loginUser(email, password);
      if (onSuccess) onSuccess();
      window.location.reload();
    } catch (err: any) {
      setError(err.message || 'Invalid credentials');
      setLoading(false);
    }
  };

  return (
    <View className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm items-center justify-center p-4">
      <View className="bg-slate-900 border border-slate-800 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden p-6">
        <View className="flex-row items-center justify-between pb-4 border-b border-slate-800">
          <View>
            <Text className="text-lg font-bold text-white">Sign In to SpaceLoop</Text>
            <Text className="text-xs text-slate-400">Access instant booking, hosting & leases</Text>
          </View>
          <Pressable onPress={onClose} className="p-1 text-slate-400 hover:text-white">
            <Text className="text-base font-bold">✕</Text>
          </Pressable>
        </View>

        {error && (
          <View className="mt-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl">
            <Text className="text-xs text-rose-300 font-medium">{error}</Text>
          </View>
        )}

        {/* 1-Click Demo Personas */}
        <View className="mt-5 space-y-2">
          <Text className="text-xs font-semibold text-indigo-300 uppercase tracking-wider">
            1-Click Demo Personas
          </Text>
          <Pressable
            onPress={() => handleDemoLogin('seeker')}
            disabled={loading}
            className="flex-row items-center justify-between p-3 rounded-xl bg-slate-800/90 border border-slate-700 hover:border-indigo-500 transition"
          >
            <View>
              <Text className="text-sm font-bold text-white">👤 Aarav Sharma (Seeker)</Text>
              <Text className="text-xs text-slate-400">Verified Student • IIT Delhi • 840 Trust</Text>
            </View>
            <Text className="text-xs font-semibold text-indigo-400">Instant Login →</Text>
          </Pressable>

          <Pressable
            onPress={() => handleDemoLogin('host')}
            disabled={loading}
            className="flex-row items-center justify-between p-3 rounded-xl bg-slate-800/90 border border-slate-700 hover:border-indigo-500 transition"
          >
            <View>
              <Text className="text-sm font-bold text-white">🏠 Sunita Deshmukh (Host)</Text>
              <Text className="text-xs text-slate-400">Property Owner • Wagholi, Pune • ₹18.4k Earned</Text>
            </View>
            <Text className="text-xs font-semibold text-indigo-400">Instant Login →</Text>
          </Pressable>
        </View>

        <View className="my-5 flex-row items-center">
          <View className="flex-1 h-px bg-slate-800" />
          <Text className="px-3 text-xs text-slate-500 font-medium uppercase">Or Credentials</Text>
          <View className="flex-1 h-px bg-slate-800" />
        </View>

        {/* Standard Form */}
        <View className="space-y-3">
          <View>
            <Text className="text-xs font-medium text-slate-300 mb-1">Email Address</Text>
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="e.g. user@spaceloop.in"
              placeholderTextColor="#64748b"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:border-indigo-500"
            />
          </View>
          <View>
            <Text className="text-xs font-medium text-slate-300 mb-1">Password</Text>
            <TextInput
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              placeholder="••••••••"
              placeholderTextColor="#64748b"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:border-indigo-500"
            />
          </View>
          <Pressable
            onPress={handleStandardLogin}
            disabled={loading}
            className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl items-center justify-center transition shadow-lg shadow-indigo-600/30"
          >
            <Text className="text-sm font-semibold text-white">
              {loading ? 'Authenticating...' : 'Sign In'}
            </Text>
          </Pressable>
        </View>
      </View>
    </View>
  );
};
