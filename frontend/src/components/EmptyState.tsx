import React from 'react';
import { Sprout, Compass, ArrowRight } from 'lucide-react';

interface EmptyStateProps {
  onSelectPrompt: (promptText: string) => void;
}

const EXAMPLE_PROMPTS = [
  {
    title: 'Semi-Arid Rangeland Degradation (Case B)',
    tag: 'Arid Soil & Compaction',
    text: 'A degraded semi-arid rangeland in Rajasthan, India with 350 mm annual rainfall, high bulk density and severe compaction from overgrazing, soil organic carbon at 0.35%, low infiltration rate, and declining native pollinator populations.',
    stressors: ['Rainfall: 350 mm/yr', 'SOC: 0.35%', 'High Compaction', 'Pollinator Loss'],
  },
  {
    title: 'Degraded Agricultural Loam (Microbiome Deficit)',
    tag: 'Cropland Restoration',
    text: 'Sandy loam cropland suffering from topsoil erosion, extreme microbial biomass depletion, organic matter at 0.4%, low water holding capacity, and persistent nutrient runoff after monsoon rains.',
    stressors: ['Soil: Sandy Loam', 'SOC: 0.40%', 'Microbial Depletion', 'Erosion'],
  },
  {
    title: 'Riparian Buffer & Nitrate Runoff',
    tag: 'Watershed & Riverbank',
    text: 'A degraded riparian buffer zone along a farming corridor with nitrate runoff measuring 45 mg/L, heavy riverbank slope instability, and dominant invasive weed species choking native willow species.',
    stressors: ['Nitrate: 45 mg/L', 'Bank Instability', 'Invasive Weeds'],
  },
];

export const EmptyState: React.FC<EmptyStateProps> = ({ onSelectPrompt }) => {
  return (
    <div className="max-w-4xl mx-auto py-6 sm:py-10 space-y-8 animate-fade-in">
      {/* Hero Title & Mission */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-botanical-100/80 border border-botanical-200 text-botanical-700 text-xs font-medium mb-1">
          <Sprout className="w-3.5 h-3.5 text-botanical-600" />
          <span>Mechanistic Biodiversity Intelligence System</span>
        </div>
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-forest-900 tracking-tight">
          Ground-Truth Causal Reasoning for Ecosystem Restoration
        </h1>
        <p className="text-xs sm:text-sm text-forest-600 max-w-2xl mx-auto leading-relaxed">
          Describe any degraded site or agricultural landscape. Darukaa parses environmental variables, identifies multi-variable causal stress pathways, queries peer-reviewed literature, and formulates verifiable restoration interventions.
        </p>
      </div>

      {/* 3-Step Methodology Flow */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-4 bg-white/60 border border-sage-200 rounded-2xl shadow-subtle">
        <div className="flex items-start space-x-3 p-2">
          <div className="w-8 h-8 rounded-lg bg-botanical-50 border border-botanical-200 flex items-center justify-center text-botanical-600 shrink-0">
            <span className="font-mono text-xs font-bold">01</span>
          </div>
          <div className="space-y-0.5">
            <h4 className="text-xs font-semibold text-forest-900">1. Parameter Extraction</h4>
            <p className="text-[11px] text-forest-600 leading-snug">
              Extracts soil, climate, terrain, and biological metrics from natural language prompts.
            </p>
          </div>
        </div>

        <div className="flex items-start space-x-3 p-2">
          <div className="w-8 h-8 rounded-lg bg-botanical-50 border border-botanical-200 flex items-center justify-center text-botanical-600 shrink-0">
            <span className="font-mono text-xs font-bold">02</span>
          </div>
          <div className="space-y-0.5">
            <h4 className="text-xs font-semibold text-forest-900">2. DAG Stress Traversal</h4>
            <p className="text-[11px] text-forest-600 leading-snug">
              Diagnoses multi-variable stress chains across soil physics, microbiome, and hydrology.
            </p>
          </div>
        </div>

        <div className="flex items-start space-x-3 p-2">
          <div className="w-8 h-8 rounded-lg bg-botanical-50 border border-botanical-200 flex items-center justify-center text-botanical-600 shrink-0">
            <span className="font-mono text-xs font-bold">03</span>
          </div>
          <div className="space-y-0.5">
            <h4 className="text-xs font-semibold text-forest-900">3. Verified Interventions</h4>
            <p className="text-[11px] text-forest-600 leading-snug">
              Returns prioritized recommendations with exact peer-reviewed DOI citations and time horizons.
            </p>
          </div>
        </div>
      </div>

      {/* Example Ecological Scenarios */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Compass className="w-4 h-4 text-botanical-600" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-forest-800">
              Benchmark Ecological Test Scenarios
            </h3>
          </div>
          <span className="text-[11px] text-forest-500">
            Click to load prompt into composer
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {EXAMPLE_PROMPTS.map((item, idx) => (
            <div
              key={idx}
              onClick={() => onSelectPrompt(item.text)}
              className="group bg-white hover:bg-sand-50/80 border border-sage-200 hover:border-botanical-400 rounded-xl p-4 cursor-pointer transition-all duration-200 shadow-subtle hover:shadow-card flex flex-col justify-between text-left"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-sage-100 text-forest-700 border border-sage-200">
                    {item.tag}
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-sage-400 group-hover:text-botanical-600 group-hover:translate-x-0.5 transition-all" />
                </div>
                <h4 className="text-xs font-semibold text-forest-900 group-hover:text-botanical-700 transition-colors leading-snug">
                  {item.title}
                </h4>
                <p className="text-[11.5px] text-forest-600 line-clamp-3 leading-relaxed font-sans">
                  {item.text}
                </p>
              </div>

              <div className="mt-3 pt-2.5 border-t border-sage-100 flex flex-wrap gap-1">
                {item.stressors.map((st, sIdx) => (
                  <span
                    key={sIdx}
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white text-forest-600 border border-sage-200/80"
                  >
                    {st}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
