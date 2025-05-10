import React, { useState } from 'react';
import { useAppStore } from '../../lib/store';
import { supabase } from '../../lib/supabase';

interface SallaDialogProps {
  projectName: string;
  persona: string;
  context: string;
  industry: string;
}

/**
 * SallaDialog component for handling Salla OAuth authentication.
 * This component provides the UI and functionality to connect to a Salla store.
 */
const SallaDialog: React.FC<SallaDialogProps> = ({ projectName, persona, context, industry }) => {
  const [showModal, setShowModal] = useState(false);
  
  /**
   * Opens the data selection modal
   */
  const handleConnect = () => {
    setShowModal(true);
  };

  return (
    <div className="salla-dialog p-4 border rounded shadow-lg bg-white">
      <h2 className="text-xl font-bold mb-4">Connect to Salla Store</h2>
      <p className="mb-4">
        Connect your Salla e-commerce store to enable data analysis of your orders and products.
      </p>
      <div className="flex justify-end">
        <button 
          className="bg-[#2B52F5] text-white px-4 py-2 rounded hover:bg-[#1d3cd8] transition-colors disabled:opacity-50"
          onClick={handleConnect}
        >
          Connect Salla Store
        </button>
      </div>
      
      {showModal && <SallaConnectModal onClose={() => setShowModal(false)} projectData={{
        projectName,
        persona,
        context,
        industry,
        lastStep: 4
      }} />}
    </div>
  );
};

interface SallaConnectModalProps {
  onClose: () => void;
  projectData: {
    projectName: string;
    persona: string;
    context: string;
    industry: string;
    lastStep: number;
  };
}

function SallaConnectModal({ onClose, projectData }: SallaConnectModalProps) {
  const [resource, setResource] = useState("orders"); // Only "orders" for now
  
  // Set default date range to last 30 days
  const today = new Date();
  const thirtyDaysAgo = new Date(today);
  thirtyDaysAgo.setDate(today.getDate() - 30);
  
  const [fromDate, setFromDate] = useState(thirtyDaysAgo.toISOString().split('T')[0]);
  const [toDate, setToDate] = useState(today.toISOString().split('T')[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Get the createProject action from the store
  const createProjectInStore = useAppStore(state => state.createProject);

  const handleStartAuth = async () => {
    try {
      // Validate date range
      if (!fromDate || !toDate) {
        setError("Please select a date range");
        return;
      }
      
      // Validate that from date is before to date
      if (new Date(fromDate) > new Date(toDate)) {
        setError("From date must be before To date");
        return;
      }

      setIsLoading(true);
      setError(null);
      
      // Generate a secure random state string
      const state = crypto.randomUUID();
      
      // First, create the project in the database using our store action
      // This will use the authenticated API client
      console.log('Creating project with data:', projectData);
      
      // Use createProject from the store which handles authentication
      // The store will automatically add the user_id from Supabase
      const projectId = await createProjectInStore({
        name: projectData.projectName,
        persona: projectData.persona,
        context: projectData.context,
        industry: projectData.industry
      });
      
      // Debug session information
      try {
        const session = await supabase.auth.getSession();
        console.log('Current session before redirect:', session);
      } catch (e) {
        console.error('Error checking session:', e);
      }
      
      console.log('Project created successfully with ID:', projectId);
      
      if (!projectId) {
        throw new Error('Failed to get project ID from server response');
      }
      
      // Save the project ID and data in multiple locations to ensure it's available after redirect
      localStorage.setItem("current_project_id", String(projectId));
      localStorage.setItem("projectId", String(projectId));
      
      // Create a simplified project data object since we don't have the full response object
      const projectDataToStore = {
        id: projectId,
        name: projectData.projectName,
        persona: projectData.persona,
        context: projectData.context,
        industry: projectData.industry,
        created_at: new Date().toISOString()
      };
      
      localStorage.setItem("project_data", JSON.stringify(projectDataToStore));
      localStorage.setItem("project_form_data", JSON.stringify({
        ...projectData,
        id: projectId
      }));
      
      // Save the state and data selection parameters in localStorage to use later in callback
      localStorage.setItem("salla_state", state);
      localStorage.setItem("salla_from_date", fromDate);
      localStorage.setItem("salla_to_date", toDate);
      localStorage.setItem("salla_resource", resource);

      // Get current session to ensure we're authenticated before redirect
      const { data: sessionData } = await supabase.auth.getSession();
      if (!sessionData.session) {
        console.warn('No active session before redirect! This could cause auth issues.');
      } else {
        console.log('Active session before redirect:', sessionData.session.user.id);
      }
      
      // Make sure the redirect URI uses the current hostname
      let redirectUri = import.meta.env.VITE_SALLA_REDIRECT_URI;
      // If the redirect URI doesn't match the current hostname, use the current origin
      if (!redirectUri.includes(window.location.hostname)) {
        const callbackPath = new URL(redirectUri).pathname;
        redirectUri = `${window.location.origin}${callbackPath}`;
        console.log('Adjusted redirect URI to current origin:', redirectUri);
      }
      
      // Build the full Salla OAuth2 authorization URL
      const authUrl = `${import.meta.env.VITE_SALLA_AUTH_URL}?client_id=${import.meta.env.VITE_SALLA_CLIENT_ID}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=offline_access orders.read&state=${state}`;

      // Log for debugging
      console.log('Project created with ID:', projectId);
      console.log('From date:', fromDate, 'To date:', toDate);
      console.log('Redirecting to Salla OAuth URL:', authUrl);

      // Redirect the user to Salla to authorize
      window.location.href = authUrl;
    } catch (err) {
      console.error('Error in Salla auth flow:', err);
      setError(err instanceof Error ? err.message : 'Failed to start authentication process');
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md space-y-4">
        <h2 className="text-lg font-bold">Connect to Salla</h2>

        <div>
          <label className="block text-sm font-medium">What do you want to import?</label>
          <select 
            value={resource} 
            onChange={(e) => setResource(e.target.value)} 
            className="w-full border rounded p-2 mt-1"
          >
            <option value="orders">🧾 Orders</option>
            {/* Add more options later */}
          </select>
        </div>

        <div className="flex gap-2">
          <div className="flex-1">
            <label className="text-sm font-medium">Start Date</label>
            <input 
              type="date" 
              className="w-full border rounded p-2 mt-1" 
              value={fromDate} 
              onChange={(e) => setFromDate(e.target.value)} 
            />
          </div>
          <div className="flex-1">
            <label className="text-sm font-medium">End Date</label>
            <input 
              type="date" 
              className="w-full border rounded p-2 mt-1" 
              value={toDate} 
              onChange={(e) => setToDate(e.target.value)} 
            />
          </div>
        </div>

        <div className="flex justify-between mt-6">
          <button 
            onClick={onClose} 
            className="border px-4 py-2 rounded hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={handleStartAuth} 
            className="bg-[#2B52F5] text-white px-4 py-2 rounded hover:bg-[#1d3cd8] transition-colors"
            disabled={!fromDate || !toDate || isLoading}
          >
            {isLoading ? 'Connecting...' : 'Authorize & Connect'}
          </button>
        </div>
        {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
      </div>
    </div>
  );
}

export default SallaDialog;
