import React, { useState, useRef } from 'react';
import { useToast } from '../../hooks/useToast';

interface GoogleAnalyticsDialogProps {
  projectId: string;
  onSuccess?: () => void;
  onClose: () => void;
  isOpen: boolean;
}

export default function GoogleAnalyticsDialog({
  projectId,
  onSuccess,
  onClose,
  isOpen
}: GoogleAnalyticsDialogProps) {
  // State for form fields
  const [propertyId, setPropertyId] = useState('');
  const [startDate, setStartDate] = useState('30daysAgo');
  const [endDate, setEndDate] = useState('today');
  const [selectedMetric, setSelectedMetric] = useState('activeUsers');
  const [isUploading, setIsUploading] = useState(false);
  const [fileName, setFileName] = useState('');
  
  // File input reference
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Toast notifications
  const { showToast } = useToast();
  
  // Available date range presets
  const dateRangePresets = [
    { label: 'Last 7 days', startValue: '7daysAgo', endValue: 'today' },
    { label: 'Last 30 days', startValue: '30daysAgo', endValue: 'today' },
    { label: 'Last 90 days', startValue: '90daysAgo', endValue: 'today' },
    { label: 'This year', startValue: 'yearStart', endValue: 'today' },
    { label: 'Last year', startValue: '365daysAgo', endValue: 'today' },
    { label: 'Custom range', startValue: '', endValue: '' }
  ];
  
  // Available metrics
  const metrics = [
    { value: 'activeUsers', label: 'Active Users' },
    { value: 'newUsers', label: 'New Users' },
    { value: 'sessions', label: 'Sessions' },
    { value: 'totalUsers', label: 'Total Users' },
    { value: 'screenPageViews', label: 'Page Views' }
  ];
  
  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      // In a real implementation, you would upload or handle the file here
    }
  };
  
  // Handle date range preset selection
  const handleDateRangePresetChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedPreset = dateRangePresets.find(preset => 
      preset.label === e.target.value
    );
    
    if (selectedPreset) {
      setStartDate(selectedPreset.startValue);
      setEndDate(selectedPreset.endValue);
    }
  };
  
  // Handle connect button click
  const handleConnect = async () => {
    if (!fileName) {
      showToast('Please upload your Google Analytics credentials file', 'error');
      return;
    }
    
    if (!propertyId) {
      showToast('Please enter your Google Analytics Property ID', 'error');
      return;
    }
    
    setIsUploading(true);
    
    try {
      // This is where you would make an API call to your backend
      // to store the credentials and configuration
      
      // Example API call (replace with actual implementation)
      // const response = await fetch('/api/data-sources/google-analytics/connect', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify({
      //     projectId,
      //     propertyId,
      //     startDate,
      //     endDate,
      //     metric: selectedMetric,
      //     // You would handle file upload separately
      //   }),
      // });
      
      // For now, we'll simulate success
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      showToast('Google Analytics connected successfully!', 'success');
      
      // Call the onSuccess callback if provided
      if (onSuccess) {
        onSuccess();
      }
      
      // Close the dialog
      onClose();
    } catch (error) {
      console.error('Error connecting Google Analytics:', error);
      showToast('Failed to connect Google Analytics', 'error');
    } finally {
      setIsUploading(false);
    }
  };
  
  // If the dialog is not open, don't render anything
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Connect Google Analytics</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 focus:outline-none"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="space-y-4">
          {/* Credentials File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Google Analytics Credentials JSON
            </label>
            <div className="flex items-center">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept=".json"
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black"
              >
                Choose File
              </button>
              <span className="ml-3 text-sm text-gray-500">
                {fileName || 'No file selected'}
              </span>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Upload your Google Analytics service account key file (JSON)
            </p>
          </div>
          
          {/* Property ID */}
          <div>
            <label htmlFor="property-id" className="block text-sm font-medium text-gray-700 mb-2">
              Property ID
            </label>
            <input
              type="text"
              id="property-id"
              value={propertyId}
              onChange={(e) => setPropertyId(e.target.value)}
              placeholder="e.g. 123456789"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-black focus:border-black"
            />
            <p className="mt-1 text-xs text-gray-500">
              From Google Analytics Admin &gt; Property Settings
            </p>
          </div>
          
          {/* Date Range */}
          <div>
            <label htmlFor="date-range" className="block text-sm font-medium text-gray-700 mb-2">
              Date Range
            </label>
            <select
              id="date-range"
              onChange={handleDateRangePresetChange}
              defaultValue="Last 30 days"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-black focus:border-black"
            >
              {dateRangePresets.map((preset) => (
                <option key={preset.label} value={preset.label}>
                  {preset.label}
                </option>
              ))}
            </select>
          </div>
          
          {/* Metrics */}
          <div>
            <label htmlFor="metrics" className="block text-sm font-medium text-gray-700 mb-2">
              Select Metric
            </label>
            <select
              id="metrics"
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-black focus:border-black"
            >
              {metrics.map((metric) => (
                <option key={metric.value} value={metric.value}>
                  {metric.label}
                </option>
              ))}
            </select>
          </div>
          
          {/* Actions */}
          <div className="flex justify-end pt-4">
            <button
              onClick={onClose}
              type="button"
              className="mr-3 bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black"
            >
              Cancel
            </button>
            <button
              onClick={handleConnect}
              disabled={isUploading}
              className="bg-black text-white py-2 px-4 rounded-md shadow-sm text-sm font-medium hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black"
            >
              {isUploading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Connecting...
                </span>
              ) : (
                'Connect'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
