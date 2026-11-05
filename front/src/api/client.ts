import type {
  AddressSearchResponse, ConsultationRequest, ConsultationResponse, FollowUpRequest, FollowUpResponse,
} from '../types';
import { mockConsultation, mockFollowUp } from './mock';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api';
const USE_MOCK = import.meta.env.VITE_USE_MOCK_API !== 'false';

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
