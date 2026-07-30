import { createTheme } from "@mui/material/styles";

// Brookhaven National Laboratory / NSLS-II inspired palette.
// BNL primary blue with an NSLS-II accent.
export const theme = createTheme({
  palette: {
    primary: {
      main: "#003087", // BNL blue
      dark: "#001f5c",
      light: "#3b5cad",
    },
    secondary: {
      main: "#0093d0", // NSLS-II cyan accent
    },
    background: {
      default: "#f4f6f9",
    },
  },
  typography: {
    fontFamily: ["Helvetica Neue", "Arial", "sans-serif"].join(","),
    h6: { fontWeight: 700 },
  },
  shape: { borderRadius: 6 },
});
