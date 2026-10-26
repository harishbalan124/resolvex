#!/usr/bin/env python3
"""
ResolveX Synthetic Data Generator & Seeder
Generates realistic enterprise CX intelligence datasets:
  - data/sentiment.csv (Customer interaction texts with labeled sentiments)
  - data/churn.csv (Customer demographics, dispute frequency, and churn outcomes)
Optionally seeds the SQLite/PostgreSQL database with customers, interactions, and transactions.
"""
import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import os
import random
import sys
import pandas as pd
import numpy as np

# Ensure backend app is on path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal, Base, engine
from app.models import Customer, Interaction, Transaction, Complaint, ComplaintStatusHistory


NEGATIVE_PHRASES = [
    "I was charged twice for transaction {txn_id} on my statement and nobody has refunded me yet.",
    "Unacceptable duplicate debit of ${amount}. This is the second time your billing system made this mistake.",
    "I demand an immediate reversal of this unauthorized transaction at {merchant}.",
    "Terrible customer service. I waited on hold for 45 minutes and was hung up on regarding my disputed charge.",
    "Your service outage caused significant downtime for our business operations today.",
    "Why was my card billed ${amount} when I explicitly canceled my subscription last month?",
    "I see fraudulent activity on my account for merchant {merchant}. Please block and investigate.",
    "Your dispute process is completely opaque. I haven't received an update in three weeks.",
    "Hidden fees on my invoice! I was promised a monthly rate of $50 but was billed ${amount}.",
    "Extremely dissatisfied with how my complaint was handled. I am strongly considering closing my account.",
    "The transaction amount does not match the merchant receipt. I was overcharged by ${amount}.",
    "My card was charged multiple times in rapid succession while I was traveling abroad."
]

NEUTRAL_PHRASES = [
    "Could you provide a detailed breakdown of the transaction fees on statement {txn_id}?",
    "How do I update my primary billing address and contact phone number on file?",
    "Inquiring about the standard processing time for wire transfers to international banks.",
    "Please send me the official tax invoices for the first quarter of 2026.",
    "Can you clarify the eligibility requirements for upgrading to the Gold customer tier?",
    "What are the daily withdrawal limits on standard business checking accounts?",
    "I would like to verify if transaction {txn_id} has settled or is still in pending status.",
    "Need instructions on enabling two-factor authentication for my team members.",
    "Confirming receipt of the dispute documentation I uploaded yesterday.",
    "Could you re-send the monthly account statement for September in PDF format?"
]

POSITIVE_PHRASES = [
    "Thank you for the prompt reversal of the disputed charge. Exceptional support!",
    "The support agent resolved my billing issue in less than five minutes. Very impressed.",
    "Great service! The explanation of the dispute investigation was clear, concise, and helpful.",
    "I truly appreciate your representative following up personally to confirm my account security.",
    "Quickest resolution I have ever experienced with a corporate dispute. Keep up the great work!",
    "The new transaction alerts helped me spot an erroneous charge immediately. Excellent feature.",
    "Kudos to the CX team for resolving my complaint ahead of the promised SLA deadline.",
    "Customer service was professional, empathetic, and resolved my inquiry on the first contact."
]

MERCHANTS = [
    "CloudTech Solutions", "AWS Infrastructure", "FastDelivery Logistics", 
    "Metro Transit", "Fintech Payment Gateway", "SaaS Software Corp", 
    "Global Air Lines", "Urban Retailers", "Enterprise Office Supplies", "Prime Stream Media"
]

CHANNELS = ["email", "chat", "phone", "portal"]


