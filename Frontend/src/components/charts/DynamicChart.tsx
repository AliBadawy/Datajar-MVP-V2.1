
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
  // Safety checks
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="w-full h-[300px] flex items-center justify-center bg-gray-50 rounded border border-gray-200">
        <p className="text-gray-500">No data available for visualization</p>
      </div>
    );
  }

  if (!config || !config.x_field || !config.y_field) {
    return (
      <div className="w-full h-[300px] flex items-center justify-center bg-gray-50 rounded border border-gray-200">
        <p className="text-gray-500">Invalid chart configuration</p>
      </div>
    );
  }

  const { x_field, y_field, chart_type } = config;

  // Ensure all data rows have the required fields
  const validData = data.filter(item => 
    item && typeof item === 'object' && 
    (x_field in item) && 
    (y_field in item) && 
    item[y_field] !== null && item[y_field] !== undefined
  );

  if (validData.length === 0) {
    return (
      <div className="w-full h-[300px] flex items-center justify-center bg-gray-50 rounded border border-gray-200">
        <p className="text-gray-500">No valid data points for the selected fields</p>
      </div>
    );
  }

  const commonProps = (
    <>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey={x_field} />
      <YAxis />
      <Tooltip />
    </>
  );

  // Determine which chart to render
  const renderChart = () => {
    if (chart_type === 'line') {
      return (
        <LineChart data={validData}>
          {commonProps}
          <Line type="monotone" dataKey={y_field} stroke="#2B52F5" strokeWidth={2} />
        </LineChart>
      );
    } else if (chart_type === 'area') {
      return (
        <AreaChart data={validData}>
          {commonProps}
          <Area type="monotone" dataKey={y_field} stroke="#2B52F5" fill="#2B52F5" />
        </AreaChart>
      );
    } else {
      // Default to bar chart
      return (
        <BarChart data={validData}>
          {commonProps}
          <Bar dataKey={y_field} fill="#2B52F5" />
        </BarChart>
      );
    }
  };

  return (
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        {renderChart()}
      </ResponsiveContainer>
    </div>
  );
}
