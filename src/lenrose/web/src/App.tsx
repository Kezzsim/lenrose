import { useMemo, useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Box,
  Alert,
  Button,
  CircularProgress,
  FormControl,
  FormControlLabel,
  FormLabel,
  IconButton,
  Radio,
  RadioGroup,
} from "@mui/material";
import SettingsIcon from "@mui/icons-material/Settings";
import { InstantSearch, Configure, useStats } from "react-instantsearch";
import { SearchBar } from "./components/SearchBar";
import { Facets } from "./components/Facets";
import { ResultList } from "./components/ResultList";
import { Pagination } from "./components/Pagination";
import { RecordDetailDrawer } from "./components/RecordDetail";
import { ApiKeySettingsDialog } from "./components/ApiKeySettings";
import { createSearchClient } from "./search/searchClient";
import { useSettings } from "./state/settings";
import { loadLayout } from "./layout/config";
import type { SearchHitDocument } from "./api/client";

function ResultsCount() {
  const { nbHits } = useStats();
  return (
    <Typography variant="body2" color="text.secondary">
      {nbHits} results
    </Typography>
  );
}

export default function App() {
  const layout = useMemo(() => loadLayout(), []);
  const { loading, error, config, typesense, credentials } = useSettings();
  const [selected, setSelected] = useState<SearchHitDocument | null>(null);
  const [displayValue, setDisplayValue] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const searchClient = useMemo(() => {
    if (!typesense || !config) return null;
    return createSearchClient(typesense, config);
  }, [typesense, config]);

  const displayFields = config?.displayFields ?? [
    { value: "uuid", label: "UUID", field: "uuid" },
  ];
  const activeDisplay =
    displayValue ?? config?.defaultDisplay ?? "uuid";
  const displayField =
    displayFields.find((o) => o.value === activeDisplay)?.field ?? "uuid";

  const includeFields = Array.from(
    new Set([
      "id",
      "uuid",
      "collection",
      "tiled_key",
      "structure_family",
      "specs",
      displayField,
    ])
  ).join(",");

  const header = (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Lenrose
        </Typography>
        <Typography variant="body2" sx={{ mr: 1 }}>
          NSLS-II Metadata Search
        </Typography>
        <IconButton
          color="inherit"
          aria-label="API key settings"
          onClick={() => setSettingsOpen(true)}
        >
          <SettingsIcon />
        </IconButton>
      </Toolbar>
    </AppBar>
  );

  const settingsDialog = (
    <ApiKeySettingsDialog
      open={settingsOpen}
      onClose={() => setSettingsOpen(false)}
    />
  );

  if (loading) {
    return (
      <>
        {header}
        <Container maxWidth="lg" sx={{ mt: 6, textAlign: "center" }}>
          <CircularProgress />
        </Container>
        {settingsDialog}
      </>
    );
  }

  if (!searchClient) {
    return (
      <>
        {header}
        <Container maxWidth="lg" sx={{ mt: 4 }}>
          <Alert
            severity={error ? "error" : "warning"}
            action={
              <Button color="inherit" onClick={() => setSettingsOpen(true)}>
                Configure keys
              </Button>
            }
          >
            {error
              ? `Could not load search configuration: ${error}`
              : "No Typesense connection is configured. Provide a host and search-only API key."}
          </Alert>
        </Container>
        {settingsDialog}
      </>
    );
  }

  return (
    <>
      {header}
      <InstantSearch searchClient={searchClient} indexName={config!.collection}>
        <Configure
          hitsPerPage={layout.resultsPerPage}
          // Passed through to Typesense by the adapter.
          {...{ include_fields: includeFields }}
        />
        <Container maxWidth="lg" sx={{ mt: 3 }}>
          {layout.showSearchBar && (
            <Box mb={3}>
              <SearchBar />
            </Box>
          )}
          <Grid container spacing={3}>
            {layout.showFacets && (
              <Grid item xs={12} md={3}>
                <Facets
                  facets={config!.facets}
                  facetTypes={config!.facetTypes}
                />
              </Grid>
            )}
            <Grid item xs={12} md={layout.showFacets ? 9 : 12}>
              <Box
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                gap={2}
                flexWrap="wrap"
                mb={1}
              >
                <ResultsCount />
                <FormControl size="small">
                  <FormLabel id="display-field-label">Display</FormLabel>
                  <RadioGroup
                    row
                    aria-labelledby="display-field-label"
                    name="display-field"
                    value={activeDisplay}
                    onChange={(event) => setDisplayValue(event.target.value)}
                  >
                    {displayFields.map((option) => (
                      <FormControlLabel
                        key={option.value}
                        value={option.value}
                        control={<Radio size="small" />}
                        label={option.label}
                      />
                    ))}
                  </RadioGroup>
                </FormControl>
              </Box>
              <ResultList onSelect={setSelected} displayField={displayField} />
              <Pagination />
            </Grid>
          </Grid>
        </Container>
      </InstantSearch>
      <RecordDetailDrawer
        doc={selected}
        tiledCredentials={credentials}
        onClose={() => setSelected(null)}
      />
      {settingsDialog}
    </>
  );
}
