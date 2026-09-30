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

export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'X-SpaceLoop-Client': 'ReactSPA',
    ...(options.headers as Record<string, string> || {}),
  };

  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  // Include credentials for Flask session cookies
  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include',
  };

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

  return response.json();
}
