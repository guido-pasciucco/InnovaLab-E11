/** First item of the list, in its own order, that is not marked as reviewed yet. */
export function nextPending<T extends { id: string }>(items: T[], reviewed: string[]): T | null {
  return items.find(item => !reviewed.includes(item.id)) ?? null;
}
