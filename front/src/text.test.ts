import { describe, expect, it } from "vitest";
import { excludedNote, listInSpanish } from "./text";

describe("listInSpanish", () => {
  it.each([
    [[], ""],
    [["Habilitación exprés"], "Habilitación exprés"],
    [["Habilitación exprés", "Trámite de bajo impacto"], "Habilitación exprés y Trámite de bajo impacto"],
    [["A", "B", "C"], "A, B y C"],
    // "y" becomes "e" before a word that starts with the i sound.
    [["Habilitación exprés", "Inscripción como empleador"], "Habilitación exprés e Inscripción como empleador"],
    [["Alta", "Higiene y seguridad"], "Alta e Higiene y seguridad"],
    [["Alta", "Hielo"], "Alta y Hielo"],
  ])("%j → %s", (items, text) => {
    expect(listInSpanish(items)).toBe(text);
  });
});

describe("excludedNote", () => {
  it("names the discarded procedures", () => {
    expect(excludedNote([{ id: "1", title: "Habilitación exprés" }, { id: "2", title: "Trámite de bajo impacto" }], 2))
      .toBe("Descartamos: Habilitación exprés y Trámite de bajo impacto.");
  });

  it("falls back to the count when the API does not send names (older backend)", () => {
    expect(excludedNote(undefined, 2)).toBe("Descartamos 2 trámites según tus respuestas.");
    expect(excludedNote(undefined, 1)).toBe("Descartamos 1 trámite según tus respuestas.");
  });

  it("says nothing when nothing was discarded", () => {
    expect(excludedNote([], 0)).toBeNull();
    expect(excludedNote(undefined, 0)).toBeNull();
  });
});
