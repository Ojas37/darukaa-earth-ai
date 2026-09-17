import React from 'react';
import { Sprout, RotateCcw, ShieldCheck } from 'lucide-react';

interface HeaderProps {
  onNewAssessment: () => void;
  conversationId: string | null;
  turnCount?: number;
}

export const Header: React.FC<HeaderProps> = ({
  onNewAssessment,
  conversationId,
  turnCount = 0,
}) => {
  return (
    <header className="sticky top-0 z-30 w-full bg-[#F7F7F2]/90 backdrop-blur-md border-b border-sage-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-forest-800 flex items-center justify-center text-botanical-300 shadow-subtle">
            <Sprout className="w-5 h-5 text-botanical-200" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-base tracking-tight text-forest-800">
                DARUKAA<span className="text-botanical-500 font-normal">.EARTH</span>
              </span>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-botanical-100 text-botanical-700 border border-botanical-200/60">
                Causal AI
              </span>
            </div>
            <p className="text-[11px] text-forest-600 hidden sm:block">
              Ecological Intelligence & Evidence-Backed Decision Support
            </p>
          </div>
        </div>

        {/* Center / Status */}
        <div className="hidden md:flex items-center space-x-4 text-xs text-forest-600">
          <div className="flex items-center space-x-1.5 bg-white/70 px-2.5 py-1 rounded-full border border-sage-200 shadow-subtle">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-botanical-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-botanical-500"></span>
            </span>
            <span className="font-mono text-[11px] text-forest-700">Groq Reasoning Engine</span>
          </div>

          {conversationId && (
            <div className="flex items-center space-x-1.5 bg-white/70 px-2.5 py-1 rounded-full border border-sage-200 shadow-subtle">
              <ShieldCheck className="w-3.5 h-3.5 text-botanical-500" />
              <span className="text-[11px] font-mono text-forest-600">
                Session: {conversationId.slice(0, 8)}... ({turnCount} {turnCount === 1 ? 'turn' : 'turns'})
              </span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          <button
            onClick={onNewAssessment}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs sm:text-sm font-medium text-forest-700 hover:text-forest-900 bg-white hover:bg-sage-50 border border-sage-300 hover:border-sage-400 rounded-lg transition-all duration-150 shadow-subtle active:scale-[0.98]"
            title="Start a fresh ecological assessment"
          >
            <RotateCcw className="w-3.5 h-3.5 text-forest-600" />
            <span>New Assessment</span>
          </button>
        </div>
      </div>
    </header>
  );
};
