import { describe, expect, it } from "vitest";
import { nextPending } from "./orientationProgress";

const items = [{ id: "a", title: "A" }, { id: "b", title: "B" }, { id: "c", title: "C" }];

describe("nextPending", () => {
  it("returns the first item, in list order, that is not reviewed yet", () => {
    expect(nextPending(items, ["a", "c"])).toEqual({ id: "b", title: "B" });
    expect(nextPending(items, [])).toEqual({ id: "a", title: "A" });
  });

  it("returns null when every item is reviewed or there are none", () => {
    expect(nextPending(items, ["c", "b", "a"])).toBeNull();
    expect(nextPending([], [])).toBeNull();
  });
});
