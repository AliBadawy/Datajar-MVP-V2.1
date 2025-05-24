import React from 'react';

import ResponseRenderer from './ResponseRenderer';
import ReactMarkdown from 'react-markdown';

interface MessageProps {
  content: string | any;
  isUser: boolean;
  type?: string;
  rawResponse?: any;
}

const Message: React.FC<MessageProps> = ({ content, isUser, rawResponse }) => {
  // Debug log to see what's coming into the Message component
  console.log("Message props:", { content, isUser, rawResponsePreview: rawResponse ? "[Present]" : "[None]" });

  // Determine if this is a complex response that needs special rendering
  // Simplified logic to handle the different cases more explicitly
  let responseData = null;
  
  if (rawResponse) {
    // If rawResponse is provided directly, use it
    console.log("Using rawResponse for rendering", typeof rawResponse);
    responseData = rawResponse;
  } else if (typeof content === 'object' && content !== null) {
    // If content is an object with a type property, it might need special rendering
    if (content.type === 'plot' || content.type === 'dataframe' || content.type === 'error') {
      console.log("Using content object for rendering as", content.type);
      responseData = content;
    } else if (content.type === 'text') {
      // For text type, use the ResponseRenderer only if we need to
      console.log("Text type detected");
      responseData = content;
    }
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
        ) : responseData ? (
          // For AI responses with visualization or structured data
          <ResponseRenderer response={responseData} />
        ) : (
          // For simple text responses from AI
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{typeof content === 'string' ? content : JSON.stringify(content, null, 2)}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
};

export default Message;
