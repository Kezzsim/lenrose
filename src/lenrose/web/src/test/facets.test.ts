import { describe, it, expect } from "vitest";
import { isNumericType } from "../components/Facets";

describe("isNumericType", () => {
  it("treats scalar and array int/float as numeric", () => {
    for (const t of ["int32", "int64", "float", "int64[]", "float[]"]) {
      expect(isNumericType(t)).toBe(true);
    }
  });

  it("treats string and bool as non-numeric", () => {
    for (const t of ["string", "string[]", "bool", "bool[]", undefined]) {
      expect(isNumericType(t)).toBe(false);
    }
  });
});
