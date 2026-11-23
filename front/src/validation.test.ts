import { describe, expect, it } from "vitest";
import { RESULT_LIMITS, TEXT_RULES, reachesThreshold, validateActivity, validateAddress, validateLimit } from "./validation";

describe("activity field", () => {
  it.each([
    ["", "Escribí la actividad que querés realizar."],
    ["    ", "Escribí algo más que espacios."],
    ["a", "Escribí al menos 2 caracteres."],
    [" a ", "Escribí al menos 2 caracteres."],
    ["x".repeat(101), "Usá como máximo 100 caracteres."],
  ])("%j → %s", (value, message) => {
    expect(validateActivity(value)).toBe(message);
  });

  it("accepts 2 to 100 characters after trimming", () => {
    expect(validateActivity("  pe  ")).toBeNull();
    expect(validateActivity("x".repeat(100))).toBeNull();
  });
});

describe("address field", () => {
  it.each([
    ["", "Escribí la dirección del local."],
    ["   ", "Escribí algo más que espacios."],
    ["ab", "Escribí al menos 3 caracteres."],
    ["x".repeat(201), "Usá como máximo 200 caracteres."],
  ])("%j → %s", (value, message) => {
    expect(validateAddress(value)).toBe(message);
  });

  it("accepts a normal address", () => {
    expect(validateAddress("Corrientes 2500")).toBeNull();
  });
});

describe("result limits match the API", () => {
  it.each([
    [RESULT_LIMITS.addresses, 1, 10],
    [RESULT_LIMITS.activities, 1, 10],
    [RESULT_LIMITS.procedures, 1, 20],
  ])("%o accepts %i..%i and rejects outside", (range, min, max) => {
    expect(validateLimit(min, range)).toBeNull();
    expect(validateLimit(max, range)).toBeNull();
    expect(validateLimit(min - 1, range)).not.toBeNull();
    expect(validateLimit(max + 1, range)).not.toBeNull();
  });
});

describe("suggestion thresholds", () => {
  it("asks for activities from 2 characters and for addresses from 3", () => {
    expect(reachesThreshold("p", TEXT_RULES.activity)).toBe(false);
    expect(reachesThreshold(" pe ", TEXT_RULES.activity)).toBe(true);
    expect(reachesThreshold("co", TEXT_RULES.address)).toBe(false);
    expect(reachesThreshold("cor", TEXT_RULES.address)).toBe(true);
    expect(reachesThreshold("   ", TEXT_RULES.procedureQuery)).toBe(false);
  });
});
