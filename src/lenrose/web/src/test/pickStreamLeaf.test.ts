import { describe, it, expect } from "vitest";
import { pickStreamLeaf } from "../tiled/viewers/ViewerDispatch";

type Child = { id: string; attributes?: { structure_family?: string } };

const c = (id: string, family = "array"): Child => ({
  id,
  attributes: { structure_family: family },
});

describe("pickStreamLeaf", () => {
  it("returns null for no children", () => {
    expect(pickStreamLeaf([])).toBeNull();
  });

  it("prefers a child named 'data'", () => {
    const children = [c("internal", "table"), c("data", "array")];
    expect(pickStreamLeaf(children)?.id).toBe("data");
  });

  it("prefers 'internal' when there is no 'data' (BMM shape)", () => {
    const children = [
      c("internal", "table"),
      c("xs_channel01", "array"),
      c("xs_channel02", "array"),
    ];
    expect(pickStreamLeaf(children)?.id).toBe("internal");
  });

  it("falls back to first non-container child", () => {
    const children = [c("sub", "container"), c("xs_channel01", "array")];
    expect(pickStreamLeaf(children)?.id).toBe("xs_channel01");
  });

  it("falls back to the first child when all are containers", () => {
    const children = [c("a", "container"), c("b", "container")];
    expect(pickStreamLeaf(children)?.id).toBe("a");
  });
});
