import React, { useState } from 'react';
import type { StressPathway, ActivePathwayResponse } from '../types/api';
import { formatMetricName } from '../utils/formatters';
import { GitBranch, ArrowRight, ChevronDown, ChevronUp, Activity } from 'lucide-react';

interface PathwayListProps {
  pathways: (StressPathway | ActivePathwayResponse)[];
}

export const PathwayList: React.FC<PathwayListProps> = ({ pathways }) => {
  const [expanded, setExpanded] = useState<boolean>(true);

  if (!pathways || pathways.length === 0) {
    return null;
  }

  const getConfidenceBadge = (conf: string) => {
    const c = (conf || '').toLowerCase();
    if (c === 'established' || c === 'high') {
      return (
        <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
          Established Causal Edge
        </span>
      );
    }
    if (c === 'likely' || c === 'moderate') {
      return (
        <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-amber-50 text-amber-800 border border-amber-200">
          Likely Mechanism
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-blue-50 text-blue-800 border border-blue-200">
        Context-Dependent
      </span>
    );
  };

  return (
    <div className="bg-white/80 border border-sage-200 rounded-xl p-4 shadow-subtle mb-4">
      {/* Header with expand/collapse */}
      <div
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between cursor-pointer select-none group"
      >
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-botanical-50 flex items-center justify-center text-botanical-600 border border-botanical-200/60">
            <GitBranch className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-forest-800 group-hover:text-botanical-700 transition-colors">
              Diagnosed Causal Stress Pathways ({pathways.length})
            </h4>
            <p className="text-[11px] text-forest-500">
              Mechanistic causal chains connecting environmental deficits to ecosystem impacts
            </p>
          </div>
        </div>

        <button
          type="button"
          className="p-1 rounded-md text-forest-500 hover:text-forest-800 hover:bg-sage-100 transition-colors"
        >
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Pathways container */}
      {expanded && (
        <div className="mt-3.5 space-y-3 pt-3 border-t border-sage-100">
          {pathways.map((pathway, idx) => {
            const nodes = pathway.nodes || [];
            return (
              <div
                key={pathway.pathway_id || idx}
                className="p-3 bg-sand-50/60 border border-sage-200/80 rounded-lg space-y-2.5"
              >
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] font-mono font-medium text-forest-600 bg-white px-1.5 py-0.5 rounded border border-sage-200">
                      Pathway #{idx + 1}
                    </span>
                    <span className="text-xs text-forest-700 font-medium">
                      {nodes.length > 0 ? `${nodes.length} Causal Nodes` : `${pathway.chain_length} Steps`}
                    </span>
                  </div>
                  {getConfidenceBadge(pathway.confidence)}
                </div>

                {/* Node-to-node chain visualization */}
                {nodes.length > 0 && (
                  <div className="flex items-center flex-wrap gap-1.5 py-1">
                    {nodes.map((node, nIdx) => (
                      <React.Fragment key={nIdx}>
                        <span className="inline-flex items-center px-2 py-1 rounded-md bg-white border border-sage-200 text-xs font-mono font-medium text-forest-800 shadow-2xs">
                          {formatMetricName(node)}
                        </span>
                        {nIdx < nodes.length - 1 && (
                          <ArrowRight className="w-3.5 h-3.5 text-botanical-500 shrink-0" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                )}

                {/* Summary mechanism */}
                {pathway.summary && (
                  <p className="text-[12px] text-forest-600 leading-relaxed bg-white/60 p-2 rounded border border-sage-100 italic">
                    <Activity className="w-3 h-3 inline mr-1 text-botanical-500" />
                    {pathway.summary}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
