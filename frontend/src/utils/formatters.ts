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
