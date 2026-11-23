import { describe, expect, it } from "vitest";
import type { Requirement } from "../types";
import { groupRequirements, requirementCount } from "./requirementGroups";

const origin = (id: string) => ({ procedure_id: id, procedure_title: `Trámite ${id}`, official_url: `https://x/${id}` });
const req = (id: string, ...origins: string[]): Requirement => ({ id, text: `Req ${id}`, heading: null, origins: origins.map(origin) });

describe("groupRequirements", () => {
  it("puts shared requirements first, then one group per procedure in the procedures order", () => {
    const groups = groupRequirements(
      [req("r1", "b"), req("r2", "a", "b"), req("r3", "a"), req("r4", "b")],
      [{ id: "a", title: "Trámite a" }, { id: "b", title: "Trámite b" }],
    );
    expect(groups.map(g => [g.id, g.items.map(i => i.id)])).toEqual([
      ["shared", ["r2"]],
      ["a", ["r3"]],
      ["b", ["r1", "r4"]],
    ]);
    expect(groups[0].title).toBe("Sirve para varios trámites");
    expect(groups[1].title).toBe("Trámite a");
  });

  it("keeps requirements of a procedure that is not listed and those without origin", () => {
    const groups = groupRequirements([req("r1", "z"), req("r2")], []);
    expect(groups.map(g => [g.id, g.title, g.items.map(i => i.id)])).toEqual([
      ["z", "Trámite z", ["r1"]],
      ["other", "Otros requisitos", ["r2"]],
    ]);
  });

  it("treats a procedure listed twice in the origins as one", () => {
    const groups = groupRequirements([req("r1", "a", "a")], [{ id: "a", title: "Trámite a" }]);
    expect(groups.map(g => [g.id, g.items.map(i => i.origins.length)])).toEqual([["a", [1]]]);
  });

  it("omits empty groups", () => {
    expect(groupRequirements([], [{ id: "a", title: "Trámite a" }])).toEqual([]);
  });
});

describe("requirementCount", () => {
  it("counts every requirement a procedure needs, shared ones included", () => {
    const requirements = [req("r1", "a"), req("r2", "a", "b"), req("r3", "b")];
    expect(requirementCount(requirements, "a")).toBe(2);
    expect(requirementCount(requirements, "c")).toBe(0);
  });
});
