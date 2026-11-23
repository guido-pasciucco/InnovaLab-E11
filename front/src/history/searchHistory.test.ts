import { describe, expect, it } from "vitest";
import {
  HISTORY_LIMIT, SEARCH_HISTORY_KEY, addEntry, clearHistory, historyKey, loadHistory, relativeTime, saveHistory,
  type NewHistoryEntry,
} from "./searchHistory";

class MemoryStorage implements Storage {
  private items = new Map<string, string>();
  get length() { return this.items.size; }
  clear() { this.items.clear(); }
  getItem(key: string) { return this.items.get(key) ?? null; }
  key(index: number) { return [...this.items.keys()][index] ?? null; }
  removeItem(key: string) { this.items.delete(key); }
  setItem(key: string, value: string) { this.items.set(key, value); }
}

function search(activity: string, address: string, searchedAt = "2026-11-22T10:00:00.000Z"): NewHistoryEntry {
  return { activity, address, activitySlug: null, point: null, summary: "3 trámites oficiales", searchedAt };
}

describe("adding searches", () => {
  it("puts the newest search first", () => {
    const history = addEntry(addEntry([], search("Peluquería", "Av Corrientes 2500")), search("Barbería", "Córdoba 1234"));
    expect(history.map(entry => entry.activity)).toEqual(["Barbería", "Peluquería"]);
  });

  it("does not duplicate a repeated search: same activity and address after normalizing", () => {
    const first = addEntry([], search("Peluquería", "Av Corrientes 2500", "2026-11-20T10:00:00.000Z"));
    const history = addEntry(first, search("  peluqueria ", "AV  CORRIENTES 2500", "2026-11-22T10:00:00.000Z"));

    expect(history).toHaveLength(1);
    expect(history[0].activity).toBe("peluqueria");
    expect(history[0].searchedAt).toBe("2026-11-22T10:00:00.000Z");
    expect(historyKey("Peluquería", "Av Corrientes 2500")).toBe(historyKey(" peluqueria", "av corrientes  2500 "));
  });

  it("keeps at most 10 searches", () => {
    let history = addEntry([], search("Actividad 0", "Dirección 0"));
    for (let index = 1; index < 12; index += 1) history = addEntry(history, search(`Actividad ${index}`, `Dirección ${index}`));

    expect(HISTORY_LIMIT).toBe(10);
    expect(history).toHaveLength(10);
    expect(history[0].activity).toBe("Actividad 11");
    expect(history[9].activity).toBe("Actividad 2");
  });
});

describe("history in localStorage", () => {
  it("survives a reload under conco.search-history.v1", () => {
    const storage = new MemoryStorage();
    const history = addEntry([], search("Peluquería", "Av Corrientes 2500"));
    saveHistory(history, storage);

    expect(SEARCH_HISTORY_KEY).toBe("conco.search-history.v1");
    expect(storage.getItem(SEARCH_HISTORY_KEY)).not.toBeNull();
    expect(loadHistory(storage)).toEqual(history);
  });

  it("stores only what the panel needs, never the response or the chat", () => {
    const storage = new MemoryStorage();
    saveHistory(addEntry([], search("Peluquería", "Av Corrientes 2500")), storage);

    const [stored] = JSON.parse(storage.getItem(SEARCH_HISTORY_KEY)!);
    expect(Object.keys(stored).sort()).toEqual(["activity", "activitySlug", "address", "id", "point", "searchedAt", "summary"]);
  });

  it("is empty after clearing", () => {
    const storage = new MemoryStorage();
    saveHistory(addEntry([], search("Peluquería", "Av Corrientes 2500")), storage);
    clearHistory(storage);

    expect(loadHistory(storage)).toEqual([]);
    expect(storage.getItem(SEARCH_HISTORY_KEY)).toBeNull();
  });

  it("drops broken data instead of failing", () => {
    const storage = new MemoryStorage();
    storage.setItem(SEARCH_HISTORY_KEY, "{oops");
    expect(loadHistory(storage)).toEqual([]);
    storage.setItem(SEARCH_HISTORY_KEY, JSON.stringify([{ activity: 1 }, search("Peluquería", "Av Corrientes 2500")]));
    expect(loadHistory(storage).map(entry => entry.activity)).toEqual(["Peluquería"]);
    expect(loadHistory(null)).toEqual([]);
  });
});

describe("relativeTime", () => {
  const now = new Date(2026, 10, 22, 15, 0);
  it.each([
    [new Date(2026, 10, 22, 14, 59, 30), "recién"],
    [new Date(2026, 10, 22, 14, 35), "hace 25 min"],
    [new Date(2026, 10, 22, 13, 0), "hace 2 h"],
    [new Date(2026, 10, 21, 23, 0), "ayer"],
    [new Date(2026, 10, 12, 9, 0), "12/11"],
    [new Date(2025, 10, 12, 9, 0), "12/11/2025"],
  ])("%s → %s", (date, text) => {
    expect(relativeTime(date.toISOString(), now)).toBe(text);
  });
});
