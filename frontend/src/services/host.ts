import { request } from './api';
import { Space, Booking } from '../types';
import {
  getHostSpaces,
  getHostSpaceDetail,
  editSpace,
  toggleSpaceStatus,
  createSpace,
  uploadSpacePhoto,
  aiScanSpace,
  publishSpace,
  unpublishSpace,
  checkSpaceAvailability,
  getSpaceAccessLogs,
} from './spaces';
import { getHostBookings, getHostBookingDetail, acceptBooking, rejectBooking, cancelBooking, checkInBooking, checkOutBooking, disputeBooking } from './bookings';

export interface HostMetricData {
  gross_revenue: number;
  platform_fee: number;
  net_earnings: number;
  total_hours: number;
  total_bookings: number;
  active_spaces_count: number;
  total_spaces_count: number;
  upcoming_count: number;
  completed_count: number;
  payout_vpa: string;
}

export interface HostNotification {
  id: string | number;
  db_id?: number | null;
  type: string;
  title: string;
  message: string;
  timestamp: string;
  unread: boolean;
  action_url: string;
  priority: 'low' | 'medium' | 'high' | string;
  icon?: string;
  color?: string;
}

export interface HostActivityEvent {
  id: string;
  type: string;
  category: 'space' | 'booking' | 'access' | 'verification' | 'settlement' | 'security';
  title: string;
  description: string;
  timestamp: string;
  resource_type?: string;
  resource_id?: number | string;
  space_id?: number;
  status?: string;
  icon?: string;
  color?: string;
}

export async function getHostDashboardData(): Promise<{
  success: boolean;
  host_bookings: Booking[];
  host_spaces: Space[];
  host_metrics: HostMetricData;
  user: any;
}> {
  return request('/api/dashboard');
}

export async function getHostNotifications(): Promise<{
  success: boolean;
  notifications: HostNotification[];
  unread_count: number;
}> {
  return request('/api/host/notifications');
}

export async function markNotificationRead(notificationId: number | string): Promise<{ success: boolean; message: string }> {
  return request(`/api/host/notifications/${notificationId}/read`, {
    method: 'POST',
  });
}

export async function markAllNotificationsRead(): Promise<{ success: boolean; message: string }> {
  return request('/api/host/notifications/read-all', {
    method: 'POST',
  });
}

export async function deleteNotification(notificationId: number | string): Promise<{ success: boolean; message: string }> {
  return request(`/api/host/notifications/${notificationId}`, {
    method: 'DELETE',
  });
}

export async function getHostEscrowLedger(): Promise<{
  success: boolean;
  transactions: any[];
  metrics: {
    total_held: number;
    total_released: number;
    settled_payouts: number;
    escrow_unit_inr: number;
    dispute_count: number;
  };
}> {
  return request('/api/host/escrow/ledger');
}

export async function getHostAccessLogs(): Promise<{
  success: boolean;
  access_logs: any[];
  count: number;
}> {
  return request('/api/host/access-logs');
}

export async function getHostActivity(category?: string): Promise<{
  success: boolean;
  events: HostActivityEvent[];
}> {
  const qs = category && category !== 'all' ? `?category=${category}` : '';
  return request(`/api/host/activity${qs}`);
}

export async function getHostSettings(): Promise<{
  success: boolean;
  settings: Record<string, any>;
  user: any;
}> {
  return request('/api/host/settings');
}

export async function updateHostSettings(settings: Record<string, any>): Promise<{
  success: boolean;
  message: string;
  user: any;
}> {
  return request('/api/host/settings', {
    method: 'POST',
    body: JSON.stringify(settings),
  });
}

// Re-export domain functions for clean consumption in Host Portal components
export {
  getHostSpaces,
  getHostSpaceDetail,
  editSpace,
  toggleSpaceStatus,
  createSpace,
  uploadSpacePhoto,
  aiScanSpace,
  publishSpace,
  unpublishSpace,
  checkSpaceAvailability,
  getSpaceAccessLogs,
  getHostBookings,
  getHostBookingDetail,
  acceptBooking,
  rejectBooking,
  cancelBooking,
  checkInBooking,
  checkOutBooking,
  disputeBooking,
};

