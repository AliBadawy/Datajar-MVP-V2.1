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
  // Determine if this is a complex response that needs the ResponseRenderer
  const isResponseObject = 
    typeof content === 'object' && 
    content !== null && 
    (content.type === 'plot' || content.type === 'dataframe' || content.type === 'text' || content.type === 'error');
  
  // If we have rawResponse from the API, use that directly
  const responseData = rawResponse || (isResponseObject ? content : null);

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
