import React from 'react';

interface MessageProps {
  content: string;
  isUser: boolean;
}

const Message: React.FC<MessageProps> = ({ content, isUser }) => {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-2`}>
      <div className={`max-w-[75%] px-4 py-3 rounded-lg ${
        isUser 
          ? 'bg-black text-white self-end' 
          : 'bg-white text-black border border-gray-200 self-start'
      }`}>
        {content}
      </div>
    </div>
  );
};

export default Message;
