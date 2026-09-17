import { request } from './api';
import { User } from '../types';

export async function getCurrentUser(): Promise<User | null> {
  try {
    const data = await request<{ user?: User } | User>('/api/v1/auth/me');
    if ('user' in data && data.user) return data.user;
    return data as User;
  } catch (err: any) {
    if (err.status === 401 || err.status === 403) return null;
    return null;
  }
}

export async function loginUser(email: string, password: string): Promise<{ success: boolean; user: User }> {
  return request('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function logoutUser(): Promise<{ success: boolean }> {
  return request('/api/v1/auth/logout', {
    method: 'POST',
  });
}

export async function demoSwitch(role: 'seeker' | 'host' | 'admin' | 'guest'): Promise<{ success: boolean; role?: string }> {
  // Demo switch triggers session update
  const resp = await fetch(`/auth/demo-switch/${role}`, {
    method: 'GET',
    credentials: 'include',
  });
  return { success: resp.ok, role };
}
