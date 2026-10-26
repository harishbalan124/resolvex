from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.dispute import Dispute
from app.models.recommendation import Recommendation
from app.models.user import User
from app.services.audit_service import log_audit_event


class AutonomousRecommendationEngine:
    """
    Explainable Recommendation Engine.
    Strictly complies with Non-Negotiable Rule 2:
    - Never auto-refunds, denies claims or moves money.
    - All recommendations are created in 'PENDING' status.
    - Requires human review and approval.
    """

    ACTION_MAP = {
        "DUPLICATE_CHARGE_WINDOW": {
            "suggested_action": "PARTIAL_CREDIT",
            "justification": (
                "Deterministic match on duplicate transaction within rolling window. "
                "Recommend issuing account credit for the duplicate amount subject to human agent approval."
            ),
            "confidence_score": 0.94,
        },
        "RAPID_VELOCITY": {
            "suggested_action": "ACCOUNT_SECURITY_HOLD",
            "justification": (
                "Rapid velocity threshold exceeded across multiple transactions. "
                "Recommend placing temporary security flag and contacting customer to verify activity."
            ),
            "confidence_score": 0.89,
        },
        "UNUSUAL_AMOUNT_DEVIATION": {
            "suggested_action": "MERCHANT_INQUIRY",
            "justification": (
                "Transaction amount exceeds 3x customer baseline spending patterns. "
                "Recommend requesting itemized merchant receipt and confirmation from cardholder."
            ),
            "confidence_score": 0.82,
        },
    }

    def generate_recommendation_for_dispute(
        self,
        db: Session,
        dispute: Dispute,
        user_id: Optional[int] = None,
    ) -> Recommendation:
        """Generate explainable resolution recommendation for a detected dispute."""
        # Avoid creating duplicate pending recommendations for the same dispute
        existing = (
            db.query(Recommendation)
            .filter(
                Recommendation.dispute_id == dispute.id,
                Recommendation.status == "PENDING"
            )
            .first()
        )
        if existing:
            return existing

        template = self.ACTION_MAP.get(
            dispute.rule_triggered,
            {
                "suggested_action": "MERCHANT_INQUIRY",
                "justification": f"Rule '{dispute.rule_triggered}' triggered. Recommend manual agent inquiry.",
                "confidence_score": 0.75,
            }
        )

        recommendation = Recommendation(
            dispute_id=dispute.id,
            complaint_id=dispute.complaint_id,
            suggested_action=template["suggested_action"],
            justification=template["justification"],
            confidence_score=template["confidence_score"],
            status="PENDING",  # Strictly pending until human approves
            reviewed_by_user_id=None,
            review_notes=None,
            reviewed_at=None,
        )
        db.add(recommendation)
        db.flush()

        # Update dispute status
        dispute.status = "ACTION_RECOMMENDED"

        log_audit_event(
            db=db,
            action="RECOMMENDATION_GENERATED",
            entity_type="recommendation",
            entity_id=str(recommendation.id),
            user_id=user_id,
            details={
                "dispute_id": dispute.id,
                "suggested_action": recommendation.suggested_action,
                "confidence_score": recommendation.confidence_score,
                "status": "PENDING",
            }
        )

        logger.info(
            f"Generated recommendation {recommendation.id} ({recommendation.suggested_action}) for Dispute {dispute.id}"
        )
        return recommendation

    def review_recommendation(
        self,
        db: Session,
        recommendation_id: int,
        reviewer_user: User,
        action: str,  # "APPROVED" or "REJECTED"
        notes: Optional[str] = None,
    ) -> Recommendation:
        """
        Human-In-The-Loop review execution.
        Applies human decision to recommendation and updates linked dispute.
        """
        recommendation = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
        if not recommendation:
            raise ValueError(f"Recommendation with ID {recommendation_id} not found")

        if recommendation.status != "PENDING":
            raise ValueError(
                f"Recommendation is already finalized with status: '{recommendation.status}'. "
                "Only PENDING recommendations can be reviewed."
            )

        action_upper = action.upper().strip()
        if action_upper not in ["APPROVED", "REJECTED"]:
            raise ValueError("Review action must be either 'APPROVED' or 'REJECTED'")

        now = datetime.now(timezone.utc)
        recommendation.status = action_upper
        recommendation.reviewed_by_user_id = reviewer_user.id
        recommendation.review_notes = notes.strip() if notes else f"Human reviewer {reviewer_user.full_name} applied {action_upper}."
        recommendation.reviewed_at = now

        # Update linked dispute if present
        if recommendation.dispute:
            if action_upper == "APPROVED":
                recommendation.dispute.status = "RESOLVED_APPROVED"
                # If transaction linked, set to DISPUTED (never auto-refund)
                if recommendation.dispute.transaction:
                    recommendation.dispute.transaction.status = "DISPUTED"
            else:
                recommendation.dispute.status = "RESOLVED_REJECTED"

        log_audit_event(
            db=db,
            action=f"RECOMMENDATION_{action_upper}",
            entity_type="recommendation",
            entity_id=str(recommendation.id),
            user_id=reviewer_user.id,
            details={
                "recommendation_id": recommendation.id,
                "action": action_upper,
                "suggested_action": recommendation.suggested_action,
                "review_notes": recommendation.review_notes,
                "reviewer_name": reviewer_user.full_name,
                "reviewer_role": reviewer_user.role.value,
            }
        )

        db.commit()
        db.refresh(recommendation)
        logger.info(
            f"Recommendation {recommendation.id} was {action_upper} by {reviewer_user.email}"
        )
        return recommendation


recommendation_engine = AutonomousRecommendationEngine()
