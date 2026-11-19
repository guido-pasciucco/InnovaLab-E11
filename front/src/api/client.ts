import type {
  ActivityProceduresResponse, ActivitySuggestionsResponse, AddressSearchResponse, ConsultationRequest, ContextAnswers,
  ConsultationResponse, FollowUpRequest, FollowUpResponse,
} from '../types';
import type { GeoPoint } from '../types';
import { mockConsultation, mockFollowUp } from './mock';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api';
const USE_MOCK = import.meta.env.VITE_USE_MOCK_API === 'true';

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!response.ok) {
    const message = await response.text().catch(() => '');
    throw new ApiError(response.status, `API ${response.status}: ${message || response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export async function submitConsultation(
  payload: ConsultationRequest,
): Promise<ConsultationResponse> {
  if (USE_MOCK) return mockConsultation(payload);
  return request<ConsultationResponse>('/consultations', {
    method: 'POST', body: JSON.stringify(payload),
  });
}

export async function submitFollowUp(
  consultationId: string, payload: FollowUpRequest,
): Promise<FollowUpResponse> {
  if (USE_MOCK) return mockFollowUp(payload);
  return request<FollowUpResponse>(
    `/consultations/${encodeURIComponent(consultationId)}/follow-up`,
    { method: 'POST', body: JSON.stringify(payload) },
  );
}

export async function searchAddresses(
  address: string, options: { limit?: number; signal?: AbortSignal } = {},
): Promise<AddressSearchResponse> {
  const params = new URLSearchParams({ address, limit: String(options.limit ?? 5) });
  return request<AddressSearchResponse>(`/geolocation/addresses?${params}`, { signal: options.signal });
}

export async function suggestActivities(
  query: string, options: { limit?: number; signal?: AbortSignal } = {},
): Promise<ActivitySuggestionsResponse> {
  const params = new URLSearchParams({ query, limit: String(options.limit ?? 5) });
  return request<ActivitySuggestionsResponse>(`/guidance/activities?${params}`, { signal: options.signal });
}

type NominatimResult = { lat: string; lon: string };

/**
 * Client-side fallback geocoder for free-text addresses, used only when the
 * backend address search is unavailable. Nominatim's usage policy asks for a
 * descriptive User-Agent and low volume; in production this should go through
 * the backend geolocation service instead.
 */
export async function geocodeAddressNominatim(
  address: string, options: { signal?: AbortSignal } = {},
): Promise<GeoPoint | null> {
  const url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=ar' +
    '&viewbox=-58.53,-34.52,-58.33,-34.71&bounded=1&q=' +
    encodeURIComponent(`${address}, Ciudad Autónoma de Buenos Aires`);
  try {
    const response = await fetch(url, {
      signal: options.signal,
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) return null;
    const results = (await response.json()) as NominatimResult[];
    const hit = results[0];
    return hit ? { lat: Number(hit.lat), lng: Number(hit.lon) } : null;
  } catch {
    return null;
  }
}

export async function getActivityProcedures(slug: string, answers: ContextAnswers = {}): Promise<ActivityProceduresResponse> {
  const params = new URLSearchParams(Object.entries(answers).map(([id, value]) => [id, String(value)]));
  const query = params.toString() ? `?${params}` : '';
  return request<ActivityProceduresResponse>(`/guidance/activities/${encodeURIComponent(slug)}/procedures${query}`);
}
