import React, { useState, useEffect } from 'react';

interface TypingMessageProps {
  content: string;
  isUser: boolean;
  onTypingComplete?: () => void;
}

const TypingMessage: React.FC<TypingMessageProps> = ({ content, isUser, onTypingComplete }) => {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showCursor, setShowCursor] = useState(true);

  // Handle the typing animation - much faster now
  useEffect(() => {
    // For very long messages (>100 chars), just show instantly
    if (content.length > 100 && currentIndex === 0) {
      setDisplayText(content);
      setCurrentIndex(content.length);
      if (onTypingComplete) {
        onTypingComplete();
      }
      return;
    }
    
    if (currentIndex < content.length) {
      // Super fast typing - 1ms per character with chunk processing
      // Process 10 characters at once for extra speed
      const chunkSize = 10;
      const endIndex = Math.min(currentIndex + chunkSize, content.length);
      const chunk = content.substring(currentIndex, endIndex);
      
      const typingTimer = setTimeout(() => {
        setDisplayText(prev => prev + chunk);
        setCurrentIndex(endIndex);
      }, 1); // Almost instant typing
      
      return () => clearTimeout(typingTimer);
    } else if (currentIndex === content.length && onTypingComplete) {
      // Notify parent when typing is complete
      onTypingComplete();
    }
  }, [content, currentIndex, onTypingComplete]);

  // Blinking cursor effect
  useEffect(() => {
    const cursorTimer = setInterval(() => {
      setShowCursor(prev => !prev);
    }, 500);
    
    return () => clearInterval(cursorTimer);
  }, []);

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-2`}>
      <div className={`max-w-[75%] px-4 py-3 rounded-lg ${
        isUser 
          ? 'bg-black text-white self-end' 
          : 'bg-white text-black border border-gray-200 self-start'
      }`}>
        {displayText}
        {currentIndex < content.length && showCursor && (
          <span className={`inline-block w-1.5 h-3.5 ml-0.5 animate-pulse ${isUser ? 'bg-white' : 'bg-gray-500'}`}></span>
        )}
      </div>
    </div>
  );
};

export default TypingMessage;
