import React from 'react';
import type { EvidenceCitation } from '../types/api';
import { BookOpen, ExternalLink, Bookmark } from 'lucide-react';

interface EvidenceSectionProps {
  evidence: EvidenceCitation[];
}

export const EvidenceSection: React.FC<EvidenceSectionProps> = ({ evidence }) => {
  if (!evidence || evidence.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 pt-4 border-t border-sage-200/90 space-y-3">
      <div className="flex items-center space-x-2">
        <BookOpen className="w-4 h-4 text-botanical-600" />
        <span className="text-[11px] font-bold uppercase tracking-wider text-forest-800">
          Scientific Evidence & Literature Grounding ({evidence.length})
        </span>
      </div>

      <div className="space-y-2.5">
        {evidence.map((item, idx) => (
          <div
            key={idx}
            className="p-3.5 bg-sand-50/70 hover:bg-sand-50 border border-sage-200 rounded-xl transition-colors text-xs space-y-2"
          >
            {/* Source & Citation link */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-start space-x-2 font-semibold text-forest-900 flex-1 min-w-0">
                <Bookmark className="w-3.5 h-3.5 text-botanical-600 shrink-0 mt-0.5" />
                <span className="leading-snug break-words">{item.source}</span>
              </div>

              {item.url && (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-1 text-botanical-700 hover:text-botanical-800 font-mono text-[11px] bg-white px-2.5 py-1 rounded-md border border-sage-200 hover:border-botanical-300 transition-all shrink-0 shadow-2xs self-start sm:self-auto"
                  title={`Open source citation: ${item.url}`}
                >
                  <span>DOI / Source</span>
                  <ExternalLink className="w-3 h-3 ml-0.5" />
                </a>
              )}
            </div>

            {/* Claim supported */}
            {item.claim_supported && (
              <div className="pl-5 text-forest-700 leading-relaxed text-xs border-l-2 border-botanical-300 ml-1">
                <span className="font-semibold text-forest-900">Empirical Finding: </span>
                <span>{item.claim_supported}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
