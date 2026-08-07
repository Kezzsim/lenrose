import { useState } from "react";
import { TextField, InputAdornment } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import { useSearchBox } from "react-instantsearch";

export function SearchBar() {
  const { query, refine } = useSearchBox();
  const [value, setValue] = useState(query);

  return (
    <TextField
      fullWidth
      placeholder="Search metadata..."
      value={value}
      onChange={(e) => {
        setValue(e.target.value);
        refine(e.target.value);
      }}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon />
          </InputAdornment>
        ),
      }}
    />
  );
}
