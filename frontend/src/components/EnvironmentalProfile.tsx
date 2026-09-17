import React, { useState } from 'react';
import type { ProfileSummaryResponse, MetricSummary } from '../types/api';
import { formatMetricName } from '../utils/formatters';
import { Layers, ChevronDown, ChevronUp, CheckCircle2, HelpCircle, AlertCircle, MapPin, Trees } from 'lucide-react';

interface EnvironmentalProfileProps {
  structuredProfile?: ProfileSummaryResponse | null;
  rawProfileSummary?: Record<string, any> | null;
}

export const EnvironmentalProfile: React.FC<EnvironmentalProfileProps> = ({
  structuredProfile,
  rawProfileSummary,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);

  // If we have structured profile:
  if (structuredProfile) {
    const { region_name, biome, known_metrics, missing_metrics, completeness_score } = structuredProfile;
    const completenessPct = Math.round((completeness_score || 0) * 100);

    return (
      <div className="bg-white/80 border border-sage-200 rounded-xl p-4 shadow-subtle mb-4">
        {/* Toggle Header */}
        <div
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center justify-between cursor-pointer select-none group"
        >
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-lg bg-botanical-50 flex items-center justify-center text-botanical-600 border border-botanical-200/60">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-forest-800 group-hover:text-botanical-700 transition-colors">
                  Site Ecological Profile
                </h4>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-sage-100 text-forest-700 border border-sage-200">
                  Completeness: {completenessPct}%
                </span>
              </div>
              <p className="text-[11px] text-forest-500">
                Extracted baseline variables, known constraints, and missing diagnostic parameters
              </p>
            </div>
          </div>

          <button
            type="button"
            className="p-1 rounded-md text-forest-500 hover:text-forest-800 hover:bg-sage-100 transition-colors"
          >
            {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>

        {/* Completeness Bar */}
        <div className="mt-3 w-full bg-sage-100 h-1.5 rounded-full overflow-hidden">
          <div
            className="bg-botanical-500 h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.max(completenessPct, 5)}%` }}
          />
        </div>

        {/* Collapsible Content */}
        {isOpen && (
          <div className="mt-3.5 pt-3 border-t border-sage-100 space-y-3">
            {/* Region / Biome badges */}
            {(region_name || biome) && (
              <div className="flex flex-wrap gap-2 text-xs">
                {region_name && (
                  <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-sage-50 border border-sage-200 text-forest-800">
                    <MapPin className="w-3.5 h-3.5 text-botanical-600" />
                    <span className="font-medium">Region:</span>
                    <span>{region_name}</span>
                  </div>
                )}
                {biome && (
                  <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-sage-50 border border-sage-200 text-forest-800">
                    <Trees className="w-3.5 h-3.5 text-botanical-600" />
                    <span className="font-medium">Biome:</span>
                    <span>{biome}</span>
                  </div>
                )}
              </div>
            )}

            {/* Known Metrics Grid */}
            {known_metrics && known_metrics.length > 0 && (
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-forest-600 mb-1.5 block">
                  Identified Variables ({known_metrics.length})
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                  {known_metrics.map((m: MetricSummary, i: number) => {
                    const isProvided = m.status === 'provided';
                    return (
                      <div
                        key={i}
                        className="p-2 bg-sand-50/70 border border-sage-200/70 rounded-lg text-xs flex flex-col justify-between"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-forest-600 font-medium">
                            {formatMetricName(m.field_name)}
                          </span>
                          {isProvided ? (
                            <span title="Provided by user">
                              <CheckCircle2 className="w-3.5 h-3.5 text-botanical-600" />
                            </span>
                          ) : (
                            <span title="Estimated by reasoning engine">
                              <HelpCircle className="w-3.5 h-3.5 text-amber-600" />
                            </span>
                          )}
                        </div>
                        <div className="mt-1 flex items-baseline justify-between">
                          <span className="font-mono font-semibold text-forest-900 text-sm">
                            {String(m.value)} {m.unit || ''}
                          </span>
                          <span className="text-[10px] text-forest-500 uppercase">
                            {m.status}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Missing Metrics */}
            {missing_metrics && missing_metrics.length > 0 && (
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-earth-amber mb-1.5 block">
                  Unspecified / Missing Variables ({missing_metrics.length})
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {missing_metrics.map((mm, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] bg-amber-50/70 text-amber-900 border border-amber-200"
                    >
                      <AlertCircle className="w-3 h-3 text-amber-600" />
                      <span>{formatMetricName(mm)}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Fallback for flat dictionary
  if (rawProfileSummary && Object.keys(rawProfileSummary).length > 0) {
    const entries = Object.entries(rawProfileSummary);
    return (
      <div className="bg-white/80 border border-sage-200 rounded-xl p-4 shadow-subtle mb-4">
        <div
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center justify-between cursor-pointer select-none group"
        >
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-lg bg-botanical-50 flex items-center justify-center text-botanical-600 border border-botanical-200/60">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-forest-800 group-hover:text-botanical-700 transition-colors">
                Site Ecological Parameters ({entries.length})
              </h4>
              <p className="text-[11px] text-forest-500">
                Variables parsed from prompt and conversation context
              </p>
            </div>
          </div>

          <button
            type="button"
            className="p-1 rounded-md text-forest-500 hover:text-forest-800 hover:bg-sage-100 transition-colors"
          >
            {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>

        {isOpen && (
          <div className="mt-3.5 pt-3 border-t border-sage-100">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              {entries.map(([key, value], idx) => (
                <div
                  key={idx}
                  className="p-2 bg-sand-50/70 border border-sage-200/70 rounded-lg text-xs"
                >
                  <span className="text-[11px] text-forest-600 block mb-0.5">
                    {formatMetricName(key)}
                  </span>
                  <span className="font-mono font-semibold text-forest-900">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return null;
};
