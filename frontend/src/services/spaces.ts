import { request } from './api';
import { Space, AIMatchResponse } from '../types';

export function getCategoryFallbackImage(category?: string): string {
  const cat = (category || '').toLowerCase();
  if (cat.includes('study')) {
    return 'https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?auto=format&fit=crop&w=1200&q=80';
  }
  if (cat.includes('work') || cat.includes('hack') || cat.includes('desk') || cat.includes('coding')) {
    return 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80';
  }
  if (cat.includes('studio') || cat.includes('podcast') || cat.includes('vocal') || cat.includes('photo')) {
    return 'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=1200&q=80';
  }
  if (cat.includes('storage') || cat.includes('gear') || cat.includes('luggage')) {
    return 'https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=1200&q=80';
  }
  if (cat.includes('meet') || cat.includes('board') || cat.includes('sprint') || cat.includes('discuss')) {
    return 'https://images.unsplash.com/photo-1517502884422-41eaead166d4?auto=format&fit=crop&w=1200&q=80';
  }
  if (cat.includes('creat') || cat.includes('design') || cat.includes('maker') || cat.includes('proto')) {
    return 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=1200&q=80';
  }
  if (cat.includes('park') || cat.includes('ev') || cat.includes('charg')) {
    return 'https://images.unsplash.com/photo-1590674899484-d5640e854abe?auto=format&fit=crop&w=1200&q=80';
  }
  return 'https://images.unsplash.com/photo-1497215728101-856f4ea42174?auto=format&fit=crop&w=1200&q=80';
}

export function normalizeSpace(raw: any): Space {
  const hourly = Number(raw.hourly_rate ?? raw.price_hourly ?? 50);
  const daily = raw.daily_rate ?? raw.price_daily ? Number(raw.daily_rate ?? raw.price_daily) : undefined;
  const loc = raw.location || (raw.neighborhood ? `${raw.neighborhood}, ${raw.city}` : raw.city || 'India');
  const photos = Array.isArray(raw.photos) && raw.photos.length > 0 ? raw.photos : [getCategoryFallbackImage(raw.category)];

  return {
    ...raw,
    id: Number(raw.id),
    host_id: Number(raw.host_id ?? raw.owner_id ?? 1),
    host_name: raw.host_name || raw.owner_name || 'Verified Host',
    host_verified: Boolean(raw.host_verified ?? raw.owner_verified ?? true),
    title: raw.title || 'Verified Space',
    description: raw.description || '',
    category: raw.category || 'Workspace',
    hourly_rate: hourly,
    price_hourly: hourly,
    daily_rate: daily,
    price_daily: daily,
    location: loc,
    address: raw.address || loc,
    city: raw.city || 'Pune',
    photos,
    amenities: Array.isArray(raw.amenities) ? raw.amenities : [],
    rating: raw.rating ? Number(raw.rating) : 4.9,
    reviews_count: raw.reviews_count ? Number(raw.reviews_count) : 8,
    is_active: raw.is_active !== false,
  };
}

export async function getSpaces(params?: {
  category?: string;
  city?: string;
  q?: string;
  max_price?: number;
  lat?: number;
  lng?: number;
  radius?: number | string;
}): Promise<Space[]> {
  const query = new URLSearchParams();
  if (params?.category && params.category !== 'All') query.append('category', params.category);
  if (params?.city && params.city !== 'All Cities' && params.city !== 'All') query.append('city', params.city);
  if (params?.q) query.append('q', params.q);
  if (params?.max_price) query.append('max_price', params.max_price.toString());
  if (params?.lat) query.append('lat', params.lat.toString());
  if (params?.lng) query.append('lng', params.lng.toString());
  if (params?.radius && params.radius !== 'All') query.append('radius', params.radius.toString());

  const qs = query.toString();
  const endpoint = `/api/spaces${qs ? `?${qs}` : ''}`;
  const data = await request<{ spaces?: any[] } | any[]>(endpoint);
  const rawList: any[] = Array.isArray(data) ? data : data.spaces || [];

  // Deduplicate and normalize by unique ID
  const seenIds = new Set<number>();
  const normalized: Space[] = [];

  for (const item of rawList) {
    if (!item || item.id === undefined || seenIds.has(Number(item.id))) continue;
    seenIds.add(Number(item.id));
    normalized.push(normalizeSpace(item));
  }

  return normalized;
}

export async function getSpaceById(id: number): Promise<Space> {
  const data = await request<{ space?: any } | any>(`/api/spaces/${id}`);
  const raw = 'space' in data && data.space ? data.space : data;
  return normalizeSpace(raw);
}

export async function aiMatchSpaces(queryText: string, lat?: number, lng?: number): Promise<AIMatchResponse> {
  const res = await request<any>('/api/spaces/ai-match', {
    method: 'POST',
    body: JSON.stringify({ query: queryText, lat, lng }),
  });

  // Extract spaces from res.spaces or res.results
  let matchedSpaces: Space[] = [];
  const seenIds = new Set<number>();

  if (Array.isArray(res.spaces)) {
    matchedSpaces = res.spaces.map(normalizeSpace);
  } else if (Array.isArray(res.results)) {
    matchedSpaces = res.results
      .filter((r: any) => r && r.space)
      .map((r: any) => {
        const norm = normalizeSpace(r.space);
        norm.ai_match_score = r.match_score;
        norm.ai_match_reasoning = (r.match_reasons && r.match_reasons[0]) || r.considerations;
        norm.pros = r.pros;
        norm.cons = r.cons;
        return norm;
      });
  }

  // Deduplicate
  const deduplicated = matchedSpaces.filter((s) => {
    if (seenIds.has(s.id)) return false;
    seenIds.add(s.id);
    return true;
  });

  return {
    query: res.query || queryText,
    match_summary: res.match_summary || `Found ${deduplicated.length} spaces matching your query.`,
    matched_count: deduplicated.length,
    spaces: deduplicated,
  };
}

export async function aiScanSpace(photoUrl: string, notes: string): Promise<any> {
  return request('/api/spaces/ai-scan', {
    method: 'POST',
    body: JSON.stringify({ photo_url: photoUrl, notes }),
  });
}

export async function submitInquiry(spaceId: number | undefined, question: string): Promise<{ success: boolean; message?: string; inquiry?: any }> {
  return request('/api/inquiries', {
    method: 'POST',
    body: JSON.stringify({ space_id: spaceId, question }),
  });
}

export async function getInquiries(): Promise<{ success: boolean; inquiries: any[] }> {
  return request('/api/inquiries', {
    method: 'GET',
  });
}

export async function createSpace(payload: Partial<Space> & Record<string, any>): Promise<{ success: boolean; space_id: number; id?: number }> {
  const hourly = Number(payload.hourly_rate ?? payload.price_hourly ?? 50);
  const dataToSend = {
    ...payload,
    hourly_rate: hourly,
    price_hourly: hourly,
    neighborhood: payload.neighborhood || payload.location || 'Downtown',
    location: payload.location || payload.neighborhood || 'Downtown',
  };
  return request('/api/spaces', {
    method: 'POST',
    body: JSON.stringify(dataToSend),
  });
}

export async function toggleSpaceStatus(spaceId: number): Promise<{ success: boolean; is_active: boolean }> {
  return request(`/api/spaces/${spaceId}/toggle-status`, {
    method: 'POST',
  });
}
