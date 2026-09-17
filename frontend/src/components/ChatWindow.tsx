import React, { useEffect, useRef } from 'react';
import type { ChatMessage } from '../types/api';
import { EmptyState } from './EmptyState';
import { UserMessage } from './UserMessage';
import { AssistantResponse } from './AssistantResponse';
import { LoadingState } from './LoadingState';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  onSelectPrompt: (promptText: string) => void;
  onSelectClarificationHint?: (hint: string) => void;
  onRetry?: () => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isLoading,
  error,
  onSelectPrompt,
  onSelectClarificationHint,
  onRetry,
}) => {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading, error]);

  return (
    <div className="flex-1 w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 overflow-y-auto">
      {/* Empty Landing View */}
      {messages.length === 0 && !isLoading && !error && (
        <EmptyState onSelectPrompt={onSelectPrompt} />
      )}

      {/* Message Sequence */}
      <div className="space-y-6">
        {messages.map((msg) => (
          <div key={msg.id} className="animate-fade-in">
            {msg.role === 'user' ? (
              <UserMessage content={msg.content} timestamp={msg.timestamp} />
            ) : msg.response ? (
              <AssistantResponse
                response={msg.response}
                onSelectClarificationHint={onSelectClarificationHint}
              />
            ) : (
              <div className="p-4 bg-white rounded-xl border border-sage-200 text-xs text-forest-800">
                {msg.content}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Loading Indicator */}
      {isLoading && <LoadingState />}

      {/* Error Banner */}
      {error && (
        <div className="my-4 max-w-xl mx-auto p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 space-y-2 animate-fade-in">
          <div className="flex items-center space-x-2 font-semibold">
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
            <span>Environmental Reasoning Error</span>
          </div>
          <p className="font-sans leading-relaxed">{error}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-red-100 hover:bg-red-200 text-red-900 font-medium rounded-lg text-xs transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Retry Request</span>
            </button>
          )}
        </div>
      )}

      {/* Scroll anchor */}
      <div ref={bottomRef} className="h-4" />
    </div>
  );
};
