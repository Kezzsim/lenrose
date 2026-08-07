import {
  Card,
  CardContent,
  Chip,
  FormControlLabel,
  Checkbox,
  Typography,
} from "@mui/material";
import { useRefinementList } from "react-instantsearch";

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

  if (!items.length) return null;

  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="subtitle2" gutterBottom>
          {attribute.replace(/__/g, ".")}
          {isDefault && <Chip label="default" size="small" sx={{ ml: 1 }} />}
        </Typography>
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
