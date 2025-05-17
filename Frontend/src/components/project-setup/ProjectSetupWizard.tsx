import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppStore } from '../../lib/store';
import { analyzeProject } from '../../lib/api';
import SallaDialog from './salla-dialog';

export default function ProjectSetupWizard() {
  const navigate = useNavigate();
  const location = useLocation();
  const { createProject } = useAppStore();
  
  // Loading and error states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  
  // Step state: 0 → 5
  const [step, setStep] = useState(0);

  // Project state
  const [projectName, setProjectName] = useState('');
  const [persona, setPersona] = useState('');
  const [context, setContext] = useState('');
  const [industry, setIndustry] = useState('');
  const [analyticsExpanded, setAnalyticsExpanded] = useState(false);

  // Project ID and analysis state tracking
  const [projectId, setProjectId] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Read step from URL parameters and restore form data when component mounts
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const stepParam = params.get('step');
    
    // Try to load saved form data if exists
    const savedFormData = localStorage.getItem('project_form_data');
    if (savedFormData) {
      try {
        const formData = JSON.parse(savedFormData);
        console.log('Loading project data from localStorage:', formData);
        
        // Restore form fields
        if (formData.projectName) setProjectName(formData.projectName);
        if (formData.persona) setPersona(formData.persona);
        if (formData.context) setContext(formData.context);
        if (formData.industry) setIndustry(formData.industry);
        
        // ✨ CRITICAL: Restore project ID
        if (formData.projectId || formData.id) {
          const id = formData.projectId || formData.id;
          console.log(`🔄 Restoring project ID from localStorage: ${id}`);
          setProjectId(id);
        }
        
        // Don't remove the data yet as we might need it if user refreshes
      } catch (error) {
        console.error('Error parsing saved form data:', error);
      }
    }
    
    // Handle step restoration
    if (stepParam) {
      const stepNumber = parseInt(stepParam, 10);
      if (!isNaN(stepNumber) && stepNumber >= 0 && stepNumber < steps.length) {
        setStep(stepNumber);
      }
    } else {
      // Check if we have a stored step in localStorage
      const storedStep = localStorage.getItem('project_setup_step');
      if (storedStep) {
        const stepNumber = parseInt(storedStep, 10);
        if (!isNaN(stepNumber) && stepNumber >= 0 && stepNumber < steps.length) {
          setStep(stepNumber);
          localStorage.removeItem('project_setup_step');
        }
      }
    }
  }, [location]);

  // Steps array
  const steps = [
    "Name Your Project",
    "Select Persona",
    "Add Context",
    "Choose Industry",
    "Import Your Data",
    "Processing Data" // New Step
  ];

  const handleNext = async () => {
    // Create project after industry selection (step 3) before moving to data import
    if (step === 3) {
      setIsSubmitting(true);
      setSubmitError(null);
      
      try {
        // Create project and store its ID
        const id = await createProject({
          name: projectName,
          persona,
          context,
          industry
        });
        
        // Store the project ID for use in subsequent steps
        setProjectId(id);
        console.log('Project created with ID:', id);
        
        // Save project ID to localStorage to ensure it persists
        const formData = {
          projectId: id,
          projectName,
          persona,
          context,
          industry,
          lastStep: step
        };
        console.log('Saving project data to localStorage:', formData);
        localStorage.setItem('project_form_data', JSON.stringify(formData));
        
        // Move to the next step
        setStep(step + 1);
      } catch (error) {
        console.error('Error creating project:', error);
        setSubmitError(
          error instanceof Error 
            ? error.message 
            : 'Failed to create the project. Please try again.'
        );
        // Don't advance to the next step if project creation failed
        return;
      } finally {
        setIsSubmitting(false);
      }
    } else if (step < steps.length - 1) {
      // For other steps, just move forward
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 0) {
      setStep(step - 1);
    }
  };

  // Analysis trigger function  // Function to trigger analysis via backend API
  const triggerProjectAnalysis = async () => {
    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      console.log("⏳ Starting analysis for project ID:", projectId);
      if (!projectId) {
        throw new Error("Project ID is missing. Cannot analyze without a project ID.");
      }
      
      const result = await analyzeProject(projectId);
      console.log("✅ Analysis completed successfully:", result);
      setAnalysisComplete(true);
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || "Unknown error";
      console.error('🔴 Analysis error details:', { 
        message: errorMessage, 
        status: err?.response?.status,
        error: err 
      });
      setAnalysisError(`❌ Analysis failed: ${errorMessage}`);
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  // Log project ID state for debugging
  useEffect(() => {
    console.log(`🔍 Current step: ${step}, Project ID: ${projectId}, Analysis complete: ${analysisComplete}`);
  }, [step, projectId, analysisComplete]);
  
  // Add effect to trigger analysis on step 5
  useEffect(() => {
    if (step === 5 && projectId && !analysisComplete && !isAnalyzing) {
      console.log(`🚀 Auto-triggering analysis for project ${projectId} on step ${step}`);
      triggerProjectAnalysis();
    }
  }, [step, projectId, analysisComplete, isAnalyzing]);


  const handleFinish = async () => {
    setIsSubmitting(true);
    setSubmitError(null);
    
    try {
      // In step 4, start analysis when clicking Next
      if (step === 4) {
        console.log("🔄 Moving to analysis step with projectId:", projectId);
        // Project is already created, just move to the analysis step
        setStep(step + 1);
      } else if (step === 5) {
        // For the final step, store project ID in localStorage and redirect to chat
        console.log("✅ Setup complete! Navigating to chat with projectId:", projectId);
        
        if (!projectId) {
          throw new Error("Missing project ID. Cannot complete setup.");
        }
        
        // Store the project ID for the chat page
        localStorage.setItem('lastProjectId', projectId as string);
        
        // Navigate to the chat page with project ID
        navigate(`/chat?project=${projectId}`);
      }
    } catch (error) {
      console.error('Error during finish step:', error);
      setSubmitError(
        error instanceof Error 
          ? error.message 
          : 'An error occurred. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Disable next button if current step's field is empty
  const isNextDisabled = () => {
    switch (step) {
      case 0:
        return !projectName.trim();
      case 1: 
        return !persona;
      case 2:
        return !context.trim();
      case 3:
        return !industry;
      default:
        return false; // File upload is optional
    }
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg border border-gray-200 shadow-sm p-8">
      {/* Progress Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          {steps.map((_, index) => (
            <React.Fragment key={index}>
              <div 
                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  index <= step ? 'bg-black text-white' : 'bg-gray-100 text-gray-400'
                }`}
              >
                {index + 1}
              </div>
              {index < steps.length - 1 && (
                <div className={`h-1 flex-1 mx-2 ${
                  index < step ? 'bg-black' : 'bg-gray-200'
                }`}></div>
              )}
            </React.Fragment>
          ))}
        </div>
        <h2 className="text-xl font-bold text-black">{steps[step]}</h2>
        <p className="text-gray-500 mt-1 text-sm">Step {step + 1} of {steps.length}</p>
      </div>

      {/* Error message */}
      {submitError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          <p>{submitError}</p>
        </div>
      )}

      {/* Step Content */}
      <div className="mb-6">
        {step === 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
            <input
              className="w-full border border-gray-300 rounded-md p-3 text-black focus:outline-none focus:ring-2 focus:ring-black"
              placeholder="Enter your project name"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
            />
            <p className="text-xs text-gray-500 mt-1">This will be displayed in your projects list</p>
          </div>
        )}
        
        {step === 1 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Select a Persona</label>
            <select
              className="w-full border border-gray-300 rounded-md p-3 text-black focus:outline-none focus:ring-2 focus:ring-black"
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
            >
              <option value="">Select persona</option>
              <option value="Business Owner">Business Owner</option>
              <option value="Data Analyst">Data Analyst</option>
              <option value="Marketer">Marketer</option>
              <option value="Developer">Developer</option>
              <option value="Student">Student</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">This affects how DataJar will analyze your data</p>
          </div>
        )}
        
        {step === 2 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Context</label>
            <textarea
              className="w-full border border-gray-300 rounded-md p-3 text-black focus:outline-none focus:ring-2 focus:ring-black"
              rows={4}
              placeholder="Describe your project goals, questions you want to answer, or specific business context..."
              value={context}
              onChange={(e) => setContext(e.target.value)}
            />
            <p className="text-xs text-gray-500 mt-1">This helps DataJar provide more relevant analysis</p>
          </div>
        )}
        
        {step === 3 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Industry</label>
            <select
              className="w-full border border-gray-300 rounded-md p-3 text-black focus:outline-none focus:ring-2 focus:ring-black"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
            >
              <option value="">Select industry</option>
              <option value="E-commerce">E-commerce</option>
              <option value="SaaS">SaaS</option>
              <option value="Healthcare">Healthcare</option>
              <option value="Finance">Finance</option>
              <option value="Education">Education</option>
              <option value="Retail">Retail</option>
              <option value="Manufacturing">Manufacturing</option>
              <option value="Technology">Technology</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">Industry-specific insights will be provided</p>
          </div>
        )}
        
        {step === 4 && (
          <div>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Connect E-commerce Store</h3>
              <p className="text-sm text-gray-600 mb-4">Connect your Salla store to analyze your e-commerce data</p>
              <SallaDialog 
                projectId={projectId || ''} // Pass the projectId to SallaDialog
                projectName={projectName}
                persona={persona}
                context={context}
                industry={industry}
              />
            </div>
            
            <div className="mb-6 border-t border-gray-200 pt-6">
              {/* Collapsible Analytics Tools Section */}
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
                <button 
                  onClick={() => setAnalyticsExpanded(!analyticsExpanded)}
                  className="flex w-full items-center justify-between text-lg font-semibold text-black mb-3 focus:outline-none bg-white p-2 rounded-md"
                >
                  <span>Connect with Analytics Tools</span>
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    className={`h-5 w-5 transition-transform ${analyticsExpanded ? 'transform rotate-180' : ''}`} 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                
                {analyticsExpanded && (
                  <div className="mt-3 pl-1 pr-1 pb-2 animate-fadeIn">
                    <p className="text-sm text-black mb-4">Connect your analytics platforms to gain deeper insights</p>
                    
                    <div className="flex flex-col space-y-3">
                      {/* Google Analytics Integration - Coming Soon */}
                      <div className="border border-gray-200 rounded-md p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="w-10 h-10 flex items-center justify-center rounded-md bg-blue-50">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-600" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M7 10.9V2.1c0-.6.4-1.1 1-1.1s1 .5 1 1.1v8.8c0 .6-.4 1.1-1 1.1s-1-.5-1-1.1zm4.5 1.5v-9c0-.8.7-1.5 1.5-1.5s1.5.7 1.5 1.5v9c0 .8-.7 1.5-1.5 1.5s-1.5-.7-1.5-1.5zm5-1.5V2.1c0-.6.4-1.1 1-1.1s1 .5 1 1.1v8.8c0 .6-.4 1.1-1 1.1s-1-.5-1-1.1z"/>
                                <path d="M19.1 20.1c-1 1-2.3 1.7-3.8 1.9-1.4.2-2.9 0-4.2-.7-1.2-.7-2.2-1.7-2.8-2.9-.6-1.3-.8-2.7-.6-4.2.2-1.4.9-2.7 1.9-3.8.5-.5 1.4-.5 1.9 0s.5 1.4 0 1.9c-.6.6-1 1.4-1.2 2.3-.1.9 0 1.8.4 2.6.4.8 1 1.4 1.8 1.8.8.4 1.7.5 2.6.4.9-.1 1.7-.6 2.3-1.2.5-.5 1.4-.5 1.9 0s.5 1.5-.2 1.9z"/>
                              </svg>
                            </div>
                            <div className="ml-3">
                              <h4 className="text-sm font-medium text-gray-900">Google Analytics</h4>
                              <p className="text-xs text-gray-500">Track user behavior and website performance</p>
                            </div>
                          </div>
                          <div className="flex items-center">
                            <span className="mr-3 px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              Coming Soon
                            </span>
                            <button 
                              className="px-3 py-1 rounded-md bg-gray-200 text-gray-500 text-sm font-medium cursor-not-allowed opacity-60"
                              disabled
                            >
                              Connect
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            <div className="mt-8 pt-6 border-t border-gray-200">
              <div className="flex items-center mb-1">
                <label className="block text-sm font-medium text-gray-700">Upload CSV Data</label>
                <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                  Coming Soon
                </span>
              </div>
              <div className="relative border border-dashed border-gray-300 p-6 text-center rounded-md bg-gray-50 opacity-60 pointer-events-none">
                <svg xmlns="http://www.w3.org/2000/svg" className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="text-sm text-gray-500 mt-2 mb-1">Drag and drop a CSV file here, or click to select</p>
                <p className="text-xs text-gray-400">Max file size: 5MB</p>
                
                {/* Disabled file input */}
                <input 
                  type="file" 
                  className="hidden" 
                  accept=".csv"
                  disabled
                />
              </div>
              <p className="text-xs text-gray-500 mt-2">CSV upload functionality will be available soon</p>
            </div>
          </div>
        )}

        {step === 5 && (
          <div className="text-center p-8">
            {isAnalyzing ? (
              <>
                <div className="animate-spin border-4 border-black border-t-transparent rounded-full w-12 h-12 mx-auto mb-4" />
                <h2 className="text-lg font-medium">Analyzing your data...</h2>
                <p className="text-gray-600 mt-2">Fetching analysis from the server</p>
              </>
            ) : analysisError ? (
              <>
                <p className="text-red-600 mb-4">{analysisError}</p>
                <button
                  onClick={triggerProjectAnalysis}
                  className="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded"
                >
                  Retry Analysis
                </button>
              </>
            ) : (
              <>
                <div className="text-green-500 mb-4 text-xl">✅ Analysis complete!</div>
                <p className="text-gray-600 mb-5">
                  Your data has been successfully analyzed and is ready for exploration.
                  Click the button below to complete the setup process.
                </p>
                <button
                  className="bg-black text-white py-2 px-5 rounded hover:bg-gray-800 transition-colors"
                  onClick={handleFinish}
                >
                  Complete Setup
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between mt-8">
        {step > 0 ? (
          <button 
            className="flex items-center bg-black text-white px-3 py-1 rounded-md hover:bg-gray-900 transition-colors focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleBack}
            disabled={isSubmitting}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </button>
        ) : <div></div>}
        
        {step < steps.length - 1 ? (
          <button 
            className="flex items-center bg-black text-white px-5 py-2 rounded-md hover:bg-gray-900 transition-colors focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleNext}
            disabled={isNextDisabled()}
          >
            Next
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        ) : (
          <button 
            className="bg-black text-white px-5 py-2 rounded-md hover:bg-gray-900 transition-colors focus:outline-none focus:ring-2 focus:ring-black focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            onClick={handleFinish}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating...
              </>
            ) : "Finish Setup"}
          </button>
        )}
      </div>
    </div>
  );
}
