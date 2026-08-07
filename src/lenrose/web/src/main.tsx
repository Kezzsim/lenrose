import React from "react";
import ReactDOM from "react-dom/client";
import { ThemeProvider, CssBaseline } from "@mui/material";
import { theme } from "./theme";
import { SettingsProvider } from "./state/settings";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <SettingsProvider>
        <App />
      </SettingsProvider>
    </ThemeProvider>
  </React.StrictMode>
);