def generate_sentiment_data(num_samples: int = 1200) -> pd.DataFrame:
    """Generate balanced synthetic interaction sentiment dataset."""
    random.seed(42)
    np.random.seed(42)
    records = []

    per_category = num_samples // 3

    # Negative records
    for i in range(per_category):
        template = random.choice(NEGATIVE_PHRASES)
        text = template.format(
            txn_id=f"TXN-{random.randint(100000, 999999)}",
            amount=f"{random.uniform(15.0, 950.0):.2f}",
            merchant=random.choice(MERCHANTS)
        )
        records.append({
            "id": f"SENT-{len(records)+1:05d}",
            "text": text,
            "channel": random.choice(CHANNELS),
            "sentiment": "negative",
        })

    # Neutral records
    for i in range(per_category):
        template = random.choice(NEUTRAL_PHRASES)
        text = template.format(
            txn_id=f"TXN-{random.randint(100000, 999999)}",
            merchant=random.choice(MERCHANTS)
        )
        records.append({
            "id": f"SENT-{len(records)+1:05d}",
            "text": text,
            "channel": random.choice(CHANNELS),
            "sentiment": "neutral",
        })

    # Positive records
    for i in range(per_category):
        template = random.choice(POSITIVE_PHRASES)
        text = template.format(
            txn_id=f"TXN-{random.randint(100000, 999999)}",
            merchant=random.choice(MERCHANTS)
        )
        records.append({
            "id": f"SENT-{len(records)+1:05d}",
            "text": text,
            "channel": random.choice(CHANNELS),
            "sentiment": "positive",
        })

    random.shuffle(records)
    df = pd.DataFrame(records)
    output_path = os.path.join(DATA_DIR, "sentiment.csv")
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} sentiment records -> {output_path}")
    return df


def generate_churn_data(num_customers: int = 1500) -> pd.DataFrame:
    """Generate realistic synthetic customer churn dataset with correlated dispute & complaint drivers."""
    random.seed(42)
    np.random.seed(42)

    data = []
    tiers = ["Standard", "Silver", "Gold", "Platinum"]
    contracts = ["Month-to-Month", "One-Year", "Two-Year"]
    payment_methods = ["Credit Card", "Bank Transfer", "Electronic Check"]

    for i in range(1, num_customers + 1):
        customer_id = f"CUST-{10000 + i}"
        tenure_months = int(np.random.gamma(shape=2.5, scale=10.0)) + 1
        tenure_months = min(max(tenure_months, 1), 72)

        contract = np.random.choice(contracts, p=[0.55, 0.30, 0.15])
        tier = np.random.choice(tiers, p=[0.50, 0.25, 0.15, 0.10])
        payment_method = np.random.choice(payment_methods, p=[0.45, 0.35, 0.20])

        monthly_charges = round(float(np.random.uniform(25.0, 220.0)), 2)
        total_charges = round(monthly_charges * tenure_months * float(np.random.uniform(0.95, 1.05)), 2)

        # Complaints & disputes correlate with tenure and risk
        complaints_lambda = 0.8 if contract != "Month-to-Month" else 1.8
        num_complaints = int(np.random.poisson(lam=complaints_lambda))
        num_complaints = min(num_complaints, 10)

        disputes_lambda = 0.3 if num_complaints < 2 else 1.2
        num_disputes = int(np.random.poisson(lam=disputes_lambda))
        num_disputes = min(num_disputes, 8)

        # Average sentiment from interactions (-1.0 negative to +1.0 positive)
        sentiment_baseline = 0.5 - (num_complaints * 0.15) - (num_disputes * 0.1)
        avg_sentiment = float(np.clip(sentiment_baseline + np.random.normal(0, 0.2), -1.0, 1.0))

        support_interactions = num_complaints * 2 + int(np.random.poisson(lam=2.0))

        # Calculate churn probability based on explainable factors
        risk_score = 0.10
        if contract == "Month-to-Month":
            risk_score += 0.25
        if tenure_months < 12:
            risk_score += 0.20
        elif tenure_months > 36:
            risk_score -= 0.15
        
        risk_score += (num_complaints * 0.08)
        risk_score += (num_disputes * 0.07)
        if avg_sentiment < -0.2:
            risk_score += 0.20
        elif avg_sentiment > 0.4:
            risk_score -= 0.15

        churn_prob = float(np.clip(risk_score, 0.02, 0.95))
        churned = int(np.random.rand() < churn_prob)

        data.append({
            "customer_id": customer_id,
            "tenure_months": tenure_months,
            "monthly_charges": monthly_charges,
            "total_charges": total_charges,
            "contract_type": contract,
            "payment_method": payment_method,
            "tier": tier,
            "num_complaints": num_complaints,
            "num_disputes": num_disputes,
            "avg_sentiment_score": round(avg_sentiment, 3),
            "support_interactions_count": support_interactions,
            "churned": churned,
        })

    df = pd.DataFrame(data)
    output_path = os.path.join(DATA_DIR, "churn.csv")
    df.to_csv(output_path, index=False)
    churn_rate = (df['churned'].mean()) * 100
    print(f"Generated {len(df)} churn records (overall churn rate: {churn_rate:.1f}%) -> {output_path}")
    return df


