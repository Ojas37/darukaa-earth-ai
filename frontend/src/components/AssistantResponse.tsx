import React, { useState } from 'react';
import type { ChatResponse, Recommendation } from '../types/api';
import { ClarificationPrompt } from './ClarificationPrompt';
import { EnvironmentalProfile } from './EnvironmentalProfile';
import { PathwayList } from './PathwayList';
import { RecommendationCard } from './RecommendationCard';
import { ConfidenceIndicator } from './ConfidenceIndicator';
import { Sparkles, Check, Copy } from 'lucide-react';

interface AssistantResponseProps {
  response: ChatResponse;
  onSelectClarificationHint?: (hint: string) => void;
}

export const AssistantResponse: React.FC<AssistantResponseProps> = ({
  response,
  onSelectClarificationHint,
}) => {
  const [copied, setCopied] = useState<boolean>(false);

  // If this turn requires clarification
  if (response.needs_clarification) {
    return (
      <div className="space-y-4 max-w-4xl mx-auto w-full">
        <ClarificationPrompt
          message={response.message || response.clarification_prompt || ''}
          missingInfo={response.missing_information}
          onSelectClarificationHint={onSelectClarificationHint}
        />
        {/* If there was an initial profile parsed, show it */}
        <EnvironmentalProfile
          rawProfileSummary={response.profile_summary}
          structuredProfile={response.report?.profile_summary}
        />
      </div>
    );
  }

  // Recommendations and Synthesis
  const recommendations: Recommendation[] =
    response.recommendations || response.report?.recommendations || [];
  const pathways =
    response.active_stress_pathways || response.report?.active_pathways || [];
  const overallConf =
    response.overall_confidence || response.report?.overall_confidence;
  const narrative =
    response.narrative_summary || response.report?.narrative_summary || response.message;

  const handleCopyFormattedText = () => {
    const textToCopy =
      response.formatted_text ||
      response.report?.formatted_text ||
      response.message ||
      '';
    if (textToCopy) {
      navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-5 max-w-4xl mx-auto w-full">
      {/* Overall Synthesis Banner */}
      <div className="bg-white border border-sage-200 rounded-2xl p-5 sm:p-6 shadow-card space-y-4">
        {/* Header with Title and Confidence */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-sage-100">
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            <div className="w-9 h-9 rounded-xl bg-botanical-500 flex items-center justify-center text-white shadow-subtle shrink-0">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-base sm:text-lg font-bold text-forest-900 leading-tight">
                Ecological Diagnostic & Intervention Report
              </h3>
              <p className="text-xs text-forest-500 font-mono mt-0.5">
                {recommendations.length} Verified Intervention{recommendations.length === 1 ? '' : 's'} &bull; {pathways.length} Diagnosed Stress Pathway{pathways.length === 1 ? '' : 's'}
              </p>
            </div>
          </div>

          {/* Overall Confidence Badge */}
          {overallConf && (
            <div className="shrink-0 pt-1 sm:pt-0">
              <ConfidenceIndicator
                score={overallConf.score}
                showBar={true}
              />
            </div>
          )}
        </div>

        {/* Executive Summary Narrative */}
        {narrative && (
          <div className="text-xs sm:text-sm text-forest-800 leading-relaxed font-sans bg-sand-50/60 p-4 rounded-xl border border-sage-100">
            <p className="whitespace-pre-line leading-relaxed">{narrative}</p>
          </div>
        )}

        {/* Quick action: Copy Report */}
        {(response.formatted_text || response.report?.formatted_text) && (
          <div className="flex items-center justify-between pt-1 text-xs text-forest-500">
            <span className="text-[11px] italic">
              {overallConf?.explanation || 'Grounded in peer-reviewed scientific literature.'}
            </span>
            <button
              onClick={handleCopyFormattedText}
              className="inline-flex items-center space-x-1.5 text-xs font-medium text-forest-700 hover:text-forest-950 bg-sage-50 hover:bg-sage-100 px-3 py-1.5 rounded-lg border border-sage-200 transition-colors shadow-2xs shrink-0"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-botanical-600" />
                  <span className="text-botanical-700 font-medium">Copied to Clipboard</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-forest-500" />
                  <span>Copy Formatted Assessment</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Environmental Profile (Collapsible) */}
      <EnvironmentalProfile
        structuredProfile={response.report?.profile_summary}
        rawProfileSummary={response.profile_summary}
      />

      {/* Causal Stress Pathways */}
      <PathwayList pathways={pathways} />

      {/* Recommendation Cards */}
      {recommendations.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center space-x-2">
              <div className="w-2.5 h-2.5 rounded-full bg-botanical-500" />
              <h4 className="text-xs sm:text-sm font-bold uppercase tracking-wider text-forest-900">
                Actionable Ecological Interventions ({recommendations.length})
              </h4>
            </div>
            <span className="text-xs text-forest-500 font-mono hidden sm:inline">
              Prioritized by multi-variable causal impact
            </span>
          </div>

          <div className="space-y-5">
            {recommendations.map((rec, idx) => (
              <RecommendationCard key={idx} rec={rec} index={idx} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
