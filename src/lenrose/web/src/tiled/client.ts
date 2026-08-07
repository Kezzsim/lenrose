// Direct browser -> Tiled HTTP API client.
//
// Ported/adapted from bluesky/tiled web-frontend/src/client.ts. Instead of
// axios we use fetch, but preserve the same behaviors:
//   - a "transformLinks" step that rewrites absolute URLs in `links` fields to
//     relative paths so the UI works regardless of the origin the server
//     reports (upstream client.ts `toRelativePath` / `transformLinks`);
//   - metadata / search / array-data helpers mirroring upstream
//     `metadata()`, `search()`, and the array `?format=application/json&slice=`
//     fetch used in components/array-1d/array-1d.tsx.
//
// For security the browser only ever authenticates to Tiled anonymously or with
// a user-supplied API key (Authorization: Apikey <key>). No password/token flow
// runs in the browser.

import type {
  Credentials,
} from "../state/credentials";
import type {
  TiledAttributes,
  TiledResource,
  TiledSearchResponse,
} from "./types";

export interface TiledClientConfig {
  /** Public Tiled REST base, e.g. https://host/api/v1. */
  apiUrl: string;
  credentials?: Credentials;
}

export class TiledUnavailableError extends Error {}

// ---- link normalization (upstream: transformLinks) -------------------------

function toRelativePath(urlString: string): string {
  try {
    const url = new URL(urlString);
    return url.pathname + url.search + url.hash;
  } catch {
    return urlString;
  }
}

// Recursively rewrite absolute URLs inside any `links` object to relative
// paths. Mirrors upstream so downstream code can resolve links against apiUrl.
function transformLinks<T>(data: T): T {
  if (typeof data === "object" && data !== null) {
    const transformed: Record<string, unknown> = Array.isArray(data)
      ? ([] as unknown as Record<string, unknown>)
      : {};
    for (const key in data as Record<string, unknown>) {
      const value = (data as Record<string, unknown>)[key];
      if (key === "links" && typeof value === "object" && value !== null) {
        const links: Record<string, unknown> = {};
        for (const linkKey in value as Record<string, unknown>) {
          const linkValue = (value as Record<string, unknown>)[linkKey];
          links[linkKey] =
            typeof linkValue === "string"
              ? toRelativePath(linkValue)
              : linkValue;
        }
        transformed[key] = links;
      } else {
        transformed[key] = transformLinks(value);
      }
    }
    return transformed as T;
  }
  return data;
}

// ---- concurrency limiting --------------------------------------------------
//
// Cap concurrent Tiled requests so fast scrolling over many result cards cannot
// stampede the Tiled server. Requests beyond the cap queue until a slot frees.

const MAX_CONCURRENT_TILED = 8;
let active = 0;
const queue: Array<() => void> = [];

function acquire(): Promise<void> {
  if (active < MAX_CONCURRENT_TILED) {
    active += 1;
    return Promise.resolve();
  }
  return new Promise((resolve) => queue.push(resolve));
}

function release(): void {
  active -= 1;
  const next = queue.shift();
  if (next) {
    active += 1;
    next();
  }
}

// ---- core request ----------------------------------------------------------

function authHeaders(credentials?: Credentials): Record<string, string> {
  if (
    credentials?.tiledAuthMethod === "api_key" &&
    credentials.tiledApiKey
  ) {
    return { Authorization: `Apikey ${credentials.tiledApiKey}` };
  }
  return {};
}

/** Resolve a possibly-relative link against the configured Tiled API origin. */
function resolveUrl(config: TiledClientConfig, link: string): string {
  if (/^https?:\/\//i.test(link)) return link;
  // apiUrl ends with /api/v1; links are absolute-from-root paths like
  // /api/v1/metadata/... after transformLinks, or bare segments.
  try {
    const origin = new URL(config.apiUrl).origin;
    if (link.startsWith("/")) return origin + link;
    return `${config.apiUrl.replace(/\/$/, "")}/${link}`;
  } catch {
    return link;
  }
}

async function request<T>(
  config: TiledClientConfig,
  url: string,
  signal: AbortSignal,
  responseType: "json" | "arraybuffer" = "json"
): Promise<T> {
  await acquire();
  try {
    const res = await fetch(url, {
      signal,
      headers: {
        ...authHeaders(config.credentials),
        Accept:
          responseType === "json" ? "application/json" : "application/octet-stream",
      },
    });
    if (!res.ok) {
      throw new TiledUnavailableError(
        `Tiled request failed (${res.status}) for ${url}`
      );
    }
    if (responseType === "arraybuffer") {
      return (await res.arrayBuffer()) as unknown as T;
    }
    const data = (await res.json()) as T;
    return transformLinks(data);
  } finally {
    release();
  }
}

// ---- public API (mirrors upstream client.ts helpers) -----------------------

/**
 * Fetch metadata for a node at the given path segments.
 * Upstream: client.ts `metadata()` -> GET {apiURL}/metadata/{segments}.
 */
export async function fetchMetadata(
  config: TiledClientConfig,
  segments: string[],
  signal: AbortSignal,
  fields: string[] = []
): Promise<TiledResource> {
  const path = segments.map(encodeURIComponent).join("/");
  const fieldQ = fields.length ? `?fields=${fields.join("&fields=")}` : "";
  const url = `${config.apiUrl.replace(/\/$/, "")}/metadata/${path}${fieldQ}`;
  const body = await request<{ data: TiledResource }>(config, url, signal);
  return body.data;
}

/**
 * List the immediate children of a container node (its streams).
 * Upstream: client.ts `search()` -> GET {apiURL}/search/{segments}. We request
 * only the structure_family field cheaply.
 */
export async function fetchContents(
  config: TiledClientConfig,
  segments: string[],
  signal: AbortSignal,
  pageLimit = 100
): Promise<TiledResource[]> {
  const path = segments.map(encodeURIComponent).join("/");
  const url =
    `${config.apiUrl.replace(/\/$/, "")}/search/${path}` +
    `?page[offset]=0&page[limit]=${pageLimit}` +
    `&fields=structure_family&fields=structure&fields=specs`;
  const body = await request<TiledSearchResponse>(config, url, signal);
  return body.data ?? [];
}

/**
 * Fetch 1-D array data as JSON, optionally sliced.
 * Upstream: components/array-1d/array-1d.tsx
 *   GET {link}?format=application/json&slice={a}:{b}
 */
export async function fetchArrayJson(
  config: TiledClientConfig,
  link: string,
  signal: AbortSignal,
  slice?: string
): Promise<number[] | number[][]> {
  let url = resolveUrl(config, link);
  const sep = url.includes("?") ? "&" : "?";
  url += `${sep}format=application/json`;
  if (slice) url += `&slice=${slice}`;
  return request<number[] | number[][]>(config, url, signal);
}

export type { TiledAttributes };
