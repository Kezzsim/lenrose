// Frontend credential storage backed by IndexedDB.
//
// Per the Lenrose ideals the web app manages its own state and talks directly
// to services. Typesense is reached with the scoped, search-only key the server
// provides, so no Typesense credentials are stored here. Users may, however,
// supply their own Tiled authentication (anonymous, API key, or
// username/password) which is forwarded to the server when loading records.
// Values are persisted in IndexedDB (not localStorage) so they are not
// trivially exposed and survive reloads.

import { openDB, type IDBPDatabase } from "idb";

const DB_NAME = "lenrose";
const STORE = "credentials";
const DB_VERSION = 1;

export type TiledAuthMethod =
  | "preconfigured"
  | "anonymous"
  | "api_key"
  | "password";

export interface Credentials {
  tiledAuthMethod?: TiledAuthMethod;
  tiledApiKey?: string;
  tiledUsername?: string;
  tiledPassword?: string;
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
