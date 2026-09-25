export interface User {
  id: number;
  email: string;
  name: string;
  role: 'seeker' | 'host' | 'owner' | 'partner' | 'admin' | string;
  is_host?: boolean;
  college_verified?: boolean;
  host_verified?: boolean;
  is_host_verified?: boolean;
  discom_provider?: string;
  discom_ca_masked?: string;
  upi_verified?: boolean;
  upi_vpa_masked?: string;
  bank_beneficiary_name?: string;
  trust_score?: number;
  objective_trust_score?: number;
  oti_breakdown?: {
    total_score: number;
    punctuality: { score: number; weight: string; description: string };
    cleanliness: { score: number; weight: string; description: string };
    identity_trust: { score: number; weight: string; description: string };
    dispute_history: { score: number; weight: string; description: string };
  };
  avatar_url?: string;
  phone?: string;
  college_name?: string;
  is_email_verified?: boolean;
  mfa_enabled?: boolean;
}

export type PortalMode = 'seeker' | 'host';

export interface SpaceSpecs {
  usable_sqft?: number;
  acoustic_db?: number;
  lighting_lux?: number;
  power_circuits?: string;
  access_type?: string;
}

export interface Space {
  id: number;
  host_id: number;
  host_name?: string;
  host_verified?: boolean;
  owner_id?: number;
  owner_name?: string;
  owner_verified?: boolean;
  title: string;
  description: string;
  category: 'Workspace' | 'Meeting' | 'Studio' | 'Podcast' | 'Workshop' | 'Retail' | 'Event' | 'Storage' | 'Study' | 'Parking' | 'Creative' | string;
  hourly_rate: number;
  price_hourly?: number;
  daily_rate?: number;
  price_daily?: number;
  location: string;
  address: string;
  neighborhood?: string;
  city: string;
  state?: string;
  latitude: number;
  longitude: number;
  photos: string[];
  amenities: string[];
  is_active: boolean;
  rating?: number;
  reviews_count?: number;
  sqft?: number;
  max_capacity?: number;
  specs?: SpaceSpecs;
  distance_km?: number;
  ai_match_score?: number;
  ai_match_reasoning?: string;
  availability_status?: string;
  match_reasons?: string[];
  pros?: string[];
  cons?: string[];
  created_at?: string;
}

export interface Booking {
  id: number;
  space_id: number;
  space_title?: string;
  space_photo?: string;
  space_address?: string;
  seeker_id: number;
  seeker_name?: string;
  seeker_email?: string;
  user_name?: string;
  start_time: string;
  end_time: string;
  start_iso?: string;
  end_iso?: string;
  end_timestamp_ms?: number;
  hours_booked?: number;
  total_price: number;
  deposit_held: number;
  escrow_deposit_amount?: number;
  status: 'pending' | 'confirmed' | 'active' | 'completed' | 'cancelled';
  session_state?: string;
  arrival_pin?: string;
  room_qr_token?: string;
  qr_code_hash?: string;
  checked_in_at?: string;
  checked_out_at?: string;
  created_at?: string;
  space?: Space;
  intended_purpose?: string;
  micro_lease_agreement?: string;
  condition_match_score?: number;
  escrow_status?: string;
  objective_punctuality_score?: number;
}

export interface AIMatchResponse {
  query: string;
  parsed_intent?: {
    category?: string;
    city?: string;
    locality?: string;
    max_price?: number;
    required_amenities?: string[];
  };
  match_summary?: string;
  matched_count: number;
  spaces: Space[];
  simulated?: boolean;
}

export interface CalculatorEstimate {
  space_type: string;
  square_feet: number;
  estimated_monthly_inr: number;
  estimated_hourly_inr: number;
  occupancy_rate_pct: number;
  peer_comparison: string;
}

export interface Inquiry {
  id: number;
  name: string;
  email: string;
  subject: string;
  message: string;
  status: string;
  created_at?: string;
}
