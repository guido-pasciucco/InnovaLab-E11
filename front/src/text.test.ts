import { describe, expect, it } from "vitest";
import { discardedByAnswer, excludedNote, listInSpanish } from "./text";

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

  it("gives only the total when the API says which answer discarded each one", () => {
    expect(excludedNote([{ id: "1", title: "A", because: ["has_employees"] }, { id: "2", title: "B", because: ["signage"] }], 2))
      .toBe("Descartamos 2 trámites según tus respuestas.");
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

describe("discardedByAnswer", () => {
  const excluded = [
    { id: "1", title: "Registro de Empleadores", because: ["has_employees"] },
    { id: "2", title: "Habilitación exprés", because: ["under_200_m2", "has_employees"] },
    { id: "3", title: "Visado de anuncio", because: ["signage"] },
  ];

  it("names what the answer to that question discarded, quoting the answer", () => {
    expect(discardedByAnswer({ id: "has_employees", answer: false }, excluded))
      .toBe("Con «No» descartamos: Registro de Empleadores y Habilitación exprés.");
    expect(discardedByAnswer({ id: "signage", answer: true }, excluded))
      .toBe("Con «Sí» descartamos: Visado de anuncio.");
  });

  it("says nothing when the question is unanswered, discarded nothing or the API sends no reasons", () => {
    expect(discardedByAnswer({ id: "has_employees", answer: null }, excluded)).toBeNull();
    expect(discardedByAnswer({ id: "takes_over_existing", answer: true }, excluded)).toBeNull();
    expect(discardedByAnswer({ id: "has_employees", answer: false }, [{ id: "1", title: "A" }])).toBeNull();
    expect(discardedByAnswer({ id: "has_employees", answer: false }, undefined)).toBeNull();
  });
});
