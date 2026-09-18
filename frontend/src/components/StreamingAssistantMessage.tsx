import React from 'react';
import { Loader2, Sparkles, Network, BookOpen, Cpu, HelpCircle, ArrowRight } from 'lucide-react';
import { formatMetricName } from '../utils/formatters';

interface StreamingAssistantMessageProps {
  stage: string;
  stageMessage: string;
  streamingText: string;
  streamingProfile?: Record<string, any> | null;
  streamingPathways?: any[] | null;
}

const STAGE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  extracting: Sparkles,
  pathways: Network,
  evidence: BookOpen,
  synthesizing: Cpu,
  clarification: HelpCircle,
};

export const StreamingAssistantMessage: React.FC<StreamingAssistantMessageProps> = ({
  stage,
  stageMessage,
  streamingText,
  streamingProfile,
  streamingPathways,
}) => {
  const IconComponent = STAGE_ICONS[stage] || Sparkles;
  const profileKeysCount = streamingProfile ? Object.keys(streamingProfile).length : 0;

  return (
    <div className="space-y-4 max-w-4xl mx-auto w-full animate-fade-in">
      {/* Live Stage Progress Header */}
      <div className="bg-white/90 border border-botanical-200 rounded-2xl p-4 sm:p-5 shadow-card space-y-3.5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-3 border-b border-sage-100">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-botanical-500 text-white flex items-center justify-center shadow-subtle shrink-0">
              <IconComponent className="w-4 h-4 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold uppercase tracking-wider text-forest-900">
                  Causal Reasoning Engine
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-botanical-100 text-botanical-800 border border-botanical-200">
                  Live Streaming
                </span>
                {profileKeysCount > 0 && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sage-100 text-forest-700 border border-sage-200 hidden sm:inline">
                    {profileKeysCount} variables extracted
                  </span>
                )}
              </div>
              <p className="text-xs text-forest-600 font-mono mt-0.5">
                {stageMessage || 'Analyzing environmental conditions...'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-xs text-forest-500 shrink-0">
            <Loader2 className="w-4 h-4 text-botanical-500 animate-spin" />
            <span className="font-mono text-[11px]">Processing tokens</span>
          </div>
        </div>

        {/* Streaming Text Output with Blinking Cursor */}
        {streamingText ? (
          <div className="bg-sand-50/70 p-4 rounded-xl border border-sage-100 text-xs sm:text-sm text-forest-900 leading-relaxed font-sans min-h-[60px]">
            <span className="whitespace-pre-line">{streamingText}</span>
            <span className="inline-block w-2 h-4 ml-1 bg-botanical-500 animate-pulse-glow align-middle" />
          </div>
        ) : (
          <div className="py-2 text-center text-xs text-forest-500 italic">
            Gathering baseline variables and traversing ecological graph...
          </div>
        )}
      </div>

      {/* Live Discovered Pathways (if available during streaming) */}
      {streamingPathways && streamingPathways.length > 0 && (
        <div className="bg-white/80 border border-sage-200 rounded-xl p-3.5 space-y-2 text-xs shadow-2xs">
          <span className="text-[11px] font-bold uppercase tracking-wider text-forest-700 block">
            Discovered Stress Chains ({streamingPathways.length})
          </span>
          <div className="space-y-1.5">
            {streamingPathways.map((p, idx) => (
              <div key={idx} className="flex items-center flex-wrap gap-1 bg-sage-50/80 p-2 rounded-lg border border-sage-200">
                {(p.nodes || []).map((n: string, nIdx: number) => (
                  <React.Fragment key={nIdx}>
                    <span className="font-mono font-medium text-forest-800 bg-white px-1.5 py-0.5 rounded text-[11px] border border-sage-200">
                      {formatMetricName(n)}
                    </span>
                    {nIdx < p.nodes.length - 1 && (
                      <ArrowRight className="w-3 h-3 text-botanical-500 shrink-0" />
                    )}
                  </React.Fragment>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
