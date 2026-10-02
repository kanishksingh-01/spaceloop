// Base API client for communicating with SpaceLoop Flask backend
export class ApiError extends Error {
  status: number;
  data: any;
  constructor(message: string, status: number, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = 'ApiError';
  }
}

export interface RequestOptions extends RequestInit {
  skipCache?: boolean;
  ttlMs?: number;
  timeoutMs?: number;
}

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

const apiCache = new Map<string, CacheEntry<any>>();
const inFlightRequests = new Map<string, Promise<any>>();

export function invalidateApiCache(prefix?: string) {
  if (!prefix) {
    apiCache.clear();
    return;
  }
  for (const key of apiCache.keys()) {
    if (key.startsWith(prefix)) {
      apiCache.delete(key);
    }
  }
}

export async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const method = (options.method || 'GET').toUpperCase();
  const isGet = method === 'GET';

  // If mutation, invalidate cache entries that could be affected
  if (!isGet) {
    invalidateApiCache();
  }

  // Cache lookup for GET requests
  const cacheKey = `${method}:${endpoint}`;
  const now = Date.now();

  if (isGet && !options.skipCache) {
    const cached = apiCache.get(cacheKey);
    if (cached && now - cached.timestamp < cached.ttl) {
      return cached.data as T;
    }

    // In-flight request deduplication (share active promise)
    if (inFlightRequests.has(cacheKey)) {
      return inFlightRequests.get(cacheKey)! as Promise<T>;
    }
  }

  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'X-SpaceLoop-Client': 'ReactSPA',
    ...(options.headers as Record<string, string> || {}),
  };

  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const timeoutMs = options.timeoutMs || 10000;
  let timeoutId: any = null;
  let signal = options.signal;
  if (!signal) {
    const controller = new AbortController();
    timeoutId = setTimeout(() => {
      try {
        controller.abort();
      } catch {}
    }, timeoutMs);
    signal = controller.signal;
  }

  // Include credentials for Flask session cookies
  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include',
    signal,
  };

  const fetchPromise = (async (): Promise<T> => {
    try {
      const response = await fetch(endpoint, config);

      if (!response.ok) {
        let errorData: any;
        try {
          errorData = await response.json();
        } catch {
          errorData = await response.text();
        }

        let message = '';
        if (typeof errorData === 'object' && errorData !== null) {
          if (typeof errorData.error === 'string' && errorData.error.trim()) {
            message = errorData.error;
          } else if (typeof errorData.message === 'string' && errorData.message.trim()) {
            message = errorData.message;
          } else if (errorData.error && typeof errorData.error === 'object') {
            if (errorData.error.code === 'ECONNREFUSED' || errorData.error.syscall === 'connect') {
              message = 'Cannot connect to backend server. Please ensure the Flask backend is running on port 5000.';
            } else if (typeof errorData.error.message === 'string') {
              message = errorData.error.message;
            } else {
              message = JSON.stringify(errorData.error);
            }
          } else if (typeof errorData.detail === 'string') {
            message = errorData.detail;
          } else {
            message = JSON.stringify(errorData);
          }
        } else if (typeof errorData === 'string' && errorData.trim()) {
          message = errorData;
        }

        if (!message || message === '{}' || message === '[object Object]') {
          if (response.status === 502 || response.status === 504 || response.status === 500) {
            message = 'Cannot connect to backend server. Please ensure the Flask backend is running on port 5000.';
          } else {
            message = `Request failed with status ${response.status}`;
          }
        }

        throw new ApiError(message, response.status, errorData);
      }

      // Handle empty responses (like 204 No Content)
      if (response.status === 204) {
        return {} as T;
      }

      const data = await response.json();

      // Store in memory cache for GET requests
      if (isGet && !options.skipCache) {
        const ttl = options.ttlMs || 30000; // 30s default TTL
        apiCache.set(cacheKey, {
          data,
          timestamp: Date.now(),
          ttl,
        });
      }

      return data as T;
    } finally {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      if (isGet) {
        inFlightRequests.delete(cacheKey);
      }
    }
  })();

  if (isGet && !options.skipCache) {
    inFlightRequests.set(cacheKey, fetchPromise);
  }

  return fetchPromise;
}

