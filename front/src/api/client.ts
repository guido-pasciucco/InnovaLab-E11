import type {
  ActivityProceduresResponse, ActivitySuggestionsResponse, AddressSearchResponse, ConsultationRequest, ContextAnswers,
  ConsultationResponse, FollowUpRequest, FollowUpResponse,
} from '../types';
import type { GeoPoint } from '../types';
import { RESULT_LIMITS, validateActivity, validateAddress, validateLimit } from '../validation';
import { mockConsultation, mockFollowUp } from './mock';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api';
const USE_MOCK = import.meta.env.VITE_USE_MOCK_API === 'true';
// Generous on purpose: a sleeping free Render instance can take about a minute to wake up.
const DEFAULT_TIMEOUT_MS = 90_000;

/**
 * `http`: the API answered with an error status (`code`/`requestId` come from its error body).
 * `network`: no answer at all (offline, DNS, CORS). `timeout`: no answer in time.
 * `aborted`: cancelled on purpose, not an error for the person. `validation`: rejected before sending.
 */
export type ApiErrorKind = 'http' | 'network' | 'timeout' | 'aborted' | 'validation';

export class ApiError extends Error {
  constructor(
    public readonly kind: ApiErrorKind,
    message: string,
    public readonly status = 0,
    public readonly code: string | null = null,
    public readonly requestId: string | null = null,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

type ErrorBody = { code?: unknown; request_id?: unknown };

async function toHttpError(response: Response): Promise<ApiError> {
  const body = (await response.json().catch(() => null)) as ErrorBody | null;
  const code = typeof body?.code === 'string' ? body.code : null;
  const requestId = typeof body?.request_id === 'string' ? body.request_id : response.headers.get('X-Request-ID');
  return new ApiError('http', `API ${response.status}${code ? ` ${code}` : ''}`, response.status, code, requestId);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { signal, ...rest } = init;
  // One controller for both reasons to stop: the caller cancelled, or the timeout expired.
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, DEFAULT_TIMEOUT_MS);
  const cancel = () => controller.abort();
  if (signal?.aborted) controller.abort();
  signal?.addEventListener('abort', cancel, { once: true });
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...rest,
      signal: controller.signal,
      headers: { 'Content-Type': 'application/json', ...rest.headers },
    });
  } catch {
    if (timedOut) throw new ApiError('timeout', `API timeout after ${DEFAULT_TIMEOUT_MS} ms`);
    if (controller.signal.aborted) throw new ApiError('aborted', 'Request cancelled');
    throw new ApiError('network', 'API unreachable');
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', cancel);
  }
  if (!response.ok) throw await toHttpError(response);
  return response.json() as Promise<T>;
}

/** Rejects before sending when the API would answer 422 anyway. */
function ensureValid(problem: string | null): void {
  if (problem) throw new ApiError('validation', problem);
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
  const limit = options.limit ?? 5;
  ensureValid(validateAddress(address) ?? validateLimit(limit, RESULT_LIMITS.addresses));
  const params = new URLSearchParams({ address: address.trim(), limit: String(limit) });
  return request<AddressSearchResponse>(`/geolocation/addresses?${params}`, { signal: options.signal });
}

export async function suggestActivities(
  query: string, options: { limit?: number; signal?: AbortSignal } = {},
): Promise<ActivitySuggestionsResponse> {
  const limit = options.limit ?? 5;
  ensureValid(validateActivity(query) ?? validateLimit(limit, RESULT_LIMITS.activities));
  const params = new URLSearchParams({ query: query.trim(), limit: String(limit) });
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
