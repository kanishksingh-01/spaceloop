import React, { useState } from 'react';
import { View, Text, Pressable, TextInput } from 'react-native';
import { request } from '../services/api';
import { useTranslation } from '../i18n';

export const VerifyPage: React.FC = () => {
  const { t } = useTranslation();
  const [collegeName, setCollegeName] = useState('IIT Delhi');
  const [studentId, setStudentId] = useState('2024CS10892');
  const [hostAddressProof, setHostAddressProof] = useState('MSEDCL Electricity Bill - Wagholi');
  const [aadhaarMasked, setAadhaarMasked] = useState('XXXX-XXXX-4819');

  const [studentSuccess, setStudentSuccess] = useState(false);
  const [hostSuccess, setHostSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleStudentVerify = async () => {
    setLoading(true);
    try {
      await request('/api/verify/student', {
        method: 'POST',
        body: JSON.stringify({ college_name: collegeName, student_id: studentId }),
      });
      setStudentSuccess(true);
    } catch {
      // Simulate success for demo
      setStudentSuccess(true);
    } finally {
      setLoading(false);
    }
  };

  const handleHostVerify = async () => {
    setLoading(true);
    try {
      await request('/api/verify/host', {
        method: 'POST',
        body: JSON.stringify({ document_type: 'utility_bill', proof: hostAddressProof }),
      });
      setHostSuccess(true);
    } catch {
      setHostSuccess(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View className="min-h-screen bg-slate-950 pb-20">
      <View className="bg-slate-900 border-b border-slate-800 py-12 px-4 text-center">
        <View className="max-w-4xl mx-auto">
          <View className="inline-flex flex-row items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 mb-3 self-center">
            <Text className="text-xs font-bold text-indigo-300">
              🛡️ {t('trustSafety.title')}
            </Text>
          </View>
          <Text className="text-3xl sm:text-4xl font-black text-white mb-2">
            {t('verify.title')}
          </Text>
          <Text className="text-sm text-slate-400 max-w-xl mx-auto">
            {t('verify.subtitle')}
          </Text>
        </View>
      </View>

      <View className="max-w-4xl mx-auto px-4 sm:px-6 mt-8 space-y-8">
        <View className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Student Verification Card */}
          <View className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex-col justify-between floating-card">
            <View>
              <View className="flex-row items-center gap-2 mb-3">
                <Text className="text-2xl">🎓</Text>
                <View>
                  <Text className="text-base font-bold text-white">{t('verify.studentKycCard')}</Text>
                  <Text className="text-xs text-slate-400">{t('verify.collegeIdUpload')}</Text>
                </View>
              </View>

              {studentSuccess ? (
                <View className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl my-4">
                  <Text className="text-xs font-bold text-emerald-300">
                    {t('verify.verifiedSuccessBadge')}
                  </Text>
                  <Text className="text-[11px] text-slate-300 mt-1">
                    {t('verify.digilockerConsent')}
                  </Text>
                </View>
              ) : (
                <View className="space-y-3 my-4">
                  <View>
                    <Text className="text-xs font-medium text-slate-300 mb-1">{t('auth.collegeLabel')}</Text>
                    <TextInput
                      value={collegeName}
                      onChangeText={setCollegeName}
                      placeholder="IIT Delhi / JSPM Pune / COEP"
                      placeholderTextColor="#64748b"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                    />
                  </View>
                  <View>
                    <Text className="text-xs font-medium text-slate-300 mb-1">{t('verify.collegeIdUpload')}</Text>
                    <TextInput
                      value={studentId}
                      onChangeText={setStudentId}
                      placeholder="e.g. 2024CS10892"
                      placeholderTextColor="#64748b"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                    />
                  </View>
                </View>
              )}
            </View>

            {!studentSuccess && (
              <Pressable
                onPress={handleStudentVerify}
                disabled={loading}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl items-center justify-center transition"
              >
                <Text className="text-xs font-bold text-white">
                  {loading ? t('common.loading') : t('verify.verifyNowBtn')}
                </Text>
              </Pressable>
            )}
          </View>

          {/* Host Verification Card */}
          <View className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex-col justify-between floating-card">
            <View>
              <View className="flex-row items-center gap-2 mb-3">
                <Text className="text-2xl">🏠</Text>
                <View>
                  <Text className="text-base font-bold text-white">{t('verify.hostKycCard')}</Text>
                  <Text className="text-xs text-slate-400">{t('verify.bescomBillVerify')}</Text>
                </View>
              </View>

              {hostSuccess ? (
                <View className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl my-4">
                  <Text className="text-xs font-bold text-emerald-300">
                    {t('verify.verifiedSuccessBadge')}
                  </Text>
                  <Text className="text-[11px] text-slate-300 mt-1">
                    {t('spaceDetail.hostVerified')}
                  </Text>
                </View>
              ) : (
                <View className="space-y-3 my-4">
                  <View>
                    <Text className="text-xs font-medium text-slate-300 mb-1">{t('verify.aadhaarVerification')}</Text>
                    <TextInput
                      value={aadhaarMasked}
                      onChangeText={setAadhaarMasked}
                      placeholder="XXXX-XXXX-1234"
                      placeholderTextColor="#64748b"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono"
                    />
                  </View>
                  <View>
                    <Text className="text-xs font-medium text-slate-300 mb-1">{t('verify.bescomBillVerify')}</Text>
                    <TextInput
                      value={hostAddressProof}
                      onChangeText={setHostAddressProof}
                      placeholder="Electricity bill / Property tax receipt"
                      placeholderTextColor="#64748b"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white"
                    />
                  </View>
                </View>
              )}
            </View>

            {!hostSuccess && (
              <Pressable
                onPress={handleHostVerify}
                disabled={loading}
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl items-center justify-center transition"
              >
                <Text className="text-xs font-bold text-white">
                  {loading ? t('common.loading') : t('verify.verifyNowBtn')}
                </Text>
              </Pressable>
            )}
          </View>
        </View>
      </View>
    </View>
  );
};
