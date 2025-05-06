import React from 'react';

const TypingIndicator: React.FC = () => {
  return (
    <div className="flex justify-start mb-2">
      <div className="max-w-[75%] px-4 py-3 rounded-lg bg-white text-black border border-gray-200">
        <div className="flex items-center">
          <div className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-pulse mr-1"></div>
          <div className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-pulse delay-100 mr-1"></div>
          <div className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-pulse delay-200"></div>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
