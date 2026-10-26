from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.dispute import Dispute
    from app.models.complaint import Complaint
    from app.models.user import User


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    dispute_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("disputes.id", ondelete="CASCADE"), nullable=True, index=True
    )
    complaint_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=True, index=True
    )
    suggested_action: Mapped[str] = mapped_column(String(100), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", nullable=False, index=True
    )  # PENDING, APPROVED, REJECTED (Enforces mandatory human in the loop)
    reviewed_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # Relationships
    dispute: Mapped[Optional["Dispute"]] = relationship("Dispute", back_populates="recommendations")
    complaint: Mapped[Optional["Complaint"]] = relationship("Complaint", back_populates="recommendations")
    reviewed_by_user: Mapped[Optional["User"]] = relationship("User", back_populates="reviewed_recommendations")

    def __repr__(self) -> str:
        return f"<Recommendation(id={self.id}, action='{self.suggested_action}', status='{self.status}')>"
