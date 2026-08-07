// Lightweight API client for the Lenrose backend.
//
// The backend is now minimal: it hands the browser its search configuration
// (public Typesense endpoint + scoped search-only key + facet/display metadata)
// and loads full record metadata from Tiled on demand. All searching happens
// client-side via the Typesense InstantSearch adapter.

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
  };
}

export interface RecordDetail {
  uuid: string;
  collection: string;
  tiled_key: string;
  structure_family: string | null;
  metadata: Record<string, unknown>;
}

const base = "";

export async function getSearchConfig(): Promise<SearchConfig> {
  const res = await fetch(`${base}/api/search-config`);
  if (!res.ok) throw new Error(`Search config failed: ${res.status}`);
  return res.json();
}

export async function getRecord(
  uuid: string,
  collection: string,
  auth?: {
    method?: "anonymous" | "api_key" | "password";
    apiKey?: string;
    username?: string;
    password?: string;
  }
): Promise<RecordDetail> {
  const qs = new URLSearchParams({ collection });
  const headers: Record<string, string> = {};
  if (auth?.method) headers["X-Tiled-Auth-Method"] = auth.method;
  if (auth?.apiKey) headers["X-Tiled-Api-Key"] = auth.apiKey;
  if (auth?.username) headers["X-Tiled-Username"] = auth.username;
  if (auth?.password) headers["X-Tiled-Password"] = auth.password;
  const res = await fetch(`${base}/api/records/${uuid}?${qs.toString()}`, {
    headers,
  });
  if (!res.ok) throw new Error(`Record load failed: ${res.status}`);
  return res.json();
}
