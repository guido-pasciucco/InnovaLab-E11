import type { ContextQuestion, ExcludedProcedure } from "./types";

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

function procedureCount(count: number): string {
  return `${count} ${count === 1 ? "trámite" : "trámites"}`;
}

/**
 * Note under the context questions: only the total. The discarded procedures themselves are shown at
 * the end of the list; an older API that only sends the count gets the count alone.
 */
export function excludedNote(excluded: ExcludedProcedure[] | undefined, excludedCount: number): string | null {
  if (excluded?.length) return `Descartamos ${procedureCount(excluded.length)} según tus respuestas. Los ves al final de la lista.`;
  if (excludedCount > 0) return `Descartamos ${procedureCount(excludedCount)} según tus respuestas.`;
  return null;
}

/** Questions (with the answer given) that discarded a procedure, in question order; empty without reasons. */
export function discardReasons(
  item: ExcludedProcedure,
  questions: ContextQuestion[],
): { question: string; answer: string }[] {
  return questions
    .filter(question => question.answer !== null && item.because?.includes(question.id))
    .map(question => ({ question: question.text, answer: question.answer ? "Sí" : "No" }));
}
