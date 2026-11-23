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
  // With reasons, each question names what it discarded; this note only gives the total.
  const withReasons = !!excluded?.length && excluded.every(item => item.because?.length);
  if (excluded?.length && !withReasons) return `Descartamos: ${listInSpanish(excluded.map(item => item.title))}.`;
  if (excludedCount > 0) return `Descartamos ${excludedCount} ${excludedCount === 1 ? "trámite" : "trámites"} según tus respuestas.`;
  return null;
}

/** Line under an answered context question: what that answer discarded, or null if nothing. */
export function discardedByAnswer(
  question: { id: string; answer: boolean | null },
  excluded: ExcludedProcedure[] | undefined,
): string | null {
  if (question.answer === null) return null;
  const titles = (excluded ?? []).filter(item => item.because?.includes(question.id)).map(item => item.title);
  if (!titles.length) return null;
  return `Con «${question.answer ? "Sí" : "No"}» descartamos: ${listInSpanish(titles)}.`;
}
