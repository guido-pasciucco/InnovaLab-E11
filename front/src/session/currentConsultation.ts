import type { ActivityProceduresResponse, ConsultationRequest, ConsultationResponse, ContextAnswers } from "../types";

/**
 * The consultation open in this tab, kept in sessionStorage so a reload (or opening /mapa directly)
 * keeps the result and the context answers. It lives only while the tab is open; the search history
 * (localStorage) is a separate, summary-only record.
 */
export const CURRENT_CONSULTATION_KEY = "conco.current-consultation.v1";

export type SavedConsultation = {
  query: ConsultationRequest;
  result: ConsultationResponse;
  activityProcedures: ActivityProceduresResponse | null;
  proceduresError: string | null;
  contextAnswers: ContextAnswers;
  checked: string[];
  checkedRequirements: string[];
};

/** sessionStorage, or null when the browser blocks it (private mode, blocked site data). */
export function sessionStore(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.sessionStorage;
  } catch {
    return null;
  }
}

function isSavedConsultation(value: unknown): value is SavedConsultation {
  if (!value || typeof value !== "object") return false;
  const saved = value as Partial<SavedConsultation>;
  return typeof saved.query?.activity === "string"
    && typeof saved.query.address === "string"
    && typeof saved.result?.consultationId === "string"
    && Array.isArray(saved.checked)
    && Array.isArray(saved.checkedRequirements)
    && !!saved.contextAnswers && typeof saved.contextAnswers === "object";
}

export function loadConsultation(storage: Storage | null = sessionStore()): SavedConsultation | null {
  try {
    const raw = storage?.getItem(CURRENT_CONSULTATION_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    return isSavedConsultation(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

export function saveConsultation(saved: SavedConsultation, storage: Storage | null = sessionStore()): void {
  try {
    storage?.setItem(CURRENT_CONSULTATION_KEY, JSON.stringify(saved));
  } catch {
    // Full or blocked storage: the consultation still works, it just will not survive a reload.
  }
}

export function clearConsultation(storage: Storage | null = sessionStore()): void {
  try {
    storage?.removeItem(CURRENT_CONSULTATION_KEY);
  } catch {
    // Nothing to clear when storage is blocked.
  }
}
