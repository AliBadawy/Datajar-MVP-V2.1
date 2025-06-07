import React, { useState, useRef, useEffect } from 'react';
import { BarChart3, FileText, Calendar, X, Check, ChevronDown } from 'lucide-react';
import { Button } from '../ui/button';

interface GoogleAnalyticsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConnect: (data: {
    serviceAccountKey: File | null;
    propertyId: string;
    startDate: string;
    endDate: string;
    selectedMetrics: string[];
  }) => void;
}

interface Metric {
  value: string;
  label: string;
}

const metrics: Metric[] = [
  { value: 'active_users', label: 'Active Users' },
  { value: 'sessions', label: 'Sessions' },
  { value: 'page_views', label: 'Page Views' },
  { value: 'bounce_rate', label: 'Bounce Rate' },
  { value: 'session_duration', label: 'Session Duration' },
  { value: 'conversion_rate', label: 'Conversion Rate' },
  { value: 'transactions', label: 'Transactions' },
  { value: 'revenue', label: 'Revenue' },
];

const GoogleAnalyticsDialog: React.FC<GoogleAnalyticsDialogProps> = ({ isOpen, onClose, onConnect }) => {
  // If dialog is not open, don't render anything
  if (!isOpen) return null;

  // Form states
  const [serviceAccountKey, setServiceAccountKey] = useState<File | null>(null);
  const [propertyId, setPropertyId] = useState('');
  
  // Date range - default to last 30 days
  const today = new Date();
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(today.getDate() - 30);
  
  const [startDate, setStartDate] = useState(thirtyDaysAgo.toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(today.toISOString().split('T')[0]);
  
  // Metrics selection
  const [isMetricsOpen, setIsMetricsOpen] = useState(false);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  
  // UI states
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsMetricsOpen(false);
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);
  
  // File handling functions
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.type !== 'application/json' && !file.name.endsWith('.json')) {
        setError('Please upload a valid JSON file');
        return;
      }
      
      if (file.size > 5 * 1024 * 1024) { // 5MB
        setError('File size exceeds 5MB limit');
        return;
      }
      
      setServiceAccountKey(file);
      setError(null);
    }
  };
  
  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.currentTarget.classList.add('border-blue-500');
  };
  
  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.currentTarget.classList.remove('border-blue-500');
  };
  
  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.currentTarget.classList.remove('border-blue-500');
    
    const file = event.dataTransfer.files?.[0];
    if (file) {
      if (file.type !== 'application/json' && !file.name.endsWith('.json')) {
        setError('Please upload a valid JSON file');
        return;
      }
      
      if (file.size > 5 * 1024 * 1024) { // 5MB
        setError('File size exceeds 5MB limit');
        return;
      }
      
      setServiceAccountKey(file);
      setError(null);
    }
  };
  
  const handleRemoveFile = () => {
    setServiceAccountKey(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  
  // Toggle metric selection
  const toggleMetric = (value: string) => {
    setSelectedMetrics(prev => {
      if (prev.includes(value)) {
        return prev.filter(m => m !== value);
      } else {
        return [...prev, value];
      }
    });
  };
  
  // Get display text for selected metrics
  const getMetricsDisplayText = () => {
    if (selectedMetrics.length === 0) {
      return 'Select metrics';
    } else if (selectedMetrics.length === 1) {
      return metrics.find(m => m.value === selectedMetrics[0])?.label || 'Select metrics';
    } else {
      return `${selectedMetrics.length} metrics selected`;
    }
  };
  
  // Validate and submit form
  const handleConnect = () => {
    // Reset error state
    setError(null);
    
    // Validation
    if (!serviceAccountKey) {
      setError('Please upload a service account key file');
      return;
    }
    
    if (!propertyId) {
      setError('Please enter a Google Analytics Property ID');
      return;
    }
    
    if (!startDate || !endDate) {
      setError('Please select a date range');
      return;
    }
    
    if (selectedMetrics.length === 0) {
      setError('Please select at least one metric');
      return;
    }
    
    // Start loading state
    setIsLoading(true);
    
    // Call the onConnect callback with form data
    // In a real implementation, you might want to handle the API call here
    // and only call onConnect after a successful response
    setTimeout(() => {
      onConnect({
        serviceAccountKey,
        propertyId,
        startDate,
        endDate,
        selectedMetrics
      });
      setIsLoading(false);
      onClose();
    }, 1500);
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <div className="bg-blue-600 p-2 rounded-md mr-3">
              <BarChart3 className="text-white" size={20} />
            </div>
            <h2 className="text-xl font-semibold">Connect Google Analytics</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={20} />
          </button>
        </div>
        
        {/* Info Box */}
        <div className="bg-blue-50 p-4 rounded-md mb-6">
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Real-time website analytics</li>
            <li>• User behavior insights</li>
            <li>• Traffic source analysis</li>
            <li>• Conversion tracking</li>
          </ul>
        </div>
        
        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}
        
        {/* Step 1: Upload Service Account Key */}
        <div className="mb-6">
          <h3 className="text-sm font-medium mb-2">
            Step 1: Upload Service Account Key
          </h3>
          {!serviceAccountKey ? (
            <div
              className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 cursor-pointer transition-colors"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".json"
                className="hidden"
              />
              <p className="text-gray-500 mb-2">Drop your service account key file here or click to upload</p>
              <p className="text-xs text-gray-400">Only .json files, max 5MB</p>
            </div>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between">
              <div className="flex items-center">
                <FileText size={20} className="text-green-600 mr-3" />
                <span className="text-sm font-medium text-green-800">{serviceAccountKey.name}</span>
              </div>
              <button
                onClick={handleRemoveFile}
                className="text-gray-500 hover:text-red-500"
              >
                <X size={18} />
              </button>
            </div>
          )}
        </div>
        
        {/* Step 2: Google Analytics Property ID */}
        <div className="mb-6">
          <label htmlFor="propertyId" className="block text-sm font-medium mb-2">
            Step 2: Google Analytics Property ID
          </label>
          <input
            type="text"
            id="propertyId"
            placeholder="123-4567890"
            value={propertyId}
            onChange={(e) => setPropertyId(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Enter your Google Analytics property ID (format: XXX-XXXXXXX)
          </p>
        </div>
        
        {/* Step 3: Select Date Range */}
        <div className="mb-6">
          <h3 className="text-sm font-medium mb-2">
            Step 3: Select Date Range
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="relative">
              <label htmlFor="startDate" className="block text-xs text-gray-600 mb-1">
                Start Date
              </label>
              <div className="relative">
                <input
                  type="date"
                  id="startDate"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <Calendar size={18} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              </div>
            </div>
            <div className="relative">
              <label htmlFor="endDate" className="block text-xs text-gray-600 mb-1">
                End Date
              </label>
              <div className="relative">
                <input
                  type="date"
                  id="endDate"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <Calendar size={18} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              </div>
            </div>
          </div>
        </div>
        
        {/* Step 4: Choose Metrics */}
        <div className="mb-8">
          <h3 className="text-sm font-medium mb-2">
            Step 4: Choose Metrics
          </h3>
          <div className="relative" ref={dropdownRef}>
            <button
              type="button"
              onClick={() => setIsMetricsOpen(!isMetricsOpen)}
              className="w-full flex items-center justify-between border border-gray-300 rounded-md px-4 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <span className="text-sm">{getMetricsDisplayText()}</span>
              <ChevronDown 
                size={18} 
                className={`transition-transform duration-200 ${isMetricsOpen ? 'transform rotate-180' : ''}`}
              />
            </button>
            
            {isMetricsOpen && (
              <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg py-2 max-h-56 overflow-auto">
                {metrics.map((metric) => (
                  <div 
                    key={metric.value}
                    className="flex items-center px-4 py-2 hover:bg-gray-100 cursor-pointer"
                    onClick={() => toggleMetric(metric.value)}
                  >
                    <div className={`w-5 h-5 flex items-center justify-center border rounded mr-3 ${selectedMetrics.includes(metric.value) ? 'bg-blue-600 border-blue-600' : 'border-gray-300'}`}>
                      {selectedMetrics.includes(metric.value) && (
                        <Check size={14} className="text-white" />
                      )}
                    </div>
                    <span className="text-sm">{metric.label}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        
        {/* Footer Buttons */}
        <div className="flex justify-end space-x-4">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleConnect}
            disabled={isLoading}
            className={`${isLoading ? 'opacity-80' : ''}`}
          >
            {isLoading ? (
              <span className="flex items-center">
                <svg 
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" 
                  xmlns="http://www.w3.org/2000/svg" 
                  fill="none" 
                  viewBox="0 0 24 24"
                >
                  <circle 
                    className="opacity-25" 
                    cx="12" 
                    cy="12" 
                    r="10" 
                    stroke="currentColor" 
                    strokeWidth="4"
                  />
                  <path 
                    className="opacity-75" 
                    fill="currentColor" 
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Connecting...
              </span>
            ) : (
              'Connect to Google Analytics'
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default GoogleAnalyticsDialog;
