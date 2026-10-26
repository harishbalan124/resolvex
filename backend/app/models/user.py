import enum
from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.complaint import Complaint
    from app.models.interaction import Interaction
    from app.models.recommendation import Recommendation
    from app.models.audit_log import AuditLog


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    SUPPORT_AGENT = "SUPPORT_AGENT"
    ANALYST = "ANALYST"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", native_enum=False),
        default=UserRole.SUPPORT_AGENT,
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    assigned_complaints: Mapped[List["Complaint"]] = relationship(
        "Complaint", back_populates="assigned_user", foreign_keys="Complaint.assigned_user_id"
    )
    handled_interactions: Mapped[List["Interaction"]] = relationship(
        "Interaction", back_populates="user", foreign_keys="Interaction.user_id"
    )
    reviewed_recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="reviewed_by_user", foreign_keys="Recommendation.reviewed_by_user_id"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", foreign_keys="AuditLog.user_id"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
