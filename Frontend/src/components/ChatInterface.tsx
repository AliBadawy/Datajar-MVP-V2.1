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
  const dataframe = useAppStore(state => state.dataframe);
  const projectMetadata = useAppStore(state => state.projectMetadata);
  const contextLoading = useAppStore(state => state.contextLoading);
  const contextError = useAppStore(state => state.contextError);
  
  // Get store actions - these won't change between renders
  const fetchMessageHistory = useAppStore(state => state.fetchMessageHistory);
  const loadProjectContext = useAppStore(state => state.loadProjectContext);
  const addMessage = useAppStore(state => state.addMessage);
  const setCurrentProject = useAppStore(state => state.setCurrentProject);
  const clearMessages = useAppStore(state => state.clearMessages);
  
  // Memoize the state info to prevent unnecessary re-renders
  const stateInfo = useMemo(() => ({
    currentProjectId,
    messagesCount: messages.length,
    isLoading: messagesLoading || contextLoading,
    hasError: messagesError !== null || contextError !== null,
    hasData: dataframe !== null,
    hasMetadata: projectMetadata !== null
  }), [currentProjectId, messages.length, messagesLoading, messagesError, dataframe, projectMetadata, contextLoading, contextError]);
  
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
  
  // Handle data fetching whenever component mounts or projectId changes - ensure reliable message loading
  useEffect(() => {
    // Always fetch fresh data when the component mounts or when project ID changes
    if (projectId) {
      console.log('Loading full context for project:', projectId);
      
      // Clear messages first to avoid showing stale messages
      // This ensures we don't see old messages while loading
      clearMessages();
      
      // Load everything at once
      loadProjectContext(projectId).catch(error => {
        console.error('Failed to load project context:', error);
        setIsError(`Failed to load project context: ${error instanceof Error ? error.message : 'Unknown error'}`);
        
        // Fall back to just fetching messages if the full context fails
        safelyFetchMessages(projectId);
      });
    }
    
    // Cleanup function when component unmounts or projectId changes
    return () => {
      console.log('Cleaning up chat component resources');
    };
  }, [projectId, loadProjectContext, safelyFetchMessages]); // Simplified dependencies

  // Format data for analysis using stored dataframe
  const getDataForAnalysis = () => {
    if (!dataframe) return undefined;
    
    return {
      rows: dataframe.rows,
      columns: dataframe.columns
    };
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
      // Call the analyze endpoint with full context
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const analyzeResponse = await axios.post(`${API_URL}/api/analyze`, {
        messages: [
          { role: "user", content: userMessage }
        ],
        // Include current project ID if available
        project_id: currentProjectId ? parseInt(currentProjectId) : undefined,
        // Include dataframe if available
        dataframe: getDataForAnalysis(),
        // Include project metadata if available
        persona: projectMetadata?.persona,
        industry: projectMetadata?.industry,
        business_context: projectMetadata?.context
      });
      
      // Handle response based on type
      console.log("Response data:", analyzeResponse.data);
      
      // After getting response, simulate typing animation
      setIsThinking(false);
      
      // Debug log the response data
      console.log("RAW API RESPONSE:", analyzeResponse.data);
      
      // The backend now returns plain text directly
      // Just use the response data as is
      const responseContent = analyzeResponse.data;
      
      // Ultra simple approach - just add the text response directly
      console.log("Adding message with content:", responseContent);
      
      // Add the AI response - no typing animation for simplicity
      addMessage({ 
        content: responseContent,
        isUser: false
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
