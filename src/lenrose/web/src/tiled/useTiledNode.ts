// Lazy, cancellable hook to load a Tiled node by its tiled_key.
//
// - Fetches metadata (structure_family, structure, metadata) for the node.
// - If the node is a container (e.g. a BlueskyRun), lists its immediate
//   children (streams) shallowly.
// - Caches results per tiled_key in an in-memory Map shared across all cards so
//   the flyout and card don't double-fetch.
// - Aborts in-flight requests on unmount (fast scroll => request cancelled),
//   which together with the concurrency cap in client.ts protects Tiled.
//
// tiled_key is "{collection}/{uuid}" (see backend ingest.make_doc_id). Tiled
// path segments are the parts of that key.

import { useEffect, useState } from "react";
import {
  fetchContents,
  fetchMetadata,
  TiledUnavailableError,
  type TiledClientConfig,
} from "./client";
import type { TiledResource } from "./types";
import { useTiledConfig } from "./TiledProvider";

export interface TiledStream {
  /** Display name, e.g. "primary" or nested "primary/config". */
  name: string;
  /** Path segments from the record root to this stream. */
  segments: string[];
  structureFamily?: string;
}

export interface TiledNode {
  resource: TiledResource;
  structureFamily?: string;
  /** Immediate child streams (shallow) if this node is a container. */
  streams: TiledStream[];
}

interface NodeState {
  node: TiledNode | null;
  loading: boolean;
  /** True when Tiled could not be reached / node unavailable. */
  unavailable: boolean;
  error: string | null;
}

// tiled_key -> cached node (keyed also by apiUrl+auth to avoid cross-config bleed).
const cache = new Map<string, TiledNode>();

function cacheKey(config: TiledClientConfig, tiledKey: string): string {
  const auth =
    config.credentials?.tiledAuthMethod === "api_key"
      ? `k:${config.credentials.tiledApiKey ?? ""}`
      : "anon";
  return `${config.apiUrl}|${auth}|${tiledKey}`;
}

function segmentsOf(tiledKey: string): string[] {
  return tiledKey.split("/").filter(Boolean);
}

async function loadNode(
  config: TiledClientConfig,
  tiledKey: string,
  signal: AbortSignal
): Promise<TiledNode> {
  const segments = segmentsOf(tiledKey);
  const resource = await fetchMetadata(config, segments, signal);
  const structureFamily = resource.attributes?.structure_family;

  let streams: TiledStream[] = [];
  if (structureFamily === "container") {
    const children = await fetchContents(config, segments, signal);
    streams = children.map((child) => ({
      name: child.id,
      segments: [...segments, child.id],
      structureFamily: child.attributes?.structure_family,
    }));
  }
  return { resource, structureFamily, streams };
}

export function useTiledNode(
  tiledKey: string | null,
  enabled = true
): NodeState {
  const config = useTiledConfig();
  const [state, setState] = useState<NodeState>({
    node: null,
    loading: false,
    unavailable: false,
    error: null,
  });

  useEffect(() => {
    if (!enabled || !tiledKey) return;
    if (!config) {
      setState({ node: null, loading: false, unavailable: true, error: null });
      return;
    }
    const key = cacheKey(config, tiledKey);
    const cached = cache.get(key);
    if (cached) {
      setState({ node: cached, loading: false, unavailable: false, error: null });
      return;
    }

    const controller = new AbortController();
    setState({ node: null, loading: true, unavailable: false, error: null });
    loadNode(config, tiledKey, controller.signal)
      .then((node) => {
        cache.set(key, node);
        setState({ node, loading: false, unavailable: false, error: null });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        const unavailable = err instanceof TiledUnavailableError;
        setState({
          node: null,
          loading: false,
          unavailable,
          error: String(err),
        });
      });

    return () => controller.abort();
  }, [config, tiledKey, enabled]);

  return state;
}

/** Lazily expand a container stream into its nested children (for '/'-joined names). */
export async function expandStream(
  config: TiledClientConfig,
  segments: string[],
  signal: AbortSignal
): Promise<TiledStream[]> {
  const children = await fetchContents(config, segments, signal);
  return children.map((child) => ({
    name: [...segments.slice(1), child.id].join("/"),
    segments: [...segments, child.id],
    structureFamily: child.attributes?.structure_family,
  }));
}
