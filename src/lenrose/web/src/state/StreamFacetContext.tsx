// Persistent, app-wide registry of streams discovered across loaded search
// results, plus the user's selection of which stream to preview.
//
// As result cards mount they introspect their Tiled node (shallowly) and report
// the streams they contain via `registerStreams`. The union of all discovered
// stream names is kept here and never shrinks when cards unmount (so scrolling
// back and forth doesn't cause the facet checkboxes to flicker). Nested streams
// are reported with a '/' separator (e.g. "primary/config").
//
// The `selected` set drives which stream each card renders. Empty selection
// means "auto" (each card shows its first available stream). This is a
// display-only facet, distinct from Typesense refinements.

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

interface StreamFacetValue {
  /** All stream names ever discovered, sorted, with counts of loaded records. */
  streams: { name: string; count: number }[];
  /** Currently selected stream names (empty => auto). */
  selected: Set<string>;
  toggle: (name: string) => void;
  clear: () => void;
  /** Called by cards to report the streams they contain. */
  registerStreams: (names: string[]) => void;
  /**
   * Resolve which stream a card should render given the streams it actually
   * contains: the first selected stream it has, else its first stream.
   */
  resolveForRecord: (available: string[]) => string | null;
}

const StreamFacetContext = createContext<StreamFacetValue | null>(null);

export function StreamFacetProvider({ children }: { children: ReactNode }) {
  const countsRef = useRef<Map<string, number>>(new Map());
  const [streams, setStreams] = useState<{ name: string; count: number }[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const registerStreams = useCallback((names: string[]) => {
    if (!names.length) return;
    const counts = countsRef.current;
    for (const name of names) {
      counts.set(name, (counts.get(name) ?? 0) + 1);
    }
    setStreams(
      Array.from(counts.entries())
        .map(([name, count]) => ({ name, count }))
        .sort((a, b) => a.name.localeCompare(b.name))
    );
  }, []);

  const toggle = useCallback((name: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }, []);

  const clear = useCallback(() => setSelected(new Set()), []);

  const resolveForRecord = useCallback(
    (available: string[]) => {
      if (!available.length) return null;
      if (selected.size) {
        const hit = available.find((s) => selected.has(s));
        if (hit) return hit;
      }
      return available[0];
    },
    [selected]
  );

  const value = useMemo<StreamFacetValue>(
    () => ({ streams, selected, toggle, clear, registerStreams, resolveForRecord }),
    [streams, selected, toggle, clear, registerStreams, resolveForRecord]
  );

  return (
    <StreamFacetContext.Provider value={value}>
      {children}
    </StreamFacetContext.Provider>
  );
}

export function useStreamFacet(): StreamFacetValue {
  const ctx = useContext(StreamFacetContext);
  if (!ctx)
    throw new Error("useStreamFacet must be used within a StreamFacetProvider");
  return ctx;
}
