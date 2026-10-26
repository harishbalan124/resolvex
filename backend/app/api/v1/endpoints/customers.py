from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db, require_roles
from app.models.customer import Customer
from app.models.user import User, UserRole
from app.schemas.customer import CustomerCreate, CustomerDetailResponse, CustomerResponse

router = APIRouter()

READ_ROLES = [UserRole.ADMIN, UserRole.SUPPORT_AGENT, UserRole.ANALYST]
WRITE_ROLES = [UserRole.ADMIN, UserRole.SUPPORT_AGENT]


@router.get("/", response_model=List[CustomerResponse])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tier: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """List customer records with search and tier filters."""
    query = db.query(Customer)
    if tier:
        query = query.filter(Customer.tier == tier)
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Customer.name.ilike(search_filter),
                Customer.external_id.ilike(search_filter),
                Customer.email.ilike(search_filter),
            )
        )
    return query.order_by(Customer.id.asc()).offset(skip).limit(limit).all()


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(WRITE_ROLES)),
):
    """Create a new customer profile."""
    existing = db.query(Customer).filter(
        or_(
            Customer.email == customer_in.email.lower().strip(),
            Customer.external_id == customer_in.external_id.strip()
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email or external ID already exists",
        )

    customer = Customer(
        external_id=customer_in.external_id.strip(),
        name=customer_in.name.strip(),
        email=customer_in.email.lower().strip(),
        phone=customer_in.phone.strip() if customer_in.phone else None,
        tier=customer_in.tier,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
def get_customer_detail(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    """Get customer record by ID with linked relation counters."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    return CustomerDetailResponse(
        id=customer.id,
        external_id=customer.external_id,
        name=customer.name,
        email=customer.email,
        phone=customer.phone,
        tier=customer.tier,
        churn_risk_score=customer.churn_risk_score,
        sentiment_score=customer.sentiment_score,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        transactions_count=len(customer.transactions),
        interactions_count=len(customer.interactions),
        complaints_count=len(customer.complaints),
        disputes_count=len(customer.disputes),
    )
