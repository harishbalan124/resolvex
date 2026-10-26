from datetime import datetime, timezone
from decimal import Decimal
from fastapi import status
import pytest
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.dispute import Dispute
from app.models.recommendation import Recommendation
from app.models.transaction import Transaction
from app.services.recommendation_engine import recommendation_engine


@pytest.fixture
def dispute_fixture(db_session, admin_user):
    customer = Customer(
        external_id="CUST-REC-01",
        name="Recommendation Test Customer",
        email="rec.test@example.com",
    )
    db_session.add(customer)
    db_session.flush()

    txn = Transaction(
        customer_id=customer.id,
        external_txn_id="TXN-REC-01",
        amount=Decimal("120.00"),
        merchant="SaaS Cloud",
        category="Software",
        txn_timestamp=datetime.now(timezone.utc),
        status="FLAGGED",
    )
    db_session.add(txn)
    db_session.flush()

    dispute = Dispute(
        dispute_reference="DSP-2026-TEST",
        transaction_id=txn.id,
        customer_id=customer.id,
        reason="Duplicate transaction match within 10-minute window",
        status="DETECTED",
        rule_triggered="DUPLICATE_CHARGE_WINDOW",
        risk_score=0.85,
    )
    db_session.add(dispute)
    db_session.commit()
    db_session.refresh(dispute)
    return dispute


def test_recommendation_generation_strictly_pending(db_session, dispute_fixture, admin_user):
    rec = recommendation_engine.generate_recommendation_for_dispute(
        db=db_session,
        dispute=dispute_fixture,
        user_id=admin_user.id,
    )
    db_session.commit()

    assert rec.id is not None
    assert rec.dispute_id == dispute_fixture.id
    assert rec.suggested_action == "PARTIAL_CREDIT"
    assert rec.confidence_score >= 0.90
    # Strictly PENDING until human review (Non-Negotiable Rule 2)
    assert rec.status == "PENDING"
    assert rec.reviewed_by_user_id is None
    assert rec.reviewed_at is None
    assert dispute_fixture.status == "ACTION_RECOMMENDED"


def test_human_approval_workflow(db_session, dispute_fixture, support_agent_user):
    rec = recommendation_engine.generate_recommendation_for_dispute(
        db=db_session,
        dispute=dispute_fixture,
    )
    db_session.commit()

    # Support Agent executes human approval
    reviewed = recommendation_engine.review_recommendation(
        db=db_session,
        recommendation_id=rec.id,
        reviewer_user=support_agent_user,
        action="APPROVED",
        notes="Verified identical timestamp with billing log. Approved credit recommendation.",
    )

    assert reviewed.status == "APPROVED"
    assert reviewed.reviewed_by_user_id == support_agent_user.id
    assert reviewed.reviewed_at is not None
    assert "Verified identical" in reviewed.review_notes
    assert dispute_fixture.status == "RESOLVED_APPROVED"
    # Never auto-refunds or moves money; transaction marked DISPUTED
    assert dispute_fixture.transaction.status == "DISPUTED"

    # Verify audit trail
    audit = (
        db_session.query(AuditLog)
        .filter(AuditLog.action == "RECOMMENDATION_APPROVED")
        .first()
    )
    assert audit is not None
    assert audit.user_id == support_agent_user.id


def test_human_rejection_workflow(db_session, dispute_fixture, admin_user):
    rec = recommendation_engine.generate_recommendation_for_dispute(
        db=db_session,
        dispute=dispute_fixture,
    )
    db_session.commit()

    reviewed = recommendation_engine.review_recommendation(
        db=db_session,
        recommendation_id=rec.id,
        reviewer_user=admin_user,
        action="REJECTED",
        notes="Customer confirmed they made two separate purchases intentionally.",
    )

    assert reviewed.status == "REJECTED"
    assert reviewed.reviewed_by_user_id == admin_user.id
    assert dispute_fixture.status == "RESOLVED_REJECTED"


def test_cannot_review_already_finalized_recommendation(db_session, dispute_fixture, admin_user):
    rec = recommendation_engine.generate_recommendation_for_dispute(
        db=db_session,
        dispute=dispute_fixture,
    )
    db_session.commit()

    # First review
    recommendation_engine.review_recommendation(
        db=db_session,
        recommendation_id=rec.id,
        reviewer_user=admin_user,
        action="APPROVED",
    )

    # Second review should fail
    with pytest.raises(ValueError) as exc:
        recommendation_engine.review_recommendation(
            db=db_session,
            recommendation_id=rec.id,
            reviewer_user=admin_user,
            action="REJECTED",
        )
    assert "already finalized" in str(exc.value)


def test_recommendation_api_and_rbac(client, dispute_fixture, support_token_headers, analyst_token_headers):
    # 1. Generate recommendation via API
    res_gen = client.post(
        f"/api/v1/recommendations/generate-for-dispute/{dispute_fixture.id}",
        headers=support_token_headers
    )
    assert res_gen.status_code == status.HTTP_200_OK
    rec_data = res_gen.json()
    assert rec_data["status"] == "PENDING"
    rec_id = rec_data["id"]

    # 2. Analyst attempts to review (Must be forbidden: Analyst is read-only)
    res_analyst = client.post(
        f"/api/v1/recommendations/{rec_id}/review",
        json={"action": "APPROVED", "notes": "Analyst approval attempt"},
        headers=analyst_token_headers
    )
    assert res_analyst.status_code == status.HTTP_403_FORBIDDEN

    # 3. Support Agent executes valid approval
    res_agent = client.post(
        f"/api/v1/recommendations/{rec_id}/review",
        json={"action": "APPROVED", "notes": "Legitimate agent review approval"},
        headers=support_token_headers
    )
    assert res_agent.status_code == status.HTTP_200_OK
    approved_data = res_agent.json()
    assert approved_data["status"] == "APPROVED"
