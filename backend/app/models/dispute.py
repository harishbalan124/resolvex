from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.transaction import Transaction
    from app.models.complaint import Complaint
    from app.models.recommendation import Recommendation


class Dispute(Base, TimestampMixin):
    __tablename__ = "disputes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    dispute_reference: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    transaction_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    complaint_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("complaints.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="DETECTED", nullable=False, index=True
    )  # DETECTED, UNDER_REVIEW, ACTION_RECOMMENDED, RESOLVED_APPROVED, RESOLVED_REJECTED
    rule_triggered: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="disputes")
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="disputes")
    complaint: Mapped[Optional["Complaint"]] = relationship("Complaint", back_populates="disputes")
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="dispute", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Dispute(id={self.id}, ref='{self.dispute_reference}', status='{self.status}')>"
