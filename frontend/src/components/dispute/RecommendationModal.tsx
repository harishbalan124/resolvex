import React, { useState } from 'react';
import { Recommendation } from '../../types/recommendation';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { CheckCircle, XCircle, ShieldAlert, AlertTriangle } from 'lucide-react';

interface RecommendationModalProps {
  isOpen: boolean;
  onClose: () => void;
  recommendation: Recommendation | null;
  onReview: (id: number, action: 'APPROVED' | 'REJECTED', notes: string) => Promise<void>;
}

export const RecommendationModal: React.FC<RecommendationModalProps> = ({
  isOpen,
  onClose,
  recommendation,
  onReview,
}) => {
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!recommendation) return null;

  const handleAction = async (action: 'APPROVED' | 'REJECTED') => {
    setIsSubmitting(true);
    setError(null);
    try {
      await onReview(recommendation.id, action, notes);
      setNotes('');
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to submit review decision.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Human Review: Autonomous Recommendation"
      maxWidth="lg"
    >
      <div className="space-y-5">
        {/* Mandatory Human Review Warning Banner */}
        <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-amber-800">
            <span className="font-semibold">Human-In-The-Loop Governance:</span> ResolveX never automatically issues refunds or denies customer claims without explicit human confirmation.
          </div>
        </div>

        {/* Recommendation Overview */}
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              Suggested Resolution
            </span>
            <Badge variant="purple" size="sm">
              Confidence {(recommendation.confidence_score * 100).toFixed(0)}%
            </Badge>
          </div>
          <div className="text-lg font-bold text-slate-900 tracking-tight">
            {recommendation.suggested_action.replace(/_/g, ' ')}
          </div>
          <div>
            <span className="text-xs font-medium text-slate-500 block mb-1">
              Autonomous Justification (LexIntel AI Engine)
            </span>
            <p className="text-sm text-slate-700 leading-relaxed bg-white p-3 rounded border border-slate-200">
              {recommendation.justification}
            </p>
          </div>
        </div>

        {/* Reviewer Notes Input */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
            Human Reviewer Rationale & Audit Notes
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            placeholder="Document verification steps, customer correspondence, or reasons for approval/rejection..."
            className="w-full text-sm rounded-lg border border-slate-300 p-3 focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white"
          />
        </div>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-xs text-rose-700 rounded-lg flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={() => handleAction('REJECTED')}
            isLoading={isSubmitting}
            icon={<XCircle className="w-4 h-4" />}
          >
            Reject Suggestion
          </Button>
          <Button
            variant="primary"
            onClick={() => handleAction('APPROVED')}
            isLoading={isSubmitting}
            icon={<CheckCircle className="w-4 h-4" />}
          >
            Approve & Authorize Action
          </Button>
        </div>
      </div>
    </Modal>
  );
};
