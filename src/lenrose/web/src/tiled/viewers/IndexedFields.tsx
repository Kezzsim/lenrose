// Fallback display: render the fields the user chose to index in Typesense for
// this record. Used when Tiled data cannot be loaded (no viewer path, node
// unavailable, or Tiled not configured) so the card/flyout still shows the
// meaningful, searchable metadata already present on the search hit.

import Box from "@mui/material/Box";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableRow from "@mui/material/TableRow";
import type { SearchHitDocument } from "../../api/client";

// System/internal fields we don't want to surface as "indexed metadata".
const HIDDEN = new Set([
  "id",
  "objectID",
  "tiled_key",
  "_parents",
  "__position",
  "_highlightResult",
]);

export function IndexedFields({
  doc,
  compact = false,
}: {
  doc: SearchHitDocument;
  compact?: boolean;
}) {
  const entries = Object.entries(doc).filter(
    ([k, v]) =>
      !HIDDEN.has(k) &&
      v !== undefined &&
      v !== null &&
      !(typeof k === "string" && k.startsWith("_"))
  );
  const shown = compact ? entries.slice(0, 6) : entries;

  return (
    <Box>
      <Table size="small">
        <TableBody>
          {shown.map(([k, v]) => (
            <TableRow key={k}>
              <TableCell
                sx={{ fontWeight: 600, width: "40%", verticalAlign: "top" }}
              >
                {k}
              </TableCell>
              <TableCell sx={{ wordBreak: "break-word" }}>
                {format(v)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  );
}

function format(value: unknown): string {
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
