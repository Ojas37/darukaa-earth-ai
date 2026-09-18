import React from 'react';
import { getConfidenceDetails } from '../utils/formatters';
import { ShieldCheck } from 'lucide-react';

interface ConfidenceIndicatorProps {
  score: number | null | undefined;
  basis?: string | null;
  showBar?: boolean;
}

export const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({
  score,
  basis,
  showBar = false,
}) => {
  const { percentage, label, colorClass, barColor } = getConfidenceDetails(score);

  return (
    <div className="flex flex-col space-y-1.5 max-w-full">
      <div className="flex items-center space-x-2">
        <span
          className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md font-mono font-medium border text-xs ${colorClass} shrink-0`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>{percentage}%</span>
          <span className="font-sans font-normal opacity-90 text-[11px]">({label})</span>
        </span>
      </div>

      {showBar && (
        <div className="w-full bg-sage-200/80 h-1.5 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ease-out ${barColor}`}
            style={{ width: `${Math.max(percentage, 5)}%` }}
          />
        </div>
      )}

      {basis && (
        <p className="text-[11px] text-forest-600/90 leading-relaxed font-mono break-words pt-0.5">
          {basis}
        </p>
      )}
    </div>
  );
};
