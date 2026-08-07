import {
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Stack,
  Typography,
} from "@mui/material";
import { useHits } from "react-instantsearch";
import type { SearchHitDocument } from "../api/client";

const VIEWABLE = new Set(["array", "table", "dataframe", "image"]);

function formatDisplayValue(value: unknown): string | null {
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed || null;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    const formatted = value
      .map(formatDisplayValue)
      .filter((part): part is string => Boolean(part));
    return formatted.length ? formatted.join(", ") : null;
  }
  return null;
}

export function ResultList({
  onSelect,
  displayField,
}: {
  onSelect: (doc: SearchHitDocument) => void;
  displayField: string;
}) {
  const { items } = useHits<SearchHitDocument>();

  if (!items.length) {
    return <Typography color="text.secondary">No results.</Typography>;
  }

  return (
    <Stack spacing={1}>
      {items.map((document) => {
        const viewable =
          document.structure_family && VIEWABLE.has(document.structure_family);
        const title =
          formatDisplayValue(document[displayField]) ?? document.uuid;
        return (
          <Card key={document.objectID ?? document.id} variant="outlined">
            <CardActionArea onClick={() => onSelect(document)}>
              <CardContent>
                <Stack
                  direction="row"
                  spacing={1}
                  alignItems="center"
                  flexWrap="wrap"
                >
                  <Typography variant="subtitle1" fontWeight={600}>
                    {title}
                  </Typography>
                  <Chip
                    label={document.collection}
                    size="small"
                    color="secondary"
                  />
                  {document.structure_family && (
                    <Chip
                      label={document.structure_family}
                      size="small"
                      variant="outlined"
                    />
                  )}
                  {viewable && (
                    <Chip label="viewable" size="small" color="primary" />
                  )}
                </Stack>
              </CardContent>
            </CardActionArea>
          </Card>
        );
      })}
    </Stack>
  );
}
