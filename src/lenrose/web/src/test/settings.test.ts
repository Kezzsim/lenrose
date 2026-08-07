import { describe, it, expect } from "vitest";
import { resolveTypesense } from "../state/settings";
import type { SearchConfig } from "../api/client";

const config: SearchConfig = {
  typesense: {
    host: "server-host",
    port: 8108,
    protocol: "https",
    apiKey: "server-scoped-key",
  },
  collection: "lenrose_records",
  queryBy: ["plan_name"],
  facets: ["collection"],
  facetTypes: {},
  displayFields: [{ value: "uuid", label: "UUID", field: "uuid" }],
  defaultDisplay: "uuid",
  tiled: { configured: true, method: "api_key", apiUrl: "http://tiled/api/v1" },
};

describe("resolveTypesense", () => {
  it("uses the server-provided scoped search key and endpoint", () => {
    expect(resolveTypesense(config)).toEqual({
      host: "server-host",
      port: 8108,
      protocol: "https",
      apiKey: "server-scoped-key",
    });
  });

  it("returns null when there is no server config", () => {
    expect(resolveTypesense(null)).toBeNull();
  });
});
