import React, { useEffect, useState } from 'react';
import { fetchEngineStatus, predictSentimentApi, evaluateCustomerChurnApi } from '../api/analytics';
import { fetchCustomers } from '../api/customers';
import { Customer } from '../types/customer';
import { EngineStatus, SentimentPrediction, ChurnPrediction } from '../types/analytics';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { getSentimentBadge, getRiskColor } from '../utils/formatters';
import { Cpu, Sparkles, Send, UserCheck, AlertTriangle, CheckCircle, BarChart2 } from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const [engineStatus, setEngineStatus] = useState<EngineStatus | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  // Sentiment workbench state
  const [sentimentText, setSentimentText] = useState(
    'I was charged twice for transaction TXN-99821 on my card and nobody has refunded me yet.'
  );
  const [sentimentResult, setSentimentResult] = useState<SentimentPrediction | null>(null);
  const [sentimentLoading, setSentimentLoading] = useState(false);
  const [sentimentError, setSentimentError] = useState<string | null>(null);

  // Churn evaluator state
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | ''>('');
  const [churnResult, setChurnResult] = useState<ChurnPrediction | null>(null);
  const [churnLoading, setChurnLoading] = useState(false);
  const [churnError, setChurnError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [statusData, customersData] = await Promise.all([
          fetchEngineStatus().catch(() => null),
          fetchCustomers({ limit: 100 }),
        ]);
        setEngineStatus(statusData);
        setCustomers(customersData);
        if (customersData.length > 0) {
          setSelectedCustomerId(customersData[0].id);
        }
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handlePredictSentiment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sentimentText.trim()) return;
    setSentimentLoading(true);
    setSentimentError(null);
    try {
      const res = await predictSentimentApi(sentimentText);
      setSentimentResult(res);
    } catch (err: any) {
      setSentimentError(err?.response?.data?.detail || 'Sentiment evaluation failed.');
    } finally {
      setSentimentLoading(false);
    }
  };

  const handleEvaluateChurn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomerId) return;
    setChurnLoading(true);
    setChurnError(null);
    try {
      const res = await evaluateCustomerChurnApi(Number(selectedCustomerId));
      setChurnResult(res);
    } catch (err: any) {
      setChurnError(err?.response?.data?.detail || 'Churn evaluation failed.');
    } finally {
      setChurnLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Connecting to LexIntel AI inference gateway..." />;
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Cpu className="w-6 h-6 text-purple-600" />
          <span>LexIntel AI: Intelligence & Machine Learning Hub</span>
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Inspect model telemetry, test real-time sentiment extraction, and evaluate customer churn risk with explainable drivers.
        </p>
      </div>

      {/* Model Telemetry Cards */}
      {engineStatus && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Sentiment Model Telemetry */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-purple-600">
                Natural Language Sentiment Engine
              </span>
              <Badge variant={engineStatus.sentiment_model.trained ? 'success' : 'warning'} size="sm">
                {engineStatus.sentiment_model.trained ? 'Model Ready' : 'Untrained'}
              </Badge>
            </div>
            <div className="text-sm font-semibold text-slate-800 mb-2">
              Architecture: TF-IDF + Logistic Regression
            </div>
            {engineStatus.sentiment_model.metadata ? (
              <div className="grid grid-cols-4 gap-2 pt-3 border-t border-slate-100 text-center">
                <div className="bg-slate-50 p-2 rounded">
                  <div className="text-[10px] text-slate-400 font-medium uppercase">Accuracy</div>
                  <div className="text-sm font-bold text-slate-900">
                    {(engineStatus.sentiment_model.metadata.metrics.accuracy * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-50 p-2 rounded">
                  <div className="text-[10px] text-slate-400 font-medium uppercase">Precision</div>
                  <div className="text-sm font-bold text-slate-900">
                    {(engineStatus.sentiment_model.metadata.metrics.precision * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-50 p-2 rounded">
                  <div className="text-[10px] text-slate-400 font-medium uppercase">Recall</div>
                  <div className="text-sm font-bold text-slate-900">
                    {(engineStatus.sentiment_model.metadata.metrics.recall * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-50 p-2 rounded">
                  <div className="text-[10px] text-slate-400 font-medium uppercase">F1 Score</div>
                  <div className="text-sm font-bold text-slate-900">
                    {(engineStatus.sentiment_model.metadata.metrics.f1_score * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400">Model not trained. Run train_models.py.</p>
            )}
          </div>

          {/* Churn Model Telemetry */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-purple-600">
                Predictive Churn Risk Engine
              </span>
              <Badge variant={engineStatus.churn_model.trained ? 'success' : 'warning'} size="sm">
                {engineStatus.churn_model.trained ? 'Model Ready' : 'Untrained'}
              </Badge>
            </div>
            <div className="text-sm font-semibold text-slate-800 mb-2">
              Architecture: ColumnTransformer + Random Forest
            </div>
            {engineStatus.churn_model.metadata ? (
              <div className="grid grid-cols-4 gap-2 pt-3 border-t border-slate-100 text-center">
                <div className="bg-slate-50 p-2 rounded">
                  <div className="text-[10px] text-slate-400 font-medium uppercase">Accuracy</div>
                  <div className="text-sm font-bold text-slate-900">
                    {(engineStatus.churn_model.metadata.metrics.accuracy * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-50 p-2 rounded">
                  <div className="text-[10px] text-slate-400 font-medium uppercase">ROC-AUC</div>
                  <div className="text-sm font-bold text-slate-900">
                    {(engineStatus.churn_model.metadata.metrics.roc_auc * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-50 p-2 rounded">
                  <div className="text-[10px] text-slate-400 font-medium uppercase">Precision</div>
                  <div className="text-sm font-bold text-slate-900">
                    {(engineStatus.churn_model.metadata.metrics.precision * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-50 p-2 rounded">
                  <div className="text-[10px] text-slate-400 font-medium uppercase">F1 Score</div>
                  <div className="text-sm font-bold text-slate-900">
                    {(engineStatus.churn_model.metadata.metrics.f1_score * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400">Model not trained. Run train_models.py.</p>
            )}
          </div>
        </div>
      )}

      {/* Interactive Toolkits */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Tool 1: Interactive Sentiment Inference */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-sky-600" />
              <h2 className="text-base font-semibold text-slate-900">
                Interactive Sentiment Analyzer
              </h2>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Submit raw customer feedback or call notes to evaluate sentiment and inspect explainable token drivers.
            </p>

            <form onSubmit={handlePredictSentiment} className="space-y-3">
              <textarea
                value={sentimentText}
                onChange={(e) => setSentimentText(e.target.value)}
                rows={3}
                placeholder="Type customer text..."
                className="w-full text-sm rounded-lg border border-slate-300 p-3 focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white"
              />
              <div className="flex justify-between items-center">
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                  isLoading={sentimentLoading}
                  icon={<Send className="w-3.5 h-3.5" />}
                >
                  Analyze Text
                </Button>
              </div>
            </form>

            {sentimentError && (
              <div className="mt-4 p-3 bg-rose-50 border border-rose-200 text-xs text-rose-700 rounded-lg">
                {sentimentError}
              </div>
            )}

            {sentimentResult && (
              <div className="mt-5 p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Predicted Sentiment
                  </span>
                  <Badge
                    variant={
                      sentimentResult.sentiment === 'positive'
                        ? 'success'
                        : sentimentResult.sentiment === 'negative'
                        ? 'danger'
                        : 'neutral'
                    }
                  >
                    {sentimentResult.sentiment.toUpperCase()} ({(sentimentResult.confidence * 100).toFixed(1)}%)
                  </Badge>
                </div>

                {/* Explainable Keywords */}
                {sentimentResult.key_drivers.length > 0 && (
                  <div>
                    <span className="text-[11px] font-semibold text-slate-500 uppercase block mb-1">
                      Key Explainable Linguistic Drivers:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {sentimentResult.key_drivers.map((driver, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded bg-white border border-slate-300 text-xs font-mono text-slate-700 shadow-2xs"
                        >
                          {driver}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Tool 2: Customer Churn Evaluator */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <UserCheck className="w-4 h-4 text-purple-600" />
              <h2 className="text-base font-semibold text-slate-900">
                Customer Churn Risk Evaluator
              </h2>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Evaluates live database transactions, interactions, and complaints to calculate real churn probabilities.
            </p>

            <form onSubmit={handleEvaluateChurn} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">
                  Select Customer Profile
                </label>
                <select
                  value={selectedCustomerId}
                  onChange={(e) => setSelectedCustomerId(Number(e.target.value))}
                  className="w-full text-sm rounded-lg border border-slate-300 p-2.5 bg-white"
                >
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.external_id}) — Tier: {c.tier}
                    </option>
                  ))}
                </select>
              </div>

              <Button
                variant="primary"
                size="sm"
                type="submit"
                isLoading={churnLoading}
                icon={<BarChart2 className="w-3.5 h-3.5" />}
              >
                Compute Real Churn Score
              </Button>
            </form>

            {churnError && (
              <div className="mt-4 p-3 bg-rose-50 border border-rose-200 text-xs text-rose-700 rounded-lg">
                {churnError}
              </div>
            )}

            {churnResult && (
              <div className="mt-5 p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Churn Probability
                    </div>
                    <div className="text-2xl font-bold text-slate-900">
                      {(churnResult.churn_risk_score * 100).toFixed(1)}%
                    </div>
                  </div>
                  <Badge
                    variant={
                      churnResult.risk_label === 'HIGH_RISK'
                        ? 'danger'
                        : churnResult.risk_label === 'MEDIUM_RISK'
                        ? 'warning'
                        : 'success'
                    }
                  >
                    {churnResult.risk_label.replace('_', ' ')}
                  </Badge>
                </div>

                {/* Explainable Top Drivers */}
                <div>
                  <span className="text-[11px] font-semibold text-slate-500 uppercase block mb-1.5">
                    Individual Account Drivers:
                  </span>
                  <div className="space-y-1.5">
                    {churnResult.top_drivers.map((driver, idx) => (
                      <div
                        key={idx}
                        className="p-2 bg-white rounded border border-slate-200 flex items-center justify-between text-xs"
                      >
                        <div>
                          <span className="font-semibold text-slate-800">{driver.factor}: </span>
                          <span className="text-slate-600">{driver.detail}</span>
                        </div>
                        <span
                          className={`font-semibold px-2 py-0.5 rounded text-[10px] ${
                            driver.impact.includes('NEGATIVE')
                              ? 'bg-rose-100 text-rose-700'
                              : 'bg-emerald-100 text-emerald-700'
                          }`}
                        >
                          {driver.impact.replace('_', ' ')}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
