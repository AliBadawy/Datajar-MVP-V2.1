import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppStore } from '../../lib/store';
import { analyzeProject } from '../../lib/api';
import SallaDialog from './salla-dialog';
import GoogleAnalyticsDialog from './google-analytics-dialog';
import { BarChart3, Database, Facebook } from 'lucide-react';
import toast from 'react-hot-toast';

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
  const [isGADialogOpen, setIsGADialogOpen] = useState(false);

  // Project ID and analysis state tracking
  const [projectId, setProjectId] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  
  // Analysis progress tracking
  type AnalysisStep = {
    name: string;
    description: string;
    status: 'waiting' | 'in-progress' | 'complete' | 'error';
  };
  
  const [analysisSteps, setAnalysisSteps] = useState<AnalysisStep[]>([
    { name: 'initialize', description: 'Initializing analysis process', status: 'waiting' },
    { name: 'analyze', description: 'Analyzing project data', status: 'waiting' },
    { name: 'save', description: 'Saving metadata to database', status: 'waiting' }
  ]);
  
  const updateAnalysisStep = (stepName: string, status: AnalysisStep['status']) => {
    setAnalysisSteps(steps => steps.map(step => 
      step.name === stepName ? { ...step, status } : step
    ));
  };

  // Read step from URL parameters and restore form data when component mounts
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const stepParam = params.get('step');
    
    const savedFormData = localStorage.getItem('project_form_data');
    if (savedFormData) {
      try {
        const formData = JSON.parse(savedFormData);
        console.log('Loading project data from localStorage:', formData);
        
        if (formData.projectName) setProjectName(formData.projectName);
        if (formData.persona) setPersona(formData.persona);
        if (formData.context) setContext(formData.context);
        if (formData.industry) setIndustry(formData.industry);
        // Google Analytics integration will be implemented in future updates
        
        if (formData.projectId || formData.id) {
          const id = formData.projectId || formData.id;
          console.log(`🔄 Restoring project ID from localStorage: ${id}`);
          setProjectId(id);
        }
      } catch (error) {
        console.error('Error parsing saved form data:', error);
      }
    }
    
    if (stepParam) {
      const stepNumber = parseInt(stepParam, 10);
      if (!isNaN(stepNumber) && stepNumber >= 0 && stepNumber < steps.length) {
        setStep(stepNumber);
      }
    } else {
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

  const steps = [
    "Name Your Project",
    "Select Persona",
    "Add Context",
    "Choose Industry",
    "Import Your Data",
    "Processing Data"
  ];

  const handleNext = async () => {
    if (step === 3) {
      setIsSubmitting(true);
      setSubmitError(null);
      
      try {
        const id = await createProject({
          name: projectName,
          persona,
          context,
          industry
        });
        
        setProjectId(id);
        console.log('Project created with ID:', id);
        
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
        
        setStep(step + 1);
      } catch (error) {
        console.error('Error creating project:', error);
        setSubmitError(
          error instanceof Error 
            ? error.message 
            : 'Failed to create the project. Please try again.'
        );
        return;
      } finally {
        setIsSubmitting(false);
      }
    } else if (step < steps.length - 1) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 0) {
      setStep(step - 1);
    }
  };

  const triggerProjectAnalysis = async () => {
    setIsAnalyzing(true);
    setAnalysisError(null);
    setAnalysisData(null);
    
    setAnalysisSteps(steps => steps.map(step => ({ ...step, status: 'waiting' as const })));

    try {
      console.log("⏳ Starting analysis for project ID:", projectId);
      updateAnalysisStep('initialize', 'in-progress');
      
      if (!projectId) {
        throw new Error("Project ID is missing. Cannot analyze without a project ID.");
      }
      
      await new Promise(resolve => setTimeout(resolve, 800));
      updateAnalysisStep('initialize', 'complete');
      
      updateAnalysisStep('analyze', 'in-progress');
      
      await new Promise(resolve => setTimeout(resolve, 1500)); 
      
      const result = await analyzeProject(projectId);
      updateAnalysisStep('analyze', 'complete');
      console.log("✅ Analysis completed successfully:", result);
      
      updateAnalysisStep('save', 'in-progress');
      await new Promise(resolve => setTimeout(resolve, 1000));
      updateAnalysisStep('save', 'complete');
      
      setAnalysisData(result);
      setAnalysisComplete(true);
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || "Unknown error";
      console.error('🔴 Analysis error details:', { 
        message: errorMessage, 
        status: err?.response?.status,
        error: err 
      });
      
      const currentStep = analysisSteps.find(step => step.status === 'in-progress')?.name || 'analyze';
      updateAnalysisStep(currentStep, 'error');
      
      setAnalysisError(`❌ Analysis failed: ${errorMessage}`);
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  useEffect(() => {
    console.log(`🔍 Current step: ${step}, Project ID: ${projectId}, Analysis complete: ${analysisComplete}`);
  }, [step, projectId, analysisComplete]);
  
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
      if (step === 4) {
        console.log("🔄 Moving to analysis step with projectId:", projectId);
        setStep(step + 1);
      } else if (step === 5) {
        console.log("✅ Setup complete! Navigating to chat with projectId:", projectId);
        
        if (!projectId) {
          throw new Error("Missing project ID. Cannot complete setup.");
        }
        
        localStorage.setItem('lastProjectId', projectId as string);
        
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
        return false;
    }
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg border border-gray-200 shadow-sm p-8">
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

      {submitError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          <p>{submitError}</p>
        </div>
      )}

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
                projectId={projectId || ''} 
                projectName={projectName}
                persona={persona}
                context={context}
                industry={industry}
              />
            </div>
            
            <div className="mb-6 border-t border-gray-200 pt-6">
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
                    
                    <div className="space-y-4">
                      {/* Google Analytics Card */}
                      <div 
                        className="border rounded-lg p-4 bg-white hover:bg-gray-50 cursor-pointer transition-colors"
                        onClick={() => setIsGADialogOpen(true)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <BarChart3 className="h-6 w-6 mr-3 text-blue-600" />
                            <div>
                              <div className="flex items-center gap-2">
                                <h3 className="font-medium text-gray-600">Connect Google Analytics</h3>
                              </div>
                              <p className="text-sm text-gray-400">Import website traffic and user behavior data</p>
                            </div>
                          </div>
                          <div className="w-10 h-6 rounded-full bg-gray-200 flex items-center p-1">
                            <div className="w-4 h-4 rounded-full bg-white"></div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Google Analytics Dialog */}
                      <GoogleAnalyticsDialog
                        isOpen={isGADialogOpen}
                        onClose={() => setIsGADialogOpen(false)}
                        onConnect={(data) => {
                          console.log('Google Analytics connection data:', data);
                          toast.success('Successfully connected to Google Analytics');
                          setIsGADialogOpen(false);
                        }}
                      />
                      
                      {/* BigQuery Card */}
                      <div className="border rounded-lg p-4 bg-gray-50 opacity-75 cursor-not-allowed">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <Database className="h-6 w-6 mr-3 text-gray-400" />
                            <div>
                              <div className="flex items-center gap-2">
                                <h3 className="font-medium text-gray-600">Connect BigQuery</h3>
                                <span className="px-2 py-1 text-xs bg-gray-200 text-gray-600 rounded-full">Coming Soon</span>
                              </div>
                              <p className="text-sm text-gray-400">Import structured data from your BigQuery tables</p>
                            </div>
                          </div>
                          <div className="w-10 h-6 rounded-full bg-gray-300 flex items-center p-1">
                            <div className="w-4 h-4 rounded-full bg-white"></div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Facebook Business Card */}
                      <div className="border rounded-lg p-4 bg-gray-50 opacity-75 cursor-not-allowed">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <Facebook className="h-6 w-6 mr-3 text-[#1877F2]" />
                            <div>
                              <div className="flex items-center gap-2">
                                <h3 className="font-medium text-gray-600">Connect Facebook Business</h3>
                                <span className="px-2 py-1 text-xs bg-gray-200 text-gray-600 rounded-full">Coming Soon</span>
                              </div>
                              <p className="text-sm text-gray-400">Import ads and page insights from Facebook</p>
                            </div>
                          </div>
                          <div className="w-10 h-6 rounded-full bg-gray-300 flex items-center p-1">
                            <div className="w-4 h-4 rounded-full bg-white"></div>
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
                <h2 className="text-lg font-medium mb-4">Analyzing your data...</h2>
                
                <div className="w-full max-w-md mx-auto space-y-3 mb-6 border border-gray-200 rounded-lg p-4 bg-gray-50">
                  {analysisSteps.map((step) => (
                    <div key={step.name} className="flex items-start">
                      <div className="mt-0.5 mr-3">
                        {step.status === 'waiting' && (
                          <div className="w-5 h-5 rounded-full border-2 border-gray-300"></div>
                        )}
                        {step.status === 'in-progress' && (
                          <div className="w-5 h-5 rounded-full border-2 border-blue-500 border-t-transparent animate-spin"></div>
                        )}
                        {step.status === 'complete' && (
                          <div className="w-5 h-5 rounded-full bg-green-500 text-white flex items-center justify-center">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path>
                            </svg>
                          </div>
                        )}
                        {step.status === 'error' && (
                          <div className="w-5 h-5 rounded-full bg-red-500 text-white flex items-center justify-center">
                            <span className="text-xs font-bold">!</span>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <p className={`font-medium ${step.status === 'error' ? 'text-red-600' : step.status === 'in-progress' ? 'text-blue-600' : step.status === 'complete' ? 'text-green-600' : 'text-gray-600'}`}>
                          {step.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
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
                <div className="mb-6 p-6 border border-green-200 rounded-lg bg-green-50">
                  <div className="flex items-center justify-center mb-4">
                    <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                      <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="text-center text-green-700 text-xl font-medium mb-2">Analysis Complete!</h3>
                  <p className="text-center text-gray-600 mb-4">
                    Your data has been successfully analyzed and is ready for exploration.
                  </p>

                  <div className="w-full max-w-md mx-auto space-y-2 mb-4">
                    {analysisSteps.map((step, index) => (
                      <div key={step.name} className="flex items-center animate-fadeIn" style={{animationDelay: `${index * 150}ms`}}>
                        <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-500 text-white flex items-center justify-center">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path>
                          </svg>
                        </div>
                        <p className="ml-3 text-sm text-gray-700">{step.description}</p>
                      </div>
                    ))}
                  </div>
                  
                  <p className="text-center text-gray-600 text-sm">
                    Please click "Finish Setup" at the bottom to complete the process.
                  </p>
                </div>
                
                {analysisData && (
                  <div className="w-full max-w-4xl mx-auto mb-5 mt-6">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-left">Analysis Results</h3>
                      <div className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">JSON Preview</div>
                    </div>
                    <div className="border border-gray-200 rounded-lg overflow-hidden">
                      <div className="bg-gray-50 border-b border-gray-200 py-2 px-4 flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-gray-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        <span className="text-xs text-gray-600 font-mono">project_metadata.json</span>
                      </div>
                      <pre className="bg-slate-100 p-4 text-left overflow-auto max-h-60 text-sm">
                        {JSON.stringify(analysisData, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
                
              </>
            )}
          </div>
        )}
      </div>

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