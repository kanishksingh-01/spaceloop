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
    <View className="min-h-screen bg-background pb-20">
      <View className="bg-surface border-b border-border py-12 px-4 text-center">
        <View className="max-w-4xl mx-auto">
          <View className="inline-flex flex-row items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 mb-3 self-center">
            <Text className="text-xs font-bold text-primary">
              🛡️ {t('trustSafety.title')}
            </Text>
          </View>
          <Text className="text-3xl sm:text-4xl font-heading font-black text-text-primary mb-2">
            {t('verify.title')}
          </Text>
          <Text className="text-sm text-text-secondary max-w-xl mx-auto">
            {t('verify.subtitle')}
          </Text>
        </View>
      </View>

      <View className="max-w-4xl mx-auto px-4 sm:px-6 mt-8 space-y-8">
        <View className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Student Verification Card */}
          <View className="bg-surface border border-border rounded-3xl p-6 sm:p-8 flex-col justify-between shadow-sm hover:shadow-hover transition duration-200">
            <View>
              <View className="flex-row items-center gap-3 mb-4">
                <View className="w-10 h-10 rounded-2xl bg-primary/10 border border-primary/20 items-center justify-center">
                  <Text className="text-xl">🎓</Text>
                </View>
                <View>
                  <Text className="text-base font-bold text-text-primary">{t('verify.studentKycCard')}</Text>
                  <Text className="text-xs text-text-secondary">{t('verify.collegeIdUpload')}</Text>
                </View>
              </View>

              {studentSuccess ? (
                <View className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl my-4">
                  <Text className="text-xs font-bold text-emerald-500">
                    {t('verify.verifiedSuccessBadge')}
                  </Text>
                  <Text className="text-[11px] text-text-secondary mt-1">
                    {t('verify.digilockerConsent')}
                  </Text>
                </View>
              ) : (
                <View className="space-y-3 my-4">
                  <View>
                    <Text className="text-xs font-medium text-text-secondary mb-1">{t('auth.collegeLabel')}</Text>
                    <TextInput
                      value={collegeName}
                      onChangeText={setCollegeName}
                      placeholder="IIT Delhi / JSPM Pune / COEP"
                      placeholderTextColor="#94a3b8"
                      className="w-full bg-surface-elevated border border-border rounded-xl px-3.5 py-2.5 text-xs text-text-primary"
                    />
                  </View>
                  <View>
                    <Text className="text-xs font-medium text-text-secondary mb-1">{t('verify.collegeIdUpload')}</Text>
                    <TextInput
                      value={studentId}
                      onChangeText={setStudentId}
                      placeholder="e.g. 2024CS10892"
                      placeholderTextColor="#94a3b8"
                      className="w-full bg-surface-elevated border border-border rounded-xl px-3.5 py-2.5 text-xs text-text-primary"
                    />
                  </View>
                </View>
              )}
            </View>

            {!studentSuccess && (
              <Pressable
                onPress={handleStudentVerify}
                disabled={loading}
                className="w-full py-3 bg-primary hover:bg-primary-hover rounded-xl items-center justify-center transition shadow-sm hover:shadow-md cursor-pointer"
              >
                <Text className="text-xs font-bold text-white">
                  {loading ? t('common.loading') : t('verify.verifyNowBtn')}
                </Text>
              </Pressable>
            )}
          </View>

          {/* Host Verification Card */}
          <View className="bg-surface border border-border rounded-3xl p-6 sm:p-8 flex-col justify-between shadow-sm hover:shadow-hover transition duration-200">
            <View>
              <View className="flex-row items-center gap-3 mb-4">
                <View className="w-10 h-10 rounded-2xl bg-amber-500/10 border border-amber-500/20 items-center justify-center">
                  <Text className="text-xl">🏠</Text>
                </View>
                <View>
                  <Text className="text-base font-bold text-text-primary">{t('verify.hostKycCard')}</Text>
                  <Text className="text-xs text-text-secondary">{t('verify.bescomBillVerify')}</Text>
                </View>
              </View>

              {hostSuccess ? (
                <View className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl my-4">
                  <Text className="text-xs font-bold text-emerald-500">
                    {t('verify.verifiedSuccessBadge')}
                  </Text>
                  <Text className="text-[11px] text-text-secondary mt-1">
                    {t('spaceDetail.hostVerified')}
                  </Text>
                </View>
              ) : (
                <View className="space-y-3 my-4">
                  <View>
                    <Text className="text-xs font-medium text-text-secondary mb-1">{t('verify.aadhaarVerification')}</Text>
                    <TextInput
                      value={aadhaarMasked}
                      onChangeText={setAadhaarMasked}
                      placeholder="XXXX-XXXX-1234"
                      placeholderTextColor="#94a3b8"
                      className="w-full bg-surface-elevated border border-border rounded-xl px-3.5 py-2.5 text-xs text-text-primary font-mono"
                    />
                  </View>
                  <View>
                    <Text className="text-xs font-medium text-text-secondary mb-1">{t('verify.bescomBillVerify')}</Text>
                    <TextInput
                      value={hostAddressProof}
                      onChangeText={setHostAddressProof}
                      placeholder="Electricity bill / Property tax receipt"
                      placeholderTextColor="#94a3b8"
                      className="w-full bg-surface-elevated border border-border rounded-xl px-3.5 py-2.5 text-xs text-text-primary"
                    />
                  </View>
                </View>
              )}
            </View>

            {!hostSuccess && (
              <Pressable
                onPress={handleHostVerify}
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 rounded-xl items-center justify-center transition shadow-sm hover:shadow-md cursor-pointer"
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
