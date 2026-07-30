import {
  Card,
  CardContent,
  Chip,
  FormControlLabel,
  Checkbox,
  Typography,
  Stack,
} from "@mui/material";
import type { FacetCount } from "../api/client";

// Filters are keyed by "field:value". collection is shown first by default.
export function Facets({
  facetCounts,
  active,
  onToggle,
}: {
  facetCounts: FacetCount[];
  active: Set<string>;
  onToggle: (field: string, value: string) => void;
}) {
  if (!facetCounts.length) return null;
  const ordered = [...facetCounts].sort((a, b) =>
    a.field_name === "collection" ? -1 : b.field_name === "collection" ? 1 : 0
  );
  return (
    <Stack spacing={2}>
      {ordered.map((facet) => (
        <Card key={facet.field_name} variant="outlined">
          <CardContent>
            <Typography variant="subtitle2" gutterBottom>
              {facet.field_name.replace(/__/g, ".")}
              {facet.field_name === "collection" && (
                <Chip label="default" size="small" sx={{ ml: 1 }} />
              )}
            </Typography>
            {facet.counts.map((c) => {
              const key = `${facet.field_name}:${c.value}`;
              return (
                <FormControlLabel
                  key={key}
                  control={
                    <Checkbox
                      size="small"
                      checked={active.has(key)}
                      onChange={() => onToggle(facet.field_name, c.value)}
                    />
                  }
                  label={`${c.value} (${c.count})`}
                />
              );
            })}
          </CardContent>
        </Card>
      ))}
    </Stack>
  );
}
