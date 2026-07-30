import {
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Stack,
  Typography,
} from "@mui/material";
import type { SearchHitDocument } from "../api/client";

// structure_family values that can be rendered graphically (Tiled web-frontend
// style viewers). Stored in the index so we can flag viewable records.
const VIEWABLE = new Set(["array", "table", "dataframe", "image"]);

export function ResultList({
  hits,
  onSelect,
}: {
  hits: { document: SearchHitDocument }[];
  onSelect: (doc: SearchHitDocument) => void;
}) {
  if (!hits.length) {
    return <Typography color="text.secondary">No results.</Typography>;
  }
  return (
    <Stack spacing={1}>
      {hits.map(({ document }) => {
        const viewable =
          document.structure_family &&
          VIEWABLE.has(document.structure_family);
        return (
          <Card key={document.id} variant="outlined">
            <CardActionArea onClick={() => onSelect(document)}>
              <CardContent>
                <Stack
                  direction="row"
                  spacing={1}
                  alignItems="center"
                  flexWrap="wrap"
                >
                  <Typography variant="subtitle1" fontWeight={600}>
                    {document.uuid}
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
