// Dialog for managing user-supplied Tiled authentication. Values are persisted
// to IndexedDB and forwarded to the server when loading full record metadata.
// Typesense is reached with the server's scoped search-only key, so no
// Typesense credentials are managed here.

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

const METHOD_LABELS: Record<string, string> = {
  anonymous: "Anonymous",
  api_key: "API Key",
  password: "Username / Password",
};

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

  // Absence of an explicit method means "use the server's preconfigured
  // connection". Reserve "anonymous" for Tiled's own anonymous auth.
  const method: TiledAuthMethod = form.tiledAuthMethod ?? "preconfigured";

  // Label the preconfigured option with the server's actual method, when known.
  const serverMethod = config?.tiled?.method;
  const preconfiguredLabel = serverMethod
    ? `Preconfigured (${METHOD_LABELS[serverMethod] ?? serverMethod})`
    : config?.tiled?.configured
    ? "Preconfigured"
    : "Preconfigured (none)";

  const authOptions: { value: TiledAuthMethod; label: string }[] = [
    { value: "preconfigured", label: preconfiguredLabel },
    { value: "anonymous", label: "Anonymous" },
    { value: "api_key", label: "API Key" },
    { value: "password", label: "Username / Password" },
  ];

  const set = (key: keyof Credentials, value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const handleSave = async () => {
    // Persist only fields relevant to the chosen auth method. "Preconfigured"
    // stores nothing so the server uses its own connection.
    const next: Credentials =
      method === "preconfigured" ? {} : { tiledAuthMethod: method };
    if (method === "api_key") next.tiledApiKey = form.tiledApiKey;
    if (method === "password") {
      next.tiledUsername = form.tiledUsername;
      next.tiledPassword = form.tiledPassword;
    }
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
          Choose how to authenticate against Tiled when loading full record
          metadata. "Preconfigured" uses the server's own connection. Choose
          "Anonymous" to explicitly use Tiled's anonymous access. Values are
          stored locally in your browser (IndexedDB).
        </DialogContentText>

        <Stack spacing={2}>
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

          {method === "password" && (
            <>
              <TextField
                size="small"
                label="Username"
                value={form.tiledUsername ?? ""}
                onChange={(e) => set("tiledUsername", e.target.value)}
                fullWidth
              />
              <TextField
                size="small"
                label="Password"
                type="password"
                value={form.tiledPassword ?? ""}
                onChange={(e) => set("tiledPassword", e.target.value)}
                fullWidth
              />
            </>
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
