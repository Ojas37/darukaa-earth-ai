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
    <div className="mt-3 pt-3 border-t border-sage-200/80">
      <div className="flex items-center space-x-1.5 mb-2">
        <BookOpen className="w-3.5 h-3.5 text-botanical-600" />
        <span className="text-[11px] font-semibold uppercase tracking-wider text-forest-700">
          Scientific Evidence & Literature Support ({evidence.length})
        </span>
      </div>

      <div className="space-y-2">
        {evidence.map((item, idx) => (
          <div
            key={idx}
            className="p-2.5 bg-sage-50/70 hover:bg-sage-50 border border-sage-200/90 rounded-lg transition-colors text-xs space-y-1"
          >
            {/* Source & Citation link */}
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center space-x-1.5 font-medium text-forest-800">
                <Bookmark className="w-3 h-3 text-botanical-500 shrink-0 mt-0.5" />
                <span className="leading-snug">{item.source}</span>
              </div>

              {item.url && (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-1 text-botanical-600 hover:text-botanical-700 font-mono text-[11px] underline shrink-0 hover:opacity-80 transition-opacity"
                  title={`Open source citation: ${item.url}`}
                >
                  <span>DOI / Source</span>
                  <ExternalLink className="w-3 h-3 ml-0.5" />
                </a>
              )}
            </div>

            {/* Claim supported */}
            {item.claim_supported && (
              <p className="text-forest-600 pl-4.5 leading-relaxed text-[11.5px]">
                <span className="text-forest-500 font-medium">Finding:</span> {item.claim_supported}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
