import React from 'react';

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
  /**
   * Handles the connection to Salla store through OAuth2 flow.
   * Generates a secure state, saves it to localStorage, and redirects to Salla's auth page.
   */
  const handleConnect = () => {
    // Generate a secure random state string
    const state = crypto.randomUUID();
    
    // Save current project form data to localStorage
    const projectData = {
      projectName,
      persona,
      context,
      industry,
      lastStep: 4 // The step we're currently on
    };
    
    localStorage.setItem("project_form_data", JSON.stringify(projectData));
    
    // Save the state in localStorage to verify it later in callback
    localStorage.setItem("salla_state", state);

    // Build the full Salla OAuth2 authorization URL
    const authUrl = `${import.meta.env.VITE_SALLA_AUTH_URL}?client_id=${import.meta.env.VITE_SALLA_CLIENT_ID}&redirect_uri=${import.meta.env.VITE_SALLA_REDIRECT_URI}&response_type=code&scope=offline_access orders.read&state=${state}`;

    // Log for debugging in development
    console.log('Redirecting to Salla OAuth URL:', authUrl);

    // Redirect the user to Salla to authorize
    window.location.href = authUrl;
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
    </div>
  );
};

export default SallaDialog;
