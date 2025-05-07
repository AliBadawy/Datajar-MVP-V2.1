import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import Message from './Message';
import TypingIndicator from './TypingIndicator';
import TypingMessage from './TypingMessage';
import { useAppStore } from '../lib/store';
import type { ChatMessage } from '../lib/store';

// We're using the ChatMessage type from the store

const ChatInterface: React.FC = () => {
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [isError, setIsError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  
  // Get URL parameters
  const { projectId } = useParams<{ projectId: string }>();
  
  // Get store state and actions using stable selectors to avoid infinite loops
  const currentProjectId = useAppStore(state => state.currentProjectId);
  const messages = useAppStore(state => state.messages);
  const messagesLoading = useAppStore(state => state.messagesLoading);
  const messagesError = useAppStore(state => state.messagesError);
  
  // Get store actions - these won't change between renders
  const fetchMessageHistory = useAppStore(state => state.fetchMessageHistory);
  const addMessage = useAppStore(state => state.addMessage);
  const setCurrentProject = useAppStore(state => state.setCurrentProject);
  
  // Memoize the state info to prevent unnecessary re-renders
  const stateInfo = useMemo(() => ({
    currentProjectId,
    messagesCount: messages.length,
    isLoading: messagesLoading,
    hasError: messagesError !== null
  }), [currentProjectId, messages.length, messagesLoading, messagesError]);
  
  // Debug state with memoized values to prevent rendering loops
  useEffect(() => {
    const info = {
      component: 'ChatInterface', 
      status: 'mounted',
      urlProjectId: projectId,
      ...stateInfo,
      error: messagesError
    };
    
    console.log('DEBUG INFO:', info);
    setDebugInfo(info);
    
    return () => {
      console.log('ChatInterface unmounted');
    };
  }, [projectId, stateInfo, messagesError]);
  
  // Track initialization and rendering state
  const [isInitialized, setIsInitialized] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [debugInfo, setDebugInfo] = useState<any>({});
  
  // Synchronize URL parameter with store - in a separate effect
  useEffect(() => {
    if (projectId && projectId !== currentProjectId) {
      console.log('Updating store with project ID from URL:', projectId);
      setCurrentProject(projectId);
    }
  }, [projectId, currentProjectId, setCurrentProject]);
  
  // Memoize the fetch messages function
  const safelyFetchMessages = useCallback(async (id: string) => {
    try {
      console.log('Loading message history for project ID:', id);
      await fetchMessageHistory(id);
      setIsInitialized(true);
      setHasError(false);
    } catch (error) {
      console.error('Error loading message history:', error);
      setHasError(true);
      setIsError(`Failed to load messages: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [fetchMessageHistory]);
  
  // Handle navigation separately from data fetching
  useEffect(() => {
    if (!projectId && currentProjectId) {
      // If URL has no project ID but store does, update URL
      console.log('Fixing URL to match store project ID:', currentProjectId);
      navigate(`/chat/${currentProjectId}`, { replace: true });
    } 
    else if (!projectId && !currentProjectId) {
      // No project ID anywhere, go to projects page
      console.log('No project ID found, redirecting to projects');
      navigate('/projects', { replace: true });
    }
  }, [projectId, currentProjectId, navigate]);
  
  // Handle data fetching in a separate effect with a ref to track loaded project ID
  const loadedProjectIdRef = useRef<string | null>(null);
  
  useEffect(() => {
    // Only fetch if we have a project ID and it's different from the last one we loaded
    if (projectId && loadedProjectIdRef.current !== projectId) {
      console.log('Fetching messages for project:', projectId);
      safelyFetchMessages(projectId);
      loadedProjectIdRef.current = projectId; // Store the project ID we've loaded
    }
    
    // Cleanup function
    return () => {
      // Nothing to clean up, but this helps React optimize the effect
    };
  }, [projectId, safelyFetchMessages]); // Removed messagesLoading from dependencies

  // Helper function to format data for analysis if needed in the future
  const formatDataForAnalysis = (data: any) => {
    // This will be used when we implement data upload and analysis
    return data;
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    
    // Reset error state
    setIsError(null);
    
    // Create new user message
    const userMessage = inputValue;
    const newUserMessage: ChatMessage = { content: userMessage, isUser: true };
    
    // Add user message immediately to the store
    addMessage(newUserMessage);
    
    // Clear the input field
    setInputValue('');
    
    // Show thinking indicator (three dots)
    setIsThinking(true);
    
    try {
      // Call the analyze endpoint instead of classify
      const analyzeResponse = await axios.post(`http://${window.location.hostname}:8000/api/analyze`, {
        messages: [
          { role: "user", content: userMessage }
        ],
        // Include current project ID if available
        project_id: currentProjectId ? parseInt(currentProjectId) : undefined,
        // Uncomment the line below to include sample data when testing
        // dataframe: sampleDataframe
      });
      
      // Handle response based on type
      const responseType = analyzeResponse.data.type;
      console.log("Response type:", responseType);
      
      // After getting response, simulate typing animation
      setIsThinking(false);
      
      // Create response content based on response type
      let responseContent = '';
      
      if (responseType === 'chat') {
        responseContent = analyzeResponse.data.response;
      } else if (responseType === 'data_analysis') {
        // For data analysis, combine the narrative with pandas result
        responseContent = `${analyzeResponse.data.narrative}\n\nRaw result: ${JSON.stringify(analyzeResponse.data.pandas_result, null, 2)}`;
      }
      
      // Add the AI response with typing animation
      addMessage({ 
        content: responseContent,
        isUser: false, 
        isTyping: true,
        type: responseType
      });
    } catch (error) {
      // Handle errors
      console.error('Error sending message to backend:', error);
      setIsThinking(false);
      setIsError('Failed to connect to the backend server. Please try again.');
      
      // Show error message to user
      addMessage({ 
        content: 'Sorry, I encountered an error connecting to the server. Please try again.', 
        isUser: false,
        isTyping: true
      });
    }
  };

  // Handle typing completed for a message
  // Function to update a message when typing is complete
  const handleTypingComplete = (index: number) => {
    // We no longer need this function since we're using the store
    // and our implementation uses isComplete instead of callback
    console.log('Typing complete for message at index', index);
  };

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  // Render chat interface with fallback states for error conditions
  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Debug Panel (only in development) */}
      {hasError && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 text-xs font-mono overflow-auto max-h-[200px]">
          <h3 className="font-bold text-yellow-800 mb-2">Debug Information</h3>
          <pre>{JSON.stringify(debugInfo, null, 2)}</pre>
        </div>
      )}
      
      {/* Message Container */}
      <div className="flex-1 overflow-y-auto p-4 bg-white">
        {/* Loading state */}
        {messagesLoading && (
          <div className="flex justify-center items-center p-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
          </div>
        )}
        
        {/* Error state */}
        {messagesError && (
          <div className="p-4 my-2 bg-red-50 text-red-800 rounded border border-red-200">
            <p className="font-bold">Error loading messages:</p>
            <p>{messagesError}</p>
            <button 
              className="mt-2 px-3 py-1 bg-red-100 hover:bg-red-200 text-red-800 rounded"
              onClick={() => projectId && fetchMessageHistory(projectId)}
            >
              Try Again
            </button>
          </div>
        )}
        
        {/* No messages state */}
        {!messagesLoading && !messagesError && messages.length === 0 && isInitialized && (
          <div className="p-8 text-center text-gray-500">
            <p className="mb-2 text-lg">No messages yet</p>
            <p>Send a message to start the conversation</p>
          </div>
        )}
        
        {/* Messages and typing indicator */}
        {messages.map((message, index) => (
          message.isTyping ? (
            <TypingMessage 
              key={index} 
              content={message.content} 
              isUser={message.isUser}
              onTypingComplete={() => handleTypingComplete(index)}
            />
          ) : (
            <Message 
              key={index} 
              content={message.content} 
              isUser={message.isUser} 
            />
          )
        ))}
        {isThinking && <TypingIndicator />}
        {isError && (
          <div className="text-red-600 bg-red-50 text-sm mt-2 mb-2 p-2 rounded text-center">
            {isError}
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input Container */}
      <div className="border-t border-gray-200 bg-white px-6 py-4">
        {isError && (
          <div className="mb-4 p-2 bg-red-50 text-red-800 rounded">
            {isError}
          </div>
        )}
        <div className="flex items-center gap-2">
          <input
            type="text"
            className="flex-1 rounded bg-white px-4 py-2 text-sm text-black placeholder-gray-500 border border-gray-300 focus:outline-none focus:ring-2 focus:ring-black"
            placeholder="Message DataJar..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <button
            onClick={handleSend}
            className="rounded bg-black px-4 py-2 text-sm text-white hover:bg-gray-900 transition-colors focus:outline-none focus:ring-2 focus:ring-black"
            disabled={isThinking}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
