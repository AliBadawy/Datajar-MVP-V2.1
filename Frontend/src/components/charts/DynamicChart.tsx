
import {
  BarChart, Bar,
  LineChart, Line,
  AreaChart, Area,
  XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer
} from 'recharts';

interface PlotConfig {
  x_field: string;
  y_field: string;
  chart_type: 'bar' | 'line' | 'area'; // Expandable
}

interface DynamicChartProps {
  data: Record<string, any>[];
  config: PlotConfig;
}

export default function DynamicChart({ data, config }: DynamicChartProps) {
  const { x_field, y_field, chart_type } = config;

  const commonProps = (
    <>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey={x_field} />
      <YAxis />
      <Tooltip />
    </>
  );

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        {chart_type === 'bar' && (
          <BarChart data={data}>
            {commonProps}
            <Bar dataKey={y_field} fill="#2B52F5" />
          </BarChart>
        )}

        {chart_type === 'line' && (
          <LineChart data={data}>
            {commonProps}
            <Line type="monotone" dataKey={y_field} stroke="#2B52F5" strokeWidth={2} />
          </LineChart>
        )}

        {chart_type === 'area' && (
          <AreaChart data={data}>
            {commonProps}
            <Area type="monotone" dataKey={y_field} stroke="#2B52F5" fill="#2B52F5" />
          </AreaChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
