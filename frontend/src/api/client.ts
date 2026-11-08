/**
 * Mind API Client
 * Wraps fetch requests with credentials, authorization headers, and error handling.
 */

const API_BASE = '/api/v1';

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('mind_session_token');
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include', // Includes HttpOnly cookies
  });

  const contentType = response.headers.get('content-type');
  const isJson = contentType && contentType.includes('application/json');
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    const error: ApiError = data?.error || {
      code: 'HTTP_ERROR',
      message: response.statusText || 'Request failed',
      details: { status: response.status }
    };
    throw error;
  }

  return data as T;
}
