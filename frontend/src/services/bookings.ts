import { request } from './api';
import { Booking } from '../types';

export async function createBooking(payload: {
  space_id: number;
  hours?: number;
  start_time: string;
  end_time: string;
  notes?: string;
  purpose?: string;
}): Promise<{ success: boolean; booking_id: number; booking?: Booking }> {
  // Ensure hours is calculated if missing
  let hours = payload.hours;
  if (!hours && payload.start_time && payload.end_time) {
    const start = new Date(payload.start_time).getTime();
    const end = new Date(payload.end_time).getTime();
    if (!isNaN(start) && !isNaN(end) && end > start) {
      hours = Math.round(((end - start) / (1000 * 60 * 60)) * 10) / 10;
    }
  }

  return request('/api/bookings', {
    method: 'POST',
    body: JSON.stringify({ ...payload, hours: hours || 2 }),
  });
}

export async function precheckBooking(
  spaceId: number,
  startTime: string,
  endTime: string,
  hours?: number
): Promise<{
  available: boolean;
  total_price: number;
  deposit: number;
  hours: number;
  message?: string;
}> {
  return request('/api/bookings/precheck', {
    method: 'POST',
    body: JSON.stringify({
      space_id: spaceId,
      start_time: startTime,
      end_time: endTime,
      hours: hours || 2,
    }),
  });
}

export async function getBooking(
  bookingId: number
): Promise<{ success: boolean; booking: Booking; space?: any }> {
  return request(`/api/booking/${bookingId}`);
}

export async function getBookingStatus(
  bookingId: number
): Promise<{ success: boolean; booking: Booking; status?: string }> {
  return request(`/api/booking/${bookingId}/status`);
}

export async function cancelBooking(bookingId: number): Promise<{
  success: boolean;
  message: string;
  error?: string;
  refund_amount?: number;
  platform_fee?: number;
  total_price?: number;
  booking?: Booking;
}> {
  return request(`/api/booking/${bookingId}/cancel`, {
    method: 'POST',
  });
}

export async function checkInBooking(
  bookingId: number,
  coords: { lat?: number; lng?: number; qr_token?: string; pin?: string; entry_photo?: string }
): Promise<{
  success: boolean;
  message: string;
  checked_in_at?: string;
  arrival_time?: string;
  status?: string;
  booking?: Booking;
}> {
  return request(`/api/booking/${bookingId}/check-in`, {
    method: 'POST',
    body: JSON.stringify(coords),
  });
}

export async function checkOutBooking(
  bookingId: number,
  coords: {
    lat?: number;
    lng?: number;
    exit_photo?: string;
    simulate_damaged?: boolean;
    simulate_cv_failure?: boolean;
  }
): Promise<{
  success: boolean;
  message: string;
  deposit_released?: boolean;
  status?: string;
  inspection?: any;
  fraud_assessment?: any;
  punctuality_score?: number;
  escrow_refund_status?: string;
  booking?: Booking;
}> {
  return request(`/api/booking/${bookingId}/check-out`, {
    method: 'POST',
    body: JSON.stringify(coords),
  });
}

export async function uploadInspectionPhoto(
  bookingId: number,
  file: File,
  type: 'entry' | 'exit' = 'entry'
): Promise<{ success: boolean; url: string; photo_url: string; filename: string }> {
  const formData = new FormData();
  formData.append('photo', file);
  formData.append('type', type);

  const res = await fetch(`/api/booking/${bookingId}/upload-inspection-photo`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || 'Failed to upload inspection photo');
  }

  return res.json();
}


export async function acceptBooking(bookingId: number): Promise<{ success: boolean; message: string; booking: Booking }> {
  return request(`/api/booking/${bookingId}/accept`, {
    method: 'POST',
  });
}

export async function rejectBooking(bookingId: number): Promise<{ success: boolean; message: string; booking: Booking }> {
  return request(`/api/booking/${bookingId}/reject`, {
    method: 'POST',
  });
}

export async function getHostBookings(params?: {
  status?: string;
  space_id?: number;
  q?: string;
}): Promise<{ success: boolean; bookings: Booking[]; count: number }> {
  const query = new URLSearchParams();
  if (params?.status && params.status !== 'all') query.append('status', params.status);
  if (params?.space_id) query.append('space_id', String(params.space_id));
  if (params?.q) query.append('q', params.q);

  const qs = query.toString();
  return request<{ success: boolean; bookings: Booking[]; count: number }>(`/api/host/bookings${qs ? `?${qs}` : ''}`);
}

export async function getHostBookingDetail(bookingId: number): Promise<{
  success: boolean;
  booking: Booking;
  space?: any;
  renter?: any;
  activity?: any[];
}> {
  return request<{
    success: boolean;
    booking: Booking;
    space?: any;
    renter?: any;
    activity?: any[];
  }>(`/api/host/bookings/${bookingId}`);
}

export async function disputeBooking(
  bookingId: number,
  reason: string,
  action: 'raise' | 'resolve' = 'raise',
  resolution?: string
): Promise<{ success: boolean; message: string; booking: Booking }> {
  return request(`/api/booking/${bookingId}/dispute`, {
    method: 'POST',
    body: JSON.stringify({ reason, action, resolution }),
  });
}

