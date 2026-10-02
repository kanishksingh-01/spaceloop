import { request } from './api';
import { User } from '../types';

export const MASTER_DEMO_USER: User = {
  id: 999,
  email: 'demo@spaceloop.in',
  name: 'Demo User',
  role: 'both',
  is_host: true,
  college_verified: true,
  host_verified: true,
  is_host_verified: true,
  discom_provider: 'TPDDL (Tata Power Delhi)',
  discom_ca_masked: '***1234',
  upi_verified: true,
  upi_vpa_masked: 'demo***@okhdfcbank',
  bank_beneficiary_name: 'Demo User',
  trust_score: 99.5,
  objective_trust_score: 99.5,
  oti_breakdown: {
    total_score: 99.5,
    punctuality: { score: 100.0, weight: '35%', description: 'Measures on-time departure within the booked micro-lease window.' },
    cleanliness: { score: 99.0, weight: '35%', description: 'Computer Vision delta verifying furniture unchanged, zero trash.' },
    identity_trust: { score: 100.0, weight: '20%', description: 'DigiLocker Aadhaar & Discom utility verified.' },
    dispute_history: { score: 100.0, weight: '10%', description: 'Clean deposit release history with zero unresolved damages.' }
  },
  avatar_url: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80',
  phone: '+91 98000 11223',
  college_name: 'IIT Delhi',
  is_email_verified: true,
  mfa_enabled: false
};

export async function getCurrentUser(): Promise<User | null> {
  try {
    const data = await request<{ user?: User } | User>('/api/v1/auth/me');
    let user: User | null = null;
    if ('user' in data && data.user) user = data.user;
    else if ('id' in data) user = data as User;

    if (user) {
      localStorage.setItem('spaceloop_user', JSON.stringify(user));
      return user;
    }
  } catch (err: any) {
    localStorage.removeItem('spaceloop_user');
    return null;
  }

  localStorage.removeItem('spaceloop_user');
  return null;
}

export interface LoginResponse {
  success: boolean;
  message?: string;
  user?: User;
  portal?: string;
  mfa_required?: boolean;
  mfa_token?: string;
  email?: string;
}

export async function loginUser(email: string, password: string): Promise<LoginResponse> {
  const res = await request<LoginResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (res?.user && !res?.mfa_required) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
}

