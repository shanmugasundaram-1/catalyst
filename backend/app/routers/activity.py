from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import ActivityLog
from app.schemas import ActivityLogResponse, CurrentUser

router = APIRouter(prefix="/api/activity", tags=["Transparency & Activity Log"])

@router.get("", response_model=List[ActivityLogResponse])
def get_activity_log(
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logs = db.query(ActivityLog).filter(
        ActivityLog.profile_id == current_user.profile_id
    ).order_by(ActivityLog.created_at.desc()).limit(limit).all()
    return logs
