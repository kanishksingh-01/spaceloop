import { request } from './api';
import { Space, Booking } from '../types';
import { getHostSpaces, getHostSpaceDetail, editSpace, toggleSpaceStatus, createSpace, uploadSpacePhoto, aiScanSpace } from './spaces';
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
  id: string;
  type: 'new_booking' | 'check_in' | 'active_session' | 'checkout' | 'verification' | 'system';
  title: string;
  message: string;
  timestamp: string;
  unread: boolean;
  action_url: string;
  priority: 'low' | 'medium' | 'high';
  icon?: string;
  color?: 'amber' | 'emerald' | 'sky' | 'rose' | 'indigo';
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

export async function getHostActivity(category?: string): Promise<{
  success: boolean;
  events: HostActivityEvent[];
}> {
  const qs = category && category !== 'all' ? `?category=${category}` : '';
  return request(`/api/host/activity${qs}`);
}

export async function updateHostSettings(settings: {
  name?: string;
  phone?: string;
  bio?: string;
  upi_vpa?: string;
  bank_beneficiary_name?: string;
}): Promise<{
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
  getHostBookings,
  getHostBookingDetail,
  acceptBooking,
  rejectBooking,
  cancelBooking,
  checkInBooking,
  checkOutBooking,
  disputeBooking,
};
