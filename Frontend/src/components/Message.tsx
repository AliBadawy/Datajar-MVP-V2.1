import React from 'react';

interface MessageProps {
  content: string | any;
  isUser: boolean;
  type?: string;
  rawResponse?: any;
}

const Message: React.FC<MessageProps> = ({ content, isUser }) => {
  // Simple message component that just displays text
  // This greatly simplifies the rendering process
  console.log("Message props:", { content, isUser });


  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-2`}>
      <div className={`max-w-[85%] px-4 py-3 rounded-lg ${
        isUser 
          ? 'bg-black text-white self-end' 
          : 'bg-white text-black border border-gray-200 self-start'
      }`}>
        {/* Ultra simple - just show the content as plain text */}
        <div>{content}</div>
      </div>
    </div>
  );
};

export default Message;
