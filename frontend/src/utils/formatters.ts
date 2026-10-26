export function formatCurrency(amount: number | string, currency: string = 'USD'): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency || 'USD',
  }).format(num);
}

export function formatDate(dateString?: string | null): string {
  if (!dateString) return '—';
  try {
    const d = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(d);
  } catch {
    return dateString;
  }
}

export function formatRuleName(rule: string): string {
  const rules: Record<string, string> = {
    DUPLICATE_CHARGE_WINDOW: 'Duplicate Charge in Window',
    RAPID_VELOCITY: 'Rapid Velocity Anomaly',
    UNUSUAL_AMOUNT_DEVIATION: 'High Amount Deviation',
  };
  return rules[rule] || rule.replace(/_/g, ' ');
}

export function getRiskColor(score: number): { bg: string; text: string; label: string } {
  if (score >= 0.7) {
    return { bg: 'bg-red-100', text: 'text-red-700', label: 'High Risk' };
  }
  if (score >= 0.4) {
    return { bg: 'bg-amber-100', text: 'text-amber-700', label: 'Medium Risk' };
  }
  return { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Low Risk' };
}

export function getSentimentBadge(sentiment?: string | null): { bg: string; text: string; label: string } {
  const s = (sentiment || '').toLowerCase();
  if (s === 'positive') {
    return { bg: 'bg-emerald-100', text: 'text-emerald-800', label: 'Positive' };
  }
  if (s === 'negative') {
    return { bg: 'bg-rose-100', text: 'text-rose-800', label: 'Negative' };
  }
  return { bg: 'bg-slate-100', text: 'text-slate-800', label: 'Neutral' };
}
