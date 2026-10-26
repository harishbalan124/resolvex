from datetime import datetime, timedelta, timezone
from decimal import Decimal
import secrets
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.customer import Customer
from app.models.dispute import Dispute
from app.models.transaction import Transaction
from app.services.audit_service import log_audit_event


class DisputeDetectionEngine:
    """
    Explainable Rule-Based Dispute Detection Engine.
    Strictly complies with Non-Negotiable Rule 2:
    - Never labels anything 'confirmed fraud'.
    - Generates explainable, deterministic rule triggers.
    - Never auto-refunds or moves money without human approval.
    """

    DUPLICATE_WINDOW_MINUTES = 10
    VELOCITY_WINDOW_MINUTES = 5
    VELOCITY_THRESHOLD_COUNT = 3
    AMOUNT_DEVIATION_MULTIPLIER = 3.0

    @classmethod
    def generate_dispute_reference(cls) -> str:
        year = datetime.now(timezone.utc).year
        suffix = secrets.token_hex(3).upper()
        return f"DSP-{year}-{suffix}"

    def evaluate_transaction(
        self,
        db: Session,
        transaction: Transaction,
        complaint_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Optional[Dispute]:
        """
        Evaluate a single transaction against explainable anomaly rules.
        If a rule matches, creates and records a Dispute.
        """
        # Avoid duplicate dispute evaluation for the same transaction
        existing_dispute = db.query(Dispute).filter(Dispute.transaction_id == transaction.id).first()
        if existing_dispute:
            return existing_dispute

        rule_triggered, reason, risk_score = self._check_rules(db, transaction)
        if not rule_triggered:
            return None

        dispute_ref = self.generate_dispute_reference()
        dispute = Dispute(
            dispute_reference=dispute_ref,
            transaction_id=transaction.id,
            customer_id=transaction.customer_id,
            complaint_id=complaint_id,
            reason=reason,
            status="DETECTED",
            rule_triggered=rule_triggered,
            risk_score=risk_score,
        )
        db.add(dispute)
        db.flush()

        # Update transaction status to FLAGGED
        transaction.status = "FLAGGED"

        # Log audit trail
        log_audit_event(
            db=db,
            action="DISPUTE_DETECTED",
            entity_type="dispute",
            entity_id=str(dispute.id),
            user_id=user_id,
            details={
                "dispute_reference": dispute_ref,
                "transaction_id": transaction.id,
                "rule_triggered": rule_triggered,
                "risk_score": risk_score,
                "reason": reason,
            }
        )

        logger.info(
            f"Dispute {dispute_ref} created for Txn {transaction.id} | Rule: {rule_triggered} | Score: {risk_score}"
        )

        return dispute

    def _check_rules(self, db: Session, transaction: Transaction) -> Tuple[Optional[str], Optional[str], float]:
        """Evaluate deterministic rules in order of precedence."""
        # Rule 1: Duplicate Charge in Window
        duplicate_match = self._check_duplicate_charge(db, transaction)
        if duplicate_match:
            return (
                "DUPLICATE_CHARGE_WINDOW",
                (
                    f"Identical charge of ${transaction.amount} at '{transaction.merchant}' "
                    f"detected within {self.DUPLICATE_WINDOW_MINUTES} minutes of transaction {duplicate_match.external_txn_id}."
                ),
                0.85,
            )

        # Rule 2: Rapid Velocity Spike
        velocity_count = self._check_rapid_velocity(db, transaction)
        if velocity_count >= self.VELOCITY_THRESHOLD_COUNT:
            return (
                "RAPID_VELOCITY",
                (
                    f"High transaction frequency detected: {velocity_count} charges executed "
                    f"within {self.VELOCITY_WINDOW_MINUTES} minutes."
                ),
                0.78,
            )

        # Rule 3: Unusual Amount Deviation
        is_deviant, avg_amt, multiplier = self._check_amount_deviation(db, transaction)
        if is_deviant:
            return (
                "UNUSUAL_AMOUNT_DEVIATION",
                (
                    f"Transaction amount of ${transaction.amount} exceeds customer baseline average "
                    f"(${avg_amt:.2f}) by {multiplier:.1f}x (threshold: {self.AMOUNT_DEVIATION_MULTIPLIER}x)."
                ),
                0.72,
            )

        return None, None, 0.0

    def _check_duplicate_charge(self, db: Session, txn: Transaction) -> Optional[Transaction]:
        """Check for identical amount + merchant for the same customer within 10-minute window."""
        window_start = txn.txn_timestamp - timedelta(minutes=self.DUPLICATE_WINDOW_MINUTES)
        window_end = txn.txn_timestamp + timedelta(minutes=self.DUPLICATE_WINDOW_MINUTES)

        potential_dup = (
            db.query(Transaction)
            .filter(
                Transaction.customer_id == txn.customer_id,
                Transaction.merchant == txn.merchant,
                Transaction.amount == txn.amount,
                Transaction.id != txn.id,
                Transaction.txn_timestamp >= window_start,
                Transaction.txn_timestamp <= window_end,
            )
            .first()
        )
        return potential_dup

    def _check_rapid_velocity(self, db: Session, txn: Transaction) -> int:
        """Check number of transactions executed within 5-minute rolling window."""
        window_start = txn.txn_timestamp - timedelta(minutes=self.VELOCITY_WINDOW_MINUTES)
        window_end = txn.txn_timestamp + timedelta(minutes=self.VELOCITY_WINDOW_MINUTES)

        count = (
            db.query(Transaction)
            .filter(
                Transaction.customer_id == txn.customer_id,
                Transaction.txn_timestamp >= window_start,
                Transaction.txn_timestamp <= window_end,
            )
            .count()
        )
        return count

    def _check_amount_deviation(self, db: Session, txn: Transaction) -> Tuple[bool, float, float]:
        """Check if amount exceeds 3x customer historical average."""
        prior_txns = (
            db.query(Transaction)
            .filter(
                Transaction.customer_id == txn.customer_id,
                Transaction.id != txn.id,
            )
            .all()
        )

        if len(prior_txns) < 2:
            return False, 0.0, 0.0

        total = sum((t.amount for t in prior_txns), Decimal("0.0"))
        avg_amount = float(total / len(prior_txns))
        if avg_amount <= 0.0:
            return False, 0.0, 0.0

        current_amount = float(txn.amount)
        multiplier = current_amount / avg_amount
        if multiplier >= self.AMOUNT_DEVIATION_MULTIPLIER and current_amount >= 100.0:
            return True, avg_amount, multiplier

        return False, avg_amount, multiplier

    def scan_unflagged_transactions(self, db: Session, limit: int = 100) -> List[Dispute]:
        """Batch scan completed transactions that have not yet been evaluated for disputes."""
        unflagged = (
            db.query(Transaction)
            .filter(Transaction.status == "COMPLETED")
            .order_by(Transaction.txn_timestamp.desc())
            .limit(limit)
            .all()
        )

        new_disputes = []
        for txn in unflagged:
            dispute = self.evaluate_transaction(db, txn)
            if dispute:
                new_disputes.append(dispute)

        db.commit()
        return new_disputes


dispute_engine = DisputeDetectionEngine()
