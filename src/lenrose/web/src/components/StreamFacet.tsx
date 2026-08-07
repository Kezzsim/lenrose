import {
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  FormControlLabel,
  FormGroup,
  Typography,
} from "@mui/material";
import { useStreamFacet } from "../state/StreamFacetContext";

// Display-only facet (not a Typesense refinement). Lists the Tiled streams
// discovered across the currently/previously loaded search results. Checking a
// stream makes every card that contains it preview that stream. Discovery is
// driven by the result cards via StreamFacetContext.registerStreams.
export function StreamFacet() {
  const { streams, selected, toggle, clear } = useStreamFacet();

  if (!streams.length) return null;

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
            Streams
          </Typography>
          {selected.size > 0 && (
            <Button size="small" onClick={clear} sx={{ minWidth: 0 }}>
              Clear
            </Button>
          )}
        </Box>
        <Typography variant="caption" color="text.secondary" display="block">
          Choose which stream to preview
        </Typography>
        <FormGroup>
          {streams.map((s) => (
            <FormControlLabel
              key={s.name}
              control={
                <Checkbox
                  size="small"
                  checked={selected.has(s.name)}
                  onChange={() => toggle(s.name)}
                />
              }
              label={`${s.name} (${s.count})`}
            />
          ))}
        </FormGroup>
      </CardContent>
    </Card>
  );
}
