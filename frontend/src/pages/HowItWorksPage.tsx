import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../i18n';

export const HowItWorksPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <View className="min-h-screen bg-slate-950 pb-20">
      <View className="bg-slate-900 border-b border-slate-800 py-12 px-4 text-center">
        <View className="max-w-4xl mx-auto">
          <View className="inline-flex flex-row items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 mb-3 self-center">
            <Text className="text-xs font-bold text-indigo-300">
              ⚡ {t('howItWorks.instantUpiGuarantee')}
            </Text>
          </View>
          <Text className="text-3xl sm:text-4xl font-black text-white mb-2">
            {t('howItWorks.title')}
          </Text>
          <Text className="text-sm text-slate-400 max-w-xl mx-auto">
            {t('howItWorks.subtitle')}
          </Text>
        </View>
      </View>

      <View className="max-w-5xl mx-auto px-4 sm:px-6 mt-10 space-y-12">
        {/* For Seekers */}
        <View className="space-y-6">
          <View className="flex-row items-center gap-2">
            <Text className="text-2xl">⚡</Text>
            <Text className="text-xl font-bold text-white">{t('landing.spacesTitle')}</Text>
          </View>

          <View className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <View className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
              <Text className="text-3xl font-black text-indigo-400 mb-2">01</Text>
              <Text className="text-base font-bold text-white mb-1">{t('howItWorks.step1Title')}</Text>
              <Text className="text-xs text-slate-400 leading-relaxed">
                {t('howItWorks.step1Desc')}
              </Text>
            </View>

            <View className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
              <Text className="text-3xl font-black text-indigo-400 mb-2">02</Text>
              <Text className="text-base font-bold text-white mb-1">{t('howItWorks.step2Title')}</Text>
              <Text className="text-xs text-slate-400 leading-relaxed">
                {t('howItWorks.step2Desc')}
              </Text>
            </View>

            <View className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
              <Text className="text-3xl font-black text-indigo-400 mb-2">03</Text>
              <Text className="text-base font-bold text-white mb-1">{t('howItWorks.step3Title')}</Text>
              <Text className="text-xs text-slate-400 leading-relaxed">
                {t('howItWorks.step3Desc')}
              </Text>
            </View>

            <View className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
              <Text className="text-3xl font-black text-indigo-400 mb-2">04</Text>
              <Text className="text-base font-bold text-white mb-1">{t('howItWorks.step4Title')}</Text>
              <Text className="text-xs text-slate-400 leading-relaxed">
                {t('howItWorks.step4Desc')}
              </Text>
            </View>
          </View>
        </View>

        {/* Guarantees Ribbon */}
        <View className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <View className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex-row items-center gap-3">
            <Text className="text-xl">🛡️</Text>
            <Text className="text-xs font-semibold text-slate-200">{t('howItWorks.sec52Guarantee')}</Text>
          </View>
          <View className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex-row items-center gap-3">
            <Text className="text-xl">📍</Text>
            <Text className="text-xs font-semibold text-slate-200">{t('howItWorks.zeroHardwareGuarantee')}</Text>
          </View>
          <View className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex-row items-center gap-3">
            <Text className="text-xl">⚡</Text>
            <Text className="text-xs font-semibold text-slate-200">{t('howItWorks.instantUpiGuarantee')}</Text>
          </View>
        </View>

        {/* Call to action */}
        <View className="p-8 bg-gradient-to-r from-indigo-900/40 via-purple-900/40 to-slate-900 rounded-3xl border border-indigo-500/30 text-center items-center">
          <Text className="text-2xl font-black text-white mb-2">
            {t('landing.ctaTitle')}
          </Text>
          <Text className="text-xs text-slate-300 max-w-md mb-6">
            {t('landing.ctaSubtitle')}
          </Text>
          <View className="flex-row gap-3">
            <Pressable
              onPress={() => navigate('/explore')}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 rounded-xl"
            >
              <Text className="text-xs font-bold text-white">{t('howItWorks.getStartedCTA')}</Text>
            </Pressable>
            <Pressable
              onPress={() => navigate('/list-space')}
              className="px-6 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl"
            >
              <Text className="text-xs font-bold text-slate-200">{t('landing.ctaHostBtn')}</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </View>
  );
};
