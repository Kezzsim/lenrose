// Dialog for managing user-supplied Tiled authentication. Values are persisted
// to IndexedDB and used by the browser to talk *directly* to the Tiled HTTP API.
// For security only anonymous access and a user-supplied API key are supported
// (no password/token flow in the browser). Typesense is reached with the
// server's scoped search-only key, so no Typesense credentials are managed here.

import { useEffect, useState } from "react";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
} from "@mui/material";
import { useSettings } from "../state/settings";
import type { Credentials, TiledAuthMethod } from "../state/credentials";

export function ApiKeySettingsDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { config, credentials, updateCredentials, resetCredentials } =
    useSettings();

  const [form, setForm] = useState<Credentials>(credentials);

  useEffect(() => {
    if (open) setForm(credentials);
  }, [open, credentials]);

  // Absence of an explicit method means "use whatever the Tiled server allows
  // anonymously" (labelled Preconfigured). No secret is shipped for it.
  const method: TiledAuthMethod = form.tiledAuthMethod ?? "preconfigured";

  const preconfiguredLabel = config?.tiled?.configured
    ? "Default (anonymous access)"
    : "Default (Tiled not configured)";

  const authOptions: { value: TiledAuthMethod; label: string }[] = [
    { value: "preconfigured", label: preconfiguredLabel },
    { value: "anonymous", label: "Anonymous" },
    { value: "api_key", label: "API Key" },
  ];

  const set = (key: keyof Credentials, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const handleSave = async () => {
    // Persist only fields relevant to the chosen auth method. "Preconfigured"
    // stores nothing so the browser accesses Tiled anonymously. The optional
    // Tiled URL override is preserved across auth methods.
    const next: Credentials =
      method === "preconfigured" ? {} : { tiledAuthMethod: method };
    if (method === "api_key") next.tiledApiKey = form.tiledApiKey;
    if (form.tiledApiUrl?.trim()) next.tiledApiUrl = form.tiledApiUrl.trim();
    await updateCredentials(next);
    onClose();
  };

  const handleReset = async () => {
    await resetCredentials();
    setForm({});
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Tiled Authentication</DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>
          Point the app at the Tiled server holding your data and choose how your
          browser authenticates against it. Leave the URL blank to use the
          server the data was ingested from. For security only anonymous access
          and an API key you supply are available — mint your own Tiled API key
          to view protected data. Values are stored locally in your browser
          (IndexedDB).
        </DialogContentText>

        <Stack spacing={2}>
          <TextField
            size="small"
            label="Tiled server URL (override)"
            placeholder={config?.tiled?.apiUrl ?? "https://tiled.example.com"}
            helperText={
              config?.tiled?.apiUrl
                ? `Leave blank to use the configured server: ${config.tiled.apiUrl}`
                : "URL of the Tiled server holding this data (e.g. https://tiled-demo.nsls2.bnl.gov)"
            }
            value={form.tiledApiUrl ?? ""}
            onChange={(e) => set("tiledApiUrl", e.target.value)}
            fullWidth
          />

          <TextField
            select
            size="small"
            label="Authentication method"
            value={method}
            onChange={(e) => set("tiledAuthMethod", e.target.value)}
            fullWidth
          >
            {authOptions.map((m) => (
              <MenuItem key={m.value} value={m.value}>
                {m.label}
              </MenuItem>
            ))}
          </TextField>

          {method === "api_key" && (
            <TextField
              size="small"
              label="Tiled API Key"
              type="password"
              value={form.tiledApiKey ?? ""}
              onChange={(e) => set("tiledApiKey", e.target.value)}
              fullWidth
            />
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button color="inherit" onClick={handleReset}>
          Reset to defaults
        </Button>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSave}>
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}
