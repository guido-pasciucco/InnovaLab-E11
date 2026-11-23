import { describe, expect, it } from "vitest";
import { discardReasons, excludedNote, listInSpanish } from "./text";

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
  it("gives the total and points to the list, where the discarded procedures are shown", () => {
    expect(excludedNote([{ id: "1", title: "A", because: ["has_employees"] }, { id: "2", title: "B" }], 2))
      .toBe("Descartamos 2 trámites según tus respuestas. Los ves al final de la lista.");
    expect(excludedNote([{ id: "1", title: "A" }], 1))
      .toBe("Descartamos 1 trámite según tus respuestas. Los ves al final de la lista.");
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

describe("discardReasons", () => {
  const questions = [
    { id: "has_employees", text: "¿Vas a contratar personal?", answer: false },
    { id: "signage", text: "¿Vas a poner un cartel?", answer: true },
    { id: "under_200_m2", text: "¿El local tiene menos de 200 m²?", answer: null },
  ];

  it("names each question that discarded the procedure with the answer given, in question order", () => {
    expect(discardReasons({ id: "1", title: "A", because: ["signage", "has_employees"] }, questions)).toEqual([
      { question: "¿Vas a contratar personal?", answer: "No" },
      { question: "¿Vas a poner un cartel?", answer: "Sí" },
    ]);
  });

  it("is empty when the API sends no reasons or they point to unknown or unanswered questions", () => {
    expect(discardReasons({ id: "1", title: "A" }, questions)).toEqual([]);
    expect(discardReasons({ id: "1", title: "A", because: ["unknown", "under_200_m2"] }, questions)).toEqual([]);
  });
});
