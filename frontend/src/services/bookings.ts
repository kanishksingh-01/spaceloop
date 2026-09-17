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

export async function cancelBooking(bookingId: number): Promise<{ success: boolean; message: string }> {
  return request(`/api/booking/${bookingId}/cancel`, {
    method: 'POST',
  });
}

export async function checkInBooking(
  bookingId: number,
  coords: { lat?: number; lng?: number; qr_token?: string; pin?: string }
): Promise<{ success: boolean; message: string; checked_in_at?: string; status?: string }> {
  return request(`/api/booking/${bookingId}/check-in`, {
    method: 'POST',
    body: JSON.stringify(coords),
  });
}

export async function checkOutBooking(
  bookingId: number,
  coords: { lat?: number; lng?: number; exit_photo?: string }
): Promise<{
  success: boolean;
  message: string;
  deposit_released?: boolean;
  status?: string;
  inspection?: any;
  punctuality_score?: number;
  escrow_refund_status?: string;
  booking?: Booking;
}> {
  return request(`/api/booking/${bookingId}/check-out`, {
    method: 'POST',
    body: JSON.stringify(coords),
  });
}
