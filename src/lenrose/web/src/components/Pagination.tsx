import { Box, Pagination as MuiPagination } from "@mui/material";
import { usePagination } from "react-instantsearch";

export function Pagination() {
  const { nbPages, currentRefinement, refine } = usePagination();

  if (nbPages <= 1) return null;

  return (
    <Box display="flex" justifyContent="center" mt={3}>
      <MuiPagination
        count={nbPages}
        page={currentRefinement + 1}
        onChange={(_, p) => refine(p - 1)}
        color="primary"
      />
    </Box>
  );
}
