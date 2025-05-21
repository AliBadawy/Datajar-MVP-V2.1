import DynamicChart from "./charts/DynamicChart";
import ReactMarkdown from 'react-markdown';

interface PlotConfig {
  x_field: string;
  y_field: string;
  chart_type: 'bar' | 'line' | 'area';
}

interface ResponseRendererProps {
  response: {
    type: string;
    response?: any;
    plot_config?: PlotConfig;
    value?: any;
    filepath?: string;
    narrative?: string;
    pandas_result?: any;
  };
}

export default function ResponseRenderer({ response }: ResponseRendererProps) {
  // Handle plot responses (new format)
  if (response.type === "plot" && response.plot_config) {
    return (
      <div className="py-4">
        <div className="bg-white border rounded-lg shadow p-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Visualized Result</h3>
          <DynamicChart data={response.response} config={response.plot_config} />
        </div>
      </div>
    );
  }

  // Legacy plot format (file-based)
  if (response.type === "plot" && response.filepath) {
    return (
      <div className="py-4">
        <div className="bg-white border rounded-lg shadow p-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Visualized Result</h3>
          <img src={response.filepath} alt="Chart" className="max-w-full h-auto" />
          <p className="text-sm text-gray-600 mt-2">{response.response}</p>
        </div>
      </div>
    );
  }

  // Handle dataframe responses
  if (response.type === "dataframe" || (response.type === "plot" && !response.plot_config)) {
    const data = response.response || response.value;
    return (
      <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto my-4">
        {JSON.stringify(data, null, 2)}
      </pre>
    );
  }

  // Handle text responses
  if (response.type === "text") {
    return (
      <div className="prose max-w-none">
        <ReactMarkdown>{response.response || response.value}</ReactMarkdown>
      </div>
    );
  }

  // Handle error responses
  if (response.type === "error") {
    return (
      <div className="text-red-600 font-semibold bg-red-50 p-3 rounded border border-red-200 my-4">
        {response.response || response.value}
      </div>
    );
  }

  // Fallback for other response types (legacy data_analysis, chat)
  if (response.narrative) {
    return (
      <div className="prose max-w-none">
        <ReactMarkdown>{response.narrative}</ReactMarkdown>
        {response.pandas_result && (
          <details className="mt-4">
            <summary className="cursor-pointer font-medium text-blue-600">View Raw Data</summary>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto mt-2">
              {JSON.stringify(response.pandas_result, null, 2)}
            </pre>
          </details>
        )}
      </div>
    );
  }

  // Default fallback
  return <p className="text-gray-800">{typeof response === 'string' ? response : JSON.stringify(response)}</p>;
}
