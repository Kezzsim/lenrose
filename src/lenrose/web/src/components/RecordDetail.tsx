import { useEffect, useState } from "react";
import {
  Drawer,
  Box,
  Typography,
  IconButton,
  Divider,
  CircularProgress,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { getRecord, type RecordDetail, type SearchHitDocument } from "../api/client";
import type { Credentials } from "../state/credentials";

export function RecordDetailDrawer({
  doc,
  tiledCredentials,
  onClose,
}: {
  doc: SearchHitDocument | null;
  tiledCredentials?: Credentials;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState<RecordDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!doc) return;
    setLoading(true);
    setError(null);
    setDetail(null);
    getRecord(doc.uuid, doc.collection, {
      method:
        tiledCredentials?.tiledAuthMethod &&
        tiledCredentials.tiledAuthMethod !== "preconfigured"
          ? tiledCredentials.tiledAuthMethod
          : undefined,
      apiKey: tiledCredentials?.tiledApiKey,
      username: tiledCredentials?.tiledUsername,
      password: tiledCredentials?.tiledPassword,
    })
      .then(setDetail)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [doc, tiledCredentials]);

  return (
    <Drawer anchor="right" open={!!doc} onClose={onClose}>
      <Box sx={{ width: 480, p: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Record</Typography>
          <IconButton onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Box>
        <Divider sx={{ my: 1 }} />
        {loading && <CircularProgress />}
        {error && <Typography color="error">{error}</Typography>}
        {detail && (
          <>
            <Typography variant="body2" color="text.secondary">
              {detail.tiled_key}
            </Typography>
            <Typography variant="subtitle2" sx={{ mt: 2 }}>
              Metadata
            </Typography>
            <Box
              component="pre"
              sx={{
                fontSize: 12,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                bgcolor: "#0d1117",
                color: "#c9d1d9",
                p: 1.5,
                borderRadius: 1,
                overflow: "auto",
              }}
            >
              {JSON.stringify(detail.metadata, null, 2)}
            </Box>
          </>
        )}
      </Box>
    </Drawer>
  );
}
