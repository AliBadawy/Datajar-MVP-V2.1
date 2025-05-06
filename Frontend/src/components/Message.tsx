import React from 'react';

interface MessageProps {
  content: string;
  isUser: boolean;
}

const Message: React.FC<MessageProps> = ({ content, isUser }) => {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-2`}>
      <div className={`max-w-[80%] px-4 py-2 rounded-xl text-sm text-left ${isUser ? 'bg-neutral-800 text-neutral-200' : 'bg-neutral-700 text-neutral-100'}`}>
        {content}
      </div>
    </div>
  );
};

export default Message;
