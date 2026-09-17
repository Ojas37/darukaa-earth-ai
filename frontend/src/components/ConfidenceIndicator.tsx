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
  showBar = true,
}) => {
  const { percentage, label, colorClass, barColor } = getConfidenceDetails(score);

  return (
    <div className="flex flex-col space-y-1">
      <div className="flex items-center space-x-2">
        <span
          className={`inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-md font-mono font-medium border text-xs ${colorClass}`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>{percentage}%</span>
          <span className="font-sans font-normal opacity-80 text-[11px]">({label})</span>
        </span>
      </div>

      {showBar && (
        <div className="w-full bg-sage-200/70 h-1.5 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ease-out ${barColor}`}
            style={{ width: `${Math.max(percentage, 5)}%` }}
          />
        </div>
      )}

      {basis && (
        <p className="text-[11px] text-forest-600/90 leading-tight italic pt-0.5">
          {basis}
        </p>
      )}
    </div>
  );
};
