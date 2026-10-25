import type {
  ConsultationRequest, ConsultationResponse, FollowUpRequest, FollowUpResponse,
} from '../types';
import { mockConsultation, mockFollowUp } from './mock';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api';
const USE_MOCK = import.meta.env.VITE_USE_MOCK_API !== 'false';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!response.ok) {
    const message = await response.text().catch(() => '');
    throw new Error(`API ${response.status}: ${message || response.statusText}`);
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
