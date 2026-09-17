import React, { useEffect, useState } from 'react';
import { Loader2, Sparkles, Network, BookOpen, Cpu } from 'lucide-react';

const STAGES = [
  { text: 'Parsing site description and extracting environmental variables...', icon: Sparkles },
  { text: 'Traversing ecological causal graph and diagnosing stress pathways...', icon: Network },
  { text: 'Querying peer-reviewed literature corpus for mechanistic evidence...', icon: BookOpen },
  { text: 'Synthesizing multi-variable restoration recommendations...', icon: Cpu },
];

export const LoadingState: React.FC = () => {
  const [stageIdx, setStageIdx] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStageIdx((prev) => (prev + 1) % STAGES.length);
    }, 2400);
    return () => clearInterval(interval);
  }, []);

  const CurrentIcon = STAGES[stageIdx].icon;

  return (
    <div className="my-4 max-w-xl mx-auto bg-white/90 border border-sage-200 rounded-2xl p-5 shadow-card text-center space-y-3 animate-fade-in">
      <div className="flex items-center justify-center space-x-3">
        <div className="relative">
          <Loader2 className="w-6 h-6 text-botanical-500 animate-spin" />
        </div>
        <div className="w-8 h-8 rounded-lg bg-botanical-50 text-botanical-600 flex items-center justify-center border border-botanical-200">
          <CurrentIcon className="w-4 h-4 animate-pulse" />
        </div>
      </div>

      <div className="space-y-1">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-forest-800">
          Causal Reasoning Engine Active
        </h4>
        <p className="text-xs text-forest-600 font-mono transition-opacity duration-300">
          {STAGES[stageIdx].text}
        </p>
      </div>

      <div className="w-48 mx-auto bg-sage-100 h-1 rounded-full overflow-hidden">
        <div className="bg-botanical-500 h-full w-full animate-pulse-glow" />
      </div>
    </div>
  );
};
