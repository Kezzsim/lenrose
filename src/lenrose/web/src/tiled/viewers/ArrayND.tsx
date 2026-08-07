// N-D array / image viewer. Adapted in spirit from bluesky/tiled
// web-frontend/src/components/array-nd/array-nd.tsx.
//
// For a 2-D array we fetch the full plane as JSON and render it to a canvas as
// a grayscale image (auto-scaled to min/max). For >2-D arrays (e.g. multi-layer
// TIFF stacks, shape [L, H, W]) we expose sliders to choose the leading indices
// and render the selected 2-D plane. This keeps requests small: only one plane
// is fetched at a time via slice=.

import { useEffect, useMemo, useRef, useState } from "react";
import Box from "@mui/material/Box";
import Skeleton from "@mui/material/Skeleton";
import Slider from "@mui/material/Slider";
import Typography from "@mui/material/Typography";
import { fetchArrayJson } from "../client";
import { useTiledConfig } from "../TiledProvider";

function drawGrayscale(
  canvas: HTMLCanvasElement,
  plane: number[][]
): void {
  const h = plane.length;
  const w = plane[0]?.length ?? 0;
  if (!h || !w) return;
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  let min = Infinity;
  let max = -Infinity;
  for (const row of plane)
    for (const v of row) {
      if (v < min) min = v;
      if (v > max) max = v;
    }
  const span = max - min || 1;

  const img = ctx.createImageData(w, h);
  for (let y = 0; y < h; y += 1) {
    for (let x = 0; x < w; x += 1) {
      const g = Math.round(((plane[y][x] - min) / span) * 255);
      const i = (y * w + x) * 4;
      img.data[i] = g;
      img.data[i + 1] = g;
      img.data[i + 2] = g;
      img.data[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
}

export function ArrayND({
  link,
  shape,
  compact = false,
}: {
  link: string;
  shape: number[];
  compact?: boolean;
}) {
  const config = useTiledConfig();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  // Leading indices for dims beyond the last two.
  const leadingDims = shape.slice(0, Math.max(0, shape.length - 2));
  const [leading, setLeading] = useState<number[]>(() =>
    leadingDims.map(() => 0)
  );
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const slice = useMemo(() => {
    // e.g. leading [3] + last two dims full => "3,:,:"
    const parts = [...leading.map(String), ...shape.slice(-2).map(() => ":")];
    return parts.join(",");
  }, [leading, shape]);

  useEffect(() => {
    if (!config) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    fetchArrayJson(config, link, controller.signal, slice)
      .then((d) => {
        const plane = d as unknown as number[][];
        if (canvasRef.current && Array.isArray(plane[0])) {
          drawGrayscale(canvasRef.current, plane);
        }
        setLoading(false);
      })
      .catch((e) => {
        if (!controller.signal.aborted) {
          setError(String(e));
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [config, link, slice]);

  if (error) {
    return (
      <Box sx={{ fontSize: 12, color: "error.main" }}>
        Could not load image data.
      </Box>
    );
  }

  return (
    <Box>
      {loading && (
        <Skeleton variant="rectangular" height={compact ? 120 : 300} />
      )}
      <canvas
        ref={canvasRef}
        style={{
          display: loading ? "none" : "block",
          maxWidth: "100%",
          height: "auto",
          imageRendering: "pixelated",
          border: "1px solid #ddd",
        }}
      />
      {!compact &&
        leadingDims.map((size, dim) => (
          <Box key={dim} sx={{ px: 1, mt: 1 }}>
            <Typography variant="caption">
              Layer axis {dim} ({leading[dim]} / {size - 1})
            </Typography>
            <Slider
              value={leading[dim]}
              min={0}
              max={size - 1}
              step={1}
              marks={size <= 20}
              valueLabelDisplay="auto"
              onChange={(_, v) =>
                setLeading((prev) => {
                  const next = [...prev];
                  next[dim] = v as number;
                  return next;
                })
              }
            />
          </Box>
        ))}
    </Box>
  );
}
