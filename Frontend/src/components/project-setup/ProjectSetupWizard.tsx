import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppStore } from '../../lib/store';
import SallaDialog from './salla-dialog';

export default function ProjectSetupWizard() {
  const navigate = useNavigate();
  const location = useLocation();
  const { createProject } = useAppStore();
  
  // Loading and error states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  
  // Step state: 0 → 4
  const [step, setStep] = useState(0);

  // Read step from URL parameters and restore form data when component mounts
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const stepParam = params.get('step');
    
    // Try to load saved form data if exists
    const savedFormData = localStorage.getItem('project_form_data');
    if (savedFormData) {
      try {
        const formData = JSON.parse(savedFormData);
        
        // Restore form fields
        if (formData.projectName) setProjectName(formData.projectName);
        if (formData.persona) setPersona(formData.persona);
        if (formData.context) setContext(formData.context);
        if (formData.industry) setIndustry(formData.industry);
        
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

  // Project state
  const [projectName, setProjectName] = useState('');
  const [persona, setPersona] = useState('');
  const [context, setContext] = useState('');
  const [industry, setIndustry] = useState('');

  // Steps array
  const steps = [
    "Name Your Project",
    "Select Persona",
    "Add Context",
    "Choose Industry",
    "Import Your Data"
  ];

  const handleNext = () => {
    if (step < steps.length - 1) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 0) {
      setStep(step - 1);
    }
  };

  const handleFinish = async () => {
    setIsSubmitting(true);
    setSubmitError(null);
    
    try {
      // Call the API via our store to create the project
      await createProject({
        name: projectName,
        persona,
        context,
        industry
      });
      
      // Redirect to /chat
      navigate("/chat");
    } catch (error) {
      console.error('Error creating project:', error);
      setSubmitError(
        error instanceof Error 
          ? error.message 
          : 'Failed to create the project. Please try again.'
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
                projectName={projectName}
                persona={persona}
                context={context}
                industry={industry}
              />
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
