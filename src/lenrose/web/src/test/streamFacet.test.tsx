import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import {
  StreamFacetProvider,
  useStreamFacet,
} from "../state/StreamFacetContext";

function wrapper({ children }: { children: React.ReactNode }) {
  return <StreamFacetProvider>{children}</StreamFacetProvider>;
}

describe("StreamFacetContext", () => {
  it("registers streams as a persistent, sorted union with counts", () => {
    const { result } = renderHook(() => useStreamFacet(), { wrapper });

    act(() => result.current.registerStreams(["primary", "baseline"]));
    act(() => result.current.registerStreams(["primary"]));

    const names = result.current.streams.map((s) => s.name);
    expect(names).toEqual(["baseline", "primary"]);
    const primary = result.current.streams.find((s) => s.name === "primary");
    expect(primary?.count).toBe(2);
  });

  it("resolveForRecord returns first available when nothing selected", () => {
    const { result } = renderHook(() => useStreamFacet(), { wrapper });
    expect(result.current.resolveForRecord(["primary", "baseline"])).toBe(
      "primary"
    );
    expect(result.current.resolveForRecord([])).toBeNull();
  });

  it("resolveForRecord prefers a selected stream the record contains", () => {
    const { result } = renderHook(() => useStreamFacet(), { wrapper });
    act(() => {
      result.current.registerStreams(["primary", "baseline"]);
      result.current.toggle("baseline");
    });
    expect(result.current.resolveForRecord(["primary", "baseline"])).toBe(
      "baseline"
    );
    // Falls back to first available when the record lacks the selected stream.
    expect(result.current.resolveForRecord(["primary"])).toBe("primary");
  });

  it("toggle and clear manage the selection set", () => {
    const { result } = renderHook(() => useStreamFacet(), { wrapper });
    act(() => result.current.toggle("primary"));
    expect(result.current.selected.has("primary")).toBe(true);
    act(() => result.current.toggle("primary"));
    expect(result.current.selected.has("primary")).toBe(false);
    act(() => {
      result.current.toggle("primary");
      result.current.clear();
    });
    expect(result.current.selected.size).toBe(0);
  });
});
