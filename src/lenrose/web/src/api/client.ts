// Lightweight API client for the Lenrose backend.
//
// The backend is minimal: it hands the browser its search configuration
// (public Typesense endpoint + scoped search-only key + facet/display metadata
// + the public Tiled API URL). All searching happens client-side via the
// Typesense InstantSearch adapter, and all record data is loaded *directly*
// from Tiled in the browser (see src/tiled/). The server does not proxy data.

export interface SearchHitDocument {
  id: string;
  objectID?: string;
  uuid: string;
  collection: string;
  tiled_key: string;
  structure_family?: string;
  specs?: string[];
  [key: string]: unknown;
}

export interface DisplayFieldOption {
  value: string;
  label: string;
  field: string;
}

export interface SearchConfig {
  typesense: {
    host: string;
    port: number;
    protocol: string;
    apiKey: string;
  };
  collection: string;
  queryBy: string[];
  facets: string[];
  facetTypes: Record<string, string>;
  displayFields: DisplayFieldOption[];
  defaultDisplay: string;
  tiled: {
    configured: boolean;
    method: "anonymous" | "api_key" | null;
    /** Public Tiled REST base (e.g. https://host/api/v1) for direct browser access. */
    apiUrl: string | null;
  };
}

const base = "";

export async function getSearchConfig(): Promise<SearchConfig> {
  const res = await fetch(`${base}/api/search-config`);
  if (!res.ok) throw new Error(`Search config failed: ${res.status}`);
  return res.json();
}
