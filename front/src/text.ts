import type { ExcludedProcedure } from "./types";

/** Starts with the "i" sound (i-, hi-), but not hie-/hia- (hielo, hiato), where Spanish keeps "y". */
function startsWithISound(word: string): boolean {
  return /^h?[ií](?![aeoáéó])/i.test(word.trim());
}

/** "A", "A y B", "A, B y C" (with "e" instead of "y" before an "i" sound, as Spanish requires). */
export function listInSpanish(items: string[]): string {
  if (items.length <= 1) return items.join("");
  const last = items[items.length - 1];
  return `${items.slice(0, -1).join(", ")} ${startsWithISound(last) ? "e" : "y"} ${last}`;
}

/**
 * Note under the context questions. It names what was discarded; an older API that only sends
 * the count still gets the previous wording.
 */
export function excludedNote(excluded: ExcludedProcedure[] | undefined, excludedCount: number): string | null {
  if (excluded?.length) return `Descartamos: ${listInSpanish(excluded.map(item => item.title))}.`;
  if (excludedCount > 0) return `Descartamos ${excludedCount} ${excludedCount === 1 ? "trámite" : "trámites"} según tus respuestas.`;
  return null;
}
