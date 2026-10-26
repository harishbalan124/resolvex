export interface SentimentPrediction {
  sentiment: 'positive' | 'neutral' | 'negative';
  confidence: number;
  probabilities: Record<string, number>;
  key_drivers: string[];
  model_version: string;
}

export interface ChurnDriver {
  factor: string;
  detail: string;
  impact: string;
}

export interface ChurnPrediction {
  customer_id: string;
  churn_risk_score: number;
  risk_label: 'LOW_RISK' | 'MEDIUM_RISK' | 'HIGH_RISK';
  top_drivers: ChurnDriver[];
  model_version: string;
}

export interface ModelTelemetry {
  trained: boolean;
  version: string;
  metadata?: {
    trained_at: string;
    samples_count: number;
    metrics: Record<string, number>;
  } | null;
}

export interface EngineStatus {
  engine: string;
  sentiment_model: ModelTelemetry;
  churn_model: ModelTelemetry;
}
