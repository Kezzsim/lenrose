import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  CircularProgress,
  Divider,
  Drawer,
  IconButton,
  MenuItem,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import type { SearchHitDocument } from "../api/client";
import { useTiledNode } from "../tiled/useTiledNode";
import { useStreamFacet } from "../state/StreamFacetContext";
import {
  NodeViewer,
  StreamViewer,
  TiledFallback,
} from "../tiled/viewers/ViewerDispatch";
import { JsonViewer } from "../tiled/viewers/JsonViewer";

const DRAWER_WIDTH = 720;

// Larger, interactive version of the result-card preview. Loads the record's
// Tiled node directly (no server proxy); lets the user pick which stream to view
// and inspect the Tiled metadata. On failure it shows a warning plus the record's
// indexed Typesense fields (there is no meaningful data behind /api/records).
export function RecordDetailDrawer({
  doc,
  onClose,
}: {
  doc: SearchHitDocument | null;
  onClose: () => void;
}) {
  return (
    <Drawer anchor="right" open={!!doc} onClose={onClose}>
      <Box sx={{ width: DRAWER_WIDTH, maxWidth: "100vw", p: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Record</Typography>
          <IconButton onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Box>
        <Divider sx={{ my: 1 }} />
        {doc && <RecordDetailBody doc={doc} />}
      </Box>
    </Drawer>
  );
}

function RecordDetailBody({ doc }: { doc: SearchHitDocument }) {
  const { node, loading, unavailable } = useTiledNode(doc.tiled_key);
  const { resolveForRecord } = useStreamFacet();
  const [tab, setTab] = useState(0);
  const [streamName, setStreamName] = useState<string | null>(null);

  const streamNames = node?.streams.map((s) => s.name) ?? [];
  const isContainer = node?.structureFamily === "container";

  // Default the selected stream to the facet-resolved one for this record.
  useEffect(() => {
    if (isContainer && streamNames.length) {
      setStreamName((prev) =>
        prev && streamNames.includes(prev)
          ? prev
          : resolveForRecord(streamNames) ?? streamNames[0]
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamNames.join("|"), isContainer]);

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        {doc.tiled_key}
      </Typography>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 1 }}>
        <Tab label="Data" />
        <Tab label="Metadata" />
      </Tabs>

      {tab === 0 && (
        <Box>
          {loading && <CircularProgress size={24} />}
          {!loading && (unavailable || !node) && (
            <TiledFallback doc={doc} />
          )}
          {!loading && node && isContainer && streamNames.length > 0 && (
            <>
              <TextField
                select
                size="small"
                label="Stream"
                value={streamName ?? ""}
                onChange={(e) => setStreamName(e.target.value)}
                sx={{ mb: 2, minWidth: 220 }}
              >
                {node.streams.map((s) => (
                  <MenuItem key={s.name} value={s.name}>
                    {s.name}
                  </MenuItem>
                ))}
              </TextField>
              {streamName &&
                (() => {
                  const stream = node.streams.find(
                    (s) => s.name === streamName
                  );
                  return stream ? (
                    <StreamViewer segments={stream.segments} doc={doc} />
                  ) : null;
                })()}
            </>
          )}
          {!loading && node && isContainer && streamNames.length === 0 && (
            <Alert severity="info" sx={{ mb: 1 }}>
              This container has no streams to display.
              <Box mt={1}>
                <TiledFallback
                  doc={doc}
                  reason="Showing indexed metadata."
                />
              </Box>
            </Alert>
          )}
          {!loading && node && !isContainer && (
            <NodeViewer resource={node.resource} />
          )}
        </Box>
      )}

      {tab === 1 && (
        <Box>
          {loading && <CircularProgress size={24} />}
          {!loading && node && (
            <JsonViewer data={node.resource.attributes?.metadata ?? {}} />
          )}
          {!loading && (unavailable || !node) && (
            <>
              <Alert severity="warning" sx={{ mb: 1 }}>
                Could not load metadata from Tiled; showing indexed fields.
              </Alert>
              <JsonViewer data={doc} />
            </>
          )}
        </Box>
      )}
    </Box>
  );
}
