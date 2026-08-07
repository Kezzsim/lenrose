import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  FormControlLabel,
  Checkbox,
  Typography,
} from "@mui/material";
import { useRefinementList, useClearRefinements } from "react-instantsearch";

// Checkbox-based facet for string / bool attributes, driven by InstantSearch's
// useRefinementList connector.
export function RefinementFacet({
  attribute,
  isDefault,
}: {
  attribute: string;
  isDefault?: boolean;
}) {
  const { items, refine } = useRefinementList({
    attribute,
    limit: 20,
    sortBy: ["count:desc", "name:asc"],
  });
  const { canRefine: canClear, refine: clear } = useClearRefinements({
    includedAttributes: [attribute],
  });

  if (!items.length) return null;

  return (
    <Card variant="outlined">
      <CardContent>
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          gap={1}
        >
          <Typography variant="subtitle2" gutterBottom>
            {attribute.replace(/__/g, ".")}
            {isDefault && <Chip label="default" size="small" sx={{ ml: 1 }} />}
          </Typography>
          {canClear && (
            <Button size="small" onClick={clear} sx={{ minWidth: 0 }}>
              Clear
            </Button>
          )}
        </Box>
        {items.map((item) => (
          <FormControlLabel
            key={item.value}
            control={
              <Checkbox
                size="small"
                checked={item.isRefined}
                onChange={() => refine(item.value)}
              />
            }
            label={`${item.label} (${item.count})`}
          />
        ))}
      </CardContent>
    </Card>
  );
}
