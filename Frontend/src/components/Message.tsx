import React from 'react';
import ResponseRenderer from './ResponseRenderer';

interface MessageProps {
  content: string | any;
  isUser: boolean;
  type?: string;
  rawResponse?: any;
}

const Message: React.FC<MessageProps> = ({ content, isUser, rawResponse }) => {
  // Debug log to see what's coming into the Message component
  console.log("Message props:", { content, isUser, contentType: typeof content, rawResponsePreview: rawResponse ? "[Present]" : "[None]" });

  // Direct passthrough approach - don't overthink the message handling
  // If we have a string or simple content, use it directly
  // If we have raw response data, use that for complex responses
  const messageContent = isUser ? content : (rawResponse || content);
  
  console.log("Final message content type:", typeof messageContent);
  if (typeof messageContent === 'object' && messageContent !== null) {
    console.log("Object content keys:", Object.keys(messageContent));
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-2`}>
      <div className={`max-w-[85%] px-4 py-3 rounded-lg ${
        isUser 
          ? 'bg-black text-white self-end' 
          : 'bg-white text-black border border-gray-200 self-start'
      }`}>
        {isUser ? (
          // User messages are always simple text
          <div>{content}</div>
        ) : (
          // For AI responses, use ResponseRenderer with our simplified messageContent
          <ResponseRenderer response={messageContent} />
        )}
      </div>
    </div>
  );
};

export default Message;
