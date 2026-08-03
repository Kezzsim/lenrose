// Lightweight API client for the Lenrose backend.

export interface SearchHitDocument {
  id: string;
  uuid: string;
  collection: string;
  tiled_key: string;
  structure_family?: string;
  specs?: string[];
  [key: string]: unknown;
}

export interface FacetCount {
  field_name: string;
  counts: { value: string; count: number }[];
}

export interface FacetsResponse {
  facets: string[];
  facetTypes: Record<string, string>;
}

export interface SearchResponse {
  found: number;
  page: number;
  hits: { document: SearchHitDocument }[];
  facet_counts?: FacetCount[];
}

export interface RecordDetail {
  uuid: string;
  collection: string;
  tiled_key: string;
  structure_family: string | null;
  metadata: Record<string, unknown>;
}

const base = "";

export async function search(params: {
  q: string;
  facetBy?: string;
  filterBy?: string;
  page?: number;
  perPage?: number;
}): Promise<SearchResponse> {
  const qs = new URLSearchParams();
  qs.set("q", params.q || "*");
  if (params.facetBy) qs.set("facet_by", params.facetBy);
  if (params.filterBy) qs.set("filter_by", params.filterBy);
  qs.set("page", String(params.page ?? 1));
  qs.set("per_page", String(params.perPage ?? 20));
  const res = await fetch(`${base}/api/search?${qs.toString()}`);
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

export async function getFacets(): Promise<FacetsResponse> {
  const res = await fetch(`${base}/api/facets`);
  if (!res.ok) return { facets: ["collection"], facetTypes: {} };
  const data = await res.json();
  return {
    facets: data.facets ?? ["collection"],
    facetTypes: data.facet_types ?? {},
  };
}

export async function getRecord(
  uuid: string,
  collection: string
): Promise<RecordDetail> {
  const qs = new URLSearchParams({ collection });
  const res = await fetch(`${base}/api/records/${uuid}?${qs.toString()}`);
  if (!res.ok) throw new Error(`Record load failed: ${res.status}`);
  return res.json();
}
