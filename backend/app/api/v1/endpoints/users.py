from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_roles
from app.core.logging import logger
from app.core.security import get_password_hash
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    role: Optional[UserRole] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles([UserRole.ADMIN])),
):
    """List system users (Admin only)."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles([UserRole.ADMIN])),
):
    """Create a new user with assigned role (Admin only)."""
    normalized_email = user_in.email.lower().strip()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
    
    new_user = User(
        email=normalized_email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name.strip(),
        role=user_in.role,
        is_active=user_in.is_active,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    client_ip = request.client.host if request.client else "unknown"
    audit = AuditLog(
        user_id=current_admin.id,
        action="USER_CREATED",
        entity_type="user",
        entity_id=str(new_user.id),
        details=f"Admin {current_admin.id} created user {new_user.id} with role {new_user.role.value}",
        ip_address=client_ip,
    )
    db.add(audit)
    db.commit()

    logger.info(f"Admin {current_admin.id} created user {new_user.id} ({new_user.role.value})")
    return new_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles([UserRole.ADMIN])),
):
    """Retrieve user details by ID (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles([UserRole.ADMIN])),
):
    """Update user role, active status, or details (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    update_data = user_update.model_dump(exclude_unset=True)
    if "email" in update_data and update_data["email"]:
        new_email = update_data["email"].lower().strip()
        existing = db.query(User).filter(User.email == new_email, User.id != user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already used by another account"
            )
        user.email = new_email
    
    if "full_name" in update_data and update_data["full_name"]:
        user.full_name = update_data["full_name"].strip()
    
    if "role" in update_data and update_data["role"]:
        user.role = update_data["role"]

    if "is_active" in update_data and update_data["is_active"] is not None:
        user.is_active = update_data["is_active"]

    if "password" in update_data and update_data["password"]:
        user.hashed_password = get_password_hash(update_data["password"])

    db.commit()
    db.refresh(user)

    client_ip = request.client.host if request.client else "unknown"
    audit = AuditLog(
        user_id=current_admin.id,
        action="USER_UPDATED",
        entity_type="user",
        entity_id=str(user.id),
        details=f"Admin {current_admin.id} updated user {user.id}",
        ip_address=client_ip,
    )
    db.add(audit)
    db.commit()

    return user
