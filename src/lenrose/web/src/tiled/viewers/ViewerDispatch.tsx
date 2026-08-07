// Chooses the right Tiled viewer for a node based on its structure_family and
// structure. Mirrors the dispatch logic in bluesky/tiled
// web-frontend/src/components/overview-array/overview-array.tsx (shape-based
// 1-D vs N-D) and the per-structure_family overview components.
//
// Resolution order:
//   - container: resolve the selected stream (by path segments) and recurse
//     into that node's metadata; if it too is a container, dig one level for a
//     viewable leaf (e.g. primary -> data column). If nothing viewable, fall
//     back to indexed Typesense fields.
//   - array: 1-D -> Array1D, >=2-D -> ArrayND (image). Record arrays are not
//     viewable inline -> fallback.
//   - table: TableViewer.
//   - anything else / unavailable: IndexedFields fallback (with a warning when
//     Tiled was expected but failed).

import { useEffect, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Skeleton from "@mui/material/Skeleton";
import { Array1D } from "./Array1D";
import { ArrayND } from "./ArrayND";
import { TableViewer } from "./TableViewer";
import { IndexedFields } from "./IndexedFields";
import { fetchContents, fetchMetadata } from "../client";
import { useTiledConfig } from "../TiledProvider";
import type { TiledResource } from "../types";
import type { SearchHitDocument } from "../../api/client";

function arrayLink(resource: TiledResource): string | null {
  const links = resource.links ?? {};
  return links.full ?? links.block ?? links.self ?? null;
}

/**
 * Choose which child of a container stream to display. BlueskyRun streams like
 * `primary`/`baseline` hold their events table under `internal` (verified
 * against tiled-demo BMM data) and other conventions use `data`. Preference:
 *   1. a child named `data` (Databroker/xarray convention),
 *   2. a child named `internal` (canonical Bluesky events table),
 *   3. the first non-container child,
 *   4. the first child.
 * Returns null when there are no children.
 */
export function pickStreamLeaf<
  T extends { id: string; attributes?: { structure_family?: string } }
>(children: T[]): T | null {
  if (!children.length) return null;
  return (
    children.find((c) => c.id === "data") ??
    children.find((c) => c.id === "internal") ??
    children.find((c) => c.attributes?.structure_family !== "container") ??
    children[0]
  );
}


function ArrayViewer({
  resource,
  compact,
}: {
  resource: TiledResource;
  compact: boolean;
}) {
  const structure = resource.attributes?.structure;
  const shape = (structure?.shape as number[] | undefined) ?? [];
  const link = arrayLink(resource);

  if (structure?.data_type?.fields) {
    // Record array: upstream declares these non-viewable inline.
    return (
      <FallbackNote compact={compact} note="Record array — download to view." />
    );
  }
  if (!link || shape.length === 0) {
    return <FallbackNote compact={compact} note="No array data." />;
  }
  const name = resource.id || "value";
  return shape.length < 2 ? (
    <Array1D link={link} shape={shape} name={name} compact={compact} />
  ) : (
    <ArrayND link={link} shape={shape} compact={compact} />
  );
}

function FallbackNote({ note, compact }: { note: string; compact: boolean }) {
  return (
    <Box sx={{ fontSize: compact ? 11 : 13, color: "text.secondary", py: 1 }}>
      {note}
    </Box>
  );
}

/**
 * Render a resolved (leaf) Tiled node with the appropriate viewer.
 */
export function NodeViewer({
  resource,
  compact = false,
}: {
  resource: TiledResource;
  compact?: boolean;
}) {
  const family = resource.attributes?.structure_family;
  switch (family) {
    case "array":
    case "sparse":
      return <ArrayViewer resource={resource} compact={compact} />;
    case "table": {
      const link = resource.links?.full ?? resource.links?.self ?? null;
      const columns = resource.attributes?.structure?.columns as
        | string[]
        | undefined;
      return link ? (
        <TableViewer link={link} columns={columns} compact={compact} />
      ) : (
        <FallbackNote compact={compact} note="No table data." />
      );
    }
    default:
      return <FallbackNote compact={compact} note="No inline viewer for this data." />;
  }
}

/**
 * Resolve a stream (by path segments) within a record and render it. Used by
 * the card and flyout for container records (BlueskyRuns). If the stream node
 * is itself a container (e.g. "primary" holding "data"/"config"), it digs one
 * level to find the first viewable leaf (prefers a child named "data").
 */
export function StreamViewer({
  segments,
  doc,
  compact = false,
}: {
  segments: string[];
  doc: SearchHitDocument;
  compact?: boolean;
}) {
  const config = useTiledConfig();
  const [resource, setResource] = useState<TiledResource | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!config) {
      setFailed(true);
      return;
    }
    const controller = new AbortController();
    setResource(null);
    setFailed(false);

    (async () => {
      let node = await fetchMetadata(config, segments, controller.signal);
      // Dig one level into container streams to find a viewable leaf.
      if (node.attributes?.structure_family === "container") {
        const children = await fetchContents(
          config,
          segments,
          controller.signal
        );
        const preferred = pickStreamLeaf(children);
        if (preferred) {
          node = await fetchMetadata(
            config,
            [...segments, preferred.id],
            controller.signal
          );
        }
      }
      setResource(node);
    })().catch(() => {
      if (!controller.signal.aborted) setFailed(true);
    });

    return () => controller.abort();
  }, [config, segments.join("/")]);

  if (failed) return <TiledFallback doc={doc} compact={compact} />;
  if (!resource)
    return <Skeleton variant="rectangular" height={compact ? 120 : 240} />;
  return <NodeViewer resource={resource} compact={compact} />;
}

/**
 * Fallback shown when Tiled data cannot be loaded: a warning plus the indexed
 * Typesense fields for the record.
 */
export function TiledFallback({
  doc,
  compact = false,
  reason,
}: {
  doc: SearchHitDocument;
  compact?: boolean;
  reason?: string;
}) {
  return (
    <Box>
      <Alert severity="warning" sx={{ py: 0, mb: 1, fontSize: compact ? 11 : 13 }}>
        {reason ?? "Could not load data from Tiled; showing indexed metadata only."}
      </Alert>
      <IndexedFields doc={doc} compact={compact} />
    </Box>
  );
}
