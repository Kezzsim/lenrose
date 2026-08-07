import { useEffect, useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Slider,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useRange } from "react-instantsearch";

// Numeric range facet backed by InstantSearch's `useRange` connector. The
// connector computes the available domain (range.min/range.max) using a
// disjunctive query that excludes this attribute's own refinement, so dragging
// the slider never collapses the rail. This is the native InstantSearch
// behaviour (equivalent to the reference ecommerce store's price slider).

const INTEGER_TYPES = new Set(["int32", "int64", "int64[]"]);

function computeStep(min: number, max: number, integer: boolean): number {
  if (integer) return 1;
  const span = max - min;
  if (span <= 0) return 1;
  const raw = span / 100;
  const magnitude = Math.pow(10, Math.floor(Math.log10(raw)));
  return magnitude > 0 ? magnitude : raw;
}

export function RangeFacet({
  attribute,
  type,
  label,
}: {
  attribute: string;
  type: string;
  label?: string;
}) {
  const { start, range, canRefine, refine } = useRange({ attribute });
  const integer = INTEGER_TYPES.has(type);

  const min = range.min ?? 0;
  const max = range.max ?? 0;

  // Current selection: fall back to full domain when unbounded.
  const selMin = Number.isFinite(start[0]) ? (start[0] as number) : min;
  const selMax = Number.isFinite(start[1]) ? (start[1] as number) : max;

  const [local, setLocal] = useState<[number, number]>([selMin, selMax]);
  const [minText, setMinText] = useState(String(selMin));
  const [maxText, setMaxText] = useState(String(selMax));

  // Re-sync when the connector reports a new selection or domain.
  useEffect(() => {
    setLocal([selMin, selMax]);
    setMinText(String(selMin));
    setMaxText(String(selMax));
  }, [selMin, selMax]);

  const title = (label ?? attribute).replace(/__/g, ".");

  if (!canRefine || min === max) {
    return (
      <Card variant="outlined">
        <CardContent>
          <Typography variant="subtitle2" gutterBottom>
            {title}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            No numeric range available.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const step = computeStep(min, max, integer);

  const commit = (rangeValue: [number, number]) => {
    const low = Math.min(Math.max(rangeValue[0], min), max);
    const high = Math.min(Math.max(rangeValue[1], min), max);
    const ordered: [number, number] = low <= high ? [low, high] : [high, low];
    setLocal(ordered);
    setMinText(String(ordered[0]));
    setMaxText(String(ordered[1]));
    // Full domain => clear the refinement.
    if (ordered[0] <= min && ordered[1] >= max) {
      refine([undefined, undefined]);
    } else {
      refine(ordered);
    }
  };

  const commitFromText = () => {
    const parsedMin = Number(minText);
    const parsedMax = Number(maxText);
    commit([
      Number.isFinite(parsedMin) ? parsedMin : local[0],
      Number.isFinite(parsedMax) ? parsedMax : local[1],
    ]);
  };

  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="subtitle2" gutterBottom>
          {title}
        </Typography>
        <Box px={1}>
          <Slider
            size="small"
            value={local}
            min={min}
            max={max}
            step={step}
            valueLabelDisplay="auto"
            onChange={(_, next) => setLocal(next as [number, number])}
            onChangeCommitted={(_, next) => commit(next as [number, number])}
          />
        </Box>
        <Stack direction="row" spacing={1} mt={1}>
          <TextField
            size="small"
            label="Min"
            type="number"
            value={minText}
            onChange={(e) => setMinText(e.target.value)}
            onBlur={commitFromText}
            onKeyDown={(e) => {
              if (e.key === "Enter") commitFromText();
            }}
            inputProps={{ min, max, step }}
            sx={{ width: "50%" }}
          />
          <TextField
            size="small"
            label="Max"
            type="number"
            value={maxText}
            onChange={(e) => setMaxText(e.target.value)}
            onBlur={commitFromText}
            onKeyDown={(e) => {
              if (e.key === "Enter") commitFromText();
            }}
            inputProps={{ min, max, step }}
            sx={{ width: "50%" }}
          />
        </Stack>
      </CardContent>
    </Card>
  );
}
