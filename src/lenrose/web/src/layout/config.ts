// Recomposable layout configuration (scaffold).
// The search UI reads this config so components (search bar, facets) can be
// moved, hidden, or reordered, and default facets changed, without code edits.
// Persisted to localStorage; a future settings editor will mutate it.

export interface LayoutConfig {
  showSearchBar: boolean;
  searchBarPosition: "top" | "sidebar";
  showFacets: boolean;
  facetsPosition: "left" | "right";
  defaultFacets: string[];
  resultsPerPage: number;
}

export const DEFAULT_LAYOUT: LayoutConfig = {
  showSearchBar: true,
  searchBarPosition: "top",
  showFacets: true,
  facetsPosition: "left",
  defaultFacets: ["collection"],
  // Kept small so that at most ~10 preview-bearing cards render per page,
  // bounding how many Tiled requests can be triggered by a single page.
  resultsPerPage: 10,
};

const STORAGE_KEY = "lenrose.layout";

export function loadLayout(): LayoutConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...DEFAULT_LAYOUT, ...JSON.parse(raw) };
  } catch {
    /* ignore */
  }
  return DEFAULT_LAYOUT;
}

export function saveLayout(config: LayoutConfig): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
}
