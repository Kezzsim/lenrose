import { Box, Button, Stack, Typography } from "@mui/material";
import { useClearRefinements } from "react-instantsearch";
import { RangeFacet } from "./RangeFacet";
import { RefinementFacet } from "./RefinementFacet";

const NUMERIC_TYPES = new Set([
  "int32",
  "int64",
  "float",
  "int64[]",
  "float[]",
]);

export function isNumericType(type: string | undefined): boolean {
  return type != null && NUMERIC_TYPES.has(type);
}

function ClearAll() {
  const { canRefine, refine } = useClearRefinements();
  return (
    <Box display="flex" justifyContent="space-between" alignItems="center">
      <Typography variant="subtitle2">Filters</Typography>
      <Button size="small" onClick={refine} disabled={!canRefine}>
        Clear all
      </Button>
    </Box>
  );
}

// Renders the configured facets. Numeric fields (int/float) become range
// sliders; everything else becomes a checkbox refinement list. `collection`
// is shown first.
export function Facets({
  facets,
  facetTypes,
}: {
  facets: string[];
  facetTypes: Record<string, string>;
}) {
  const ordered = [...facets].sort((a, b) =>
    a === "collection" ? -1 : b === "collection" ? 1 : 0
  );

  return (
    <Stack spacing={2}>
      <ClearAll />
      {ordered.map((field) => {
        const type = facetTypes[field];
        if (isNumericType(type)) {
          return <RangeFacet key={field} attribute={field} type={type} />;
        }
        return (
          <RefinementFacet
            key={field}
            attribute={field}
            isDefault={field === "collection"}
          />
        );
      })}
    </Stack>
  );
}
