// Provides the Tiled client configuration (public API URL + user credentials)
// to the component tree. Data fetching itself is done per-component via
// useTiledNode so it can lazy-load and be cancelled on unmount.

import { createContext, useContext, useMemo, type ReactNode } from "react";
import type { TiledClientConfig } from "./client";
import type { Credentials } from "../state/credentials";

const TiledConfigContext = createContext<TiledClientConfig | null>(null);

export function TiledProvider({
  apiUrl,
  credentials,
  children,
}: {
  apiUrl: string | null;
  credentials?: Credentials;
  children: ReactNode;
}) {
  const value = useMemo<TiledClientConfig | null>(
    () => (apiUrl ? { apiUrl, credentials } : null),
    [apiUrl, credentials]
  );
  return (
    <TiledConfigContext.Provider value={value}>
      {children}
    </TiledConfigContext.Provider>
  );
}

/** Returns the Tiled client config, or null when Tiled is not configured. */
export function useTiledConfig(): TiledClientConfig | null {
  return useContext(TiledConfigContext);
}
