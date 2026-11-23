import { describe, expect, it } from "vitest";
import type { ConsultationResponse } from "../types";
import { CURRENT_CONSULTATION_KEY, clearConsultation, loadConsultation, saveConsultation, type SavedConsultation } from "./currentConsultation";

class MemoryStorage implements Storage {
  private items = new Map<string, string>();
  get length() { return this.items.size; }
  clear() { this.items.clear(); }
  getItem(key: string) { return this.items.get(key) ?? null; }
  key(index: number) { return [...this.items.keys()][index] ?? null; }
  removeItem(key: string) { this.items.delete(key); }
  setItem(key: string, value: string) { this.items.set(key, value); }
}

const result: ConsultationResponse = {
  consultationId: "c_eyJzIjoicGVsdXF1ZXJpYSJ9", interpretedActivity: "Peluquería", normalizedAddress: "Av. Corrientes 2500, CABA",
  point: { lat: -34.6, lng: -58.4 }, summary: "Resumen", steps: [], territorialFeatures: [], sources: [], limitations: [],
};

const saved: SavedConsultation = {
  query: { activity: "Peluquería", address: "Av. Corrientes 2500, CABA", point: { lat: -34.6, lng: -58.4 }, activitySlug: "peluqueria" },
  result,
  activityProcedures: null,
  proceduresError: null,
  contextAnswers: { has_employees: true },
  checked: ["p1"],
  checkedRequirements: ["r1"],
};

describe("current consultation in the tab session", () => {
  it("survives a reload with the context answers", () => {
    const storage = new MemoryStorage();
    saveConsultation(saved, storage);

    expect(loadConsultation(storage)).toEqual(saved);
    expect(storage.getItem(CURRENT_CONSULTATION_KEY)).not.toBeNull();
  });

  it("is gone after clearing", () => {
    const storage = new MemoryStorage();
    saveConsultation(saved, storage);
    clearConsultation(storage);

    expect(loadConsultation(storage)).toBeNull();
  });

  it("ignores broken or foreign data instead of failing", () => {
    const storage = new MemoryStorage();
    storage.setItem(CURRENT_CONSULTATION_KEY, "{not json");
    expect(loadConsultation(storage)).toBeNull();
    storage.setItem(CURRENT_CONSULTATION_KEY, JSON.stringify({ query: {}, result: {} }));
    expect(loadConsultation(storage)).toBeNull();
  });

  it("works without storage (private mode, blocked site data)", () => {
    expect(loadConsultation(null)).toBeNull();
    expect(() => saveConsultation(saved, null)).not.toThrow();
    expect(() => clearConsultation(null)).not.toThrow();
  });
});
