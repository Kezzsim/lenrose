import { useEffect, useRef, useState } from "react";
import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Divider,
  Skeleton,
  Stack,
  Typography,
} from "@mui/material";
import { useHits } from "react-instantsearch";
import type { SearchHitDocument } from "../api/client";
import { useTiledNode } from "../tiled/useTiledNode";
import { useStreamFacet } from "../state/StreamFacetContext";
import { NodeViewer, StreamViewer, TiledFallback } from "../tiled/viewers/ViewerDispatch";

function formatDisplayValue(value: unknown): string | null {
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed || null;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    const formatted = value
      .map(formatDisplayValue)
      .filter((part): part is string => Boolean(part));
    return formatted.length ? formatted.join(", ") : null;
  }
  return null;
}

// Lazy preview: only fetch from Tiled once the card scrolls into view. Combined
// with the concurrency cap in the Tiled client, this keeps the number of live
// Tiled requests bounded even when many results are rendered.
function useInView<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || inView) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setInView(true);
          observer.disconnect();
        }
      },
      { rootMargin: "100px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [inView]);
  return { ref, inView };
}

function Preview({ doc }: { doc: SearchHitDocument }) {
  const { node, loading, unavailable } = useTiledNode(doc.tiled_key);
  const { registerStreams, resolveForRecord } = useStreamFacet();

  // Report discovered streams to the app-wide facet registry.
  const streamNames = node?.streams.map((s) => s.name) ?? [];
  const streamKey = streamNames.join("|");
  useEffect(() => {
    if (streamNames.length) registerStreams(streamNames);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamKey]);

  if (loading) return <Skeleton variant="rectangular" height={120} />;
  if (unavailable || !node) return <TiledFallback doc={doc} compact />;

  // Container (BlueskyRun): render the resolved/selected stream.
  if (node.structureFamily === "container") {
    if (!node.streams.length) return <TiledFallback doc={doc} compact />;
    const chosenName = resolveForRecord(streamNames);
    const stream = node.streams.find((s) => s.name === chosenName);
    if (!stream) return <TiledFallback doc={doc} compact />;
    return <StreamViewer segments={stream.segments} doc={doc} compact />;
  }

  // Leaf node (array/table/etc.): render directly.
  return <NodeViewer resource={node.resource} compact />;
}

function ResultCard({
  doc,
  displayField,
  onSelect,
}: {
  doc: SearchHitDocument;
  displayField: string;
  onSelect: (doc: SearchHitDocument) => void;
}) {
  const { ref, inView } = useInView<HTMLDivElement>();
  const title = formatDisplayValue(doc[displayField]) ?? doc.uuid;

  return (
    <Card variant="outlined" ref={ref}>
      <CardActionArea onClick={() => onSelect(doc)}>
        <CardContent>
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
            <Typography variant="subtitle1" fontWeight={600}>
              {title}
            </Typography>
            <Chip label={doc.collection} size="small" color="secondary" />
            {doc.structure_family && (
              <Chip
                label={doc.structure_family}
                size="small"
                variant="outlined"
              />
            )}
          </Stack>
        </CardContent>
      </CardActionArea>
      <Divider />
      <Box sx={{ px: 2, py: 1 }}>
        {inView ? (
          <Preview doc={doc} />
        ) : (
          <Skeleton variant="rectangular" height={120} />
        )}
      </Box>
    </Card>
  );
}

export function ResultList({
  onSelect,
  displayField,
}: {
  onSelect: (doc: SearchHitDocument) => void;
  displayField: string;
}) {
  const { items } = useHits<SearchHitDocument>();

  if (!items.length) {
    return <Typography color="text.secondary">No results.</Typography>;
  }

  return (
    <Stack spacing={1}>
      {items.map((document) => (
        <ResultCard
          key={document.objectID ?? document.id}
          doc={document}
          displayField={displayField}
          onSelect={onSelect}
        />
      ))}
    </Stack>
  );
}
