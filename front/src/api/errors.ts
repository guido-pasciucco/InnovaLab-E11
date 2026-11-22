import { ApiError } from "./client";

/**
 * The one place that turns errors into messages for the person, so the same error reads the same
 * everywhere. Backend codes come from the API error body `{ code, request_id, detail }`.
 */
const MESSAGES_BY_CODE: Record<string, string> = {
  PROCEDURE_NOT_FOUND: "No encontramos ese trámite.",
  PROCEDURES_UNAVAILABLE: "No pudimos consultar los trámites. Intentá de nuevo.",
  PROCEDURES_LOADING: "Estamos cargando los trámites, volvé a intentar.",
  ACTIVITY_NOT_FOUND: "No encontramos esa actividad. Elegí otra de la lista.",
  ACTIVITIES_UNAVAILABLE: "La búsqueda de actividades no está disponible.",
  ADDRESSES_UNAVAILABLE: "El servicio de direcciones no está disponible.",
  CONSULTATIONS_UNAVAILABLE: "El servicio de consultas no está disponible. Intentá de nuevo más tarde.",
  INVALID_CONSULTATION_ID: "No pudimos continuar con esta consulta. Hacé una consulta nueva.",
  INTERNAL_ERROR: "Ocurrió un error inesperado. Intentá de nuevo más tarde.",
};

export const OFFLINE_MESSAGE = "Sin conexión. Revisá tu internet e intentá de nuevo.";
export const TIMEOUT_MESSAGE = "El servicio está tardando demasiado en responder. Intentá de nuevo en unos segundos.";
export const INVALID_INPUT_MESSAGE = "Revisá los datos ingresados: hay un valor que no es válido.";
export const UNEXPECTED_MESSAGE = "Ocurrió un error inesperado. Intentá de nuevo.";

function describeHttp(error: ApiError): string {
  if (error.code && MESSAGES_BY_CODE[error.code]) return MESSAGES_BY_CODE[error.code];
  // 422 bodies list technical validation details: never show them as they come.
  if (error.status === 422) return INVALID_INPUT_MESSAGE;
  if (error.status === 404) return "No encontramos lo que buscabas.";
  if (error.status >= 500) return "El servicio no está disponible en este momento. Intentá de nuevo más tarde.";
  return "No pudimos procesar el pedido. Revisá los datos e intentá de nuevo.";
}

/**
 * Message to show for an error, or null when nothing should be shown (the request was cancelled,
 * for example because the person kept typing or left the page).
 */
export function describeError(error: unknown): string | null {
  if (!(error instanceof ApiError)) return UNEXPECTED_MESSAGE;
  switch (error.kind) {
    case "aborted": return null;
    case "network": return OFFLINE_MESSAGE;
    case "timeout": return TIMEOUT_MESSAGE;
    case "validation": return error.message;
    case "http": return describeHttp(error);
  }
}
