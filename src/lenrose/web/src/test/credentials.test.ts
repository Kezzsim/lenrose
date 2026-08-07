import { describe, it, expect, beforeEach } from "vitest";
import {
  loadCredentials,
  saveCredentials,
  clearCredentials,
} from "../state/credentials";

describe("credentials store", () => {
  beforeEach(async () => {
    await clearCredentials();
  });

  it("returns empty object when nothing stored", async () => {
    expect(await loadCredentials()).toEqual({});
  });

  it("persists and reloads Tiled password credentials", async () => {
    await saveCredentials({
      tiledAuthMethod: "password",
      tiledUsername: "alice",
      tiledPassword: "hunter2",
    });
    expect(await loadCredentials()).toEqual({
      tiledAuthMethod: "password",
      tiledUsername: "alice",
      tiledPassword: "hunter2",
    });
  });

  it("persists Tiled API key credentials", async () => {
    await saveCredentials({ tiledAuthMethod: "api_key", tiledApiKey: "k" });
    expect(await loadCredentials()).toEqual({
      tiledAuthMethod: "api_key",
      tiledApiKey: "k",
    });
  });

  it("drops empty strings", async () => {
    await saveCredentials({ tiledAuthMethod: "api_key", tiledApiKey: "" });
    expect(await loadCredentials()).toEqual({ tiledAuthMethod: "api_key" });
  });

  it("clears credentials", async () => {
    await saveCredentials({ tiledAuthMethod: "api_key", tiledApiKey: "k" });
    await clearCredentials();
    expect(await loadCredentials()).toEqual({});
  });
});
