from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db, require_roles
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.user import User, UserRole
from app.schemas.dispute import DisputeResponse
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.dispute_engine import dispute_engine

router = APIRouter()

READ_ROLES = [UserRole.ADMIN, UserRole.SUPPORT_AGENT, UserRole.ANALYST]
WRITE_ROLES = [UserRole.ADMIN, UserRole.SUPPORT_AGENT]


@router.get("/", response_model=List[TransactionResponse])
def list_transactions(
    customer_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """List customer transactions with customer and status filtering."""
    query = db.query(Transaction)
    if customer_id:
        query = query.filter(Transaction.customer_id == customer_id)
    if status_filter:
        query = query.filter(Transaction.status == status_filter)

    return query.order_by(Transaction.txn_timestamp.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    txn_in: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(WRITE_ROLES)),
):
    """Record a transaction in the system."""
    customer = db.query(Customer).filter(Customer.id == txn_in.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {txn_in.customer_id} does not exist",
        )

    txn = Transaction(
        customer_id=txn_in.customer_id,
        external_txn_id=txn_in.external_txn_id.strip(),
        amount=txn_in.amount,
        currency=txn_in.currency.upper().strip(),
        merchant=txn_in.merchant.strip(),
        category=txn_in.category.strip(),
        txn_timestamp=txn_in.txn_timestamp,
        status=txn_in.status.upper().strip(),
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


@router.post("/{transaction_id}/scan-dispute", response_model=Optional[DisputeResponse])
def scan_single_transaction_for_dispute(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(WRITE_ROLES)),
):
    """Run explainable dispute rule evaluation on a specific transaction."""
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    dispute = dispute_engine.evaluate_transaction(db, txn, user_id=current_user.id)
    db.commit()
    if dispute:
        db.refresh(dispute)
    return dispute
