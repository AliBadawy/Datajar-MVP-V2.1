import React from 'react';

const TypingIndicator: React.FC = () => {
  return (
    <div className="flex justify-start mb-2">
      <div className="max-w-[80%] px-4 py-2 rounded-xl text-sm bg-neutral-700 text-neutral-100 text-left">
        <div className="flex items-center">
          <div className="w-1.5 h-1.5 bg-neutral-400 rounded-full animate-pulse mr-1"></div>
          <div className="w-1.5 h-1.5 bg-neutral-400 rounded-full animate-pulse delay-100 mr-1"></div>
          <div className="w-1.5 h-1.5 bg-neutral-400 rounded-full animate-pulse delay-200"></div>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
