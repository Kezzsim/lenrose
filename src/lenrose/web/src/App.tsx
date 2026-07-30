import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Box,
  Pagination,
} from "@mui/material";
import { SearchBar } from "./components/SearchBar";
import { Facets } from "./components/Facets";
import { ResultList } from "./components/ResultList";
import { RecordDetailDrawer } from "./components/RecordDetail";
import {
  search,
  getFacets,
  type SearchResponse,
  type SearchHitDocument,
} from "./api/client";
import { loadLayout } from "./layout/config";

export default function App() {
  const layout = useMemo(() => loadLayout(), []);
  const [query, setQuery] = useState("");
  const [facetFields, setFacetFields] = useState<string[]>(
    layout.defaultFacets
  );
  const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [selected, setSelected] = useState<SearchHitDocument | null>(null);

  useEffect(() => {
    getFacets().then(setFacetFields).catch(() => undefined);
  }, []);

  const filterBy = useMemo(() => {
    const byField: Record<string, string[]> = {};
    for (const entry of activeFilters) {
      const idx = entry.indexOf(":");
      const field = entry.slice(0, idx);
      const value = entry.slice(idx + 1);
      (byField[field] ||= []).push(value);
    }
    return Object.entries(byField)
      .map(([f, vals]) => `${f}:=[${vals.map((v) => `\`${v}\``).join(",")}]`)
      .join(" && ");
  }, [activeFilters]);

  const runSearch = useCallback(() => {
    search({
      q: query,
      facetBy: facetFields.join(","),
      filterBy: filterBy || undefined,
      page,
      perPage: layout.resultsPerPage,
    })
      .then(setResponse)
      .catch(() => setResponse(null));
  }, [query, facetFields, filterBy, page, layout.resultsPerPage]);

  useEffect(() => {
    runSearch();
  }, [runSearch]);

  const toggleFilter = (field: string, value: string) => {
    const key = `${field}:${value}`;
    setActiveFilters((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
    setPage(1);
  };

  const totalPages = response
    ? Math.max(1, Math.ceil(response.found / layout.resultsPerPage))
    : 1;

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Lenrose
          </Typography>
          <Typography variant="body2">NSLS-II Metadata Search</Typography>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ mt: 3 }}>
        {layout.showSearchBar && (
          <Box mb={3}>
            <SearchBar
              value={query}
              onChange={(v) => {
                setQuery(v);
                setPage(1);
              }}
            />
          </Box>
        )}
        <Grid container spacing={3}>
          {layout.showFacets && (
            <Grid item xs={12} md={3}>
              <Facets
                facetCounts={response?.facet_counts ?? []}
                active={activeFilters}
                onToggle={toggleFilter}
              />
            </Grid>
          )}
          <Grid item xs={12} md={layout.showFacets ? 9 : 12}>
            <Typography variant="body2" color="text.secondary" mb={1}>
              {response?.found ?? 0} results
            </Typography>
            <ResultList
              hits={response?.hits ?? []}
              onSelect={setSelected}
            />
            <Box display="flex" justifyContent="center" mt={3}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(_, p) => setPage(p)}
                color="primary"
              />
            </Box>
          </Grid>
        </Grid>
      </Container>
      <RecordDetailDrawer doc={selected} onClose={() => setSelected(null)} />
    </>
  );
}
