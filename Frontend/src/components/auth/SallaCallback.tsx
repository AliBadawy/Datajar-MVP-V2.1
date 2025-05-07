import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

/**
 * SallaCallback component that handles the OAuth callback from Salla.
 * This component is rendered when the user is redirected back from Salla's authorization page.
 */
const SallaCallback: React.FC = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Extract URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const storedState = localStorage.getItem('salla_state');

        // Verify the state parameter for security
        if (!code) {
          throw new Error('Authorization code is missing from the callback URL');
        }

        if (!state || state !== storedState) {
          throw new Error('State mismatch. This could be a CSRF attack.');
        }

        // Clean up the stored state
        localStorage.removeItem('salla_state');

        // Send to backend for token exchange
        const response = await axios.post(`http://${window.location.hostname}:8000/api/salla/callback`, { 
          code, 
          state 
        });

        // Handle successful response
        console.log('Salla authentication successful:', response.data);
        
        // Store tokens and connection state in localStorage for persistence
        localStorage.setItem('salla_access_token', response.data.access_token);
        localStorage.setItem('salla_refresh_token', response.data.refresh_token);
        localStorage.setItem('salla_store_id', response.data.merchant);
        localStorage.setItem('salla_connected', 'true');
        localStorage.setItem('salla_connected_at', new Date().toISOString());
        
        // Check if we have saved form data
        const savedFormData = localStorage.getItem('project_form_data');
        if (savedFormData) {
          try {
            // We'll keep this for the redirect, but we don't need to modify it
            // The ProjectSetupWizard will use this data
            console.log('Found saved project form data, will be restored after redirect');
          } catch (error) {
            console.error('Error parsing saved form data:', error);
          }
        } else {
          // If no form data, at least set the step
          localStorage.setItem('project_setup_step', '4'); // Last step
        }
        
        setStatus('success');
        
        // Redirect back to the project setup after a short delay
        setTimeout(() => {
          // Pass step=4 as a URL parameter to ensure we return to the last step
          navigate('/setup-project?step=4');
        }, 2000);
        
      } catch (error) {
        console.error('Error during Salla callback:', error);
        setStatus('error');
        setErrorMessage(error instanceof Error ? error.message : 'Failed to authenticate with Salla');
      }
    };

    handleCallback();
  }, [navigate]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-lg">
        <h1 className="text-2xl font-bold text-center text-gray-800">Salla Integration</h1>
        
        {status === 'loading' && (
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#2B52F5]"></div>
            <p className="text-gray-600">Connecting to your Salla store...</p>
          </div>
        )}
        
        {status === 'success' && (
          <div className="flex flex-col items-center space-y-4 text-center">
            <div className="bg-green-100 p-3 rounded-full">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-800">Successfully Connected!</h2>
            <p className="text-gray-600">Your Salla store has been connected successfully.</p>
            <p className="text-gray-500 text-sm">Redirecting you back to continue setup...</p>
          </div>
        )}
        
        {status === 'error' && (
          <div className="flex flex-col items-center space-y-4 text-center">
            <div className="bg-red-100 p-3 rounded-full">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-800">Connection Failed</h2>
            <p className="text-gray-600">{errorMessage || 'Unable to connect to your Salla store'}</p>
            <button 
              onClick={() => navigate('/setup-project?step=4')}
              className="px-4 py-2 bg-[#2B52F5] text-white rounded hover:bg-[#1d3cd8] transition-colors"
            >
              Back to Setup
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SallaCallback;
