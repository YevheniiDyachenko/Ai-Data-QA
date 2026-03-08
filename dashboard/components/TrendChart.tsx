import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts';
import { TrendPoint } from '../types/report';

interface TrendChartProps {
  history: TrendPoint[];
}

export default function TrendChart({ history }: TrendChartProps) {
  if (history.length === 0) {
    return null;
  }

  return (
    <section className="card">
      <h3>Data quality trend</h3>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={history}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="run_date" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="tests_passed" stroke="#16a34a" strokeWidth={2} />
            <Line type="monotone" dataKey="tests_failed" stroke="#dc2626" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
