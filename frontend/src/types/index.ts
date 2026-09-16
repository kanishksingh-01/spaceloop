export interface Space {
  id: number;
  title: string;
  category: string;
  price_hourly: number;
  sqft: number;
  address: string;
  latitude: number;
  longitude: number;
  room_qr_token: string;
  ai_suitability_score: number;
}

export interface Booking {
  id: number;
  space_id: number;
  hours_booked: number;
  total_price: number;
  session_state: string;
  arrival_pin: string;
}

export interface User {
  id: number;
  name: string;
  email: string;
  role: 'seeker' | 'owner' | 'admin';
  is_student_verified: boolean;
  is_host_verified: boolean;
}
