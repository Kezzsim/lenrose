// Frontend credential storage backed by IndexedDB.
//
// Per the Lenrose ideals the web app manages its own state and talks directly
// to services. Typesense is reached with the scoped, search-only key the server
// provides, so no Typesense credentials are stored here. For Tiled, the browser
// talks *directly* to the Tiled HTTP API, so for security we only support
// anonymous access or a user-supplied API key (no password/token flow in the
// browser). Users who need authenticated data mint their own Tiled API key.
// Values are persisted in IndexedDB (not localStorage) so they are not
// trivially exposed and survive reloads.

import { openDB, type IDBPDatabase } from "idb";

const DB_NAME = "lenrose";
const STORE = "credentials";
const DB_VERSION = 1;

// "preconfigured" is a label-only mode: it means "use whatever the Tiled server
// allows anonymously". No secret is ever shipped to the browser for it.
export type TiledAuthMethod = "preconfigured" | "anonymous" | "api_key";

export interface Credentials {
  tiledAuthMethod?: TiledAuthMethod;
  tiledApiKey?: string;
  /**
   * Optional user override for the Tiled server URL. When set, the browser
   * talks to this Tiled instead of the one the server reports (env /
   * TUI-saved connection). Highest precedence.
   */
  tiledApiUrl?: string;
}

let dbPromise: Promise<IDBPDatabase> | null = null;

function getDb(): Promise<IDBPDatabase> {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains(STORE)) {
          db.createObjectStore(STORE);
        }
      },
    });
  }
  return dbPromise;
}

const KEY = "user";

export async function loadCredentials(): Promise<Credentials> {
  try {
    const db = await getDb();
    const value = (await db.get(STORE, KEY)) as Credentials | undefined;
    return value ?? {};
  } catch {
    return {};
  }
}

export async function saveCredentials(creds: Credentials): Promise<void> {
  const db = await getDb();
  // Drop empty strings so they don't shadow server defaults.
  const cleaned: Credentials = {};
  for (const [k, v] of Object.entries(creds)) {
    if (v !== "" && v !== undefined && v !== null) {
      (cleaned as Record<string, unknown>)[k] = v;
    }
  }
  await db.put(STORE, cleaned, KEY);
}

export async function clearCredentials(): Promise<void> {
  const db = await getDb();
  await db.delete(STORE, KEY);
}
