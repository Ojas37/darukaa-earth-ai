import React from 'react';
import { User } from 'lucide-react';

interface UserMessageProps {
  content: string;
  timestamp?: string;
}

export const UserMessage: React.FC<UserMessageProps> = ({ content, timestamp }) => {
  return (
    <div className="flex justify-end my-3">
      <div className="max-w-2xl bg-forest-800 text-sand-50 rounded-2xl rounded-tr-sm px-4 py-3.5 shadow-card border border-forest-700/60">
        <div className="flex items-center justify-between space-x-4 mb-1.5 pb-1 border-b border-forest-700/50">
          <div className="flex items-center space-x-1.5 text-botanical-300 text-xs font-medium">
            <User className="w-3.5 h-3.5" />
            <span>Ecologist / Site Practitioner</span>
          </div>
          {timestamp && (
            <span className="text-[10px] text-sage-400 font-mono">
              {timestamp}
            </span>
          )}
        </div>
        <p className="text-xs sm:text-[13px] text-sand-100 font-sans leading-relaxed whitespace-pre-wrap">
          {content}
        </p>
      </div>
    </div>
  );
};
