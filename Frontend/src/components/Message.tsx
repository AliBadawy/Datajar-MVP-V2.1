import React from 'react';

interface MessageProps {
  content: string | any;
  isUser: boolean;
  type?: string;
  rawResponse?: any;
}

const Message: React.FC<MessageProps> = ({ content, isUser, rawResponse }) => {
  // Display message with optional Salla data
  console.log("Message props:", { content, isUser, rawResponse });

  // Check if we have Salla data in the raw response
  const hasSallaData = rawResponse && rawResponse.salla_data && rawResponse.salla_data.length > 0;
  const messageText = typeof content === 'object' && content.message ? content.message : content;
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-2`}>
      <div className={`max-w-[85%] px-4 py-3 rounded-lg ${
        isUser 
          ? 'bg-black text-white self-end' 
          : 'bg-white text-black border border-gray-200 self-start'
      }`}>
        {/* Show the echo message */}
        <div className="mb-2">{messageText}</div>
        
        {/* Show Salla data if available */}
        {!isUser && hasSallaData && (
          <div className="mt-4">
            <details className="text-sm">
              <summary className="cursor-pointer font-medium text-blue-600">View Salla Data</summary>
              <pre className="bg-gray-100 p-4 rounded text-xs overflow-x-auto mt-2">
                {JSON.stringify(rawResponse.salla_data, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </div>
  );
};

export default Message;
