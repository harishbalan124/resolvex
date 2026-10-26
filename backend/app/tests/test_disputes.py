from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from app.models.customer import Customer
from app.models.dispute import Dispute
from app.models.transaction import Transaction
from app.services.dispute_engine import dispute_engine


@pytest.fixture
def sample_customer(db_session):
    customer = Customer(
        external_id="CUST-DSP-01",
        name="Dispute Test User",
        email="dispute.test@example.com",
        tier="Standard",
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


def test_duplicate_charge_window_rule(db_session, sample_customer, admin_user):
    now = datetime.now(timezone.utc)

    # First transaction
    txn1 = Transaction(
        customer_id=sample_customer.id,
        external_txn_id="TXN-DUP-001",
        amount=Decimal("89.50"),
        merchant="Streaming Service Pro",
        category="Subscription",
        txn_timestamp=now,
        status="COMPLETED",
    )
    db_session.add(txn1)
    db_session.commit()

    # Second transaction: same merchant, same amount, 3 minutes later
    txn2 = Transaction(
        customer_id=sample_customer.id,
        external_txn_id="TXN-DUP-002",
        amount=Decimal("89.50"),
        merchant="Streaming Service Pro",
        category="Subscription",
        txn_timestamp=now + timedelta(minutes=3),
        status="COMPLETED",
    )
    db_session.add(txn2)
    db_session.commit()

    dispute = dispute_engine.evaluate_transaction(db_session, txn2, user_id=admin_user.id)
    assert dispute is not None
    assert dispute.rule_triggered == "DUPLICATE_CHARGE_WINDOW"
    assert dispute.status == "DETECTED"
    assert dispute.risk_score >= 0.80
    assert "Streaming Service Pro" in dispute.reason
    assert txn2.status == "FLAGGED"
    # Verify non-negotiable rule: never labeled "confirmed fraud"
    assert "confirmed fraud" not in dispute.reason.lower()


def test_no_dispute_if_outside_duplicate_window(db_session, sample_customer):
    now = datetime.now(timezone.utc)

    # First transaction
    txn1 = Transaction(
        customer_id=sample_customer.id,
        external_txn_id="TXN-NO-DUP-01",
        amount=Decimal("50.00"),
        merchant="Metro Supermarket",
        category="Groceries",
        txn_timestamp=now,
        status="COMPLETED",
    )
    db_session.add(txn1)
    db_session.commit()

    # Second transaction: same merchant and amount, but 3 days later
    txn2 = Transaction(
        customer_id=sample_customer.id,
        external_txn_id="TXN-NO-DUP-02",
        amount=Decimal("50.00"),
        merchant="Metro Supermarket",
        category="Groceries",
        txn_timestamp=now + timedelta(days=3),
        status="COMPLETED",
    )
    db_session.add(txn2)
    db_session.commit()

    dispute = dispute_engine.evaluate_transaction(db_session, txn2)
    assert dispute is None
    assert txn2.status == "COMPLETED"


def test_rapid_velocity_rule(db_session, sample_customer):
    now = datetime.now(timezone.utc)

    # Create 3 transactions in 2 minutes
    txns = []
    for i in range(3):
        t = Transaction(
            customer_id=sample_customer.id,
            external_txn_id=f"TXN-VEL-{i+1}",
            amount=Decimal(f"{25.00 + i}"),
            merchant=f"Merchant-{i+1}",
            category="Retail",
            txn_timestamp=now + timedelta(seconds=30 * i),
            status="COMPLETED",
        )
        db_session.add(t)
        txns.append(t)
    db_session.commit()

    # Evaluating the third transaction should trigger velocity anomaly
    dispute = dispute_engine.evaluate_transaction(db_session, txns[2])
    assert dispute is not None
    assert dispute.rule_triggered == "RAPID_VELOCITY"
    assert dispute.risk_score >= 0.70


def test_unusual_amount_deviation_rule(db_session, sample_customer):
    now = datetime.now(timezone.utc)

    # Historical average: $40.00 (two transactions: $30 and $50)
    t1 = Transaction(
        customer_id=sample_customer.id,
        external_txn_id="TXN-HIST-01",
        amount=Decimal("30.00"),
        merchant="Coffee Roasters",
        category="Food",
        txn_timestamp=now - timedelta(days=10),
        status="COMPLETED",
    )
    t2 = Transaction(
        customer_id=sample_customer.id,
        external_txn_id="TXN-HIST-02",
        amount=Decimal("50.00"),
        merchant="Books & Media",
        category="Retail",
        txn_timestamp=now - timedelta(days=5),
        status="COMPLETED",
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    # Sudden high transaction: $450.00 (>11x average)
    deviant_txn = Transaction(
        customer_id=sample_customer.id,
        external_txn_id="TXN-SPIKE-01",
        amount=Decimal("450.00"),
        merchant="Luxury Electronics Store",
        category="Electronics",
        txn_timestamp=now,
        status="COMPLETED",
    )
    db_session.add(deviant_txn)
    db_session.commit()

    dispute = dispute_engine.evaluate_transaction(db_session, deviant_txn)
    assert dispute is not None
    assert dispute.rule_triggered == "UNUSUAL_AMOUNT_DEVIATION"
    assert "exceeds customer baseline" in dispute.reason
