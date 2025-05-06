import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import Message from './Message';
import TypingIndicator from './TypingIndicator';
import TypingMessage from './TypingMessage';

interface ChatMessage {
  content: string;
  isUser: boolean;
  isTyping?: boolean;
  intent?: string;
  type?: string;
  pandas_result?: any;
  narrative?: string;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [isError, setIsError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  // Sample data for testing data analysis - you can remove or modify this
  const sampleDataframe = {
    "product": ["Product A", "Product B", "Product C"],
    "revenue": [1200, 2500, 1800],
    "marketing_cost": [500, 800, 400]
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    
    // Reset error state
    setIsError(null);
    
    // Add user message immediately
    setMessages((prev) => [...prev, { content: inputValue, isUser: true }]);
    
    // Save the input value and clear the input field
    const userMessage = inputValue;
    setInputValue('');
    
    // Show thinking indicator (three dots)
    setIsThinking(true);
    
    try {
      // Call the analyze endpoint instead of classify
      const analyzeResponse = await axios.post(`http://${window.location.hostname}:8000/api/analyze`, {
        messages: [
          { role: "user", content: userMessage }
        ],
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
      setMessages((prev) => [...prev, { 
        content: responseContent,
        isUser: false, 
        isTyping: true,
        type: responseType
      }]);
    } catch (error) {
      // Handle errors
      console.error('Error sending message to backend:', error);
      setIsThinking(false);
      setIsError('Failed to connect to the backend server. Please try again.');
      
      // Show error message to user
      setMessages((prev) => [...prev, { 
        content: 'Sorry, I encountered an error connecting to the server. Please try again.', 
        isUser: false,
        isTyping: true
      }]);
    }
  };

  // Handle typing completed for a message
  const handleTypingComplete = (index: number) => {
    setMessages(prev => 
      prev.map((msg, i) => 
        i === index ? { ...msg, isTyping: false } : msg
      )
    );
  };

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Message Container */}
      <div className="flex-1 overflow-auto px-6 py-4">
        {messages.map((msg, idx) => (
          msg.isTyping && !msg.isUser ? (
            <TypingMessage 
              key={idx} 
              content={msg.content} 
              isUser={msg.isUser} 
              onTypingComplete={() => handleTypingComplete(idx)} 
            />
          ) : (
            <Message key={idx} content={msg.content} isUser={msg.isUser} />
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