def seed_database(num_customers: int = 50):
    """Seed initial customers, interactions, and transactions into the database."""
    print("\nSeeding initial records into database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing_customers = db.query(Customer).count()
        if existing_customers > 0:
            print(f"Database already contains {existing_customers} customer records. Skipping re-seed.")
            return

        now = datetime.now(timezone.utc)
        created_count = 0

        for i in range(1, num_customers + 1):
            ext_id = f"CUST-{10000 + i}"
            customer = Customer(
                external_id=ext_id,
                name=f"Customer {ext_id}",
                email=f"customer.{ext_id.lower()}@example.corp",
                phone=f"+1-555-01{i:02d}",
                tier=random.choice(["Standard", "Silver", "Gold", "Platinum"]),
                churn_risk_score=None,  # Unscored until LexIntel AI evaluates
                sentiment_score=None,
            )
            db.add(customer)
            db.flush()

            # Seed 2-5 transactions per customer
            for t in range(random.randint(2, 5)):
                txn = Transaction(
                    customer_id=customer.id,
                    external_txn_id=f"TXN-{random.randint(100000, 999999)}",
                    amount=Decimal(f"{random.uniform(19.99, 499.00):.2f}"),
                    currency="USD",
                    merchant=random.choice(MERCHANTS),
                    category=random.choice(["Software", "Logistics", "Office Supplies", "Subscription", "Travel"]),
                    txn_timestamp=now - timedelta(days=random.randint(1, 90)),
                    status="COMPLETED",
                )
                db.add(txn)

            # Seed 1-3 interactions per customer
            for n in range(random.randint(1, 3)):
                interaction = Interaction(
                    customer_id=customer.id,
                    channel=random.choice(CHANNELS),
                    direction=random.choice(["inbound", "outbound"]),
                    subject="Account & Billing Inquiry",
                    content=random.choice(NEGATIVE_PHRASES + NEUTRAL_PHRASES + POSITIVE_PHRASES).format(
                        txn_id=f"TXN-{random.randint(100000, 999999)}",
                        amount=f"{random.uniform(20.0, 300.0):.2f}",
                        merchant=random.choice(MERCHANTS)
                    ),
                    sentiment=None,  # Unscored until LexIntel AI runs
                    sentiment_confidence=None,
                    created_at=now - timedelta(days=random.randint(0, 30)),
                )
                db.add(interaction)

            created_count += 1

        db.commit()
        print(f"[SUCCESS] Successfully seeded {created_count} customers with transactions and interactions.")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="ResolveX Synthetic Data Generator")
    parser.add_argument("--sentiment-samples", type=int, default=1200, help="Number of sentiment samples")
    parser.add_argument("--churn-samples", type=int, default=1500, help="Number of churn samples")
    parser.add_argument("--seed-db", action="store_true", help="Seed database with synthetic customers and transactions")

    args = parser.parse_args()
    print("=== ResolveX / LexIntel AI Synthetic Data Generation ===")
    generate_sentiment_data(args.sentiment_samples)
    generate_churn_data(args.churn_samples)

    if args.seed_db:
        seed_database(50)
    print("Done.\n")


if __name__ == "__main__":
    main()
