import React from 'react';

/**
 * Formats a dotted metric key (e.g., "soil.organic_carbon_percent") 
 * into a clean, human-readable label (e.g., "Soil Organic Carbon Percent")
 */
export function formatMetricName(metric: string): string {
  if (!metric) return '';
  
  // Remove category prefix if present (soil., climate., land., bio.)
  const parts = metric.split('.');
  const rawName = parts.length > 1 ? parts.slice(1).join(' ') : parts[0];
  
  return rawName
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .replace(/Percent\b/i, '(%)')
    .replace(/Ppm\b/i, '(ppm)')
    .replace(/Mm\b/i, '(mm)');
}

/**
 * Strips raw markdown asterisks (e.g. **Land** -> Land, *Note* -> Note)
 */
export function stripMarkdownStars(text: string): string {
  if (!text) return '';
  return text
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/_([^_]+)_/g, '$1');
}

/**
 * Formats markdown bold/italic tags into clean React elements without raw asterisks
 */
export function renderFormattedText(text: string): React.ReactNode {
  if (!text) return null;

  // Split lines
  const lines = text.split('\n');

  return lines.map((line, lineIdx) => {
    // Process **bold** and *italic* tokens
    const parts: React.ReactNode[] = [];
    const regex = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(line)) !== null) {
      if (match.index > lastIndex) {
        parts.push(line.substring(lastIndex, match.index));
      }
      const token = match[0];
      if (token.startsWith('**') && token.endsWith('**')) {
        parts.push(
          <strong key={`${lineIdx}-${match.index}`} className="font-semibold text-forest-950">
            {token.slice(2, -2)}
          </strong>
        );
      } else if (token.startsWith('*') && token.endsWith('*')) {
        parts.push(
          <em key={`${lineIdx}-${match.index}`} className="italic text-forest-700">
            {token.slice(1, -1)}
          </em>
        );
      }
      lastIndex = regex.lastIndex;
    }

    if (lastIndex < line.length) {
      parts.push(line.substring(lastIndex));
    }

    return (
      <React.Fragment key={lineIdx}>
        {parts.length > 0 ? parts : line}
        {lineIdx < lines.length - 1 && <br />}
      </React.Fragment>
    );
  });
}

/**
 * Format time horizon tag text and CSS classes
 */
export function formatTimeHorizon(horizon: string): { label: string; className: string } {
  const norm = (horizon || '').toLowerCase();
  if (norm.includes('short')) {
    return {
      label: 'SHORT TERM (0-6 mo)',
      className: 'bg-emerald-50 text-emerald-800 border-emerald-200/80',
    };
  }
  if (norm.includes('med')) {
    return {
      label: 'MEDIUM TERM (6-24 mo)',
      className: 'bg-amber-50 text-amber-800 border-amber-200/80',
    };
  }
  if (norm.includes('long')) {
    return {
      label: 'LONG TERM (2+ yr)',
      className: 'bg-teal-50 text-teal-800 border-teal-200/80',
    };
  }
  return {
    label: horizon.toUpperCase(),
    className: 'bg-sage-100 text-forest-700 border-sage-300',
  };
}

/**
 * Get styling and label for confidence score
 */
export function getConfidenceDetails(score: number | null | undefined): {
  percentage: number;
  label: string;
  colorClass: string;
  barColor: string;
} {
  const safeScore = score ?? 0;
  const pct = Math.round(safeScore <= 1 ? safeScore * 100 : safeScore);

  if (pct >= 75) {
    return {
      percentage: pct,
      label: 'High Confidence',
      colorClass: 'text-botanical-500 bg-botanical-50 border-botanical-200',
      barColor: 'bg-botanical-500',
    };
  }
  if (pct >= 50) {
    return {
      percentage: pct,
      label: 'Moderate Confidence',
      colorClass: 'text-earth-amber bg-amber-50 border-amber-200',
      barColor: 'bg-amber-500',
    };
  }
  return {
    percentage: pct,
    label: 'Preliminary',
    colorClass: 'text-earth-rust bg-orange-50 border-orange-200',
    barColor: 'bg-orange-500',
  };
}