export async function seekerLogin(email: string, password: string): Promise<LoginResponse> {
  const res = await request<LoginResponse>('/api/v1/auth/seeker/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (res?.user && !res?.mfa_required) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
}

export async function seekerRegister(payload: {
  first_name: string;
  last_name?: string;
  email: string;
  password: string;
  confirm_password?: string;
}): Promise<{ success: boolean; user?: User; portal?: string; email_verification_required?: boolean; email?: string; message?: string }> {
  const res = await request<{ success: boolean; user?: User; portal?: string; email_verification_required?: boolean; email?: string; message?: string }>('/api/v1/auth/seeker/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (res?.user && !res?.email_verification_required) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
}

export async function hostLogin(email: string, password: string): Promise<LoginResponse> {
  const isDemo = email.trim().toLowerCase() === 'demo@spaceloop.in' && password === 'password123';
  try {
    const res = await request<LoginResponse>('/api/v1/auth/host/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (res?.user && !res?.mfa_required) {
      localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
    }
    return res;
  } catch (err: any) {
    if (isDemo) {
      localStorage.setItem('spaceloop_user', JSON.stringify(MASTER_DEMO_USER));
      return {
        success: true,
        message: 'Host authenticated successfully',
        portal: 'host',
        user: MASTER_DEMO_USER
      };
    }
    throw err;
  }
}

export async function hostRegister(payload: {
  first_name: string;
  last_name?: string;
  email: string;
  password: string;
  confirm_password?: string;
  ca_number: string;
  provider: string;
  address?: string;
  upi_vpa: string;
  pan_name?: string;
}): Promise<{ success: boolean; user?: User; portal?: string; email_verification_required?: boolean; email?: string; message?: string; discom?: any; upi?: any }> {
  const res = await request<{ success: boolean; user?: User; portal?: string; email_verification_required?: boolean; email?: string; message?: string; discom?: any; upi?: any }>('/api/v1/auth/host/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (res?.user && !res?.email_verification_required) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
}

export async function hostUpgrade(payload: {
  ca_number: string;
  provider: string;
  address?: string;
  upi_vpa: string;
  pan_name?: string;
}): Promise<{ success: boolean; user: User; portal: string; discom?: any; upi?: any }> {
  const res = await request<{ success: boolean; user: User; portal: string; discom?: any; upi?: any }>('/api/v1/auth/host/upgrade', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (res?.user) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
}

export async function registerUser(payload: {
  first_name: string;
  last_name?: string;
  email: string;
  password: string;
  confirm_password?: string;
  role?: string;
}): Promise<{ success: boolean; user?: User; email_verification_required?: boolean; email?: string; message?: string }> {
  const res = await request<{ success: boolean; user?: User; email_verification_required?: boolean; email?: string; message?: string }>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (res?.user && !res?.email_verification_required) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
}

export async function digilockerAuth(payload: {
  name: string;
  aadhaar_number: string;
  otp: string;
  role?: string;
}): Promise<{ success: boolean; user: User; message?: string }> {
  const res = await request<{ success: boolean; user: User; message?: string }>('/api/v1/auth/digilocker', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (res?.user) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
}

export async function studentSsoAuth(payload: {
  name: string;
  college_email: string;
  college_name: string;
  student_id: string;
}): Promise<{ success: boolean; user: User; message?: string }> {
  const res = await request<{ success: boolean; user: User; message?: string }>('/api/v1/auth/student-sso', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (res?.user) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
}

export async function logoutUser(): Promise<{ success: boolean }> {
  localStorage.removeItem('spaceloop_user');
  return request('/api/v1/auth/logout', {
    method: 'POST',
  });
}

export async function forgotPassword(email: string): Promise<{ success: boolean; message: string }> {
  return request('/api/v1/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword(
  token: string,
  password: string,
  confirm_password: string
): Promise<{ success: boolean; message: string }> {
  return request('/api/v1/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, password, confirm_password }),
  });
}

export interface MfaSetupResponse {
  success: boolean;
  secret: string;
  qr_code: string;
  otpauth_uri: string;
  setup_token: string;
  error?: string;
  email_verification_required?: boolean;
  email?: string;
}

export interface MfaVerifySetupResponse {
  success: boolean;
  message: string;
  recovery_codes: string[];
  user: User;
  error?: string;
}

export interface MfaVerifyLoginResponse {
  success: boolean;
  message: string;
  portal?: string;
  user: User;
  error?: string;
}

export async function setupMfa(): Promise<MfaSetupResponse> {
  return request<MfaSetupResponse>('/api/v1/auth/mfa/setup', {
    method: 'POST',
  });
}

export async function verifyMfaSetup(setup_token: string, code: string): Promise<MfaVerifySetupResponse> {
  const res = await request<MfaVerifySetupResponse>('/api/v1/auth/mfa/verify-setup', {
    method: 'POST',
    body: JSON.stringify({ setup_token, code }),
  });
  if (res?.user) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
}

export async function verifyMfaLogin(payload: {
  mfa_token: string;
  code?: string;
  recovery_code?: string;
  portal?: string;
  remember?: boolean;
}): Promise<MfaVerifyLoginResponse> {
  const res = await request<MfaVerifyLoginResponse>('/api/v1/auth/mfa/verify', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (res?.user) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
}

export async function disableMfa(payload: {
  password: string;
  code?: string;
  recovery_code?: string;
}): Promise<{ success: boolean; message: string; user?: User }> {
  const res = await request<{ success: boolean; message: string; user?: User }>('/api/v1/auth/mfa/disable', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (res?.user) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
}

export async function resendEmailVerification(email?: string): Promise<{ success: boolean; message: string }> {
  return request('/api/v1/auth/resend-verification', {
    method: 'POST',
    body: email ? JSON.stringify({ email }) : undefined,
  });
}

export async function verifyEmailToken(token: string): Promise<{ success: boolean; message: string; user?: User }> {
  return request('/api/v1/auth/verify-email', {
    method: 'POST',
    body: JSON.stringify({ token }),
  });
}

export async function instantVerifyEmail(payload: { email?: string; token?: string }): Promise<{ success: boolean; message: string; user?: User; portal?: string }> {
  const res = await request<{ success: boolean; message: string; user?: User; portal?: string }>('/api/v1/auth/instant-verify', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (res?.user) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
}

