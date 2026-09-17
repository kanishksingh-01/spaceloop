import { request } from './api';
import { User } from '../types';

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
    if (err.status === 401 || err.status === 403) {
      localStorage.removeItem('spaceloop_user');
      return null;
    }
  }

  const cached = localStorage.getItem('spaceloop_user');
  if (cached) {
    try {
      return JSON.parse(cached);
    } catch {
      return null;
    }
  }
  return null;
}

export async function loginUser(email: string, password: string): Promise<{ success: boolean; user: User }> {
  const res = await request<{ success: boolean; user: User }>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (res?.user) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
}

export async function seekerLogin(email: string, password: string): Promise<{ success: boolean; user: User; portal: string }> {
  const res = await request<{ success: boolean; user: User; portal: string }>('/api/v1/auth/seeker/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (res?.user) {
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
}): Promise<{ success: boolean; user: User; portal: string }> {
  const res = await request<{ success: boolean; user: User; portal: string }>('/api/v1/auth/seeker/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (res?.user) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
}

export async function hostLogin(email: string, password: string): Promise<{ success: boolean; user: User; portal: string }> {
  const res = await request<{ success: boolean; user: User; portal: string }>('/api/v1/auth/host/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (res?.user) {
    localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
  }
  return res;
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
}): Promise<{ success: boolean; user: User; portal: string; discom?: any; upi?: any }> {
  const res = await request<{ success: boolean; user: User; portal: string; discom?: any; upi?: any }>('/api/v1/auth/host/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (res?.user) {
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
}): Promise<{ success: boolean; user: User; message?: string }> {
  const res = await request<{ success: boolean; user: User; message?: string }>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (res?.user) {
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

export async function demoSwitch(role: 'seeker' | 'host' | 'admin' | 'guest'): Promise<{ success: boolean; role?: string; user?: User }> {
  try {
    const res = await request<{ success: boolean; user?: User }>(`/api/v1/auth/demo-switch/${role}`, {
      method: 'POST',
    });
    if (res?.user) {
      localStorage.setItem('spaceloop_user', JSON.stringify(res.user));
    }
    return { success: res.success, role, user: res.user };
  } catch (err) {
    const resp = await fetch(`/auth/demo-switch/${role}`, {
      method: 'GET',
      credentials: 'include',
    });
    return { success: resp.ok, role };
  }
}
