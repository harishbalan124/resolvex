import React, { useEffect, useState } from 'react';
import { fetchDisputes, triggerBatchScanApi } from '../api/disputes';
import { fetchRecommendations, reviewRecommendationApi } from '../api/recommendations';
import { Dispute } from '../types/dispute';
import { Recommendation } from '../types/recommendation';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { RecommendationModal } from '../components/dispute/RecommendationModal';
import { formatRuleName, formatDate } from '../utils/formatters';
import { useAuth } from '../hooks/useAuth';
import { canReviewRecommendations } from '../utils/permissions';
import { AlertOctagon, Scan, CheckCircle2, Clock, AlertTriangle, ShieldCheck } from 'lucide-react';

export const DisputesPage: React.FC = () => {
  const { role } = useAuth();
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [isScanning, setIsScanning] = useState(false);
  const [selectedRec, setSelectedRec] = useState<Recommendation | null>(null);
  const [scanMessage, setScanMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [disputesData, recsData] = await Promise.all([
        fetchDisputes({ limit: 100 }),
        fetchRecommendations({ limit: 100 }),
      ]);
      setDisputes(disputesData);
      setRecommendations(recsData);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleScan = async () => {
    setIsScanning(true);
    setScanMessage(null);
    try {
      const result = await triggerBatchScanApi(100);
      setScanMessage(
        `Scanned ${result.scanned_count} transactions. Detected ${result.disputes_detected} new anomalies requiring review.`
      );
      await loadData();
    } catch {
      setScanMessage('Failed to execute batch transaction scan.');
    } finally {
      setIsScanning(false);
    }
  };

  const handleReviewSubmit = async (
    id: number,
    action: 'APPROVED' | 'REJECTED',
    notes: string
  ) => {
    await reviewRecommendationApi(id, { action, notes });
    await loadData();
  };

  if (loading) {
    return <LoadingSpinner label="Loading dispute records and resolution queue..." />;
  }

  // Map recommendations by dispute_id
  const recsByDispute = recommendations.reduce((acc, r) => {
    if (r.dispute_id) acc[r.dispute_id] = r;
    return acc;
  }, {} as Record<number, Recommendation>);

  return (
    <div className="space-y-6">
      {/* Header & Scan Button */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Dispute Detection & Resolution Queue
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Explainable rule-based anomaly detection. Every financial resolution requires human verification.
          </p>
        </div>

        {canReviewRecommendations(role || undefined) && (
          <Button
            variant="primary"
            onClick={handleScan}
            isLoading={isScanning}
            icon={<Scan className="w-4 h-4" />}
          >
            Run Transaction Anomaly Scan
          </Button>
        )}
      </div>

      {scanMessage && (
        <div className="p-3.5 bg-sky-50 border border-sky-200 text-xs text-sky-800 rounded-lg flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-sky-600 flex-shrink-0" />
          <span>{scanMessage}</span>
        </div>
      )}

      {/* Disputes Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                <th className="px-6 py-3.5">Reference</th>
                <th className="px-6 py-3.5">Explainable Rule Triggered</th>
                <th className="px-6 py-3.5">Reason & Detail</th>
                <th className="px-6 py-3.5">Risk Score</th>
                <th className="px-6 py-3.5">Dispute Status</th>
                <th className="px-6 py-3.5">Recommendation</th>
                <th className="px-6 py-3.5 text-right">Human Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {disputes.length > 0 ? (
                disputes.map((dispute) => {
                  const linkedRec = recsByDispute[dispute.id];
                  return (
                    <tr key={dispute.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4 font-mono font-semibold text-xs text-slate-900">
                        {dispute.dispute_reference}
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant="purple" size="sm">
                          {formatRuleName(dispute.rule_triggered)}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-600 max-w-xs truncate" title={dispute.reason}>
                        {dispute.reason}
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-semibold text-xs text-slate-700">
                          {(dispute.risk_score * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <Badge
                          variant={
                            dispute.status === 'RESOLVED_APPROVED'
                              ? 'success'
                              : dispute.status === 'RESOLVED_REJECTED'
                              ? 'danger'
                              : 'warning'
                          }
                          size="sm"
                        >
                          {dispute.status.replace(/_/g, ' ')}
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        {linkedRec ? (
                          <div className="flex flex-col gap-1">
                            <span className="text-xs font-semibold text-slate-800">
                              {linkedRec.suggested_action.replace(/_/g, ' ')}
                            </span>
                            <Badge
                              variant={
                                linkedRec.status === 'APPROVED'
                                  ? 'success'
                                  : linkedRec.status === 'REJECTED'
                                  ? 'danger'
                                  : 'warning'
                              }
                              size="sm"
                            >
                              {linkedRec.status}
                            </Badge>
                          </div>
                        ) : (
                          <span className="text-xs text-slate-400">None</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {linkedRec && linkedRec.status === 'PENDING' ? (
                          canReviewRecommendations(role || undefined) ? (
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => setSelectedRec(linkedRec)}
                            >
                              Review & Decide
                            </Button>
                          ) : (
                            <span className="text-xs text-amber-600 font-medium flex items-center justify-end gap-1">
                              <Clock className="w-3.5 h-3.5" /> Pending Review
                            </span>
                          )
                        ) : linkedRec ? (
                          <span className="text-xs text-slate-500 font-medium">
                            Reviewed ({linkedRec.status})
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-400 text-xs">
                    No disputes recorded yet. Run a transaction scan to evaluate records.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Human Review Modal */}
      <RecommendationModal
        isOpen={!!selectedRec}
        onClose={() => setSelectedRec(null)}
        recommendation={selectedRec}
        onReview={handleReviewSubmit}
      />
    </div>
  );
};
