import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Box,
  FormControl,
  FormControlLabel,
  FormLabel,
  Pagination,
  Radio,
  RadioGroup,
} from "@mui/material";
import { SearchBar } from "./components/SearchBar";
import { Facets } from "./components/Facets";
import { ResultList } from "./components/ResultList";
import { RecordDetailDrawer } from "./components/RecordDetail";
import {
  search,
  getFacets,
  getDisplayFields,
  type SearchResponse,
  type SearchHitDocument,
  type DisplayFieldOption,
} from "./api/client";
import { loadLayout } from "./layout/config";

export default function App() {
  const layout = useMemo(() => loadLayout(), []);
  const [query, setQuery] = useState("");
  const [facetFields, setFacetFields] = useState<string[]>(
    layout.defaultFacets
  );
  const [facetTypes, setFacetTypes] = useState<Record<string, string>>({});
  const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [selected, setSelected] = useState<SearchHitDocument | null>(null);
  const [displayOptions, setDisplayOptions] = useState<DisplayFieldOption[]>([
    { value: "uuid", label: "UUID", field: "uuid" },
  ]);
  const [displayValue, setDisplayValue] = useState("uuid");

  useEffect(() => {
    getFacets()
      .then(({ facets, facetTypes }) => {
        setFacetFields(facets);
        setFacetTypes(facetTypes);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    getDisplayFields()
      .then(({ default: defaultValue, options }) => {
        const nextOptions = options.length
          ? options
          : [{ value: "uuid" as const, label: "UUID", field: "uuid" }];
        setDisplayOptions(nextOptions);
        setDisplayValue(
          nextOptions.some((option) => option.value === defaultValue)
            ? defaultValue
            : nextOptions[0]?.value ?? "uuid"
        );
      })
      .catch(() => undefined);
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
      .map(([f, vals]) => {
        if (facetTypes[f] === "bool") {
          return vals.length === 1
            ? `${f}:=${vals[0]}`
            : `${f}:=[${vals.join(",")}]`;
        }
        return `${f}:=[${vals.map((v) => `\`${v}\``).join(",")}]`;
      })
      .join(" && ");
  }, [activeFilters, facetTypes]);

  const displayField =
    displayOptions.find((option) => option.value === displayValue)?.field ??
    "uuid";
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

  const runSearch = useCallback(() => {
    search({
      q: query,
      facetBy: facetFields.join(","),
      filterBy: filterBy || undefined,
      includeFields,
      page,
      perPage: layout.resultsPerPage,
    })
      .then(setResponse)
      .catch(() => setResponse(null));
  }, [query, facetFields, filterBy, includeFields, page, layout.resultsPerPage]);

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
            <Box
              display="flex"
              justifyContent="space-between"
              alignItems="center"
              gap={2}
              flexWrap="wrap"
              mb={1}
            >
              <Typography variant="body2" color="text.secondary">
                {response?.found ?? 0} results
              </Typography>
              <FormControl size="small">
                <FormLabel id="display-field-label">Display</FormLabel>
                <RadioGroup
                  row
                  aria-labelledby="display-field-label"
                  name="display-field"
                  value={displayValue}
                  onChange={(event) =>
                    setDisplayValue(event.target.value)
                  }
                >
                  {displayOptions.map((option) => (
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
            <ResultList
              hits={response?.hits ?? []}
              onSelect={setSelected}
              displayField={displayField}
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
