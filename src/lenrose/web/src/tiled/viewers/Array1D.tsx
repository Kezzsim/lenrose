// 1-D array viewer. Adapted from bluesky/tiled
// web-frontend/src/components/array-1d/array-1d.tsx.
//
// In the upstream component a range slider selects a window and data is fetched
// via `${link}?format=application/json&slice=a:b`. We use the same slicing but
// fetch through our concurrency-limited client (fetchArrayJson) and support a
// compact mode (no controls, capped points) for the small preview card.

import { useEffect, useMemo, useState } from "react";
import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormLabel from "@mui/material/FormLabel";
import Radio from "@mui/material/Radio";
import RadioGroup from "@mui/material/RadioGroup";
import Skeleton from "@mui/material/Skeleton";
import Slider from "@mui/material/Slider";
import Box from "@mui/material/Box";
import { debounce } from "ts-debounce";
import { ArrayLineChart } from "./Line";
import { fetchArrayJson } from "../client";
import { useTiledConfig } from "../TiledProvider";

const LIMIT = 1000; // largest window we request at once (upstream LIMIT)
const MAX_DEFAULT_RANGE = 1000;

export function Array1D({
  link,
  shape,
  name,
  compact = false,
  height,
}: {
  link: string;
  shape: number[];
  name: string;
  compact?: boolean;
  height?: number;
}) {
  const config = useTiledConfig();
  const max = shape[0] ?? 0;
  const compactWindow = Math.min(max, 200);
  const [range, setRange] = useState<number[]>([
    0,
    compact ? compactWindow : Math.min(max, MAX_DEFAULT_RANGE),
  ]);
  const [displayType, setDisplayType] = useState<"chart" | "list">("chart");
  const [data, setData] = useState<number[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const debouncedSetRange = useMemo(
    () => debounce(setRange, 100, { maxWait: 200 }),
    []
  );

  useEffect(() => {
    if (!config) return;
    const controller = new AbortController();
    setData(null);
    setError(null);
    const [a, b] = range;
    fetchArrayJson(config, link, controller.signal, `${a}:${b}`)
      .then((d) => setData(d as number[]))
      .catch((e) => {
        if (!controller.signal.aborted) setError(String(e));
      });
    return () => controller.abort();
  }, [config, link, range]);

  if (error) {
    return (
      <Box sx={{ fontSize: 12, color: "error.main" }}>
        Could not load array data.
      </Box>
    );
  }

  const chart =
    data === null ? (
      <Skeleton variant="rectangular" height={height ?? (compact ? 120 : 300)} />
    ) : displayType === "chart" ? (
      <ArrayLineChart
        data={data}
        startingIndex={range[0]}
        name={name}
        height={height ?? (compact ? 120 : 300)}
      />
    ) : (
      <Box
        component="pre"
        sx={{ fontSize: 11, maxHeight: 240, overflow: "auto", m: 0 }}
      >
        {data.join("\n")}
      </Box>
    );

  if (compact) return chart;

  return (
    <Box>
      <FormControl sx={{ mb: 1 }}>
        <FormLabel>View as</FormLabel>
        <RadioGroup
          row
          value={displayType}
          onChange={(e) => setDisplayType(e.target.value as "chart" | "list")}
        >
          <FormControlLabel value="chart" control={<Radio />} label="Chart" />
          <FormControlLabel value="list" control={<Radio />} label="List" />
        </RadioGroup>
      </FormControl>
      {max > 1 && (
        <Box sx={{ px: 1 }}>
          <Slider
            value={range}
            min={0}
            max={max}
            onChange={(_, v) => {
              const next = v as number[];
              // Cap the window to LIMIT points, mirroring upstream RangeSlider.
              if (next[1] - next[0] > LIMIT) next[1] = next[0] + LIMIT;
              debouncedSetRange(next);
            }}
            valueLabelDisplay="auto"
          />
        </Box>
      )}
      {chart}
    </Box>
  );
}
