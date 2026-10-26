from datetime import datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError
from app.models import (
    AuditLog,
    Complaint,
    ComplaintStatusHistory,
    Customer,
    Dispute,
    Interaction,
    Prediction,
    Recommendation,
    Transaction,
    User,
    UserRole,
)


def test_customer_model_and_relations(db_session, admin_user):
    customer = Customer(
        external_id="CUST-1001",
        name="Acme Corp",
        email="contact@acme.corp",
        phone="+1-555-0199",
        tier="Gold",
        churn_risk_score=0.15,
        sentiment_score=0.82,
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    assert customer.id is not None
    assert customer.external_id == "CUST-1001"
    assert customer.tier == "Gold"

    # Interaction
    interaction = Interaction(
        customer_id=customer.id,
        channel="email",
        direction="inbound",
        subject="Invoice inquiry",
        content="Could you clarify the transaction charge from yesterday?",
        sentiment="neutral",
        sentiment_confidence=0.91,
        user_id=admin_user.id,
    )
    db_session.add(interaction)

    # Complaint
    complaint = Complaint(
        ticket_number="CMP-2026-0001",
        customer_id=customer.id,
        assigned_user_id=admin_user.id,
        title="Unrecognized charge",
        description="Customer noticed a fee discrepancy.",
        category="Billing",
        priority="HIGH",
        status="OPEN",
    )
    db_session.add(complaint)
    db_session.commit()
    db_session.refresh(complaint)

    # Complaint Status History
    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        changed_by_user_id=admin_user.id,
        old_status="OPEN",
        new_status="IN_INVESTIGATION",
        comment="Beginning verification of transaction log.",
    )
    db_session.add(history)

    # Transaction
    txn = Transaction(
        customer_id=customer.id,
        external_txn_id="TXN-2026-9901",
        amount=Decimal("149.99"),
        currency="USD",
        merchant="CloudStorage SaaS",
        category="Subscription",
        txn_timestamp=datetime.now(timezone.utc),
        status="FLAGGED",
    )
    db_session.add(txn)
    db_session.commit()
    db_session.refresh(txn)

    # Prediction (LexIntel AI Churn & Sentiment)
    prediction = Prediction(
        customer_id=customer.id,
        model_type="CHURN",
        model_version="v1.0.0",
        prediction_label="Low Risk",
        score=0.15,
        explanation="Tenure: 24mo; Interaction sentiment predominantly positive.",
    )
    db_session.add(prediction)

    # Dispute (Explainable rule-based)
    dispute = Dispute(
        dispute_reference="DSP-2026-0001",
        transaction_id=txn.id,
        customer_id=customer.id,
        complaint_id=complaint.id,
        reason="Duplicate recurring charge detected within 10 minute window",
        status="ACTION_RECOMMENDED",
        rule_triggered="DUPLICATE_CHARGE_WINDOW",
        risk_score=0.88,
    )
    db_session.add(dispute)
    db_session.commit()
    db_session.refresh(dispute)

    # Recommendation (Requires Human Approval)
    recommendation = Recommendation(
        dispute_id=dispute.id,
        complaint_id=complaint.id,
        suggested_action="PARTIAL_CREDIT",
        justification="Automated rule matched duplicate billing event. Human review required before issuance.",
        confidence_score=0.92,
        status="PENDING",
    )
    db_session.add(recommendation)

    # Audit Log
    audit = AuditLog(
        user_id=admin_user.id,
        action="DISPUTE_EVALUATION",
        entity_type="dispute",
        entity_id=str(dispute.id),
        details="Dispute flagged by LexIntel AI rule engine.",
        ip_address="127.0.0.1",
    )
    db_session.add(audit)
    db_session.commit()

    # Verify all entities created
    assert db_session.query(Interaction).count() == 1
    assert db_session.query(Complaint).count() == 1
    assert db_session.query(ComplaintStatusHistory).count() == 1
    assert db_session.query(Transaction).count() == 1
    assert db_session.query(Prediction).count() == 1
    assert db_session.query(Dispute).count() == 1
    assert db_session.query(Recommendation).count() == 1
    assert db_session.query(AuditLog).count() == 1

    # Verify relationships
    assert dispute.transaction.external_txn_id == "TXN-2026-9901"
    assert dispute.recommendations[0].suggested_action == "PARTIAL_CREDIT"
    assert dispute.recommendations[0].status == "PENDING"  # Must remain pending for human


def test_unique_constraints(db_session):
    c1 = Customer(external_id="CUST-DUP", name="Org A", email="org@a.com")
    db_session.add(c1)
    db_session.commit()

    # Duplicate external_id
    c2 = Customer(external_id="CUST-DUP", name="Org B", email="org@b.com")
    db_session.add(c2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Duplicate email
    c3 = Customer(external_id="CUST-DIFF", name="Org C", email="org@a.com")
    db_session.add(c3)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
