// 1-D line chart. Ported from bluesky/tiled
// web-frontend/src/components/line/line.tsx (recharts LineChart).

import Box from "@mui/material/Box";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function ArrayLineChart({
  data,
  startingIndex,
  name,
  height = 300,
}: {
  data: number[];
  startingIndex: number;
  name: string;
  height?: number;
}) {
  return (
    <Box height={height}>
      <ResponsiveContainer>
        <LineChart
          data={data.map((value, index) => ({
            index: index + startingIndex,
            [name]: value,
          }))}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="index" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" stroke="#1976d2" dot={false} dataKey={name} />
        </LineChart>
      </ResponsiveContainer>
    </Box>
  );
}
