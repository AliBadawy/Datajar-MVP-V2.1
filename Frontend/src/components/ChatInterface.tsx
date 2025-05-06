import React, { useState, useRef, useEffect } from 'react';
import Message from './Message';
import TypingIndicator from './TypingIndicator';
import TypingMessage from './TypingMessage';

interface ChatMessage {
  content: string;
  isUser: boolean;
  isTyping?: boolean;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  const handleSend = () => {
    if (!inputValue.trim()) return;
    
    // Add user message immediately
    setMessages((prev) => [...prev, { content: inputValue, isUser: true }]);
    
    // Save the input value and clear the input field
    const userMessage = inputValue;
    setInputValue('');
    
    // Show thinking indicator (three dots)
    setIsThinking(true);
    
    // Simulate thinking delay (between 1-2 seconds)
    const thinkingDelay = Math.floor(Math.random() * 1000) + 1000;
    
    // After thinking, start typing the response letter by letter
    setTimeout(() => {
      setIsThinking(false);
      setMessages((prev) => [...prev, { content: userMessage, isUser: false, isTyping: true }]);
    }, thinkingDelay);
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
    <div className="flex flex-col h-full bg-neutral-900">
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
        <div ref={endRef} />
      </div>

      {/* Input Container */}
      <div className="border-t border-neutral-800 bg-neutral-900 px-6 py-4">
        <div className="flex items-center gap-2">
          <input
            type="text"
            className="flex-1 rounded-md bg-neutral-800 px-4 py-2 text-sm text-neutral-100 placeholder-neutral-500 border border-neutral-700 focus:outline-none focus:border-neutral-600"
            placeholder="Message DataJar..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <button
            onClick={handleSend}
            className="rounded-md bg-neutral-800 px-4 py-2 text-sm text-neutral-300 border border-neutral-700 hover:bg-neutral-700"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
