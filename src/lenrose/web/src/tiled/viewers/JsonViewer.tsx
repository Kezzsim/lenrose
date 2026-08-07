// JSON / metadata viewer. Analogous to bluesky/tiled
// web-frontend/src/components/json-viewer + metadata-view: a pretty-printed,
// scrollable JSON block. Used for Tiled metadata and as a fallback display.

import Box from "@mui/material/Box";

export function JsonViewer({
  data,
  maxHeight = 400,
}: {
  data: unknown;
  maxHeight?: number | string;
}) {
  return (
    <Box
      component="pre"
      sx={{
        fontSize: 12,
        whiteSpace: "pre-wrap",
        wordBreak: "break-word",
        bgcolor: "#0d1117",
        color: "#c9d1d9",
        p: 1.5,
        borderRadius: 1,
        overflow: "auto",
        maxHeight,
        m: 0,
      }}
    >
      {JSON.stringify(data, null, 2)}
    </Box>
  );
}
