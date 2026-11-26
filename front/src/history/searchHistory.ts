import type { GeoPoint } from "../types";

/**
 * Recent searches kept in this browser only (localStorage): never sent to a server or to analytics.
 * Each entry holds just what the panel shows plus what is needed to run the same query again;
 * the response and the chat are not stored (they would be large and go stale).
 */
export const SEARCH_HISTORY_KEY = "conco.search-history.v1";
export const HISTORY_LIMIT = 10;

export type HistoryEntry = {
  /** Normalized activity + address: two searches with the same key are the same search. */
  id: string;
  activity: string;
  address: string;
  /** Needed to run the same consultation again (curated activity and map point). */
  activitySlug: string | null;
  point: GeoPoint | null;
  /** Brief summary of what the search found. */
  summary: string;
  /** ISO date of the last time it was searched. */
  searchedAt: string;
};

export type NewHistoryEntry = Omit<HistoryEntry, "id">;

/** Accent- and case-insensitive comparison criterion shared with the rubro filter (S10). */
export function normalize(text: string): string {
  return text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().replace(/\s+/g, " ").trim();
}

export function historyKey(activity: string, address: string): string {
  return `${normalize(activity)}|${normalize(address)}`;
}

/** Newest first; a repeated search moves to the top instead of being duplicated; at most 10. */
export function addEntry(history: HistoryEntry[], entry: NewHistoryEntry): HistoryEntry[] {
  const activity = entry.activity.trim();
  const address = entry.address.trim();
  const id = historyKey(activity, address);
  return [{ ...entry, activity, address, id }, ...history.filter(item => item.id !== id)].slice(0, HISTORY_LIMIT);
}

/** localStorage, or null when the browser blocks it (private mode, blocked site data). */
export function localStore(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    return null;
  }
}

function isPoint(value: unknown): value is GeoPoint | null {
  if (value === null) return true;
  const point = value as GeoPoint | undefined;
  return typeof point?.lat === "number" && typeof point.lng === "number";
}

function toEntry(value: unknown): HistoryEntry | null {
  if (!value || typeof value !== "object") return null;
  const item = value as Partial<HistoryEntry>;
  if (typeof item.activity !== "string" || typeof item.address !== "string" || typeof item.searchedAt !== "string") return null;
  return {
    id: historyKey(item.activity, item.address),
    activity: item.activity,
    address: item.address,
    activitySlug: typeof item.activitySlug === "string" ? item.activitySlug : null,
    point: isPoint(item.point) ? item.point : null,
    summary: typeof item.summary === "string" ? item.summary : "",
    searchedAt: item.searchedAt,
  };
}

export function loadHistory(storage: Storage | null = localStore()): HistoryEntry[] {
  try {
    const raw = storage?.getItem(SEARCH_HISTORY_KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(parsed)) return [];
    return parsed.map(toEntry).filter((entry): entry is HistoryEntry => entry !== null).slice(0, HISTORY_LIMIT);
  } catch {
    return [];
  }
}

export function saveHistory(history: HistoryEntry[], storage: Storage | null = localStore()): void {
  try {
    storage?.setItem(SEARCH_HISTORY_KEY, JSON.stringify(history));
  } catch {
    // Full or blocked storage: the search still works, it just is not remembered.
  }
}

export function clearHistory(storage: Storage | null = localStore()): void {
  try {
    storage?.removeItem(SEARCH_HISTORY_KEY);
  } catch {
    // Nothing to clear when storage is blocked.
  }
}

function startOfDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

/** "recién", "hace 25 min", "hace 2 h", "ayer", "12/11" (with the year when it is not this year). */
export function relativeTime(iso: string, now: Date = new Date()): string {
  const date = new Date(iso);
  const minutes = Math.floor((now.getTime() - date.getTime()) / 60_000);
  const today = startOfDay(now);
  if (startOfDay(date) === today) {
    if (minutes < 1) return "recién";
    if (minutes < 60) return `hace ${minutes} min`;
    return `hace ${Math.floor(minutes / 60)} h`;
  }
  // The start of the previous day, computed from the calendar so 23/25-hour DST days still work.
  if (startOfDay(date) === startOfDay(new Date(today - 1))) return "ayer";
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  return date.getFullYear() === now.getFullYear() ? `${day}/${month}` : `${day}/${month}/${date.getFullYear()}`;
}
