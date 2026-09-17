import React from 'react';
import type { Recommendation } from '../types/api';
import { formatMetricName, formatTimeHorizon } from '../utils/formatters';
import { ConfidenceIndicator } from './ConfidenceIndicator';
import { EvidenceSection } from './EvidenceSection';
import { AlertTriangle, Clock, ArrowUpRight, Cpu } from 'lucide-react';

interface RecommendationCardProps {
  rec: Recommendation;
  index: number;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({ rec, index }) => {
  const horizon = formatTimeHorizon(rec.time_horizon);

  return (
    <div className="bg-white border border-sage-200 rounded-xl p-5 shadow-card hover:border-botanical-300 transition-all duration-200 space-y-4">
      {/* Top Bar: Index, Action Title, Time Horizon & Confidence */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-3 border-b border-sage-100">
        <div className="flex items-start space-x-3">
          <span className="w-6 h-6 rounded-md bg-forest-800 text-botanical-200 flex items-center justify-center font-mono text-xs font-semibold shrink-0 mt-0.5">
            {index + 1}
          </span>
          <div className="space-y-1">
            <h3 className="text-sm sm:text-base font-semibold text-forest-900 leading-snug">
              {rec.recommendation}
            </h3>
            {rec.pathway_id && (
              <div className="flex items-center space-x-1 text-[11px] text-forest-500 font-mono">
                <Cpu className="w-3 h-3 text-botanical-500" />
                <span>Targeted Causal Link: {rec.pathway_id}</span>
              </div>
            )}
          </div>
        </div>

        {/* Badges: Time Horizon & Confidence */}
        <div className="flex sm:flex-col items-end gap-2 shrink-0 self-start sm:self-auto">
          <span
            className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-[10.5px] font-semibold border ${horizon.className}`}
          >
            <Clock className="w-3 h-3" />
            <span>{horizon.label}</span>
          </span>

          <ConfidenceIndicator
            score={rec.confidence_score}
            basis={rec.confidence_basis}
            showBar={false}
          />
        </div>
      </div>

      {/* Mechanism: Why it works */}
      <div className="space-y-1.5">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-forest-600">
          Causal Mechanism & Restoration Dynamics
        </span>
        <p className="text-xs sm:text-[13px] text-forest-800 leading-relaxed bg-sand-50/70 p-3 rounded-lg border border-sage-200/60">
          {rec.why_it_works}
        </p>
      </div>

      {/* Affected Metrics */}
      {rec.affected_metrics && rec.affected_metrics.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-forest-600">
            Remediated Environmental Metrics ({rec.affected_metrics.length})
          </span>
          <div className="flex flex-wrap gap-1.5">
            {rec.affected_metrics.map((metric, mIdx) => (
              <span
                key={mIdx}
                className="inline-flex items-center space-x-1 px-2 py-1 rounded-md bg-botanical-50 text-botanical-700 border border-botanical-200/80 text-[11.5px] font-medium"
              >
                <ArrowUpRight className="w-3 h-3 text-botanical-500" />
                <span>{formatMetricName(metric)}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Constraint / Ecological Caveats */}
      {rec.constraint_notes && (
        <div className="p-2.5 bg-amber-50/60 border border-amber-200/80 rounded-lg flex items-start space-x-2 text-xs text-amber-900">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
          <div className="leading-tight">
            <span className="font-medium">Site Constraint / Caveat: </span>
            <span>{rec.constraint_notes}</span>
          </div>
        </div>
      )}

      {/* Validation Warnings if any */}
      {rec.validation_warnings && rec.validation_warnings.length > 0 && (
        <div className="space-y-1">
          {rec.validation_warnings.map((warn, wIdx) => (
            <div
              key={wIdx}
              className="p-2 bg-orange-50 text-orange-900 border border-orange-200 rounded text-[11px] flex items-center space-x-1.5"
            >
              <AlertTriangle className="w-3 h-3 text-orange-600 shrink-0" />
              <span>{warn}</span>
            </div>
          ))}
        </div>
      )}

      {/* Literature Evidence Section */}
      <EvidenceSection evidence={rec.evidence} />
    </div>
  );
};
