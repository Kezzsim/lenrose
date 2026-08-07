// Application settings context: loads server-provided search config and merges
// user-supplied Tiled credentials (from IndexedDB). Typesense is always reached
// with the server's scoped, search-only key.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { getSearchConfig, type SearchConfig } from "../api/client";
import {
  loadCredentials,
  saveCredentials,
  clearCredentials,
  type Credentials,
} from "./credentials";

export interface ResolvedTypesense {
  host: string;
  port: number;
  protocol: string;
  apiKey: string;
}

interface SettingsValue {
  loading: boolean;
  error: string | null;
  config: SearchConfig | null;
  credentials: Credentials;
  typesense: ResolvedTypesense | null;
  updateCredentials: (creds: Credentials) => Promise<void>;
  resetCredentials: () => Promise<void>;
  reloadConfig: () => void;
}

const SettingsContext = createContext<SettingsValue | null>(null);

export function resolveTypesense(
  config: SearchConfig | null
): ResolvedTypesense | null {
  if (!config) return null;
  return {
    host: config.typesense.host,
    port: config.typesense.port,
    protocol: config.typesense.protocol,
    apiKey: config.typesense.apiKey,
  };
}

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState<SearchConfig | null>(null);
  const [credentials, setCredentials] = useState<Credentials>({});
  const [configNonce, setConfigNonce] = useState(0);

  useEffect(() => {
    loadCredentials().then(setCredentials).catch(() => undefined);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getSearchConfig()
      .then((cfg) => {
        if (!cancelled) setConfig(cfg);
      })
      .catch((e) => {
        if (!cancelled) setError(String(e));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [configNonce]);

  const updateCredentials = useCallback(async (creds: Credentials) => {
    await saveCredentials(creds);
    const next = await loadCredentials();
    setCredentials(next);
  }, []);

  const resetCredentials = useCallback(async () => {
    await clearCredentials();
    setCredentials({});
  }, []);

  const reloadConfig = useCallback(() => setConfigNonce((n) => n + 1), []);

  const typesense = useMemo(() => resolveTypesense(config), [config]);

  const value: SettingsValue = {
    loading,
    error,
    config,
    credentials,
    typesense,
    updateCredentials,
    resetCredentials,
    reloadConfig,
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings(): SettingsValue {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used within SettingsProvider");
  return ctx;
}
