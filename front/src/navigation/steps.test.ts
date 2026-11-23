import { describe, expect, it } from "vitest";
import { NAV_STEPS, STEPS, isStepAvailable, pathOf, stepFromPath } from "./steps";

describe("step routes", () => {
  it("gives each step its own address", () => {
    expect(STEPS.map(({ path }) => path)).toEqual(["/consulta", "/analisis", "/orientacion", "/mapa", "/asistente"]);
    expect(STEPS.map(({ label }) => label)).toEqual(["Consulta", "Análisis", "Orientación", "Mapa", "Asistente"]);
  });

  it("maps addresses to steps and back", () => {
    for (const { step, path } of STEPS) {
      expect(stepFromPath(path)).toBe(step);
      expect(stepFromPath(`${path}/`)).toBe(step);
      expect(pathOf(step)).toBe(path);
    }
  });

  it("does not know other addresses", () => {
    expect(stepFromPath("/")).toBeNull();
    expect(stepFromPath("/historial")).toBeNull();
  });
});

describe("steps bar", () => {
  it("shows every step except the Análisis loading screen", () => {
    expect(NAV_STEPS.map(({ label }) => label)).toEqual(["Consulta", "Orientación", "Mapa", "Asistente"]);
  });
});

describe("which steps can be opened", () => {
  it("without a consultation only Consulta is available", () => {
    const state = { analyzing: false, hasResult: false };
    expect(STEPS.map(({ step }) => isStepAvailable(step, state))).toEqual([true, false, false, false, false]);
  });

  it("while the consultation runs, Análisis is available too", () => {
    const state = { analyzing: true, hasResult: false };
    expect(STEPS.map(({ step }) => isStepAvailable(step, state))).toEqual([true, true, false, false, false]);
  });

  it("with a result every step but Análisis is available", () => {
    const state = { analyzing: false, hasResult: true };
    expect(STEPS.map(({ step }) => isStepAvailable(step, state))).toEqual([true, false, true, true, true]);
  });
});
