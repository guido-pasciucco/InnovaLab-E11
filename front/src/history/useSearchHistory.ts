import { useCallback, useEffect, useState } from "react";
import { SEARCH_HISTORY_KEY, addEntry, clearHistory, loadHistory, saveHistory, type HistoryEntry, type NewHistoryEntry } from "./searchHistory";

/** Recent searches of this browser, kept in sync across open tabs through the `storage` event. */
export function useSearchHistory() {
  const [entries, setEntries] = useState<HistoryEntry[]>(() => loadHistory());

  useEffect(() => {
    function sync(event: StorageEvent) {
      // key === null means another tab cleared the whole storage.
      if (event.key === SEARCH_HISTORY_KEY || event.key === null) setEntries(loadHistory());
    }
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);

  const record = useCallback((entry: NewHistoryEntry) => {
    // Read the stored list again so a search made in another tab is not overwritten.
    const next = addEntry(loadHistory(), entry);
    saveHistory(next);
    setEntries(next);
  }, []);

  const clear = useCallback(() => {
    clearHistory();
    setEntries([]);
  }, []);

  return { entries, record, clear };
}
