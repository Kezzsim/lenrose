// Minimal subset of Tiled's OpenAPI types actually used by the Lenrose viewers.
//
// Derived from the shapes in bluesky/tiled web-frontend
// (web-frontend/src/openapi_schemas.ts). We keep only what we consume so we
// don't have to vendor the full generated schema.

export interface TiledStructure {
  // Array structures
  shape?: number[];
  data_type?: {
    kind?: string;
    itemsize?: number;
    fields?: unknown; // record arrays: presence means "not viewable inline"
  };
  chunks?: number[][];
  dims?: string[] | null;
  // Table / dataframe structures
  columns?: string[];
  // Container structures expose contents via links, not here.
  [key: string]: unknown;
}

export interface TiledLinks {
  self?: string;
  full?: string;
  block?: string;
  search?: string;
  // Tiled emits many more; keep it open.
  [key: string]: string | undefined;
}

export interface TiledAttributes {
  ancestors?: string[];
  structure_family?: string;
  specs?: Array<{ name: string; version?: string | null }>;
  metadata?: Record<string, unknown>;
  structure?: TiledStructure | null;
  sorting?: unknown;
  [key: string]: unknown;
}

export interface TiledResource {
  id: string;
  attributes: TiledAttributes;
  links: TiledLinks;
  meta?: Record<string, unknown> | null;
}

export interface TiledSearchResponse {
  data: TiledResource[];
  links?: TiledLinks & { next?: string | null };
  meta?: { count?: number } & Record<string, unknown>;
}

export type StructureFamily =
  | "container"
  | "array"
  | "table"
  | "awkward"
  | "sparse"
  | string;
