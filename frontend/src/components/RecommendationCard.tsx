import React, { useState } from 'react';
import type { Recommendation } from '../types/api';
import { formatMetricName, formatTimeHorizon } from '../utils/formatters';
import { ConfidenceIndicator } from './ConfidenceIndicator';
import { EvidenceSection } from './EvidenceSection';
import { AlertTriangle, Clock, ArrowUpRight, Cpu, ChevronDown, ChevronUp, Info } from 'lucide-react';

interface RecommendationCardProps {
  rec: Recommendation;
  index: number;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({ rec, index }) => {
  const horizon = formatTimeHorizon(rec.time_horizon);
  const [showProvenance, setShowProvenance] = useState<boolean>(false);

  return (
    <div className="bg-white border border-sage-200 rounded-2xl p-5 sm:p-6 shadow-card hover:border-botanical-300 transition-all duration-200 space-y-5">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-4 border-b border-sage-100">
        {/* Left: Index + Action Title */}
        <div className="flex items-start space-x-3.5 flex-1 min-w-0">
          <span className="w-7 h-7 rounded-lg bg-forest-800 text-botanical-200 flex items-center justify-center font-mono text-xs font-bold shrink-0 mt-0.5 shadow-2xs">
            {index + 1}
          </span>
          <div className="space-y-1.5 flex-1 min-w-0">
            <h3 className="text-base sm:text-lg font-bold text-forest-900 leading-snug break-words">
              {rec.recommendation}
            </h3>
            {rec.pathway_id && (
              <div className="inline-flex items-center space-x-1.5 text-[11px] text-forest-600 font-mono bg-sage-50 px-2 py-0.5 rounded border border-sage-200">
                <Cpu className="w-3 h-3 text-botanical-500" />
                <span>Targeted Pathway: {rec.pathway_id}</span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Horizon & Confidence Badges */}
        <div className="flex flex-wrap sm:flex-col sm:items-end gap-2 shrink-0 pt-1 sm:pt-0">
          <span
            className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border ${horizon.className} shrink-0`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>{horizon.label}</span>
          </span>

          <div className="shrink-0">
            <ConfidenceIndicator score={rec.confidence_score} showBar={false} />
          </div>
        </div>
      </div>

      {/* Mechanism: Why it works */}
      <div className="space-y-2">
        <span className="text-[11px] font-bold uppercase tracking-wider text-forest-700 block">
          Causal Mechanism & Restoration Dynamics
        </span>
        <div className="bg-sand-50/80 p-4 rounded-xl border border-sage-200/70 text-xs sm:text-[13px] text-forest-900 leading-relaxed font-sans">
          {rec.why_it_works}
        </div>
      </div>

      {/* Affected Metrics */}
      {rec.affected_metrics && rec.affected_metrics.length > 0 && (
        <div className="space-y-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-forest-700 block">
            Remediated Environmental Metrics ({rec.affected_metrics.length})
          </span>
          <div className="flex flex-wrap gap-2">
            {rec.affected_metrics.map((metric, mIdx) => (
              <span
                key={mIdx}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-botanical-50 text-botanical-700 border border-botanical-200/90 text-xs font-medium"
              >
                <ArrowUpRight className="w-3.5 h-3.5 text-botanical-500" />
                <span>{formatMetricName(metric)}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Constraint / Ecological Caveats */}
      {rec.constraint_notes && (
        <div className="p-3.5 bg-amber-50/80 border border-amber-200 rounded-xl flex items-start space-x-2.5 text-xs text-amber-950">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-semibold">Ecological Guardrail / Constraint: </span>
            <span>{rec.constraint_notes}</span>
          </div>
        </div>
      )}

      {/* Validation Warnings if any */}
      {rec.validation_warnings && rec.validation_warnings.length > 0 && (
        <div className="space-y-1.5">
          {rec.validation_warnings.map((warn, wIdx) => (
            <div
              key={wIdx}
              className="p-2.5 bg-orange-50 text-orange-950 border border-orange-200 rounded-lg text-xs flex items-center space-x-2"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-orange-600 shrink-0" />
              <span>{warn}</span>
            </div>
          ))}
        </div>
      )}

      {/* Literature Evidence Section */}
      <EvidenceSection evidence={rec.evidence} />

      {/* Confidence Provenance Breakdown (Collapsible) */}
      {rec.confidence_basis && (
        <div className="pt-2 border-t border-sage-100">
          <button
            type="button"
            onClick={() => setShowProvenance(!showProvenance)}
            className="inline-flex items-center space-x-1.5 text-[11px] text-forest-500 hover:text-forest-800 transition-colors"
          >
            <Info className="w-3.5 h-3.5" />
            <span>Mathematical Confidence Basis</span>
            {showProvenance ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
          {showProvenance && (
            <div className="mt-2 p-3 bg-sage-50 rounded-lg text-[11px] font-mono text-forest-700 border border-sage-200 leading-relaxed break-words">
              {rec.confidence_basis}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
