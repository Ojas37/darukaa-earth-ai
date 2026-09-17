import React from 'react';
import type { MissingInfoItem } from '../types/api';
import { HelpCircle, ArrowRight, Lightbulb } from 'lucide-react';

interface ClarificationPromptProps {
  message: string;
  missingInfo?: MissingInfoItem[];
  onSelectClarificationHint?: (hint: string) => void;
}

export const ClarificationPrompt: React.FC<ClarificationPromptProps> = ({
  message,
  missingInfo,
  onSelectClarificationHint,
}) => {
  return (
    <div className="bg-amber-50/70 border border-amber-200/90 rounded-xl p-4 sm:p-5 shadow-subtle space-y-4">
      {/* Header */}
      <div className="flex items-start space-x-3">
        <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center text-amber-800 shrink-0 mt-0.5 border border-amber-300/60">
          <HelpCircle className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-semibold text-amber-950">
              Site Clarification Needed for Precision Reasoning
            </h3>
            <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-amber-200/70 text-amber-900 border border-amber-300">
              Diagnostic Step
            </span>
          </div>
          <p className="text-xs text-amber-900/90 leading-relaxed font-sans">
            To construct accurate causal pathways and prevent maladaptive interventions, please provide additional context on the following parameters:
          </p>
        </div>
      </div>

      {/* Main Clarification Prompt Message from LLM */}
      {message && (
        <div className="p-3.5 bg-white/90 rounded-lg border border-amber-200 text-xs text-forest-800 leading-relaxed space-y-2 font-sans shadow-2xs">
          <div className="whitespace-pre-line">{message}</div>
        </div>
      )}

      {/* Structured Missing Info Breakdown */}
      {missingInfo && missingInfo.length > 0 && (
        <div className="space-y-2 pt-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-900 block">
            Targeted Diagnostic Inquiries ({missingInfo.length})
          </span>
          <div className="grid grid-cols-1 gap-2">
            {missingInfo.map((item, idx) => (
              <div
                key={idx}
                className="p-3 bg-white/80 border border-amber-200/80 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-2"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-semibold text-forest-900">
                      {item.question}
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 uppercase">
                      {item.category}
                    </span>
                  </div>
                  {item.reason && (
                    <p className="text-[11px] text-forest-600 flex items-center space-x-1">
                      <Lightbulb className="w-3 h-3 text-amber-600 shrink-0 inline mr-1" />
                      <span>{item.reason}</span>
                    </p>
                  )}
                </div>

                {onSelectClarificationHint && (
                  <button
                    type="button"
                    onClick={() => onSelectClarificationHint(item.question)}
                    className="inline-flex items-center space-x-1 text-xs text-amber-800 hover:text-amber-950 font-medium px-2.5 py-1 bg-amber-100/70 hover:bg-amber-200 rounded border border-amber-300/80 transition-colors shrink-0 self-start sm:self-center"
                  >
                    <span>Answer</span>
                    <ArrowRight className="w-3 h-3 ml-0.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
