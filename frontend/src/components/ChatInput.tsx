import React, { useRef, useEffect } from 'react';
import { Send, X } from 'lucide-react';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (e?: React.FormEvent) => void;
  isLoading: boolean;
  onClear?: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSubmit,
  isLoading,
  onClear,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Auto-resize textarea as text grows
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !isLoading) {
        onSubmit();
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim() && !isLoading) {
      onSubmit(e);
    }
  };

  return (
    <div className="sticky bottom-0 z-20 w-full bg-gradient-to-t from-[#F7F7F2] via-[#F7F7F2]/95 to-transparent pt-3 pb-4 sm:pb-6 px-4">
      <div className="max-w-4xl mx-auto">
        <form
          onSubmit={handleSubmit}
          className="relative bg-white border border-sage-300 focus-within:border-botanical-500 focus-within:ring-2 focus-within:ring-botanical-500/20 rounded-2xl shadow-elevated transition-all duration-200"
        >
          {/* Main Input Textarea */}
          <div className="p-3 sm:p-4">
            <textarea
              ref={textareaRef}
              rows={2}
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe your site (e.g. soil texture, rainfall mm/yr, organic carbon %, compaction, visible plant/pollinator indicators)..."
              disabled={isLoading}
              className="w-full resize-none bg-transparent text-forest-900 placeholder:text-forest-400 focus:outline-none text-xs sm:text-sm leading-relaxed"
            />
          </div>

          {/* Bottom Bar inside Input Box */}
          <div className="flex items-center justify-between px-3 sm:px-4 py-2 border-t border-sage-100 bg-sand-50/50 rounded-b-2xl">
            <div className="flex items-center space-x-2 text-[11px] text-forest-500">
              <span className="hidden sm:inline">Press</span>
              <kbd className="px-1.5 py-0.5 bg-white border border-sage-200 rounded text-[10px] font-mono text-forest-700 shadow-2xs">
                Enter ↵
              </kbd>
              <span className="hidden sm:inline">to analyze,</span>
              <kbd className="hidden sm:inline px-1.5 py-0.5 bg-white border border-sage-200 rounded text-[10px] font-mono text-forest-700 shadow-2xs">
                Shift + Enter
              </kbd>
              <span className="hidden sm:inline">for newline</span>
            </div>

            <div className="flex items-center space-x-2">
              {value && !isLoading && onClear && (
                <button
                  type="button"
                  onClick={onClear}
                  className="p-1.5 text-forest-400 hover:text-forest-700 hover:bg-sage-100 rounded-lg transition-colors"
                  title="Clear input"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}

              <button
                type="submit"
                disabled={!value.trim() || isLoading}
                className="inline-flex items-center space-x-1.5 px-4 py-2 bg-botanical-500 hover:bg-botanical-600 disabled:bg-sage-200 text-white disabled:text-forest-400 font-medium text-xs sm:text-sm rounded-xl transition-all duration-150 shadow-subtle disabled:shadow-none active:scale-[0.98]"
              >
                <span>{isLoading ? 'Reasoning...' : 'Analyze Site'}</span>
                <Send className="w-3.5 h-3.5 ml-0.5" />
              </button>
            </div>
          </div>
        </form>

        <p className="text-center text-[11px] text-forest-500 mt-2">
          Darukaa Ground-Truth AI &bull; Uses Groq Causal DAG Traversal & Peer-Reviewed Ecological Literature
        </p>
      </div>
    </div>
  );
};
