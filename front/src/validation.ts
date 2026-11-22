/**
 * Input rules shared by the form and the API client. They mirror the backend's query validation
 * (FastAPI `Query`/`Field` constraints, published in OpenAPI) so the UI never sends a request the API
 * would reject with a 422.
 */

export type TextRule = { min: number; max: number };
export type LimitRange = { min: number; max: number };

export const TEXT_RULES = {
  /** GET /guidance/activities `query`: 2–100 characters, pattern `\S`. */
  activity: { min: 2, max: 100 },
  /** GET /geolocation/addresses `address`: 3–200 characters, pattern `\S`. */
  address: { min: 3, max: 200 },
  /** GET /guidance/procedures `query`: 3–100 characters, pattern `\S` (no UI uses it yet). */
  procedureQuery: { min: 3, max: 100 },
} as const satisfies Record<string, TextRule>;

export const RESULT_LIMITS = {
  addresses: { min: 1, max: 10 },
  activities: { min: 1, max: 10 },
  procedures: { min: 1, max: 20 },
} as const satisfies Record<string, LimitRange>;

type TextMessages = { empty: string };

/** Returns a message for the person, or null when the value is valid. */
export function validateText(value: string, rule: TextRule, messages: TextMessages): string | null {
  if (value.length === 0) return messages.empty;
  const trimmed = value.trim();
  if (!trimmed) return "Escribí algo más que espacios.";
  if (trimmed.length < rule.min) return `Escribí al menos ${rule.min} caracteres.`;
  if (trimmed.length > rule.max) return `Usá como máximo ${rule.max} caracteres.`;
  return null;
}

export function validateActivity(value: string): string | null {
  return validateText(value, TEXT_RULES.activity, { empty: "Escribí la actividad que querés realizar." });
}

export function validateAddress(value: string): string | null {
  return validateText(value, TEXT_RULES.address, { empty: "Escribí la dirección del local." });
}

export function validateLimit(limit: number, range: LimitRange): string | null {
  if (Number.isInteger(limit) && limit >= range.min && limit <= range.max) return null;
  return `La cantidad de resultados tiene que estar entre ${range.min} y ${range.max}.`;
}

/** True when the text is long enough to ask the API for suggestions (below the threshold, no request). */
export function reachesThreshold(value: string, rule: TextRule): boolean {
  const trimmed = value.trim();
  return trimmed.length >= rule.min && trimmed.length <= rule.max;
}
