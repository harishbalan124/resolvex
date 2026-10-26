from fastapi import APIRouter
from app.api.v1.endpoints import (
    analytics,
    audit_logs,
    auth,
    complaints,
    customers,
    disputes,
    interactions,
    recommendations,
    transactions,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users (Admin)"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["LexIntel AI Analytics"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(complaints.router, prefix="/complaints", tags=["Complaints"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(disputes.router, prefix="/disputes", tags=["Disputes"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Autonomous Recommendations"])
api_router.include_router(interactions.router, prefix="/interactions", tags=["Interactions"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
