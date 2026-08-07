// Table / dataframe viewer. Adapted from bluesky/tiled
// web-frontend/src/components/overview-table. Tiled serves table data as JSON
// (list of column arrays or records) at the node's `full` link with
// ?format=application/json. We render a bounded MUI table.

import { useEffect, useState } from "react";
import Box from "@mui/material/Box";
import Skeleton from "@mui/material/Skeleton";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import { fetchArrayJson } from "../client";
import { useTiledConfig } from "../TiledProvider";

// Tiled returns a table as an object mapping column -> array of values.
type TableData = Record<string, unknown[]>;

export function TableViewer({
  link,
  columns,
  compact = false,
  maxRows,
}: {
  link: string;
  columns?: string[];
  compact?: boolean;
  maxRows?: number;
}) {
  const config = useTiledConfig();
  const [data, setData] = useState<TableData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!config) return;
    const controller = new AbortController();
    setData(null);
    setError(null);
    // Reuse fetchArrayJson: it just does ?format=application/json on the link.
    fetchArrayJson(config, link, controller.signal)
      .then((d) => setData(d as unknown as TableData))
      .catch((e) => {
        if (!controller.signal.aborted) setError(String(e));
      });
    return () => controller.abort();
  }, [config, link]);

  if (error)
    return (
      <Box sx={{ fontSize: 12, color: "error.main" }}>
        Could not load table data.
      </Box>
    );
  if (!data) return <Skeleton variant="rectangular" height={compact ? 120 : 240} />;

  const cols = columns ?? Object.keys(data);
  const rowCount = cols.length ? (data[cols[0]]?.length ?? 0) : 0;
  const limit = maxRows ?? (compact ? 5 : 100);
  const shownRows = Math.min(rowCount, limit);

  return (
    <TableContainer sx={{ maxHeight: compact ? 200 : 400 }}>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            {cols.map((c) => (
              <TableCell key={c}>{c}</TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {Array.from({ length: shownRows }).map((_, r) => (
            <TableRow key={r}>
              {cols.map((c) => (
                <TableCell key={c}>{formatCell(data[c]?.[r])}</TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {rowCount > shownRows && (
        <Box sx={{ fontSize: 11, color: "text.secondary", p: 1 }}>
          Showing {shownRows} of {rowCount} rows.
        </Box>
      )}
    </TableContainer>
  );
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "number") return String(value);
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
